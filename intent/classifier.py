"""Saved scikit-learn model with an offline rule fallback."""

from __future__ import annotations

import re
from pathlib import Path

from brain.parser import extract_entities, normalize_text
from brain.schemas import IntentResult


RULES: list[tuple[str, tuple[str, ...]]] = [
    ("UNMUTE", ("unmute", "turn sound back on", "sound back on", "เปิดเสียง", "เปดเสยง")),
    ("MUTE", ("mute", "ปิดเสียง", "ปดเสยง")),
    ("SET_VOLUME", ("set volume", "ตั้งเสียง", "ตงเสยง")),
    ("VOLUME_DOWN", ("volume down", "the volume down", "lower volume", "ลดเสียง", "ลดเสยง", "เสียงดังไป", "เสยงดงไป")),
    ("VOLUME_UP", ("volume up", "the volume up", "increase volume", "เพิ่มเสียง", "เพมเสยง")),
    ("MEDIA_NEXT", ("next track", "next song", "skip this song", "skip track", "เพลงถัดไป", "เพลงถดไป")),
    ("MEDIA_PAUSE", ("pause", "stop the song", "stop music", "หยุดเพลง", "หยดเพลง")),
    ("MEDIA_PREVIOUS", ("previous track", "previous song", "go back one song", "กลับไปเพลง", "เพลงก่อน", "เพลงกอน")),
    ("MEDIA_PLAY", ("play music", "play song", "resume the song", "resume music", "เล่นเพลง", "เลนเพลง")),
    ("SCREENSHOT", ("screenshot", "capture screen", "แคปหน้าจอ", "แคปหนาจอ", "ถ่ายหน้าจอ")),
    ("GET_SYSTEM_INFO", ("system info", "cpu usage", "ram usage", "gpu info", "uptime", "เช็ค gpu", "เชค gpu", "ข้อมูลระบบ")),
    ("GET_TIME", ("what time", "current time", "กี่โมง", "เวลาเท่าไร")),
    ("SHUTDOWN", ("shutdown", "turn off computer", "turn off this pc", "ปิดเครื่อง", "ปดเครอง")),
    ("RESTART", ("restart computer", "reboot", "รีสตาร์ท", "เริ่มระบบใหม่", "เรมระบบใหม")),
    ("LOCK_PC", ("lock pc", "lock computer", "lock my computer", "ล็อกเครื่อง", "ลอกเครอง")),
    ("OPEN_PROJECT", ("open project", " project", "เปิดโปรเจกต์", "เปดโปรเจกต")),
    ("OPEN_FOLDER", ("open folder", "show folder", "เปิดโฟลเดอร์", "เปดโฟลเดอร")),
    ("WEB_SEARCH", ("search google", "google for", "search for", "ค้น google", "คน google", "ค้นหา", "คนหา")),
    ("OPEN_URL", ("open website", "open url", "go to http", "go to localhost", "เข้าเว็บ", "เปดเวบ")),
    ("CLOSE_APP", ("close app", "close program", "close ", "quit ", "ปิดโปรแกรม", "ปดโปรแกรม")),
    ("OPEN_APP", ("open ", "launch ", "start ", "เปิด", "เปด")),
]


class IntentClassifier:
    def __init__(self, model_path: str | Path, threshold: float = 0.70, allow_rule_fallback: bool = True) -> None:
        self.model_path = Path(model_path)
        self.threshold = threshold
        self.allow_rule_fallback = allow_rule_fallback
        self.model = None
        if self.model_path.exists():
            import joblib
            self.model = joblib.load(self.model_path)

    def predict(self, text: str) -> IntentResult:
        normalized = normalize_text(text)
        if self.model is not None:
            probabilities = self.model.predict_proba([normalized])[0]
            index = int(probabilities.argmax())
            confidence = float(probabilities[index])
            intent = str(self.model.classes_[index]) if confidence >= self.threshold else "UNKNOWN"
            if intent != "UNKNOWN" or not self.allow_rule_fallback:
                return IntentResult(
                    intent=intent,
                    confidence=confidence,
                    entities=extract_entities(normalized, intent),
                )
        if self.allow_rule_fallback:
            if re.search(r"\bvolume\s+(?:to\s+)?\d{1,3}\b", normalized):
                return IntentResult(
                    intent="SET_VOLUME", confidence=0.82,
                    entities=extract_entities(normalized, "SET_VOLUME"),
                )
            for intent, phrases in RULES:
                if any(phrase in normalized for phrase in phrases):
                    return IntentResult(
                        intent=intent,
                        confidence=0.82,
                        entities=extract_entities(normalized, intent),
                    )
        return IntentResult(intent="UNKNOWN", confidence=0.0, entities={})
