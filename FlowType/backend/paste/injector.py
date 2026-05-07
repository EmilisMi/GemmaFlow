"""
FlowType — Paste Injector
Copies transcribed text to the clipboard and simulates Ctrl+V
to paste into the currently focused application.
"""

import sys
import time
import threading
from typing import Optional
import pyperclip
import keyboard


def _log(*args):
    print(*args, file=sys.stderr, flush=True)


class PasteInjector:
    """
    Pastes text into the currently focused window by:
    1. Saving the existing clipboard content
    2. Copying the transcribed text to the clipboard
    3. Simulating Ctrl+V
    4. Restoring the original clipboard after a short delay
    """

    def __init__(self, paste_delay_ms: int = 150):
        self.paste_delay_ms = paste_delay_ms
        self._lock = threading.Lock()

    def paste(self, text: str) -> bool:
        """
        Paste text into the active window.
        Returns True on success, False on failure.
        """
        if not text or not text.strip():
            return False

        with self._lock:
            return self._do_paste(text.strip())

    def _do_paste(self, text: str) -> bool:
        # Save current clipboard
        original_clipboard = self._safe_get_clipboard()

        try:
            # Write our text to clipboard
            pyperclip.copy(text)

            # Brief delay to ensure clipboard is ready
            time.sleep(self.paste_delay_ms / 1000.0)

            # Simulate paste
            keyboard.press_and_release("ctrl+v")

            # Give the app time to receive the paste before we restore clipboard
            time.sleep(0.25)

            return True

        except Exception as e:
            _log(f"[paste] Error during paste: {e}")
            return False

        finally:
            # Restore original clipboard content asynchronously
            if original_clipboard is not None:
                def _restore():
                    time.sleep(0.5)
                    try:
                        pyperclip.copy(original_clipboard)
                    except Exception:
                        pass

                threading.Thread(target=_restore, daemon=True).start()

    def _safe_get_clipboard(self) -> Optional[str]:
        """Get current clipboard content, returning None on failure."""
        try:
            return pyperclip.paste()
        except Exception:
            return None

    def update_delay(self, delay_ms: int) -> None:
        self.paste_delay_ms = max(0, delay_ms)
