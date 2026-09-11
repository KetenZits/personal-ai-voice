"""Allow-listed application resolution and launch/close operations."""

from __future__ import annotations

import subprocess
from pathlib import Path

from config.loader import AppConfig


class AppController:
    def __init__(self, apps: dict[str, AppConfig], popen: object = subprocess.Popen) -> None:
        self.apps = apps
        self._popen = popen

    def resolve(self, name: str) -> tuple[str, AppConfig] | None:
        needle = name.casefold().strip()
        for key, app in self.apps.items():
            if needle == key.casefold() or needle in {alias.casefold() for alias in app.aliases}:
                return key, app
        return None

    def command_for(self, app: AppConfig, extra: list[str] | None = None) -> list[str]:
        executable = app.path or app.executable
        if not executable:
            raise ValueError("Application has neither path nor executable")
        if app.path and not Path(app.path).is_file():
            raise FileNotFoundError(f"Configured application path does not exist: {app.path}")
        return [executable, *(extra or [])]

    def open(self, name: str, extra: list[str] | None = None) -> str:
        resolved = self.resolve(name)
        if resolved is None:
            raise KeyError(f"Application is not configured: {name}")
        key, app = resolved
        self._popen(self.command_for(app, extra), shell=False)
        return key

    def close(self, name: str) -> tuple[str, int]:
        import psutil
        resolved = self.resolve(name)
        if resolved is None:
            raise KeyError(f"Application is not configured: {name}")
        key, app = resolved
        allowed = {item.casefold() for item in app.process_names}
        if not allowed:
            raise ValueError(f"No process_names configured for {key}")
        count = 0
        for process in psutil.process_iter(["name"]):
            if (process.info["name"] or "").casefold() in allowed:
                process.terminate(); count += 1
        return key, count

