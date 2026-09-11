"""Train the TF-IDF + logistic-regression intent classifier."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def train(dataset_path: Path, output_dir: Path, runs_dir: Path, seed: int = 42) -> dict[str, object]:
    import joblib
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, log_loss
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline

    from .dataset import load_examples

    examples = load_examples(dataset_path)
    texts = [e.text for e in examples]
    labels = [e.intent.upper() for e in examples]
    classes = sorted(set(labels))
    test_size = max(len(classes), round(len(examples) * 0.25))
    train_x, val_x, train_y, val_y = train_test_split(
        texts, labels, test_size=test_size, random_state=seed, stratify=labels,
    )
    model = Pipeline([
        ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=1, sublinear_tf=True)),
        ("classifier", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=seed)),
    ])
    model.fit(train_x, train_y)
    predictions = model.predict(val_x)
    probabilities = model.predict_proba(val_x)
    metrics: dict[str, object] = {
        "train_loss": float(log_loss(train_y, model.predict_proba(train_x), labels=model.classes_)),
        "validation_loss": float(log_loss(val_y, probabilities, labels=model.classes_)),
        "accuracy": float(accuracy_score(val_y, predictions)),
        "macro_f1": float(f1_score(val_y, predictions, average="macro")),
        "classes": list(model.classes_),
        "confusion_matrix": confusion_matrix(val_y, predictions, labels=model.classes_).tolist(),
        "per_class": classification_report(val_y, predictions, output_dict=True, zero_division=0),
        "train_examples": len(train_x), "validation_examples": len(val_x),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_dir / "best.joblib")
    run = runs_dir / datetime.now().strftime("%Y%m%d-%H%M%S")
    run.mkdir(parents=True, exist_ok=True)
    (run / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    (run / "confusion_matrix.json").write_text(
        json.dumps({"labels": list(model.classes_), "matrix": metrics["confusion_matrix"]}, indent=2), encoding="utf-8",
    )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("intent/dataset/intents.json"))
    parser.add_argument("--output", type=Path, default=Path("intent/models"))
    parser.add_argument("--runs", type=Path, default=Path("runs/intent"))
    args = parser.parse_args()
    print(json.dumps(train(args.dataset, args.output, args.runs), indent=2))


if __name__ == "__main__":
    main()
