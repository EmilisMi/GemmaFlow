"""
FlowType — Settings Manager
Handles reading and writing user configuration to a JSON file.
"""

import sys
import json
import os
from pathlib import Path
from typing import Any


def _log(*args):
    print(*args, file=sys.stderr, flush=True)

# Default configuration
DEFAULT_SETTINGS: dict[str, Any] = {
    "hotkey": "ctrl+space",
    "mode": "toggle",           # "toggle" or "push_to_talk"
    "model": "base",            # "tiny", "base", "small"
    "device_index": None,       # None = system default
    "launch_at_startup": False,
    "paste_delay_ms": 150,
    "audio_feedback": True,
    "indicator_position": {"x": None, "y": None},  # None = auto-center
    "language": None,           # None = auto-detect
    "compute_type": "int8",     # faster-whisper compute type
}

# Config file lives two levels up from this file: project root /config/settings.json
_CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
_CONFIG_PATH = _CONFIG_DIR / "settings.json"


def _ensure_config_dir() -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_settings() -> dict[str, Any]:
    """Load settings from disk, filling in any missing keys with defaults."""
    _ensure_config_dir()
    if not _CONFIG_PATH.exists():
        save_settings(DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)

    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Merge: start with defaults, overlay saved values
        merged = dict(DEFAULT_SETTINGS)
        merged.update(data)
        return merged
    except (json.JSONDecodeError, OSError) as e:
        _log(f"[settings] Failed to load config, using defaults: {e}")
        return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict[str, Any]) -> None:
    """Persist settings to disk."""
    _ensure_config_dir()
    try:
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except OSError as e:
        _log(f"[settings] Failed to save config: {e}")


def update_setting(key: str, value: Any) -> dict[str, Any]:
    """Update a single setting key and save."""
    current = load_settings()
    current[key] = value
    save_settings(current)
    return current


def get_setting(key: str, default: Any = None) -> Any:
    """Get a single setting value."""
    return load_settings().get(key, default)
