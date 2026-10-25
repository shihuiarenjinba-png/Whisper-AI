from pathlib import Path
import json
import tempfile
import unittest

from whisper_local.preferences import load_preferences, save_preferences


class PreferenceTests(unittest.TestCase):
    def test_allowlist_and_no_url_or_consent_persistence(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "settings.json"
            self.assertTrue(save_preferences({
                "model": "C:/Models/ggml-base.bin", "locale": "en",
                "youtube_url": "https://www.youtube.com/watch?v=private",
                "permission_confirmed": "true", "audio": "secret.wav",
            }, path))
            data = load_preferences(path)
            self.assertEqual(data, {"model": "C:/Models/ggml-base.bin", "locale": "en"})
            raw = path.read_text(encoding="utf-8")
            self.assertNotIn("private", raw)
            self.assertNotIn("secret", raw)

    def test_bad_or_missing_preferences_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "settings.json"
            self.assertEqual(load_preferences(path), {})
            path.write_text("{bad json", encoding="utf-8")
            self.assertEqual(load_preferences(path), {})
            path.write_text(json.dumps({"locale": "fr", "audio_language": "xx", "output": "a"}), encoding="utf-8")
            self.assertEqual(load_preferences(path), {"output": "a"})

    def test_saving_requires_writable_directory(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "not-a-folder"
            path.write_text("blocking", encoding="utf-8")
            self.assertFalse(save_preferences({"locale": "ja"}, path / "settings.json"))


if __name__ == "__main__":
    unittest.main()
