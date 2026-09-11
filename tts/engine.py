"""Thread-safe local SAPI speech via pyttsx3."""

from __future__ import annotations

import logging
import threading

from .voices import select_voice


class TTSEngine:
    def __init__(self, enabled: bool = True, voice: str | None = None, rate: int = 175, volume: float = 1.0) -> None:
        self.enabled = enabled
        self.log = logging.getLogger(__name__)
        self._lock = threading.Lock()
        self.engine = None
        if enabled:
            try:
                import pyttsx3
                self.engine = pyttsx3.init()
                self.engine.setProperty("rate", rate); self.engine.setProperty("volume", volume)
                voice_id = select_voice(self.engine, voice)
                if voice_id:
                    self.engine.setProperty("voice", voice_id)
            except Exception:
                self.log.exception("TTS initialization failed; speech output is disabled")
                self.enabled = False

    def speak(self, text: str) -> None:
        if not self.enabled or not self.engine or not text:
            return
        try:
            with self._lock:
                self.engine.say(text)
                self.engine.runAndWait()
        except Exception:
            self.log.exception("TTS failed")

