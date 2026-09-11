"""Windows UI actions with validated paths."""

from __future__ import annotations

import ctypes
import subprocess
from datetime import datetime
from pathlib import Path


def open_folder(target: str, popen: object = subprocess.Popen) -> str:
    path = Path(target).expanduser().resolve(strict=True)
    if not path.is_dir():
        raise NotADirectoryError(str(path))
    popen(["explorer.exe", str(path)], shell=False)
    return str(path)


def screenshot(directory: str | Path = "screenshots") -> str:
    import pyautogui
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / f"screenshot-{datetime.now():%Y%m%d-%H%M%S}.png"
    pyautogui.screenshot(str(path))
    return str(path)


def lock_pc() -> None:
    if not ctypes.windll.user32.LockWorkStation():
        raise OSError("LockWorkStation failed")

