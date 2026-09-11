"""VAD-controlled utterance recorder with rolling pre-roll."""

from __future__ import annotations

from collections import deque

import numpy as np


class UtteranceRecorder:
    def __init__(self, vad: object, sample_rate: int = 16000, frame_ms: int = 30,
                 pre_roll_seconds: float = 0.6, silence_seconds: float = 1.0,
                 max_seconds: float = 15.0) -> None:
        self.vad = vad
        self.sample_rate = sample_rate
        self.frame_ms = frame_ms
        self.pre_roll_frames = max(1, int(pre_roll_seconds * 1000 / frame_ms))
        self.silence_frames = max(1, int(silence_seconds * 1000 / frame_ms))
        self.max_frames = max(1, int(max_seconds * 1000 / frame_ms))

    def record(self, frames: object) -> np.ndarray:
        pre_roll: deque[np.ndarray] = deque(maxlen=self.pre_roll_frames)
        recorded: list[np.ndarray] = []
        started = False
        silent = 0
        for frame in frames:
            frame = np.asarray(frame, dtype=np.float32)
            speech = self.vad.is_speech(frame)
            if not started:
                pre_roll.append(frame)
                if speech:
                    started = True
                    recorded.extend(pre_roll)
                continue
            recorded.append(frame)
            silent = 0 if speech else silent + 1
            if silent >= self.silence_frames or len(recorded) >= self.max_frames:
                break
        return np.concatenate(recorded) if recorded else np.empty(0, dtype=np.float32)

