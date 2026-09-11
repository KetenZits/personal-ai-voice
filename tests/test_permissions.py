import time

from brain.permissions import ConfirmationManager, PermissionManager
from brain.schemas import Action, ActionType, AuthorizationContext
from config.loader import PermissionConfig


def test_permission_levels_and_confirmation() -> None:
    manager = PermissionManager({
        "get_time": PermissionConfig(level=0),
        "open_app": PermissionConfig(level=1),
        "shutdown": PermissionConfig(level=2, confirmation=True),
        "run_shell": PermissionConfig(enabled=False, level=3),
    })
    anonymous = AuthorizationContext()
    owner = AuthorizationContext(speaker_verified=True)
    assert manager.check(Action(type=ActionType.GET_TIME), anonymous).allowed
    assert not manager.check(Action(type=ActionType.OPEN_APP, target="vscode"), anonymous).allowed
    assert manager.check(Action(type=ActionType.OPEN_APP, target="vscode"), owner).allowed
    assert manager.check(Action(type=ActionType.SHUTDOWN), owner).requires_confirmation
    assert not manager.check(Action(type=ActionType.UNKNOWN), owner).allowed


def test_confirmation_is_single_use_and_expires() -> None:
    action = Action(type=ActionType.SHUTDOWN)
    manager = ConfirmationManager(timeout_seconds=1)
    pending = manager.request(action)
    assert manager.respond("ยืนยัน!", pending.token) == action
    assert manager.respond("confirm", pending.token) is None
    expiring = ConfirmationManager(timeout_seconds=0.01)
    pending = expiring.request(action)
    time.sleep(0.03)
    assert expiring.respond("confirm", pending.token) is None


def test_replay_protection_master_switch() -> None:
    action = Action(type=ActionType.LOCK_PC)
    policy = {"lock_pc": PermissionConfig(level=2, confirmation=True, challenge=True)}
    owner = AuthorizationContext(speaker_verified=True)
    disabled = PermissionManager(policy, replay_enabled=False)
    enabled = PermissionManager(policy, replay_enabled=True, challenge_for_level=2)
    assert not disabled.check(action, owner).requires_challenge
    assert disabled.check(action, owner).requires_confirmation
    assert enabled.check(action, owner).requires_challenge
