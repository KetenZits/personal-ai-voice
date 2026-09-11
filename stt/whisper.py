"""faster-whisper transcription with automatic CUDA-to-CPU recovery."""

from __future__ import annotations

import logging
import math
import time

import numpy as np

from brain.schemas import SpeechResult
from .preprocessing import prepare_for_whisper


class WhisperTranscriber:
    def __init__(self, model_name: str = "small", language: str = "auto", device: str = "auto",
                 compute_type: str = "auto", beam_size: int = 5) -> None:
        self.model_name = model_name
        self.language = None if language == "auto" else language
        self.beam_size = beam_size
        self.log = logging.getLogger(__name__)
        selected = self._select_device(device)
        precision = compute_type if compute_type != "auto" else ("float16" if selected == "cuda" else "int8")
        self.device = selected
        self.model = self._load(selected, precision)

    @staticmethod
    def _select_device(requested: str) -> str:
        if requested != "auto":
            return requested
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"

    def _load(self, device: str, compute_type: str) -> object:
        from faster_whisper import WhisperModel
        try:
            return WhisperModel(self.model_name, device=device, compute_type=compute_type)
        except Exception:
            if device != "cuda":
                raise
            self.log.exception("CUDA Whisper initialization failed; falling back to CPU int8")
            self.device = "cpu"
            return WhisperModel(self.model_name, device="cpu", compute_type="int8")

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> SpeechResult:
        started = time.perf_counter()
        waveform = prepare_for_whisper(audio, sample_rate)
        if waveform.size < 1600:
            return SpeechResult(text="", language=None, confidence=0, duration_seconds=0)
        segments, info = self.model.transcribe(
            waveform, language=self.language, beam_size=self.beam_size,
            vad_filter=True, condition_on_previous_text=False,
        )
        items = list(segments)
        text = " ".join(segment.text.strip() for segment in items).strip()
        if items:
            confidence = sum(math.exp(min(0.0, segment.avg_logprob)) for segment in items) / len(items)
        else:
            confidence = 0.0
        return SpeechResult(
            text=text, language=getattr(info, "language", self.language),
            confidence=float(max(0, min(1, confidence))),
            duration_seconds=time.perf_counter() - started,
        )
