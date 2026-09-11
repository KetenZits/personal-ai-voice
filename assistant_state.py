"""Thread-safe assistant state and debug snapshot."""

from __future__ import annotations

import threading
from enum import Enum
from typing import Any


class AssistantState(str, Enum):
    IDLE = "IDLE"
    LISTENING_FOR_WAKE_WORD = "LISTENING_FOR_WAKE_WORD"
    VERIFYING_SPEAKER = "VERIFYING_SPEAKER"
    LISTENING_FOR_COMMAND = "LISTENING_FOR_COMMAND"
    PROCESSING = "PROCESSING"
    EXECUTING = "EXECUTING"
    SPEAKING = "SPEAKING"


ALLOWED_TRANSITIONS = {
    AssistantState.IDLE: {AssistantState.LISTENING_FOR_WAKE_WORD, AssistantState.LISTENING_FOR_COMMAND},
    AssistantState.LISTENING_FOR_WAKE_WORD: {AssistantState.VERIFYING_SPEAKER, AssistantState.IDLE},
    AssistantState.VERIFYING_SPEAKER: {AssistantState.LISTENING_FOR_COMMAND, AssistantState.LISTENING_FOR_WAKE_WORD, AssistantState.IDLE},
    AssistantState.LISTENING_FOR_COMMAND: {AssistantState.PROCESSING, AssistantState.IDLE, AssistantState.LISTENING_FOR_WAKE_WORD},
    AssistantState.PROCESSING: {AssistantState.EXECUTING, AssistantState.SPEAKING, AssistantState.IDLE, AssistantState.LISTENING_FOR_WAKE_WORD},
    AssistantState.EXECUTING: {AssistantState.SPEAKING, AssistantState.IDLE, AssistantState.LISTENING_FOR_WAKE_WORD},
    AssistantState.SPEAKING: {AssistantState.IDLE, AssistantState.LISTENING_FOR_WAKE_WORD,
                              AssistantState.LISTENING_FOR_COMMAND, AssistantState.PROCESSING},
}


class StateMachine:
    def __init__(self) -> None:
        self._state = AssistantState.IDLE
        self._data: dict[str, Any] = {}
        self._lock = threading.RLock()

    @property
    def state(self) -> AssistantState:
        with self._lock:
            return self._state

    def transition(self, state: AssistantState, **data: Any) -> None:
        with self._lock:
            if state not in ALLOWED_TRANSITIONS[self._state]:
                raise ValueError(f"Invalid state transition: {self._state.value} -> {state.value}")
            self._state = state
            self._data.update(data)

    def update(self, **data: Any) -> None:
        with self._lock:
            self._data.update(data)

    def reset(self, state: AssistantState = AssistantState.IDLE) -> None:
        """Recover to a known state after a hardware/model error."""
        with self._lock:
            self._state = state

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {"state": self._state.value, **self._data}
