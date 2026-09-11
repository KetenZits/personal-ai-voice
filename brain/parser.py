"""Rule-backed entity extraction and conversion from intents to actions."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from brain.schemas import Action, ActionPlan, ActionType, IntentResult


INTENT_TO_ACTION = {item.name: item for item in ActionType}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold().strip())


def _after_any(text: str, markers: list[str]) -> str | None:
    for marker in sorted(markers, key=len, reverse=True):
        match = re.search(rf"(?:^|\s){re.escape(marker)}(?:\s+|$)(.*)", text)
        if match and match.group(1).strip():
            return match.group(1).strip()
    return None


def extract_entities(text: str, intent: str) -> dict[str, object]:
    value = normalize_text(text)
    intent = intent.upper()
    if intent == "SET_VOLUME":
        match = re.search(r"(?<!\d)(100|[1-9]?\d)(?:\s*(?:%|percent|เปอร์เซ็นต์|เปอรเซนต))?", value)
        return {"volume": int(match.group(1))} if match else {}
    if intent in {"OPEN_APP", "CLOSE_APP"}:
        markers = [
            "open", "launch", "start", "close", "quit", "exit",
            "เปิด", "เปด", "ปิด", "ปด", "โปรแกรม", "app",
        ]
        target = _after_any(value, markers)
        if target:
            target = re.sub(r"\s*(?:ให้หน่อย|ที|please)$", "", target).strip()
        return {"app": target} if target else {}
    if intent == "OPEN_PROJECT":
        target = _after_any(value, ["open project", "project", "เปิดโปรเจกต์", "เปดโปรเจกต", "โปรเจกต์", "โปรเจกต"])
        return {"project": target} if target else {}
    if intent == "OPEN_FOLDER":
        target = _after_any(value, ["open folder", "folder", "เปิดโฟลเดอร์", "เปดโฟลเดอร", "โฟลเดอร์"])
        return {"path": target} if target else {}
    if intent == "WEB_SEARCH":
        target = _after_any(value, ["search google for", "google", "search for", "search", "ค้น google เรื่อง", "คน google เรอง", "ค้นหา", "คนหา"])
        return {"query": target} if target else {}
    if intent == "OPEN_URL":
        match = re.search(r"(?:https?://)?(?:localhost(?:[:\s]\d+)?|(?:[\w-]+\.)+[a-z]{2,})(?:/\S*)?", value)
        if match:
            return {"url": re.sub(r"^(localhost)\s+(\d+)", r"\1:\2", match.group(0))}
        localhost = re.search(r"localhost\s+(\d{2,5})", value)
        if localhost:
            return {"url": f"localhost:{localhost.group(1)}"}
        return {}
    return {}


def intent_to_action(result: IntentResult) -> Action:
    action_type = INTENT_TO_ACTION.get(result.intent.upper(), ActionType.UNKNOWN)
    entity_keys = {
        ActionType.OPEN_APP: "app",
        ActionType.CLOSE_APP: "app",
        ActionType.OPEN_PROJECT: "project",
        ActionType.OPEN_FOLDER: "path",
        ActionType.OPEN_URL: "url",
        ActionType.WEB_SEARCH: "query",
    }
    target_key = entity_keys.get(action_type)
    target = str(result.entities[target_key]) if target_key and target_key in result.entities else None
    parameters = dict(result.entities) if action_type == ActionType.SET_VOLUME else {}
    return Action(type=action_type, target=target, parameters=parameters, confidence=result.confidence)


def split_compound_command(text: str) -> list[str]:
    # Keep query text intact unless the conjunction clearly starts another command.
    pattern = r"\s+(?:and then|then|แล้ว|แลว)\s+(?=(?:open|close|launch|เปิด|เปด|ปิด|ปด|set|ตั้ง|ตง|search|ค้น|คน))"
    return [part.strip() for part in re.split(pattern, text, flags=re.IGNORECASE) if part.strip()]


def validate_url_target(target: str) -> str:
    candidate = target.strip()
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", candidate):
        candidate = "http://" + candidate if candidate.startswith("localhost") else "https://" + candidate
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Only valid HTTP(S) URLs are allowed")
    return candidate


class CommandParser:
    def __init__(self, classifier: object) -> None:
        self.classifier = classifier

    def parse(self, text: str) -> ActionPlan:
        actions: list[Action] = []
        for part in split_compound_command(text):
            predicted = self.classifier.predict(part)
            if not predicted.entities:
                predicted.entities = extract_entities(part, predicted.intent)
            actions.append(intent_to_action(predicted))
        return ActionPlan(actions=actions)
