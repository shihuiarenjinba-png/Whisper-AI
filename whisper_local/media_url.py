"""Opt-in, rights-gated YouTube import for offline transcription.

This module does NOT use any AI API. Network access occurs only after an
explicit user action and a statement that downloading is authorized by both
YouTube's terms and relevant rights holders. No DRM/cookies/auth bypass.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import tempfile
import threading
from typing import Callable
from urllib.parse import parse_qs, urlsplit

from .core import (
    OperationCancelled, TranscriptionError, TranscriptionJob,
    SUPPORTED_EXTENSIONS, _resolve_program, run_process, transcribe,
)

_VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_MAX_BYTES = 200 * 1024 * 1024


def normalize_youtube_url(url: str) -> str:
    """Restrict to a single public YouTube video; never accept arbitrary hosts."""
    try:
        parts = urlsplit(url.strip())
        host = (parts.hostname or "").lower().rstrip(".")
        port = parts.port
    except ValueError as exc:
        raise TranscriptionError("YouTube URL が不正です / Invalid YouTube URL") from exc
    if (parts.scheme != "https" or parts.username or parts.password or
        port not in (None, 443) or host not in {
            "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtu.be"
        }):
        raise TranscriptionError("HTTPSのYouTube動画URLのみ対応 / Only HTTPS YouTube video URLs are supported")
    if host.endswith("youtu.be"):
        video_id = parts.path.strip("/")
    elif parts.path == "/watch":
        video_ids = parse_qs(parts.query).get("v", [])
        video_id = video_ids[0] if len(video_ids) == 1 else ""
    else:
        match = re.fullmatch(r"/(?:shorts|live)/([A-Za-z0-9_-]{11})/?", parts.path)
        video_id = match.group(1) if match else ""
    if not _VIDEO_ID.fullmatch(video_id):
        raise TranscriptionError("単一動画のURLを指定してください / Please provide a single video URL")
    return f"https://www.youtube.com/watch?v={video_id}"


@dataclass(frozen=True)
class YouTubeJob:
    url: str
    model: Path
    whisper_cli: str
    ffmpeg: str
    yt_dlp: str
    output_directory: Path
    language: str = "auto"
    permission_confirmed: bool = False


def transcribe_youtube(
    job: YouTubeJob,
    cancel: threading.Event | None = None,
    on_stage: Callable[[str], None] | None = None,
) -> tuple[Path, Path]:
    """Import one permitted video, then reuse the existing offline pipeline.

    Limits: 20-minute video metadata, 200-MiB downloaded media. Metadata can
    be inaccurate; avoid use with untrusted, very large media. Downloaded media
    is held only in a temporary folder and removed on cancellation/error.
    """
    if not job.permission_confirmed:
        raise TranscriptionError("ダウンロード権限と利用規約の確認が必要です / Confirm permission and service terms first")
    url = normalize_youtube_url(job.url)
    cancel = cancel or threading.Event()
    on_stage = on_stage or (lambda _stage: None)
    if cancel.is_set():
        raise OperationCancelled("キャンセルしました / Cancelled")
    # Check local prerequisites before attempting any online access.
    output = job.output_directory.expanduser().resolve()
    if not output.is_dir():
        raise TranscriptionError("保存先フォルダが見つかりません / Output directory not found")
    if job.language not in ("auto", "ja", "en"):
        raise TranscriptionError("未対応の言語設定 / Unsupported language")
    if not job.model.is_file() or job.model.suffix.lower() != ".bin":
        raise TranscriptionError("GGMLモデル(.bin)を指定してください / Select a GGML model")
    _resolve_program(job.whisper_cli, "whisper-cli")
    _resolve_program(job.ffmpeg, "ffmpeg")
    downloader = _resolve_program(job.yt_dlp, "yt-dlp")

    with tempfile.TemporaryDirectory(prefix="whisper_youtube_", dir=output) as folder:
        temp = Path(folder)
        on_stage("downloading")
        run_process([
            downloader, "--ignore-config", "--no-playlist", "--no-overwrites",
            "--no-continue", "--no-part", "--no-cache-dir", "--no-mtime",
            "--no-write-subs", "--no-write-auto-subs", "--no-write-info-json",
            "--socket-timeout", "20", "--retries", "2", "--max-filesize", "200M",
            "--match-filter", "duration <= 1200", "-f", "bestaudio/best",
            "--output", str(temp / "youtube_audio.%(ext)s"), "--", url,
        ], cancel)
        if cancel.is_set():
            raise OperationCancelled("キャンセルしました / Cancelled")
        files = [p for p in temp.iterdir() if p.is_file() and p.name.startswith("youtube_audio.")]
        if len(files) != 1:
            raise TranscriptionError("動画の取得に失敗しました / Video download produced no usable file")
        audio = files[0]
        if audio.suffix.lower() not in SUPPORTED_EXTENSIONS or audio.stat().st_size > _MAX_BYTES:
            raise TranscriptionError("取得形式・容量が未対応です / Downloaded media is unsupported or too large")
        local_job = TranscriptionJob(
            audio=audio, model=job.model, whisper_cli=job.whisper_cli,
            ffmpeg=job.ffmpeg, output_directory=output, language=job.language,
        )
        return transcribe(local_job, cancel=cancel, on_stage=on_stage)
