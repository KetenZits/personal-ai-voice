from pathlib import Path
from unittest.mock import Mock

import pytest

from config.loader import AppConfig, ProjectConfig
from executor.apps import AppController
from executor.projects import ProjectController


def test_app_alias_resolution_and_safe_argv() -> None:
    popen = Mock()
    apps = AppController({"vscode": AppConfig(aliases=["visual studio code"], executable="code")}, popen=popen)
    assert apps.resolve("Visual Studio Code")[0] == "vscode"
    apps.open("vscode", [r"C:\Project;not-a-command"])
    popen.assert_called_once_with(["code", r"C:\Project;not-a-command"], shell=False)


def test_unknown_app_is_rejected() -> None:
    with pytest.raises(KeyError):
        AppController({}).open("notepad")


def test_project_alias_and_existing_path(tmp_path: Path) -> None:
    popen = Mock()
    apps = AppController({"vscode": AppConfig(executable="code")}, popen=popen)
    projects = ProjectController({"demo": ProjectConfig(aliases=["my demo"], path=str(tmp_path), editor="vscode")}, apps)
    assert projects.resolve("my demo")[0] == "demo"
    assert projects.open("my demo") == "demo"
    popen.assert_called_once_with(["code", str(tmp_path)], shell=False)

