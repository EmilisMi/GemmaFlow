"""
FlowType — Backend Entry Point
JSON-Lines IPC loop. Electron spawns this process and communicates
via stdin (commands) and stdout (events).

Protocol: one JSON object per line, newline-terminated.

IMPORTANT: Only emit() writes to stdout. All debug/log output uses
           log() which writes to stderr so Electron's JSON parser
           never sees non-JSON lines.
"""

import sys
import json
import threading
import time
import os
import signal
from typing import Any, Optional

# Ensure backend package is importable
sys.path.insert(0, os.path.dirname(__file__))

from config.settings import load_settings, save_settings, update_setting
from audio.recorder import AudioRecorder
from audio.devices import list_input_devices, get_default_input_index
from transcription.engine import WhisperEngine
from transcription.model_manager import list_models
from hotkeys.manager import HotkeyManager
from paste.injector import PasteInjector
from audio_feedback import sounds


# ------------------------------------------------------------------ #
#  IPC helpers                                                         #
# ------------------------------------------------------------------ #

def log(*args) -> None:
    """Write debug output to stderr — never pollutes the JSON IPC channel."""
    print(*args, file=sys.stderr, flush=True)


def emit(event: str, **kwargs: Any) -> None:
    """Send a JSON event to Electron (stdout)."""
    payload = {"event": event, **kwargs}
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


def emit_error(message: str) -> None:
    log(f"[error] {message}")
    emit("error", message=message)


# ------------------------------------------------------------------ #
#  Application State                                                   #
# ------------------------------------------------------------------ #

class FlowTypeApp:
    def __init__(self):
        self.settings = load_settings()
        self.recorder = AudioRecorder(on_level=self._on_audio_level)
        self.whisper = WhisperEngine()
        self.injector = PasteInjector(
            paste_delay_ms=self.settings.get("paste_delay_ms", 150)
        )
        self.hotkeys = HotkeyManager(
            on_start=self._on_record_start,
            on_stop=self._on_record_stop,
        )
        self._shutdown_event = threading.Event()

    def start(self) -> None:
        """Initialize subsystems and start the IPC read loop."""
        # Pre-load the whisper model in background
        self.whisper.ensure_loaded(
            self.settings.get("model", "base"),
            self.settings.get("compute_type", "int8"),
        )

        # Register hotkey
        self.hotkeys.register(
            self.settings.get("hotkey", "ctrl+space"),
            self.settings.get("mode", "toggle"),
        )

        log("[app] Backend ready.")
        emit("ready", settings=self.settings)
        self._ipc_loop()

    # ---------------------------------------------------------------- #
    #  Recording callbacks (called from hotkey thread)                  #
    # ---------------------------------------------------------------- #

    def _on_record_start(self) -> None:
        try:
            if self.settings.get("audio_feedback", True):
                sounds.play_start()

            device_index = self.settings.get("device_index", None)
            self.recorder.start(device_index=device_index)
            log("[app] Recording started.")
            emit("recording_started")
        except Exception as e:
            emit_error(f"Failed to start recording: {e}")

    def _on_record_stop(self) -> None:
        try:
            if self.settings.get("audio_feedback", True):
                sounds.play_stop()

            audio_path = self.recorder.stop()
            log("[app] Recording stopped.")
            emit("recording_stopped")

            if not audio_path:
                emit_error("No audio captured.")
                return

            emit("transcription_started")

            def _on_transcription_done(text: str) -> None:
                self.recorder.cleanup(audio_path)

                log(f"[app] Transcription result: '{text[:60]}'")
                if not text:
                    emit_error("Transcription returned empty result.")
                    return

                if self.settings.get("audio_feedback", True):
                    sounds.play_done()

                emit("transcription_done", text=text)

                # Paste into active window
                success = self.injector.paste(text)
                if not success:
                    emit_error("Paste failed.")

            model = self.settings.get("model", "base")
            language = self.settings.get("language", None)
            compute_type = self.settings.get("compute_type", "int8")

            log("[app] Transcription started.")
            self.whisper.transcribe(
                audio_path,
                model_name=model,
                language=language,
                compute_type=compute_type,
                on_done=_on_transcription_done,
            )
        except Exception as e:
            emit_error(f"Failed during stop/transcribe: {e}")

    def _on_audio_level(self, level: float) -> None:
        """Called when audio volume level changes."""
        emit("audio_level", level=level)

    # ---------------------------------------------------------------- #
    #  IPC command dispatch                                              #
    # ---------------------------------------------------------------- #

    def _ipc_loop(self) -> None:
        """Read JSON commands from stdin and dispatch them."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                emit_error(f"Invalid JSON: {line!r}")
                continue

            cmd = msg.get("cmd")
            data = msg.get("data", {})

            try:
                log(f"[ipc] cmd={cmd}")
                self._dispatch(cmd, data)
            except Exception as e:
                emit_error(f"Command '{cmd}' failed: {e}")

    def _dispatch(self, cmd: Optional[str], data: dict) -> None:
        if cmd == "start_recording":
            self._on_record_start()

        elif cmd == "stop_recording":
            self._on_record_stop()

        elif cmd == "get_devices":
            devices = list_input_devices()
            default = get_default_input_index()
            emit("devices", devices=devices, default_index=default)

        elif cmd == "get_settings":
            emit("settings", settings=self.settings)

        elif cmd == "save_settings":
            merged = {**self.settings, **data}
            save_settings(merged)
            self.settings = merged

            # Re-register hotkey if it changed
            self.hotkeys.register(
                merged.get("hotkey", "ctrl+space"),
                merged.get("mode", "toggle"),
            )

            # Update paste delay
            self.injector.update_delay(merged.get("paste_delay_ms", 150))

            # Reload model if changed
            if data.get("model") and data["model"] != self.whisper._model_name:
                self.whisper.unload()
                self.whisper.ensure_loaded(
                    merged.get("model", "base"),
                    merged.get("compute_type", "int8"),
                )

            emit("settings_saved", settings=merged)

        elif cmd == "get_models":
            emit("models", models=list_models())

        elif cmd == "quit":
            self._shutdown()

        else:
            emit_error(f"Unknown command: {cmd!r}")

    def _shutdown(self) -> None:
        emit("shutdown")
        self.hotkeys.shutdown()
        self.whisper.shutdown()
        if self.recorder.is_recording:
            self.recorder.stop()
        sys.exit(0)


# ------------------------------------------------------------------ #
#  Entry point                                                         #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    # Ensure stdout is unbuffered (line-buffered mode doesn't work well on Windows)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)

    app = FlowTypeApp()
    try:
        app.start()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        emit_error(f"Fatal error: {e}")
        sys.exit(1)
