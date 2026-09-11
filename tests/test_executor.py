from unittest.mock import Mock

from brain.schemas import Action, ActionType
from executor.executor import ActionExecutor


def test_executor_dispatches_only_typed_actions() -> None:
    hook = Mock(return_value=("safe", {"checked": True}))
    executor = ActionExecutor(Mock(), Mock(), hooks={ActionType.OPEN_APP: hook})
    action = Action(type=ActionType.OPEN_APP, target="vscode")
    result = executor.execute(action)
    assert result.success and result.data["checked"]
    hook.assert_called_once_with(action)


def test_unknown_is_never_executed() -> None:
    result = ActionExecutor(Mock(), Mock()).execute(Action(type=ActionType.UNKNOWN))
    assert not result.success
    assert "Unsupported action" in result.message

