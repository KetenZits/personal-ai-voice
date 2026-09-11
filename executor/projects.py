"""Allow-listed project launching."""

from __future__ import annotations

from pathlib import Path

from config.loader import ProjectConfig

from .apps import AppController


class ProjectController:
    def __init__(self, projects: dict[str, ProjectConfig], apps: AppController) -> None:
        self.projects = projects
        self.apps = apps

    def resolve(self, name: str) -> tuple[str, ProjectConfig] | None:
        needle = name.casefold().strip()
        for key, project in self.projects.items():
            if needle == key.casefold() or needle in {alias.casefold() for alias in project.aliases}:
                return key, project
        return None

    def open(self, name: str) -> str:
        resolved = self.resolve(name)
        if resolved is None:
            raise KeyError(f"Project is not configured: {name}")
        key, project = resolved
        path = Path(project.path)
        if not path.is_dir():
            raise FileNotFoundError(f"Configured project directory does not exist: {path}")
        self.apps.open(project.editor, [str(path)])
        return key

