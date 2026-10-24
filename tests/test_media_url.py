"""YouTube URL is opt-in. Tests are fully offline, no unapproved downloads."""
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from whisper_local import TranscriptionError, YouTubeJob, normalize_youtube_url, transcribe_youtube


class YouTubeImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.model = root / "ggml-base.bin"
        self.model.write_bytes(b"test model")
        self.ffmpeg = root / "ffmpeg.exe"
        self.ffmpeg.write_text("fake")
        self.whisper = root / "whisper-cli.exe"
        self.whisper.write_text("fake")
        self.ytdlp = root / "yt-dlp.exe"
        self.ytdlp.write_text("fake")
        self.dest = root / "out"
        self.dest.mkdir()
        self.job = YouTubeJob("https://www.youtube.com/watch?v=dQw4w9WgXcQ", self.model,
                              str(self.whisper), str(self.ffmpeg), str(self.ytdlp),
                              self.dest, "ja", True)

    def test_valid_video_urls_and_canonicalization(self):
        urls = [
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=33",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/shorts/dQw4w9WgXcQ",
            "https://www.youtube.com/live/dQw4w9WgXcQ",
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(normalize_youtube_url(url), "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_invalid_or_unsafe_urls(self):
        urls = [
            "http://youtu.be/dQw4w9WgXcQ", "file:///etc/passwd",
            "https://youtube.com.evil.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/playlist?list=PLsomething",
            "https://user:pass@youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/../../something", "https://youtube.com:444/watch?v=dQw4w9WgXcQ",
            "https://127.0.0.1/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=x&v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&v=another",
        ]
        for url in urls:
            with self.subTest(url=url), self.assertRaises(TranscriptionError):
                normalize_youtube_url(url)

    def test_permission_confirmation_required_without_network_or_processes(self):
        job = YouTubeJob(**{**self.job.__dict__, "permission_confirmed": False})
        with patch("whisper_local.media_url.run_process") as runner:
            with self.assertRaisesRegex(TranscriptionError, "権限"):
                transcribe_youtube(job)
            runner.assert_not_called()

    def test_missing_downloader_rejected_before_any_network(self):
        job = YouTubeJob(**{**self.job.__dict__, "yt_dlp": "does-not-exist-2026"})
        with patch("whisper_local.media_url.run_process") as runner:
            with self.assertRaisesRegex(TranscriptionError, "yt-dlp"):
                transcribe_youtube(job)
            runner.assert_not_called()

    def test_download_and_local_transcription_pipeline(self):
        stages = []
        def runner(cmd, cancel, cwd=None):
            self.assertIn("--ignore-config", cmd)
            self.assertIn("--no-playlist", cmd)
            self.assertIn("--max-filesize", cmd)
            self.assertTrue(cmd[-1].startswith("https://www.youtube.com/watch?v="))
            template = cmd[cmd.index("--output") + 1]
            Path(template.replace("%(ext)s", "webm")).write_bytes(b"simulated audio stream")

        def transcriber(job, cancel=None, on_stage=None):
            self.assertTrue(job.audio.is_file())
            self.assertEqual(job.audio.suffix, ".webm")
            on_stage("converting")
            return (self.dest / "example.txt", self.dest / "example.srt")

        with patch("whisper_local.media_url.run_process", side_effect=runner) as run, \
             patch("whisper_local.media_url.transcribe", side_effect=transcriber):
            result = transcribe_youtube(self.job, on_stage=stages.append)
        self.assertEqual(result[0].name, "example.txt")
        self.assertEqual(stages, ["downloading", "converting"])
        self.assertEqual(run.call_count, 1)
        self.assertEqual(len(list(self.dest.glob("whisper_youtube_*"))), 0)

    def test_empty_and_oversize_downloads_are_rejected(self):
        with patch("whisper_local.media_url.run_process"):
            with self.assertRaisesRegex(TranscriptionError, "no usable file"):
                transcribe_youtube(self.job)
        self.assertFalse(list(self.dest.glob("whisper_youtube_*")))

    def test_pre_cancelled_job_does_not_download(self):
        cancel = threading.Event()
        cancel.set()
        with patch("whisper_local.media_url.run_process") as runner:
            with self.assertRaises(TranscriptionError):
                transcribe_youtube(self.job, cancel=cancel)
            runner.assert_not_called()


if __name__ == "__main__":
    unittest.main()
