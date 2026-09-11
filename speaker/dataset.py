"""Speaker audio discovery and embedding dataset creation."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from wakeword.dataset import find_audio


def extract_dataset(embedder: object, owner_dir: str | Path, negative_dir: str | Path) -> tuple[np.ndarray, np.ndarray, list[str]]:
    owner = find_audio(owner_dir)
    negatives = find_audio(negative_dir)
    if len(owner) < 2 or len(negatives) < 2:
        raise ValueError("Speaker training needs at least 2 owner and 2 negative recordings")
    paths = owner + negatives
    embeddings = np.stack([embedder.encode_file(path) for path in paths])
    labels = np.asarray([1] * len(owner) + [0] * len(negatives), dtype=np.int64)
    return embeddings, labels, [str(path) for path in paths]

