"""Wake-word inference adapters."""

from __future__ import annotations

from collections import deque
from pathlib import Path

import numpy as np


class CustomWakeWordDetector:
    def __init__(self, model_path: str | Path, threshold: float | None = None, device: str = "auto") -> None:
        import torch
        from .models import WakeWordCNN
        self.torch = torch
        selected = "cuda" if device == "auto" and torch.cuda.is_available() else ("cpu" if device == "auto" else device)
        self.device = torch.device(selected)
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"Wake-word model not found: {path}. Run python -m wakeword.train")
        checkpoint = torch.load(path, map_location=self.device, weights_only=False)
        self.model = WakeWordCNN(checkpoint.get("n_mels", 40)).to(self.device)
        self.model.load_state_dict(checkpoint["state_dict"]); self.model.eval()
        self.threshold = float(threshold if threshold is not None else checkpoint.get("threshold", 0.8))
        self.sample_rate = int(checkpoint.get("sample_rate", 16000))
        self.seconds = float(checkpoint.get("seconds", 2.0))
        self.buffer: deque[np.ndarray] = deque()
        self.samples = 0

    def predict(self, audio: np.ndarray) -> float:
        from .dataset import log_mel
        feature = self.torch.from_numpy(log_mel(audio, self.sample_rate, self.seconds)).unsqueeze(0).unsqueeze(0).to(self.device)
        with self.torch.inference_mode():
            return float(self.torch.sigmoid(self.model(feature)).item())

    def process_frame(self, frame: np.ndarray) -> tuple[bool, float]:
        array = np.asarray(frame, dtype=np.float32)
        self.buffer.append(array); self.samples += len(array)
        limit = int(self.sample_rate * self.seconds)
        while self.buffer and self.samples - len(self.buffer[0]) >= limit:
            self.samples -= len(self.buffer.popleft())
        if self.samples < limit:
            return False, 0.0
        score = self.predict(np.concatenate(tuple(self.buffer))[-limit:])
        return score >= self.threshold, score


class OpenWakeWordDetector:
    def __init__(self, model_path: str | None = None, phrase: str = "Hey Nova", threshold: float = 0.8) -> None:
        from openwakeword.model import Model
        kwargs = {"wakeword_models": [model_path]} if model_path and Path(model_path).exists() else {}
        self.model = Model(**kwargs)
        self.phrase = phrase.casefold().replace(" ", "_")
        self.threshold = threshold

    def process_frame(self, frame: np.ndarray) -> tuple[bool, float]:
        pcm = (np.clip(frame, -1, 1) * 32767).astype(np.int16)
        scores = self.model.predict(pcm)
        score = max((float(value) for key, value in scores.items() if self.phrase in key.casefold()), default=0.0)
        return score >= self.threshold, score


def create_detector(backend: str, model_path: str, phrase: str, threshold: float) -> object:
    if backend == "openwakeword":
        return OpenWakeWordDetector(model_path, phrase, threshold)
    return CustomWakeWordDetector(model_path, threshold)

