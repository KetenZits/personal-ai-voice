"""Evaluate a trained speaker verifier, including FAR, FRR, ROC-AUC, and thresholds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def main() -> None:
    import joblib
    from sklearn.metrics import roc_curve
    from .dataset import extract_dataset
    from .embeddings import ECAPAEmbedder
    from .train import best_threshold, verification_metrics
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=Path("speaker/models/best.joblib"))
    parser.add_argument("--owner", type=Path, default=Path("data/speakers/owner"))
    parser.add_argument("--negatives", type=Path, default=Path("data/speakers/negatives"))
    parser.add_argument("--output", type=Path, default=Path("runs/speaker/evaluation.json"))
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = parser.parse_args()
    artifact = joblib.load(args.model)
    x, y, _ = extract_dataset(ECAPAEmbedder(args.device), args.owner, args.negatives)
    scores = x @ artifact["owner_embedding"] if artifact["kind"] == "cosine" else artifact["classifier"].predict_proba(x)[:, 1]
    tuned, sweep = best_threshold(y, scores)
    fpr, tpr, roc_thresholds = roc_curve(y, scores)
    result = {"configured": verification_metrics(y, scores, artifact["threshold"]),
              "tuned": verification_metrics(y, scores, tuned), "threshold_sweep": sweep["sweep"],
              "roc": {"false_positive_rate": fpr.tolist(), "true_positive_rate": tpr.tolist(),
                      "thresholds": roc_thresholds.tolist()}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["configured"], indent=2))


if __name__ == "__main__": main()
