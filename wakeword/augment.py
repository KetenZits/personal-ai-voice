"""Waveform augmentations used by custom wake-word training."""

from __future__ import annotations

import random
from pathlib import Path

import numpy as np


def augment_audio(audio: np.ndarray, sample_rate: int, noise_files: list[Path] | None = None) -> np.ndarray:
    """Apply random gain, shift/silence, stretch, pitch, noise, and lightweight reverb."""
    import librosa
    result = np.asarray(audio, dtype=np.float32).copy()
    result *= 10 ** (random.uniform(-8, 5) / 20)
    if random.random() < 0.35:
        result = librosa.effects.time_stretch(result, rate=random.uniform(0.88, 1.12))
    if random.random() < 0.30:
        result = librosa.effects.pitch_shift(result, sr=sample_rate, n_steps=random.uniform(-1.5, 1.5))
    if random.random() < 0.45:
        silence = np.zeros(random.randint(0, int(sample_rate * 0.35)), dtype=np.float32)
        result = np.concatenate((silence, result))
    if random.random() < 0.35:
        decay = np.exp(-np.arange(int(sample_rate * 0.15)) / (sample_rate * 0.04))
        impulse = np.zeros_like(decay)
        impulse[0] = 1
        impulse[:: max(1, sample_rate // 80)] += decay[:: max(1, sample_rate // 80)] * 0.08
        result = np.convolve(result, impulse, mode="full")[: len(result)]
    if noise_files and random.random() < 0.6:
        noise, _ = librosa.load(str(random.choice(noise_files)), sr=sample_rate, mono=True)
        if len(noise) < len(result):
            noise = np.resize(noise, len(result))
        start = random.randint(0, max(0, len(noise) - len(result)))
        noise = noise[start:start + len(result)]
        result += noise * random.uniform(0.02, 0.18)
    elif random.random() < 0.3:
        result += np.random.normal(0, random.uniform(0.001, 0.012), len(result)).astype(np.float32)
    return np.clip(result, -1, 1).astype(np.float32)

