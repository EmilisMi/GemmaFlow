"""
FlowType — Audio Recorder
Captures microphone input via sounddevice and saves to a temporary WAV file.
"""

import sys
import threading
import tempfile
import os
import time
from pathlib import Path
from typing import Optional, Callable
import numpy as np
import sounddevice as sd
import soundfile as sf


def _log(*args):
    print(*args, file=sys.stderr, flush=True)


SAMPLE_RATE = 16000   # Whisper natively uses 16kHz
CHANNELS = 1          # Mono is sufficient for speech
DTYPE = "float32"
BLOCK_SIZE = 1024     # Frames per callback


class AudioRecorder:
    """
    Thread-safe audio recorder.
    
    Usage:
        recorder = AudioRecorder()
        recorder.start(device_index=None)
        # ... wait ...
        path = recorder.stop()  # returns path to WAV file
    """

    def __init__(self, on_level: Optional[Callable[[float], None]] = None):
        self._lock = threading.Lock()
        self._frames: list[np.ndarray] = []
        self._stream: Optional[sd.InputStream] = None
        self._recording = False
        self._temp_path: Optional[str] = None
        self._on_level = on_level  # Optional callback for VU meter (0.0–1.0)

    @property
    def is_recording(self) -> bool:
        return self._recording

    def start(self, device_index: Optional[int] = None) -> None:
        """Begin capturing audio from the given device (None = system default)."""
        with self._lock:
            if self._recording:
                return

            self._frames = []
            self._recording = True

            try:
                self._stream = sd.InputStream(
                    device=device_index,
                    samplerate=SAMPLE_RATE,
                    channels=CHANNELS,
                    dtype=DTYPE,
                    blocksize=BLOCK_SIZE,
                    callback=self._audio_callback,
                )
                self._stream.start()
            except Exception as e:
                self._recording = False
                raise RuntimeError(f"Failed to open audio stream: {e}") from e

    def stop(self) -> Optional[str]:
        """
        Stop recording and save audio to a temp WAV file.
        Returns the path to the WAV file, or None if nothing was recorded.
        """
        with self._lock:
            if not self._recording:
                return None

            self._recording = False

            if self._stream is not None:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception:
                    pass
                self._stream = None

            frames = self._frames[:]
            self._frames = []

        if not frames:
            return None

        audio_data = np.concatenate(frames, axis=0)

        # Minimum 0.1s of audio required
        if len(audio_data) < SAMPLE_RATE * 0.1:
            return None

        # Write to temp file
        tmp = tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False, prefix="flowtype_"
        )
        tmp.close()
        self._temp_path = tmp.name

        try:
            sf.write(self._temp_path, audio_data, SAMPLE_RATE)
        except Exception as e:
            os.unlink(self._temp_path)
            self._temp_path = None
            raise RuntimeError(f"Failed to write audio file: {e}") from e

        return self._temp_path

    def cleanup(self, path: Optional[str]) -> None:
        """Delete a temp audio file after transcription."""
        if path and os.path.exists(path):
            try:
                os.unlink(path)
            except OSError:
                pass

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info,
        status,
    ) -> None:
        """sounddevice callback — called on audio thread."""
        if status:
            _log(f"[recorder] Stream status: {status}")

        if self._recording:
            self._frames.append(indata.copy())

            # Emit audio level for VU meter
            if self._on_level is not None:
                rms = float(np.sqrt(np.mean(indata ** 2)))
                level = min(1.0, rms * 10)  # scale to 0–1
                self._on_level(level)
