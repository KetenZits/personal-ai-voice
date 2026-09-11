"""Wave file helpers."""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

from .preprocessing import float_to_pcm16


def save_wav(path: str | Path, audio: np.ndarray, sample_rate: int = 16000) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(sample_rate)
        stream.writeframes(float_to_pcm16(audio))
    return output


def load_wav(path: str | Path, sample_rate: int = 16000) -> np.ndarray:
    import librosa
    audio, _ = librosa.load(str(path), sr=sample_rate, mono=True)
    return np.asarray(audio, dtype=np.float32)

