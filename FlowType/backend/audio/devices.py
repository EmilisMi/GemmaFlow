"""
FlowType — Audio Device Enumerator
Lists available input (microphone) devices via sounddevice.
"""

import sys
import sounddevice as sd
from typing import Optional


def _log(*args):
    print(*args, file=sys.stderr, flush=True)


def list_input_devices() -> list[dict]:
    """
    Return a list of available microphone/input devices.
    Each entry: {"index": int, "name": str, "channels": int, "sample_rate": float}
    """
    devices = []
    try:
        device_list = sd.query_devices()
        for i, dev in enumerate(device_list):
            if dev["max_input_channels"] > 0:
                devices.append({
                    "index": i,
                    "name": dev["name"],
                    "channels": dev["max_input_channels"],
                    "sample_rate": dev["default_samplerate"],
                    "is_default": False,
                })

        # Mark the default input device
        try:
            default_info = sd.query_devices(kind="input")
            default_name = default_info["name"]
            for d in devices:
                if d["name"] == default_name:
                    d["is_default"] = True
                    break
        except Exception:
            pass

    except Exception as e:
        _log(f"[devices] Error querying devices: {e}")

    return devices


def get_default_input_index() -> Optional[int]:
    """Return the index of the system default input device, or None."""
    try:
        default = sd.query_devices(kind="input")
        all_devices = sd.query_devices()
        for i, dev in enumerate(all_devices):
            if dev["name"] == default["name"]:
                return i
    except Exception:
        pass
    return None


def validate_device_index(index: Optional[int]) -> bool:
    """Check that a given device index is a valid input device."""
    if index is None:
        return True
    try:
        dev = sd.query_devices(index)
        return dev["max_input_channels"] > 0
    except Exception:
        return False
