"""
FlowType — Global Hotkey Manager
Registers and manages system-wide hotkeys using the `keyboard` library.
Supports Toggle mode and Push-to-talk mode.
"""

import sys
import threading
import time
from typing import Callable, Optional
import keyboard


def _log(*args):
    print(*args, file=sys.stderr, flush=True)


class HotkeyManager:
    """
    Manages a single configurable global hotkey with two activation modes:
    
    - "toggle":        Press once → start; press again → stop.
    - "push_to_talk":  Hold → record; release → stop.
    """

    def __init__(
        self,
        on_start: Callable[[], None],
        on_stop: Callable[[], None],
    ):
        self._on_start = on_start
        self._on_stop = on_stop
        self._hotkey: Optional[str] = None
        self._mode: str = "toggle"
        self._is_recording = False
        self._lock = threading.Lock()
        self._hook_id = None
        self._ptt_pressed = False

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def register(self, hotkey: str, mode: str = "toggle") -> None:
        """Register (or re-register) the global hotkey."""
        self.unregister()

        self._hotkey = hotkey
        self._mode = mode
        self._is_recording = False
        self._ptt_pressed = False

        if mode == "toggle":
            self._hook_id = keyboard.add_hotkey(
                hotkey,
                self._on_toggle_press,
                suppress=False,
            )
        elif mode == "push_to_talk":
            # For PTT we use raw key events to detect press and release
            keyboard.hook(self._on_key_event)

        _log(f"[hotkeys] Registered '{hotkey}' in '{mode}' mode.")

    def unregister(self) -> None:
        """Remove the currently registered hotkey."""
        try:
            if self._hotkey and self._mode == "toggle" and self._hook_id is not None:
                keyboard.remove_hotkey(self._hook_id)
            elif self._mode == "push_to_talk":
                keyboard.unhook(self._on_key_event)
        except Exception:
            pass
        finally:
            self._hook_id = None
            self._hotkey = None

    def shutdown(self) -> None:
        """Clean up all hooks."""
        try:
            keyboard.unhook_all()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    #  Internal handlers                                                   #
    # ------------------------------------------------------------------ #

    def _on_toggle_press(self) -> None:
        with self._lock:
            if not self._is_recording:
                self._is_recording = True
                self._fire_start()
            else:
                self._is_recording = False
                self._fire_stop()

    def _on_key_event(self, event: keyboard.KeyboardEvent) -> None:
        """Handle raw keyboard events for push-to-talk."""
        if self._hotkey is None:
            return

        # Check if the event key matches our hotkey combination
        hotkey_keys = set(self._hotkey.lower().replace(" ", "").split("+"))
        event_key = event.name.lower() if event.name else ""

        # Simple matching: check if the triggering key is the last key in the combo
        # keyboard library handles modifier state internally
        if event_key not in hotkey_keys and event.scan_code != 57:  # 57 = space
            return

        if event.event_type == keyboard.KEY_DOWN and not self._ptt_pressed:
            # Check all modifier keys are held
            try:
                if keyboard.is_pressed(self._hotkey):
                    self._ptt_pressed = True
                    with self._lock:
                        self._is_recording = True
                    self._fire_start()
            except Exception:
                pass

        elif event.event_type == keyboard.KEY_UP and self._ptt_pressed:
            # Stop when any key in the combo is released
            try:
                if not keyboard.is_pressed(self._hotkey):
                    self._ptt_pressed = False
                    with self._lock:
                        self._is_recording = False
                    self._fire_stop()
            except Exception:
                pass

    def _fire_start(self) -> None:
        threading.Thread(target=self._on_start, daemon=True).start()

    def _fire_stop(self) -> None:
        threading.Thread(target=self._on_stop, daemon=True).start()
