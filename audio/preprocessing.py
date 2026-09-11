"""Shared waveform preprocessing."""

from __future__ import annotations

import numpy as np


def to_mono(audio: np.ndarray) -> np.ndarray:
    array = np.asarray(audio, dtype=np.float32)
    return array.mean(axis=1) if array.ndim == 2 else array.reshape(-1)


def normalize_audio(audio: np.ndarray, peak: float = 0.95) -> np.ndarray:
    array = to_mono(audio)
    array = np.nan_to_num(array, copy=False)
    maximum = float(np.max(np.abs(array))) if array.size else 0.0
    return array if maximum < 1e-7 else (array * (peak / maximum)).astype(np.float32)


def resample_audio(audio: np.ndarray, source_rate: int, target_rate: int) -> np.ndarray:
    if source_rate == target_rate:
        return np.asarray(audio, dtype=np.float32)
    from scipy.signal import resample_poly
    from math import gcd
    divisor = gcd(source_rate, target_rate)
    return resample_poly(audio, target_rate // divisor, source_rate // divisor).astype(np.float32)


def float_to_pcm16(audio: np.ndarray) -> bytes:
    clipped = np.clip(to_mono(audio), -1.0, 1.0)
    return (clipped * 32767).astype("<i2").tobytes()

