"""Validated contracts passed between assistant components."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ActionType(str, Enum):
    OPEN_APP = "open_app"
    CLOSE_APP = "close_app"
    OPEN_PROJECT = "open_project"
    OPEN_FOLDER = "open_folder"
    OPEN_URL = "open_url"
    WEB_SEARCH = "web_search"
    VOLUME_UP = "volume_up"
    VOLUME_DOWN = "volume_down"
    SET_VOLUME = "set_volume"
    MUTE = "mute"
    UNMUTE = "unmute"
    MEDIA_PLAY = "media_play"
    MEDIA_PAUSE = "media_pause"
    MEDIA_NEXT = "media_next"
    MEDIA_PREVIOUS = "media_previous"
    SCREENSHOT = "screenshot"
    LOCK_PC = "lock_pc"
    RESTART = "restart"
    SHUTDOWN = "shutdown"
    GET_TIME = "get_time"
    GET_SYSTEM_INFO = "get_system_info"
    UNKNOWN = "unknown"


class Action(BaseModel):
    """A single allow-listed request. Extra LLM fields are rejected."""

    model_config = ConfigDict(extra="forbid")
    type: ActionType
    target: str | None = Field(default=None, max_length=2048)
    parameters: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = Field(default=None, ge=0, le=1)

    @field_validator("target")
    @classmethod
    def strip_target(cls, value: str | None) -> str | None:
        return value.strip() if value else value


class ActionPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actions: list[Action] = Field(default_factory=list, max_length=8)
    response: str | None = Field(default=None, max_length=1000)


class SpeechResult(BaseModel):
    text: str
    language: str | None = None
    confidence: float = Field(ge=0, le=1)
    duration_seconds: float | None = Field(default=None, ge=0)


class IntentResult(BaseModel):
    intent: str
    confidence: float = Field(ge=0, le=1)
    entities: dict[str, Any] = Field(default_factory=dict)


class ExecutionResult(BaseModel):
    action: ActionType
    success: bool
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    duration_seconds: float = Field(default=0, ge=0)


class AuthorizationContext(BaseModel):
    speaker_verified: bool = False
    speaker_score: float | None = None
    challenge_passed: bool = False


class PermissionDecision(BaseModel):
    allowed: bool
    requires_confirmation: bool = False
    requires_challenge: bool = False
    reason: str = ""
    level: int = 0
