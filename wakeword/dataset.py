"""PyTorch wake-word dataset and feature extraction."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset

from audio.utils import load_wav
from .augment import augment_audio


AUDIO_SUFFIXES = {".wav", ".flac", ".mp3", ".m4a", ".ogg"}


def find_audio(directory: str | Path) -> list[Path]:
    path = Path(directory)
    return sorted(item for item in path.rglob("*") if item.suffix.lower() in AUDIO_SUFFIXES)


def log_mel(audio: np.ndarray, sample_rate: int = 16000, seconds: float = 2.0, n_mels: int = 40) -> np.ndarray:
    import librosa
    length = int(sample_rate * seconds)
    waveform = np.zeros(length, dtype=np.float32)
    source = np.asarray(audio, dtype=np.float32)
    if len(source) >= length:
        start = (len(source) - length) // 2
        waveform[:] = source[start:start + length]
    else:
        start = (length - len(source)) // 2
        waveform[start:start + len(source)] = source
    mel = librosa.feature.melspectrogram(y=waveform, sr=sample_rate, n_fft=512, hop_length=160, n_mels=n_mels)
    db = librosa.power_to_db(mel, ref=np.max)
    return ((db + 80.0) / 80.0).astype(np.float32)


class WakeWordDataset(Dataset[tuple[torch.Tensor, torch.Tensor]]):
    def __init__(self, positive_dir: str | Path, negative_dir: str | Path,
                 sample_rate: int = 16000, augment: bool = False) -> None:
        self.items = [(path, 1.0) for path in find_audio(positive_dir)]
        self.items += [(path, 0.0) for path in find_audio(negative_dir)]
        self.sample_rate = sample_rate
        self.augment = augment
        self.noise_files = find_audio(Path(negative_dir) / "noise")
        if not self.items:
            raise ValueError("No audio found in the positive/negative dataset directories")

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        path, label = self.items[index]
        audio = load_wav(path, self.sample_rate)
        if self.augment:
            audio = augment_audio(audio, self.sample_rate, self.noise_files)
        feature = torch.from_numpy(log_mel(audio, self.sample_rate)).unsqueeze(0)
        return feature, torch.tensor(label, dtype=torch.float32)

