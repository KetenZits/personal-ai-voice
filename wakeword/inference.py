"""Wake-word inference adapters."""

from __future__ import annotations

from collections import deque
from pathlib import Path

import numpy as np


class CustomWakeWordDetector:
    def __init__(self, model_path: str | Path, threshold: float | None = None,
                 device: str = "auto", input_sample_rate: int = 16000) -> None:
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
        self.input_sample_rate = input_sample_rate
        self.seconds = float(checkpoint.get("seconds", 2.0))
        self.buffer: deque[np.ndarray] = deque()
        self.samples = 0

    def reset(self) -> None:
        self.buffer.clear()
        self.samples = 0

    def predict(self, audio: np.ndarray) -> float:
        from .dataset import log_mel
        feature = self.torch.from_numpy(log_mel(audio, self.sample_rate, self.seconds)).unsqueeze(0).unsqueeze(0).to(self.device)
        with self.torch.inference_mode():
            return float(self.torch.sigmoid(self.model(feature)).item())

    def process_frame(self, frame: np.ndarray) -> tuple[bool, float]:
        array = np.asarray(frame, dtype=np.float32)
        if self.input_sample_rate != self.sample_rate:
            from audio.preprocessing import resample_audio
            array = resample_audio(array, self.input_sample_rate, self.sample_rate)
        self.buffer.append(array); self.samples += len(array)
        limit = int(self.sample_rate * self.seconds)
        while self.buffer and self.samples - len(self.buffer[0]) >= limit:
            self.samples -= len(self.buffer.popleft())
        if self.samples < limit:
            return False, 0.0
        score = self.predict(np.concatenate(tuple(self.buffer))[-limit:])
        return score >= self.threshold, score


class OpenWakeWordDetector:
    def __init__(self, model_path: str | None = None, phrase: str = "Hey Nova",
                 threshold: float = 0.8, input_sample_rate: int = 16000) -> None:
        from openwakeword.model import Model
        kwargs: dict[str, object] = {}
        if model_path:
            path = Path(model_path)
            if not path.is_file():
                raise FileNotFoundError(f"openWakeWord model not found: {path}")
            if path.suffix.lower() not in {".onnx", ".tflite"}:
                raise ValueError("openWakeWord model must be an ONNX or TFLite file")
            kwargs = {
                "wakeword_models": [str(path)],
                "inference_framework": "onnx" if path.suffix.lower() == ".onnx" else "tflite",
            }
        self.model = Model(**kwargs)
        self.phrase = phrase.casefold().replace(" ", "_")
        model_names = [str(name) for name in getattr(self.model, "models", {})]
        if model_names and not any(self.phrase in name.casefold() for name in model_names):
            available = ", ".join(model_names)
            raise ValueError(
                f"openWakeWord has no score key matching '{self.phrase}'. "
                f"Available models: {available}"
            )
        self.threshold = threshold
        self.sample_rate = 16000
        self.input_sample_rate = input_sample_rate
        self._pending = np.empty(0, dtype=np.float32)

    def reset(self) -> None:
        self._pending = np.empty(0, dtype=np.float32)
        reset = getattr(self.model, "reset", None)
        if callable(reset):
            reset()

    def process_frame(self, frame: np.ndarray) -> tuple[bool, float]:
        if self.input_sample_rate != self.sample_rate:
            from audio.preprocessing import resample_audio
            frame = resample_audio(frame, self.input_sample_rate, self.sample_rate)
        self._pending = np.concatenate((self._pending, np.asarray(frame, dtype=np.float32)))
        best_score = 0.0
        # openWakeWord's efficient streaming unit is 80 ms / 1,280 samples.
        while self._pending.size >= 1280:
            chunk, self._pending = self._pending[:1280], self._pending[1280:]
            pcm = (np.clip(chunk, -1, 1) * 32767).astype(np.int16)
            scores = self.model.predict(pcm)
            score = max(
                (float(value) for key, value in scores.items()
                 if self.phrase in key.casefold()),
                default=0.0,
            )
            best_score = max(best_score, score)
        return best_score >= self.threshold, best_score


def create_detector(backend: str, model_path: str, phrase: str, threshold: float,
                    input_sample_rate: int = 16000) -> object:
    if backend == "openwakeword":
        return OpenWakeWordDetector(model_path, phrase, threshold, input_sample_rate)
    return CustomWakeWordDetector(model_path, threshold, input_sample_rate=input_sample_rate)
