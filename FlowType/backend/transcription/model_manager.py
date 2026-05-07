"""
FlowType — Model Manager
Tracks available faster-whisper models and their cache state.
"""

from pathlib import Path
from typing import Optional

# faster-whisper downloads to huggingface cache by default
# We can also specify a custom download dir

AVAILABLE_MODELS = {
    "tiny": {
        "name": "tiny",
        "size_mb": 75,
        "description": "Fastest, lowest accuracy",
        "hf_id": "guillaumekln/faster-whisper-tiny",
    },
    "base": {
        "name": "base",
        "size_mb": 145,
        "description": "Balanced speed and accuracy (recommended)",
        "hf_id": "guillaumekln/faster-whisper-base",
    },
    "small": {
        "name": "small",
        "size_mb": 465,
        "description": "Slower, higher accuracy",
        "hf_id": "guillaumekln/faster-whisper-small",
    },
}

# Custom cache directory inside the project
_MODELS_DIR = Path(__file__).resolve().parents[2] / "models"


def get_models_dir() -> Path:
    _MODELS_DIR.mkdir(parents=True, exist_ok=True)
    return _MODELS_DIR


def get_model_cache_path(model_name: str) -> Path:
    return get_models_dir() / f"faster-whisper-{model_name}"


def is_model_cached(model_name: str) -> bool:
    """Check whether a model has already been downloaded."""
    path = get_model_cache_path(model_name)
    # faster-whisper stores model as a directory with config.json
    return (path / "config.json").exists() or (path / "model.bin").exists()


def list_models() -> list[dict]:
    """Return all models with their cache status."""
    result = []
    for key, info in AVAILABLE_MODELS.items():
        entry = dict(info)
        entry["cached"] = is_model_cached(key)
        entry["cache_path"] = str(get_model_cache_path(key))
        result.append(entry)
    return result


def get_model_info(model_name: str) -> Optional[dict]:
    if model_name not in AVAILABLE_MODELS:
        return None
    info = dict(AVAILABLE_MODELS[model_name])
    info["cached"] = is_model_cached(model_name)
    return info
