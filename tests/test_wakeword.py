import numpy as np

from wakeword.inference import OpenWakeWordDetector


class FakeOpenWakeWordModel:
    def __init__(self) -> None:
        self.chunks: list[np.ndarray] = []
        self.reset_count = 0

    def predict(self, chunk: np.ndarray) -> dict[str, float]:
        self.chunks.append(chunk)
        return {"hey_nova_v1": 0.9}

    def reset(self) -> None:
        self.reset_count += 1


def test_openwakeword_buffers_vad_sized_frames() -> None:
    detector = OpenWakeWordDetector.__new__(OpenWakeWordDetector)
    detector.model = FakeOpenWakeWordModel()
    detector.phrase = "hey_nova"
    detector.threshold = 0.8
    detector.sample_rate = detector.input_sample_rate = 16000
    detector._pending = np.empty(0, dtype=np.float32)

    assert detector.process_frame(np.zeros(480, dtype=np.float32)) == (False, 0.0)
    assert detector.process_frame(np.zeros(480, dtype=np.float32)) == (False, 0.0)
    assert detector.process_frame(np.zeros(480, dtype=np.float32)) == (True, 0.9)
    assert detector.model.chunks[0].shape == (1280,)
    assert detector._pending.shape == (160,)

    detector.reset()
    assert detector._pending.size == 0
    assert detector.model.reset_count == 1
