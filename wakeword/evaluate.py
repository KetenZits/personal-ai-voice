"""Evaluate wake-word files and sweep decision thresholds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=Path("wakeword/models/best.pt"))
    parser.add_argument("--positive", type=Path, default=Path("data/wakeword/positive"))
    parser.add_argument("--negative", type=Path, default=Path("data/wakeword/negative"))
    parser.add_argument("--output", type=Path, default=Path("runs/wakeword/evaluation.json"))
    args = parser.parse_args()
    from .dataset import find_audio
    from .inference import CustomWakeWordDetector
    from .train import _metrics
    from audio.utils import load_wav
    detector = CustomWakeWordDetector(args.model)
    negative_paths = find_audio(args.negative)
    positive_paths = find_audio(args.positive)
    if not negative_paths or not positive_paths:
        raise ValueError("Evaluation needs at least one positive and one negative file")
    paths = negative_paths + positive_paths
    labels = [0] * len(negative_paths) + [1] * len(positive_paths)
    scores = [detector.predict(load_wav(path, detector.sample_rate)) for path in paths]
    sweep = [_metrics(labels, scores, float(t)) for t in np.arange(0.05, 0.96, 0.01)]
    result = {"best": max(sweep, key=lambda x: float(x["f1"])), "thresholds": sweep, "samples": len(paths)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["best"], indent=2))


if __name__ == "__main__": main()
