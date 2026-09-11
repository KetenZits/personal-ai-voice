from pathlib import Path

import pytest

from config.loader import load_apps, load_permissions, load_projects, load_settings


def test_default_configuration_loads() -> None:
    assert load_settings().wakeword.phrase == "Hey Nova"
    assert "vscode" in load_apps()
    assert "study-platform" in load_projects()
    assert load_permissions()["shutdown"].confirmation


def test_invalid_configuration_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("wakeword:\n  threshold: 2\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_settings(path)


def test_ollama_environment_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOVA_OLLAMA_URL", "http://127.0.0.1:9999")
    monkeypatch.setenv("NOVA_OLLAMA_MODEL", "test-model")
    settings = load_settings()
    assert settings.llm.url == "http://127.0.0.1:9999"
    assert settings.llm.model == "test-model"
