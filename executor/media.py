"""Media key actions."""

from __future__ import annotations


KEYS = {"play": "play/pause media", "pause": "play/pause media", "next": "next track", "previous": "previous track"}


def press_media(action: str) -> None:
    import keyboard
    keyboard.send(KEYS[action])

