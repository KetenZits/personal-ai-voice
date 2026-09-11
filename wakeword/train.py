"""Train a custom PyTorch wake-word CNN and tune its threshold."""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime
from pathlib import Path

import numpy as np


def _metrics(labels: list[int], scores: list[float], threshold: float) -> dict[str, float | list[list[int]]]:
    from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score
    predicted = [int(score >= threshold) for score in scores]
    matrix = confusion_matrix(labels, predicted, labels=[0, 1])
    tn, fp, fn, tp = matrix.ravel()
    return {
        "threshold": threshold,
        "precision": float(precision_score(labels, predicted, zero_division=0)),
        "recall": float(recall_score(labels, predicted, zero_division=0)),
        "f1": float(f1_score(labels, predicted, zero_division=0)),
        "false_positive_rate": float(fp / max(1, fp + tn)),
        "false_negative_rate": float(fn / max(1, fn + tp)),
        "confusion_matrix": matrix.tolist(),
    }


def train(positive: Path, negative: Path, output: Path, runs: Path, epochs: int = 20,
          batch_size: int = 16, seed: int = 42) -> dict[str, object]:
    import torch
    from torch import nn
    from torch.utils.data import DataLoader, Subset
    from sklearn.model_selection import train_test_split
    from .dataset import WakeWordDataset
    from .models import WakeWordCNN

    if epochs < 1 or batch_size < 1:
        raise ValueError("epochs and batch_size must both be positive")
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    dataset = WakeWordDataset(positive, negative, augment=False)
    labels = [int(label) for _, label in dataset.items]
    if len(set(labels)) != 2 or min(labels.count(0), labels.count(1)) < 2:
        raise ValueError("Wake-word training needs at least two positive and two negative files")
    indices = list(range(len(dataset)))
    train_indices, val_indices = train_test_split(indices, test_size=0.25, random_state=seed, stratify=labels)
    train_dataset = WakeWordDataset(positive, negative, augment=True)
    loaders = {
        "train": DataLoader(Subset(train_dataset, train_indices), batch_size=batch_size, shuffle=True),
        "validation": DataLoader(Subset(dataset, val_indices), batch_size=batch_size),
    }
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = WakeWordCNN().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    loss_fn = nn.BCEWithLogitsLoss()
    history: list[dict[str, float]] = []
    best = -1.0
    best_metrics: dict[str, object] = {}
    best_candidates: list[dict[str, object]] = []
    output.mkdir(parents=True, exist_ok=True)
    for epoch in range(1, epochs + 1):
        epoch_data: dict[str, float] = {"epoch": float(epoch)}
        validation_labels: list[int] = []
        validation_scores: list[float] = []
        for phase in ("train", "validation"):
            model.train(phase == "train")
            losses = []
            for features, targets in loaders[phase]:
                features, targets = features.to(device), targets.to(device)
                optimizer.zero_grad(set_to_none=True)
                with torch.set_grad_enabled(phase == "train"):
                    logits = model(features)
                    loss = loss_fn(logits, targets)
                    if phase == "train":
                        loss.backward(); optimizer.step()
                losses.append(float(loss.item()))
                if phase == "validation":
                    validation_scores.extend(torch.sigmoid(logits).detach().cpu().tolist())
                    validation_labels.extend(targets.int().cpu().tolist())
            epoch_data[f"{phase}_loss"] = float(np.mean(losses))
        candidates = [_metrics(validation_labels, validation_scores, float(t)) for t in np.arange(0.2, 0.96, 0.02)]
        selected = max(candidates, key=lambda item: (float(item["f1"]), float(item["precision"])))
        epoch_data["validation_f1"] = float(selected["f1"])
        history.append(epoch_data)
        if float(selected["f1"]) >= best:
            best = float(selected["f1"])
            torch.save({"state_dict": model.state_dict(), "threshold": selected["threshold"],
                        "sample_rate": 16000, "seconds": 2.0, "n_mels": 40}, output / "best.pt")
            best_metrics = selected
            best_candidates = candidates
    run = runs / datetime.now().strftime("%Y%m%d-%H%M%S")
    run.mkdir(parents=True, exist_ok=True)
    report = {"device": str(device), "history": history, "validation": best_metrics}
    (run / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (run / "threshold_evaluation.json").write_text(
        json.dumps(best_candidates, indent=2), encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--positive", type=Path, default=Path("data/wakeword/positive"))
    parser.add_argument("--negative", type=Path, default=Path("data/wakeword/negative"))
    parser.add_argument("--output", type=Path, default=Path("wakeword/models"))
    parser.add_argument("--runs", type=Path, default=Path("runs/wakeword"))
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()
    print(json.dumps(train(args.positive, args.negative, args.output, args.runs, args.epochs, args.batch_size), indent=2))


if __name__ == "__main__": main()
