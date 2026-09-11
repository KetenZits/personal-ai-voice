"""Single strict dispatch point for every executable action."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Callable

from brain.schemas import Action, ActionType, ExecutionResult

from . import browser, media, system, windows
from .apps import AppController
from .audio import AudioController
from .projects import ProjectController


class ActionExecutor:
    """Dispatch typed actions only; arbitrary commands have no execution path."""

    def __init__(self, apps: AppController, projects: ProjectController,
                 audio: AudioController | None = None,
                 hooks: dict[ActionType, Callable[[Action], tuple[str, dict[str, object]]]] | None = None) -> None:
        self.apps = apps
        self.projects = projects
        self.audio = audio or AudioController()
        self.hooks = hooks or {}

    @staticmethod
    def _target(action: Action) -> str:
        if not action.target:
            raise ValueError(f"{action.type.value} requires a target")
        return action.target

    def execute(self, action: Action) -> ExecutionResult:
        started = time.perf_counter()
        try:
            message, data = self._dispatch(action)
            return ExecutionResult(action=action.type, success=True, message=message, data=data,
                                   duration_seconds=time.perf_counter() - started)
        except Exception as exc:
            return ExecutionResult(action=action.type, success=False, message=str(exc),
                                   duration_seconds=time.perf_counter() - started)

    def _dispatch(self, action: Action) -> tuple[str, dict[str, object]]:
        if action.type in self.hooks:
            return self.hooks[action.type](action)
        if action.type == ActionType.OPEN_APP:
            name = self.apps.open(self._target(action)); return f"Opened {name}", {"app": name}
        if action.type == ActionType.CLOSE_APP:
            name, count = self.apps.close(self._target(action)); return f"Closed {name}", {"app": name, "processes": count}
        if action.type == ActionType.OPEN_PROJECT:
            name = self.projects.open(self._target(action)); return f"Opened project {name}", {"project": name}
        if action.type == ActionType.OPEN_FOLDER:
            path = windows.open_folder(self._target(action)); return f"Opened folder {path}", {"path": path}
        if action.type == ActionType.OPEN_URL:
            url = browser.open_url(self._target(action)); return f"Opened {url}", {"url": url}
        if action.type == ActionType.WEB_SEARCH:
            url = browser.web_search(self._target(action)); return "Search opened", {"url": url}
        if action.type == ActionType.VOLUME_UP:
            value = self.audio.adjust(5); return f"Volume is {value}%", {"volume": value}
        if action.type == ActionType.VOLUME_DOWN:
            value = self.audio.adjust(-5); return f"Volume is {value}%", {"volume": value}
        if action.type == ActionType.SET_VOLUME:
            if "volume" not in action.parameters:
                raise ValueError("set_volume requires a numeric volume")
            value = self.audio.set_volume(int(action.parameters["volume"])); return f"Volume is {value}%", {"volume": value}
        if action.type in {ActionType.MUTE, ActionType.UNMUTE}:
            muted = self.audio.mute(action.type == ActionType.MUTE); return ("Muted" if muted else "Unmuted"), {"muted": muted}
        if action.type in {ActionType.MEDIA_PLAY, ActionType.MEDIA_PAUSE, ActionType.MEDIA_NEXT, ActionType.MEDIA_PREVIOUS}:
            key = action.type.value.removeprefix("media_"); media.press_media(key); return f"Media {key}", {}
        if action.type == ActionType.SCREENSHOT:
            path = windows.screenshot(); return f"Screenshot saved to {path}", {"path": path}
        if action.type == ActionType.LOCK_PC:
            windows.lock_pc(); return "PC locked", {}
        if action.type == ActionType.GET_TIME:
            value = datetime.now().astimezone().isoformat(); return datetime.now().strftime("It is %H:%M"), {"time": value}
        if action.type == ActionType.GET_SYSTEM_INFO:
            info = system.get_system_info(); return f"CPU {info['cpu_percent']}%, RAM {info['ram_percent']}%", info
        if action.type == ActionType.RESTART:
            system.shutdown(restart=True); return "Restart requested", {}
        if action.type == ActionType.SHUTDOWN:
            system.shutdown(restart=False); return "Shutdown requested", {}
        raise ValueError(f"Unsupported action: {action.type.value}")

