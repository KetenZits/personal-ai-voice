from intent.classifier import IntentClassifier


def test_rule_fallback_predicts_and_extracts() -> None:
    classifier = IntentClassifier("missing.joblib")
    result = classifier.predict("ตงเสยง 40 เปอรเซนต")
    assert result.intent == "SET_VOLUME"
    assert result.entities["volume"] == 40
    assert classifier.predict("launch vscode").intent == "OPEN_APP"

