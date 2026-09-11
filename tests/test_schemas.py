import pytest
from pydantic import ValidationError

from brain.schemas import Action, ActionPlan, ActionType


def test_llm_action_contract_rejects_unknown_actions_and_fields() -> None:
    with pytest.raises(ValidationError):
        Action.model_validate({"type": "run_shell", "target": "whoami"})
    with pytest.raises(ValidationError):
        Action.model_validate({"type": "get_time", "command": "whoami"})


def test_action_plan_is_bounded() -> None:
    actions = [Action(type=ActionType.GET_TIME) for _ in range(9)]
    with pytest.raises(ValidationError):
        ActionPlan(actions=actions)
