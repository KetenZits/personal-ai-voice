"""Runtime speaker verification using a trained comparison artifact."""

from __future__ import annotations

from pathlib import Path

import numpy as np


class SpeakerVerifier:
    def __init__(self, model_path: str | Path, threshold: float | None = None, device: str = "auto") -> None:
        import joblib
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"Speaker model not found: {path}. Run python -m speaker.train")
        self.artifact = joblib.load(path)
        self.threshold = float(threshold if threshold is not None else self.artifact["threshold"])
        from .embeddings import ECAPAEmbedder
        self.embedder = ECAPAEmbedder(device=device)

    def score(self, audio: np.ndarray, sample_rate: int = 16000) -> float:
        embedding = self.embedder.encode(audio, sample_rate)
        if self.artifact["kind"] == "cosine":
            return float(embedding @ self.artifact["owner_embedding"])
        return float(self.artifact["classifier"].predict_proba(embedding.reshape(1, -1))[0, 1])

    def verify(self, audio: np.ndarray, sample_rate: int = 16000) -> tuple[bool, float]:
        score = self.score(audio, sample_rate)
        return score >= self.threshold, score

