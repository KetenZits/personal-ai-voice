"""Lightweight terminal debugging dashboard."""

from __future__ import annotations

from assistant_state import StateMachine


class DebugDashboard:
    def __init__(self, state: StateMachine, enabled: bool = False) -> None:
        self.state = state
        self.enabled = enabled

    def show(self) -> None:
        if not self.enabled:
            return
        snapshot = self.state.snapshot()
        fields = ["state", "microphone", "wake_word", "wake_confidence", "speaker",
                  "speaker_score", "transcription", "intent", "intent_confidence", "last_action"]
        print("\n[Nova debug] " + " | ".join(f"{key}={snapshot[key]}" for key in fields if key in snapshot))

