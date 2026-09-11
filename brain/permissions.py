"""Central authorization and expiring confirmation state."""

from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass

from config.loader import PermissionConfig

from .schemas import Action, AuthorizationContext, PermissionDecision


class PermissionManager:
    def __init__(self, policies: dict[str, PermissionConfig]) -> None:
        self._policies = policies

    def check(self, action: Action, auth: AuthorizationContext) -> PermissionDecision:
        policy = self._policies.get(action.type.value)
        if policy is None:
            return PermissionDecision(allowed=False, reason="Action has no permission policy")
        if not policy.enabled:
            return PermissionDecision(allowed=False, reason="Action is disabled", level=policy.level)
        if policy.level >= 1 and not auth.speaker_verified:
            return PermissionDecision(
                allowed=False,
                reason="Authorized speaker required",
                level=policy.level,
            )
        if policy.challenge and not auth.challenge_passed:
            return PermissionDecision(
                allowed=False,
                requires_challenge=True,
                reason="Challenge-response required",
                level=policy.level,
            )
        return PermissionDecision(
            allowed=not policy.confirmation,
            requires_confirmation=policy.confirmation,
            level=policy.level,
            reason="Confirmation required" if policy.confirmation else "Allowed",
        )


@dataclass(frozen=True)
class PendingConfirmation:
    token: str
    action: Action
    expires_at: float


class ConfirmationManager:
    """Stores exactly one pending action and consumes it at most once."""

    YES_WORDS = {"yes", "confirm", "confirmed", "ok", "okay", "ยืนยัน", "ใช่", "ตกลง"}
    NO_WORDS = {"no", "cancel", "stop", "ไม่", "ยกเลิก"}

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self.timeout_seconds = timeout_seconds
        self._pending: PendingConfirmation | None = None
        self._lock = threading.Lock()

    def request(self, action: Action) -> PendingConfirmation:
        with self._lock:
            pending = PendingConfirmation(
                token=secrets.token_urlsafe(16),
                action=action,
                expires_at=time.monotonic() + self.timeout_seconds,
            )
            self._pending = pending
            return pending

    def respond(self, text: str, token: str | None = None) -> Action | None:
        normalized = text.casefold().strip()
        with self._lock:
            pending, self._pending = self._pending, None
            if pending is None or time.monotonic() > pending.expires_at:
                return None
            if token is not None and not secrets.compare_digest(token, pending.token):
                return None
            if any(word == normalized or word in normalized.split() for word in self.NO_WORDS):
                return None
            if any(word == normalized or word in normalized.split() for word in self.YES_WORDS):
                return pending.action
            return None

    def cancel(self) -> None:
        with self._lock:
            self._pending = None

    @property
    def pending(self) -> PendingConfirmation | None:
        with self._lock:
            if self._pending and time.monotonic() > self._pending.expires_at:
                self._pending = None
            return self._pending

