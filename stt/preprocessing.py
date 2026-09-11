"""Speech-to-text waveform preparation."""

from __future__ import annotations

import numpy as np

from audio.preprocessing import normalize_audio, resample_audio, to_mono


def prepare_for_whisper(audio: np.ndarray, sample_rate: int) -> np.ndarray:
    result = resample_audio(to_mono(audio), sample_rate, 16000)
    # Conservative normalization preserves relative dynamics while helping quiet mics.
    if result.size and float(np.max(np.abs(result))) < 0.25:
        result = normalize_audio(result, peak=0.7)
    return result.astype(np.float32)

