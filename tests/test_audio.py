import numpy as np

from audio.microphone import MicrophoneStream
from audio.recorder import UtteranceRecorder


class SequenceVAD:
    def __init__(self, decisions: list[bool]) -> None:
        self.decisions = iter(decisions)

    def is_speech(self, frame: np.ndarray) -> bool:
        return next(self.decisions)


def test_microphone_clear_discards_buffered_tts_frames() -> None:
    microphone = MicrophoneStream()
    microphone._queue.put_nowait(np.ones(10, dtype=np.float32))
    microphone._queue.put_nowait(np.ones(10, dtype=np.float32))
    assert microphone.clear() == 2
    assert microphone._queue.empty()


def test_recorder_keeps_preroll_and_stops_after_silence() -> None:
    frames = [np.full(4, number, dtype=np.float32) for number in range(6)]
    recorder = UtteranceRecorder(
        SequenceVAD([False, True, True, False, False, True]),
        sample_rate=100, frame_ms=10, pre_roll_seconds=0.02,
        silence_seconds=0.02, max_seconds=1,
    )
    result = recorder.record(iter(frames))
    assert result.tolist() == np.concatenate(frames[:5]).tolist()
