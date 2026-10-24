from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from whisper_local.core import (
    OperationCancelled, TranscriptionError, TranscriptionJob,
    next_output_base, run_process, transcribe, validate,
)


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.audio = self.root / "音声;安全.mp3"
        self.audio.write_bytes(b"placeholder input")
        self.model = self.root / "ggml-small.bin"
        self.model.write_bytes(b"placeholder model")
        self.cli = self.root / "whisper-cli.exe"
        self.cli.write_bytes(b"fake")
        self.ffmpeg = self.root / "ffmpeg.exe"
        self.ffmpeg.write_bytes(b"fake")
        self.out = self.root / "exports"
        self.out.mkdir()
        self.job = TranscriptionJob(self.audio, self.model, str(self.cli), str(self.ffmpeg), self.out, "ja")

    def test_validation_and_language(self):
        c, f, audio, model, dest = validate(self.job)
        self.assertEqual(Path(c), self.cli)
        self.assertEqual(Path(f), self.ffmpeg)
        self.assertEqual(audio, self.audio)
        self.assertEqual(dest, self.out)
        with self.assertRaises(TranscriptionError):
            validate(TranscriptionJob(self.audio, self.model, str(self.cli), str(self.ffmpeg), self.out, "zz"))

    def test_missing_model(self):
        job = TranscriptionJob(self.audio, self.root / "missing.bin", str(self.cli), str(self.ffmpeg), self.out)
        with self.assertRaisesRegex(TranscriptionError, "GGML"):
            validate(job)

    def test_invalid_input(self):
        text_file = self.root / "note.txt"
        text_file.write_text("hello", encoding="utf-8")
        with self.assertRaises(TranscriptionError):
            validate(TranscriptionJob(text_file, self.model, str(self.cli), str(self.ffmpeg), self.out))

    def test_unique_outputs(self):
        first = next_output_base(self.out, "recording")
        first.with_suffix(".srt").write_text("x")
        self.assertEqual(next_output_base(self.out, "recording").name, "recording_2")
        self.assertEqual(next_output_base(self.out, "bad:name").name, "bad_name")

    def test_success_without_any_network_and_no_overwrite(self):
        stages = []
        def fake_run(cmd, cancel, cwd=None):
            if "-c:a" in cmd:
                Path(cmd[-1]).write_bytes(b"WAV")
            else:
                base = Path(cmd[cmd.index("-of") + 1])
                base.with_suffix(".txt").write_text("こんにちは", encoding="utf-8")
                base.with_suffix(".srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nこんにちは\n", encoding="utf-8")
        with patch("whisper_local.core.run_process", side_effect=fake_run) as run:
            txt, srt = transcribe(self.job, on_stage=stages.append)
            self.assertEqual(txt.read_text(encoding="utf-8"), "こんにちは")
            self.assertIn("こんにちは", srt.read_text(encoding="utf-8"))
            self.assertEqual(stages, ["converting", "transcribing", "saving"])
            self.assertEqual(run.call_count, 2)
            self.assertEqual(run.call_args_list[0].args[0][0], str(self.ffmpeg))
            self.assertEqual(run.call_args_list[1].args[0][0], str(self.cli))
            self.assertEqual(run.call_args_list[1].args[0][-2], "-of")
            txt2, srt2 = transcribe(self.job)
            self.assertNotEqual(txt, txt2)
            self.assertNotEqual(srt, srt2)
            self.assertTrue(txt.is_file() and txt2.is_file())

    def test_failure_does_not_leave_partial_results(self):
        def fake_run(cmd, cancel, cwd=None):
            if "-c:a" in cmd:
                Path(cmd[-1]).write_bytes(b"WAV")
            else:
                base = Path(cmd[cmd.index("-of") + 1])
                base.with_suffix(".txt").write_text("partial", encoding="utf-8")
        with patch("whisper_local.core.run_process", side_effect=fake_run):
            with self.assertRaisesRegex(TranscriptionError, "SRT"):
                transcribe(self.job)
        self.assertFalse(list(self.out.glob("*.txt")))
        self.assertFalse(list(self.out.glob("*.srt")))
        self.assertFalse(list(self.out.glob("whisper_local_*")))

    def test_cancelled_before_launch(self):
        e = threading.Event()
        e.set()
        with self.assertRaises(OperationCancelled):
            transcribe(self.job, cancel=e)

    def test_shell_free_command_and_nonzero_exit(self):
        import sys
        cancel = threading.Event()
        with self.assertRaisesRegex(TranscriptionError, "終了コード 4"):
            run_process([sys.executable, "-c", "import sys; sys.exit(4)"], cancel)

    def test_cancel_long_process(self):
        import sys
        cancel = threading.Event()
        def later():
            import time
            time.sleep(0.3)
            cancel.set()
        t = threading.Thread(target=later)
        t.start()
        try:
            with self.assertRaises(OperationCancelled):
                run_process([sys.executable, "-c", "import time; time.sleep(20)"], cancel)
        finally:
            t.join()


if __name__ == "__main__":
    unittest.main()
