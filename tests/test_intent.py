from intent.classifier import IntentClassifier
from intent.dataset import load_examples


def test_rule_fallback_predicts_and_extracts() -> None:
    classifier = IntentClassifier("missing.joblib")
    result = classifier.predict("ตงเสยง 40 เปอรเซนต")
    assert result.intent == "SET_VOLUME"
    assert result.entities["volume"] == 40
    assert classifier.predict("launch vscode").intent == "OPEN_APP"


def test_rule_fallback_covers_bundled_first_run_examples() -> None:
    """The assistant must work before the optional intent model is trained."""
    classifier = IntentClassifier("missing.joblib")
    for example in load_examples("intent/dataset/intents.json"):
        assert classifier.predict(example.text).intent == example.intent, example.text
