import pytest

from assistant_state import AssistantState, StateMachine


def test_state_machine_accepts_push_to_talk_verification_path() -> None:
    state = StateMachine()
    state.transition(AssistantState.LISTENING_FOR_COMMAND)
    state.transition(AssistantState.VERIFYING_SPEAKER)
    state.transition(AssistantState.PROCESSING)
    assert state.state == AssistantState.PROCESSING


def test_state_machine_rejects_invalid_transition_and_clears_on_reset() -> None:
    state = StateMachine()
    state.update(transcription="old")
    with pytest.raises(ValueError):
        state.transition(AssistantState.EXECUTING)
    state.reset()
    assert state.snapshot() == {"state": "IDLE"}
