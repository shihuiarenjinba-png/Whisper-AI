"""Safe, local-only preferences: no video URLs, audio paths or rights consent."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

ALLOWED = frozenset({"locale", "audio_language", "model", "cli", "ffmpeg", "ytdlp", "output"})


def preference_path() -> Path:
    root = os.environ.get("LOCALAPPDATA") if os.name == "nt" else None
    if root:
        return Path(root) / "LocalSpeechStudio" / "preferences.json"
    return Path.home() / ".config" / "LocalSpeechStudio" / "preferences.json"


def _sanitize(data: object) -> dict[str, str]:
    if not isinstance(data, dict):
        return {}
    values = {key: value for key, value in data.items()
              if key in ALLOWED and isinstance(value, str) and len(value) <= 4096}
    if values.get("locale") not in (None, "ja", "en"):
        values.pop("locale", None)
    if values.get("audio_language") not in (None, "auto", "ja", "en"):
        values.pop("audio_language", None)
    return values


def load_preferences(path: Path | None = None) -> dict[str, str]:
    target = path if path is not None else preference_path()
    try:
        if target.stat().st_size > 16384:
            return {}
        return _sanitize(json.loads(target.read_text(encoding="utf-8")))
    except (OSError, ValueError, UnicodeError):
        return {}


def save_preferences(data: dict[str, str], path: Path | None = None) -> bool:
    target = path if path is not None else preference_path()
    scratch: Path | None = None
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=target.parent,
                                         prefix=".preferences-", suffix=".tmp", delete=False) as stream:
            scratch = Path(stream.name)
            json.dump(_sanitize(data), stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        scratch.replace(target)
        return True
    except (OSError, ValueError):
        return False
    finally:
        if scratch is not None:
            scratch.unlink(missing_ok=True)
