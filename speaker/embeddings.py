"""SpeechBrain ECAPA-TDNN embedding extraction with CUDA fallback."""

from __future__ import annotations

from pathlib import Path

import numpy as np


class ECAPAEmbedder:
    def __init__(self, device: str = "auto", cache_dir: str | Path = "speaker/models/ecapa") -> None:
        import torch
        try:
            from speechbrain.inference.speaker import EncoderClassifier
        except ImportError:  # SpeechBrain < 1.0 compatibility
            from speechbrain.pretrained import EncoderClassifier
        selected = "cuda" if device == "auto" and torch.cuda.is_available() else ("cpu" if device == "auto" else device)
        if selected == "cuda" and not torch.cuda.is_available():
            selected = "cpu"
        self.torch = torch
        try:
            self.model = EncoderClassifier.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                savedir=str(cache_dir), run_opts={"device": selected},
            )
            self.device = selected
        except Exception:
            if selected != "cuda":
                raise
            self.model = EncoderClassifier.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                savedir=str(cache_dir), run_opts={"device": "cpu"},
            )
            self.device = "cpu"

    def encode(self, audio: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
        from audio.preprocessing import resample_audio
        waveform = np.asarray(audio, dtype=np.float32)
        if sample_rate != 16000:
            waveform = resample_audio(waveform, sample_rate, 16000)
        tensor = self.torch.from_numpy(waveform).unsqueeze(0).to(self.device)
        with self.torch.inference_mode():
            embedding = self.model.encode_batch(tensor).squeeze().detach().cpu().numpy()
        norm = np.linalg.norm(embedding)
        return (embedding / max(float(norm), 1e-9)).astype(np.float32)

    def encode_file(self, path: str | Path) -> np.ndarray:
        from audio.utils import load_wav
        return self.encode(load_wav(path, 16000), 16000)
