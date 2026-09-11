"""Voice enumeration and fuzzy selection."""

from __future__ import annotations


def list_voices(engine: object) -> list[dict[str, object]]:
    result = []
    for voice in engine.getProperty("voices"):
        result.append({"id": voice.id, "name": voice.name, "languages": list(getattr(voice, "languages", []))})
    return result


def select_voice(engine: object, requested: str | None, language: str | None = None) -> str | None:
    voices = list_voices(engine)
    needle = (requested or language or "").casefold()
    if not needle:
        return None
    for voice in voices:
        searchable = f"{voice['id']} {voice['name']} {voice['languages']}".casefold()
        if needle in searchable:
            return str(voice["id"])
    return None

