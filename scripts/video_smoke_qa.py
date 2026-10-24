"""Local media-pipeline QA with a generated speech MP4 and simulated ASR.

Run: python scripts/video_smoke_qa.py
Requires local FFmpeg and (for voiced English demo) espeak. No network/API.
This does NOT test recognition accuracy; it tests actual MP4 audio demux and the
full file-to-TXT/SRT pipeline with a deterministic fake whisper CLI.
"""
from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import wave
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from whisper_local.core import TranscriptionJob, run_process, transcribe  # noqa: E402


def main():
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("SKIP: ffmpeg is not installed")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        voice = root / "speech.wav"
        if shutil.which("espeak"):
            subprocess.run(["espeak", "-s", "125", "-w", str(voice),
                            "This is a local audio and video transcription test."], check=True)
        else:
            import math, struct
            # Synthetic tone for machines without speech synthesis; valid MP4 nevertheless.
            with wave.open(str(voice), "wb") as f:
                f.setnchannels(1);f.setsampwidth(2);f.setframerate(16000)
                f.writeframes(b"".join(struct.pack("<h", int(8000*math.sin(2*math.pi*440*i/16000))) for i in range(16000*2)))
        video = root / "public_domain_generated_QA.mp4"
        subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                        "-f", "lavfi", "-i", "color=c=royalblue:s=640x360:r=15",
                        "-i", str(voice), "-shortest", "-c:v", "mpeg4", "-q:v", "5",
                        "-c:a", "aac", "-pix_fmt", "yuv420p", str(video)], check=True)
        model = root / "dummy-model.bin";model.write_bytes(b"test model not real inference")
        outputs = root / "outputs";outputs.mkdir()
        whisper_fake = root / "fake_whisper.py";whisper_fake.write_text("# only a test double",encoding="utf-8")
        stages = []
        def runner(command, cancel, cwd=None):
            if "-c:a" in command:
                run_process(command, cancel, cwd=cwd)
                wav = Path(command[-1])
                with wave.open(str(wav), "rb") as audio:
                    assert audio.getframerate() == 16000 and audio.getnchannels() == 1
                    assert audio.getnframes() > 16000
            else:
                output = Path(command[command.index("-of")+1])
                output.with_suffix(".txt").write_text("FAKE ASR: Audio extracted from an actual MP4.", encoding="utf-8")
                output.with_suffix(".srt").write_text(
                    "1\n00:00:00,000 --> 00:00:03,000\nFAKE ASR: Test output.\n", encoding="utf-8")
        with patch("whisper_local.core.run_process", side_effect=runner):
            txt,srt=transcribe(TranscriptionJob(video, model, str(whisper_fake),
                                                ffmpeg, outputs, "en"), on_stage=stages.append)
        assert txt.exists() and srt.exists()
        assert stages == ["converting","transcribing","saving"]
        print("PASS: actual MP4 -> real FFmpeg PCM WAV -> mocked ASR -> TXT/SRT; no external API")
        print("Note: Whisper recognition accuracy NOT verified")
        demo=Path(os.environ.get("QA_DEMO_DEST", ""))
        if str(demo) != "." and os.environ.get("QA_DEMO_DEST"):
            shutil.copyfile(video, demo)
            print(f"QA clip: {demo}")

if __name__ == "__main__":
    main()
