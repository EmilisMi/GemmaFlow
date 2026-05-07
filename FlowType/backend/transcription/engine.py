"""
FlowType — Transcription Engine
Wraps faster-whisper for async, non-blocking speech-to-text.
"""

import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Callable
from pathlib import Path


def _log(*args):
    print(*args, file=sys.stderr, flush=True)

from .model_manager import get_model_cache_path, is_model_cached, AVAILABLE_MODELS


class WhisperEngine:
    """
    Lazy-loading faster-whisper transcription engine.
    
    The model is loaded once on first use and kept in memory.
    Transcription runs in a thread pool to avoid blocking the IPC loop.
    """

    def __init__(self):
        self._model = None
        self._model_name: Optional[str] = None
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="whisper")

    def _load_model(self, model_name: str, compute_type: str = "int8") -> None:
        """Load or reload the model. Must be called with self._lock held."""
        from faster_whisper import WhisperModel

        if self._model is not None and self._model_name == model_name:
            return  # Already loaded

        _log(f"[whisper] Loading model '{model_name}' (compute_type={compute_type})...")

        # Use project-local models dir if cached there, otherwise let faster-whisper
        # download to its default HuggingFace cache
        cache_path = get_model_cache_path(model_name)
        if is_model_cached(model_name):
            model_path = str(cache_path)
        else:
            model_path = model_name  # faster-whisper will download from HuggingFace

        self._model = WhisperModel(
            model_path,
            device="cpu",
            compute_type=compute_type,
            download_root=str(cache_path.parent),
            num_workers=1,
        )
        self._model_name = model_name
        _log(f"[whisper] Model '{model_name}' loaded.")

    def ensure_loaded(self, model_name: str, compute_type: str = "int8") -> None:
        """Pre-load the model in the background (call at startup)."""
        def _load():
            with self._lock:
                self._load_model(model_name, compute_type)

        threading.Thread(target=_load, daemon=True, name="whisper-preload").start()

    def transcribe(
        self,
        audio_path: str,
        model_name: str = "base",
        language: Optional[str] = None,
        compute_type: str = "int8",
        on_done: Optional[Callable[[str], None]] = None,
    ) -> "Future":
        """
        Transcribe audio_path asynchronously.
        
        If on_done is provided, it is called with the transcribed text when complete.
        Returns a Future that resolves to the transcribed string.
        """
        future = self._executor.submit(
            self._do_transcribe, audio_path, model_name, language, compute_type, on_done
        )
        return future

    def _do_transcribe(
        self,
        audio_path: str,
        model_name: str,
        language: Optional[str],
        compute_type: str,
        on_done: Optional[Callable[[str], None]],
    ) -> str:
        try:
            with self._lock:
                self._load_model(model_name, compute_type)

            _log(f"[whisper] Transcribing {audio_path}...")

            segments, info = self._model.transcribe(
                audio_path,
                language=language,
                beam_size=1,           # Fastest beam search
                best_of=1,
                temperature=0.0,
                vad_filter=True,       # Skip silence
                vad_parameters={"min_silence_duration_ms": 300},
            )

            text = " ".join(seg.text.strip() for seg in segments).strip()
            _log(f"[whisper] Result: '{text}'")

            if on_done:
                on_done(text)

            return text

        except Exception as e:
            err = f"[whisper] Transcription error: {e}"
            _log(err)
            if on_done:
                on_done("")
            return ""

    def unload(self) -> None:
        """Free the model from memory."""
        with self._lock:
            self._model = None
            self._model_name = None

    def shutdown(self) -> None:
        """Shut down the thread pool."""
        self._executor.shutdown(wait=False)
