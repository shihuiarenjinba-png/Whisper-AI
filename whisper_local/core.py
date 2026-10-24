"""Local-only transcription pipeline using an installed whisper.cpp CLI.

No external AI API, network request, telemetry or automatic model download.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import threading
import time
from typing import Callable

SUPPORTED_EXTENSIONS = frozenset({".wav", ".mp3", ".m4a", ".flac", ".ogg", ".mp4", ".mkv", ".webm", ".aac", ".wma"})
LANGUAGES = ("auto", "ja", "en")


class TranscriptionError(Exception):
    """A recoverable input or processing failure."""


class OperationCancelled(TranscriptionError):
    """The user cancelled the running process."""


@dataclass(frozen=True)
class TranscriptionJob:
    audio: Path
    model: Path
    whisper_cli: str
    ffmpeg: str
    output_directory: Path
    language: str = "auto"


def _resolve_program(program: str, label: str) -> str:
    program = program.strip().strip('"')
    if not program:
        raise TranscriptionError(f"{label} が指定されていません / {label} not specified")
    expanded = Path(os.path.expandvars(os.path.expanduser(program)))
    # A bare executable name may be provided via PATH.
    resolved = shutil.which(program)
    if resolved:
        return str(Path(resolved).resolve())
    if expanded.is_file():
        return str(expanded.resolve())
    raise TranscriptionError(f"{label} が見つかりません / {label} not found: {program}")


def validate(job: TranscriptionJob) -> tuple[str, str, Path, Path, Path]:
    audio = job.audio.expanduser().resolve()
    model = job.model.expanduser().resolve()
    if not audio.is_file():
        raise TranscriptionError("音声・動画ファイルが見つかりません / Input file not found")
    if audio.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise TranscriptionError(f"未対応の形式 / Unsupported input type: {audio.suffix}")
    if not model.is_file() or model.suffix.lower() != ".bin":
        raise TranscriptionError("whisper.cpp対応のGGMLモデル(.bin)を指定してください / Select a GGML .bin model")
    if job.language not in LANGUAGES:
        raise TranscriptionError("未対応の言語設定 / Unsupported language")
    output = job.output_directory.expanduser().resolve()
    if not output.is_dir():
        raise TranscriptionError("保存先フォルダが見つかりません / Output directory not found")
    if not os.access(output, os.W_OK):
        raise TranscriptionError("保存先への書き込み権限がありません / Output directory not writable")
    cli = _resolve_program(job.whisper_cli, "whisper-cli")
    ffmpeg = _resolve_program(job.ffmpeg, "ffmpeg")
    return cli, ffmpeg, audio, model, output


def run_process(command: list[str], cancel: threading.Event, cwd: Path | None = None) -> None:
    """Execute without shell invocation, spool output to a file, and support cancel."""
    if cancel.is_set():
        raise OperationCancelled("キャンセルしました / Cancelled")
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    with tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as log:
        try:
            proc = subprocess.Popen(
                command, cwd=str(cwd) if cwd else None,
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                creationflags=flags, shell=False,
            )
        except OSError as exc:
            raise TranscriptionError(f"処理を起動できません / Failed to start process: {exc}") from exc
        try:
            while proc.poll() is None:
                if cancel.wait(0.15):
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait(timeout=3)
                    raise OperationCancelled("キャンセルしました / Cancelled")
            if cancel.is_set():
                raise OperationCancelled("キャンセルしました / Cancelled")
            if proc.returncode != 0:
                log.seek(0)
                tail = log.read()[-1800:]
                raise TranscriptionError(f"処理が失敗しました (終了コード {proc.returncode}) / Processing failed\n{tail}")
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()


def next_output_base(output_dir: Path, stem: str) -> Path:
    """Never overwrite an existing transcript or subtitle pair."""
    # The input basename is already a legal filename; limit length for Windows.
    clean = "".join(ch if ch not in '<>:"/\\|?*' else "_" for ch in stem).strip(" .")[:90] or "transcript"
    for idx in range(1, 10000):
        filename = clean if idx == 1 else f"{clean}_{idx}"
        candidate = output_dir / filename
        if not candidate.with_suffix(".txt").exists() and not candidate.with_suffix(".srt").exists():
            return candidate
    raise TranscriptionError("出力ファイル名を作成できません / Too many existing outputs")


def transcribe(
    job: TranscriptionJob,
    cancel: threading.Event | None = None,
    on_stage: Callable[[str], None] | None = None,
) -> tuple[Path, Path]:
    """Convert input to PCM WAV then create TXT/SRT locally.

    The selected model is provided by the user. No network access is made.
    Outputs are moved into place only after both generated files exist.
    """
    cancel = cancel or threading.Event()
    on_stage = on_stage or (lambda _stage: None)
    cli, ffmpeg, audio, model, output = validate(job)
    if cancel.is_set():
        raise OperationCancelled("キャンセルしました / Cancelled")
    dest = next_output_base(output, audio.stem)
    # Use the destination drive for temporary files; publishing is an atomic rename on the same drive.
    with tempfile.TemporaryDirectory(prefix="whisper_local_", dir=output) as tmp:
        tmp_path = Path(tmp)
        wav = tmp_path / "input.wav"
        temp_out_base = tmp_path / "result"
        on_stage("converting")
        run_process([
            ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", str(audio),
            "-vn", "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(wav),
        ], cancel)
        if not wav.is_file() or wav.stat().st_size == 0:
            raise TranscriptionError("音声の変換に失敗しました / WAV conversion produced no file")
        on_stage("transcribing")
        run_process([
            cli, "-m", str(model), "-f", str(wav), "-l", job.language,
            "-otxt", "-osrt", "-of", str(temp_out_base),
        ], cancel)
        if cancel.is_set():
            raise OperationCancelled("キャンセルしました / Cancelled")
        txt_src = temp_out_base.with_suffix(".txt")
        srt_src = temp_out_base.with_suffix(".srt")
        if not txt_src.is_file() or not srt_src.is_file():
            raise TranscriptionError("文字起こし出力が不足しています / TXT or SRT output missing")
        on_stage("saving")
        # Recheck for an unexpected file created during transcription.
        dest = next_output_base(output, audio.stem)
        txt_target = dest.with_suffix(".txt")
        srt_target = dest.with_suffix(".srt")
        txt_src.replace(txt_target)
        try:
            srt_src.replace(srt_target)
        except OSError:
            txt_target.unlink(missing_ok=True)
            raise
        return txt_target, srt_target
