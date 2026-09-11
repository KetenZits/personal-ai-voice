"""Evaluate a saved intent classifier on a labeled JSON dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def evaluate(model_path: Path, dataset_path: Path, output: Path) -> dict[str, object]:
    import joblib
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
    from .dataset import load_examples

    model = joblib.load(model_path)
    examples = load_examples(dataset_path)
    x, y = [e.text for e in examples], [e.intent.upper() for e in examples]
    predicted = model.predict(x)
    labels = list(model.classes_)
    result = {
        "accuracy": float(accuracy_score(y, predicted)),
        "macro_f1": float(f1_score(y, predicted, average="macro")),
        "labels": labels,
        "confusion_matrix": confusion_matrix(y, predicted, labels=labels).tolist(),
        "per_class": classification_report(y, predicted, output_dict=True, zero_division=0),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=Path("intent/models/best.joblib"))
    parser.add_argument("--dataset", type=Path, default=Path("intent/dataset/intents.json"))
    parser.add_argument("--output", type=Path, default=Path("runs/intent/evaluation.json"))
    args = parser.parse_args()
    print(json.dumps(evaluate(args.model, args.dataset, args.output), indent=2))


if __name__ == "__main__":
    main()

