"""Read-only system information plus explicit shutdown/restart helpers."""

from __future__ import annotations

import platform
import subprocess
from datetime import timedelta


def get_system_info() -> dict[str, object]:
    import psutil
    info: dict[str, object] = {
        "os": platform.platform(), "cpu_percent": psutil.cpu_percent(interval=0.2),
        "ram_percent": psutil.virtual_memory().percent,
        "uptime": str(timedelta(seconds=int(__import__("time").time() - psutil.boot_time()))),
    }
    try:
        import torch
        info["gpu"] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "No CUDA GPU"
    except ImportError:
        info["gpu"] = "PyTorch not installed"
    return info


def shutdown(restart: bool = False, runner: object = subprocess.run) -> None:
    # Static argument lists only. This function is reached only after permission/confirmation.
    args = ["shutdown.exe", "/r" if restart else "/s", "/t", "0"]
    runner(args, shell=False, check=True)

