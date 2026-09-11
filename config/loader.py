"""Typed YAML configuration loader with environment-variable expansion."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

ROOT = Path(__file__).resolve().parents[1]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AssistantConfig(StrictModel):
    name: str = "Nova"
    greeting: str = "ว่าไง"
    confirmation_timeout_seconds: float = Field(10.0, gt=0)


class AudioConfig(StrictModel):
    sample_rate: int = Field(16000, ge=8000)
    device: int | str | None = None
    frame_ms: Literal[10, 20, 30] = 30
    pre_roll_seconds: float = Field(1.0, ge=0, le=5)
    silence_seconds: float = Field(1.0, gt=0)
    max_command_seconds: float = Field(15.0, gt=1)
    vad_backend: Literal["auto", "webrtc", "energy"] = "auto"
    energy_threshold: float = Field(0.015, gt=0)


class WakeWordConfig(StrictModel):
    phrase: str = "Hey Nova"
    backend: Literal["custom", "openwakeword"] = "custom"
    model_path: str = "wakeword/models/best.pt"
    threshold: float = Field(0.80, ge=0, le=1)
    cooldown_seconds: float = Field(2.0, ge=0)


class SpeakerConfig(StrictModel):
    enabled: bool = True
    model_path: str = "speaker/models/best.joblib"
    enrollment_path: str = "speaker/models/owner_embedding.npy"
    threshold: float = Field(0.78, ge=-1, le=1)
    device: Literal["auto", "cpu", "cuda"] = "auto"


class STTConfig(StrictModel):
    model: str = "small"
    language: str = "auto"
    device: Literal["auto", "cpu", "cuda"] = "auto"
    compute_type: str = "auto"
    beam_size: int = Field(5, ge=1, le=20)


class IntentConfig(StrictModel):
    model_path: str = "intent/models/best.joblib"
    dataset_path: str = "intent/dataset/intents.json"
    threshold: float = Field(0.70, ge=0, le=1)
    allow_rule_fallback: bool = True


class TTSConfig(StrictModel):
    enabled: bool = True
    voice: str | None = None
    rate: int = Field(175, ge=50, le=400)
    volume: float = Field(1.0, ge=0, le=1)


class LLMConfig(StrictModel):
    enabled: bool = False
    url: str = "http://127.0.0.1:11434"
    model: str = "llama3.2:3b"
    timeout_seconds: float = Field(20, gt=0)


class LoggingConfig(StrictModel):
    level: str = "INFO"
    file: str = "logs/nova.jsonl"
    audio_enabled: bool = False


class ReplayProtectionConfig(StrictModel):
    enabled: bool = False
    challenge_for_level: int = Field(2, ge=0, le=3)


class Settings(StrictModel):
    assistant: AssistantConfig = AssistantConfig()
    audio: AudioConfig = AudioConfig()
    wakeword: WakeWordConfig = WakeWordConfig()
    speaker: SpeakerConfig = SpeakerConfig()
    stt: STTConfig = STTConfig()
    intent: IntentConfig = IntentConfig()
    tts: TTSConfig = TTSConfig()
    llm: LLMConfig = LLMConfig()
    logging: LoggingConfig = LoggingConfig()
    replay_protection: ReplayProtectionConfig = ReplayProtectionConfig()


class AppConfig(StrictModel):
    aliases: list[str] = []
    path: str | None = None
    executable: str | None = None
    process_names: list[str] = []

    @field_validator("aliases", "process_names")
    @classmethod
    def non_empty_values(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]


class ProjectConfig(StrictModel):
    aliases: list[str] = []
    path: str
    editor: str = "vscode"


class PermissionConfig(StrictModel):
    enabled: bool = True
    level: int = Field(0, ge=0, le=3)
    confirmation: bool = False
    challenge: bool = False


def _read_yaml(path: str | Path) -> dict[str, Any]:
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = ROOT / resolved
    if not resolved.exists():
        raise FileNotFoundError(f"Configuration file not found: {resolved}")
    raw = os.path.expandvars(resolved.read_text(encoding="utf-8"))
    data = yaml.safe_load(raw) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping in {resolved}")
    return data


def load_settings(path: str | Path = "config/settings.yaml") -> Settings:
    try:
        from dotenv import load_dotenv
    except ImportError:
        load_dotenv = None
    if load_dotenv is not None:
        load_dotenv(ROOT / ".env", override=False)
    data = _read_yaml(path)
    llm_overrides = {
        "url": os.getenv("NOVA_OLLAMA_URL"),
        "model": os.getenv("NOVA_OLLAMA_MODEL"),
    }
    if any(llm_overrides.values()):
        llm = dict(data.get("llm") or {})
        llm.update({key: value for key, value in llm_overrides.items() if value})
        data["llm"] = llm
    return Settings.model_validate(data)


def load_apps(path: str | Path = "config/apps.yaml") -> dict[str, AppConfig]:
    raw = _read_yaml(path).get("apps", {})
    return {name: AppConfig.model_validate(value or {}) for name, value in raw.items()}


def load_projects(path: str | Path = "config/projects.yaml") -> dict[str, ProjectConfig]:
    raw = _read_yaml(path).get("projects", {})
    return {name: ProjectConfig.model_validate(value or {}) for name, value in raw.items()}


def load_permissions(path: str | Path = "config/permissions.yaml") -> dict[str, PermissionConfig]:
    raw = _read_yaml(path).get("permissions", {})
    return {name.lower(): PermissionConfig.model_validate(value or {}) for name, value in raw.items()}
