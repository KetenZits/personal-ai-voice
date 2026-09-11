from brain.parser import CommandParser, extract_entities, split_compound_command, validate_url_target
from brain.schemas import IntentResult


class FakeClassifier:
    def predict(self, text: str) -> IntentResult:
        if "project" in text:
            return IntentResult(intent="OPEN_PROJECT", confidence=0.9,
                                entities={"project": text.split("project", 1)[1].strip()})
        return IntentResult(intent="OPEN_APP", confidence=0.9, entities={"app": "chrome"})


def test_entity_extraction_multilingual() -> None:
    assert extract_entities("ตั้งเสียงไว้ 40 เปอร์เซ็นต์", "SET_VOLUME") == {"volume": 40}
    assert extract_entities("search google for pytorch transformer", "WEB_SEARCH") == {"query": "pytorch transformer"}
    assert extract_entities("เปิด vscode ให้หน่อย", "OPEN_APP") == {"app": "vscode"}
    assert extract_entities("เปดโปรเจกตพอร์ตโฟลิโอ", "OPEN_PROJECT") == {
        "project": "พอร์ตโฟลิโอ",
    }
    assert extract_entities("ปิดโปรแกรม vscode", "CLOSE_APP") == {"app": "vscode"}


def test_compound_plan() -> None:
    plan = CommandParser(FakeClassifier()).parse("open chrome and then open project study platform")
    assert [action.type.value for action in plan.actions] == ["open_app", "open_project"]
    assert plan.actions[1].target == "study platform"


def test_url_validation_rejects_non_http() -> None:
    assert validate_url_target("localhost:3000") == "http://localhost:3000"
    assert extract_entities("go to localhost 3000", "OPEN_URL") == {"url": "localhost:3000"}
    try:
        validate_url_target("file:///C:/secret")
    except ValueError:
        pass
    else:
        raise AssertionError("file URL should be rejected")


def test_english_project_target_is_cleaned() -> None:
    assert extract_entities("launch my portfolio project", "OPEN_PROJECT") == {
        "project": "portfolio",
    }
