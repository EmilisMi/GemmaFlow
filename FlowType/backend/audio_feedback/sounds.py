"""
FlowType — Audio Feedback
Plays subtle start/stop/done sound effects using numpy + sounddevice.
All sounds are generated programmatically — no external audio files required.
"""

import threading
import numpy as np
import sounddevice as sd


SAMPLE_RATE = 44100


def _play_async(audio: np.ndarray) -> None:
    """Play a numpy audio array in a background thread."""
    def _play():
        try:
            sd.play(audio, samplerate=SAMPLE_RATE, blocking=True)
        except Exception as e:
            print(f"[sounds] Playback error: {e}", flush=True)

    threading.Thread(target=_play, daemon=True).start()


def _generate_tone(
    freq: float,
    duration: float,
    volume: float = 0.3,
    fade_ms: float = 20.0,
) -> np.ndarray:
    """Generate a sine wave tone with fade-in/out to avoid clicking."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    wave = volume * np.sin(2 * np.pi * freq * t).astype(np.float32)

    # Apply fade-in and fade-out to prevent clicks
    fade_samples = int(SAMPLE_RATE * fade_ms / 1000)
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)
    wave[:fade_samples] *= fade_in
    wave[-fade_samples:] *= fade_out

    return wave


def _generate_chime(
    freqs: list[float],
    duration: float,
    volume: float = 0.25,
) -> np.ndarray:
    """Generate a multi-frequency chord chime."""
    combined = np.zeros(int(SAMPLE_RATE * duration), dtype=np.float32)
    for freq in freqs:
        combined += _generate_tone(freq, duration, volume / len(freqs))
    return combined


def play_start() -> None:
    """
    Play a subtle rising two-tone chime — signals recording started.
    C5 → E5 quick sequence.
    """
    c5 = _generate_tone(523.25, 0.08, volume=0.2)
    e5 = _generate_tone(659.25, 0.10, volume=0.25)
    audio = np.concatenate([c5, e5])
    _play_async(audio)


def play_stop() -> None:
    """
    Play a subtle falling two-tone chime — signals recording stopped.
    E5 → C5 quick sequence.
    """
    e5 = _generate_tone(659.25, 0.08, volume=0.25)
    c5 = _generate_tone(523.25, 0.10, volume=0.18)
    audio = np.concatenate([e5, c5])
    _play_async(audio)


def play_done() -> None:
    """
    Play a soft three-note ascending chime — signals transcription complete.
    C5 → E5 → G5 chord-like.
    """
    c5 = _generate_tone(523.25, 0.07, volume=0.18)
    e5 = _generate_tone(659.25, 0.07, volume=0.18)
    g5 = _generate_tone(783.99, 0.12, volume=0.22)
    audio = np.concatenate([c5, e5, g5])
    _play_async(audio)


def play_error() -> None:
    """Play a low flat tone — signals an error."""
    audio = _generate_tone(220.0, 0.15, volume=0.2)
    _play_async(audio)
