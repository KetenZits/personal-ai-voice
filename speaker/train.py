"""Compare cosine, logistic regression, SVM, and MLP speaker verifiers."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import numpy as np


def verification_metrics(y_true: np.ndarray, scores: np.ndarray, threshold: float) -> dict[str, float | list[list[int]]]:
    from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
    predicted = (scores >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, predicted, labels=[0, 1]).ravel()
    return {
        "threshold": float(threshold), "accuracy": float(accuracy_score(y_true, predicted)),
        "precision": float(precision_score(y_true, predicted, zero_division=0)),
        "recall": float(recall_score(y_true, predicted, zero_division=0)),
        "f1": float(f1_score(y_true, predicted, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, scores)),
        "far": float(fp / max(1, fp + tn)), "frr": float(fn / max(1, fn + tp)),
        "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
    }


def best_threshold(y_true: np.ndarray, scores: np.ndarray) -> tuple[float, dict[str, object]]:
    low, high = float(scores.min()), float(scores.max())
    candidates = np.linspace(low, high, 201)
    reports = [verification_metrics(y_true, scores, float(t)) for t in candidates]
    report = max(reports, key=lambda x: (float(x["f1"]), -abs(float(x["far"]) - float(x["frr"]))))
    return float(report["threshold"]), {"selected": report, "sweep": reports}


def train(owner: Path, negatives: Path, output: Path, runs: Path, device: str = "auto", seed: int = 42) -> dict[str, object]:
    import joblib
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.neural_network import MLPClassifier
    from sklearn.svm import SVC
    from .dataset import extract_dataset
    from .embeddings import ECAPAEmbedder

    embedder = ECAPAEmbedder(device=device)
    x, y, paths = extract_dataset(embedder, owner, negatives)
    train_x, val_x, train_y, val_y = train_test_split(x, y, test_size=0.3, random_state=seed, stratify=y)
    owner_centroid = train_x[train_y == 1].mean(axis=0)
    owner_centroid /= max(float(np.linalg.norm(owner_centroid)), 1e-9)
    candidates: dict[str, tuple[object | None, np.ndarray]] = {
        "cosine": (None, val_x @ owner_centroid),
    }
    models = {
        "logistic_regression": LogisticRegression(class_weight="balanced", max_iter=2000, random_state=seed),
        "svm": SVC(kernel="rbf", class_weight="balanced", probability=True, random_state=seed),
        "mlp": MLPClassifier(hidden_layer_sizes=(64, 16), max_iter=1000, early_stopping=True, random_state=seed),
    }
    for name, model in models.items():
        model.fit(train_x, train_y)
        candidates[name] = (model, model.predict_proba(val_x)[:, 1])
    reports: dict[str, object] = {}
    fitted: dict[str, tuple[object | None, float]] = {}
    for name, (model, scores) in candidates.items():
        threshold, report = best_threshold(val_y, scores)
        reports[name] = report
        fitted[name] = (model, threshold)
    best_name = max(reports, key=lambda name: float(reports[name]["selected"]["f1"]))
    best_model, threshold = fitted[best_name]
    output.mkdir(parents=True, exist_ok=True)
    artifact = {"kind": best_name, "classifier": best_model, "threshold": threshold,
                "owner_embedding": owner_centroid, "embedding_model": "speechbrain/spkrec-ecapa-voxceleb"}
    joblib.dump(artifact, output / "best.joblib")
    np.save(output / "owner_embedding.npy", owner_centroid)
    run = runs / datetime.now().strftime("%Y%m%d-%H%M%S"); run.mkdir(parents=True, exist_ok=True)
    result = {"best_approach": best_name, "validation": reports, "samples": len(y), "device": embedder.device}
    (run / "metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    np.savez_compressed(run / "embeddings.npz", embeddings=x, labels=y, paths=np.asarray(paths))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", type=Path, default=Path("data/speakers/owner"))
    parser.add_argument("--negatives", type=Path, default=Path("data/speakers/negatives"))
    parser.add_argument("--output", type=Path, default=Path("speaker/models"))
    parser.add_argument("--runs", type=Path, default=Path("runs/speaker"))
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = parser.parse_args()
    print(json.dumps(train(args.owner, args.negatives, args.output, args.runs, args.device), indent=2))


if __name__ == "__main__": main()

