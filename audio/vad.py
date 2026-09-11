"""Voice activity detection with WebRTC and energy-based fallback."""

from __future__ import annotations

import numpy as np

from .preprocessing import float_to_pcm16


class VoiceActivityDetector:
    def __init__(self, sample_rate: int = 16000, frame_ms: int = 30, backend: str = "auto", energy_threshold: float = 0.015) -> None:
        self.sample_rate = sample_rate
        self.frame_ms = frame_ms
        self.energy_threshold = energy_threshold
        self._webrtc = None
        if backend in {"auto", "webrtc"}:
            try:
                import webrtcvad
                self._webrtc = webrtcvad.Vad(2)
            except ImportError:
                if backend == "webrtc":
                    raise RuntimeError("webrtcvad-wheels is required for the configured VAD backend")
        self.backend = "webrtc" if self._webrtc is not None else "energy"

    def is_speech(self, frame: np.ndarray) -> bool:
        mono = np.asarray(frame, dtype=np.float32).reshape(-1)
        if self._webrtc is not None and self.sample_rate in {8000, 16000, 32000, 48000}:
            expected = self.sample_rate * self.frame_ms // 1000
            if mono.size == expected:
                return bool(self._webrtc.is_speech(float_to_pcm16(mono), self.sample_rate))
        rms = float(np.sqrt(np.mean(np.square(mono)))) if mono.size else 0.0
        return rms >= self.energy_threshold

