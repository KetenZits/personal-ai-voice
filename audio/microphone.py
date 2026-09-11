"""Reusable blocking microphone stream built on sounddevice."""

from __future__ import annotations

import queue
from collections.abc import Iterator
from typing import Any

import numpy as np


def list_input_devices() -> list[dict[str, Any]]:
    import sounddevice as sd
    devices = []
    for index, device in enumerate(sd.query_devices()):
        if int(device["max_input_channels"]) > 0:
            devices.append({
                "index": index,
                "name": str(device["name"]),
                "channels": int(device["max_input_channels"]),
                "default_sample_rate": int(device["default_samplerate"]),
            })
    return devices


class MicrophoneStream:
    def __init__(self, sample_rate: int = 16000, frame_ms: int = 30, device: int | str | None = None) -> None:
        self.sample_rate = sample_rate
        self.frame_ms = frame_ms
        self.device = device
        self.blocksize = sample_rate * frame_ms // 1000
        self._queue: queue.Queue[np.ndarray | None] = queue.Queue(maxsize=100)
        self._stream: object | None = None

    def _callback(self, indata: np.ndarray, frames: int, time_info: object, status: object) -> None:
        if status:
            # Status is not fatal; overruns are surfaced by the logging layer.
            pass
        frame = np.asarray(indata[:, 0], dtype=np.float32).copy()
        try:
            self._queue.put_nowait(frame)
        except queue.Full:
            try:
                self._queue.get_nowait()
                self._queue.put_nowait(frame)
            except queue.Empty:
                pass

    def __enter__(self) -> "MicrophoneStream":
        import sounddevice as sd
        self._stream = sd.InputStream(
            samplerate=self.sample_rate, blocksize=self.blocksize, device=self.device,
            channels=1, dtype="float32", callback=self._callback,
        )
        self._stream.start()
        return self

    def __exit__(self, *args: object) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
        self._stream = None

    def frames(self) -> Iterator[np.ndarray]:
        while self._stream is not None:
            frame = self._queue.get()
            if frame is None:
                break
            yield frame

