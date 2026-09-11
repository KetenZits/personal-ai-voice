"""Basic challenge-response helper for high-risk commands."""

from __future__ import annotations

import random
import secrets
import time
import unicodedata
from dataclasses import dataclass


@dataclass
class Challenge:
    phrase: str
    expires_at: float


class ChallengeResponse:
    WORDS = ("blue", "green", "nova", "river", "seven", "nine", "tiger", "moon")

    def __init__(self, timeout_seconds: float = 15.0) -> None:
        self.timeout_seconds = timeout_seconds
        self._challenge: Challenge | None = None

    def create(self) -> Challenge:
        rng = random.SystemRandom()
        phrase = f"{rng.choice(self.WORDS)} {rng.choice(self.WORDS)} {rng.randrange(10, 100)}"
        self._challenge = Challenge(phrase, time.monotonic() + self.timeout_seconds)
        return self._challenge

    def verify(self, transcript: str) -> bool:
        current, self._challenge = self._challenge, None
        normalized = "".join(
            " " if unicodedata.category(character)[0] in {"P", "S"} else character
            for character in transcript.casefold()
        )
        normalized = " ".join(normalized.split())
        return bool(
            current and time.monotonic() <= current.expires_at
            and secrets.compare_digest(normalized, current.phrase.casefold())
        )
