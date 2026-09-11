"""Interactively collect positive or negative wake-word WAV samples."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np

from audio.utils import save_wav


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", choices=["positive", "negative"], default="positive")
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--seconds", type=float, default=2.5)
    parser.add_argument("--device", default=None)
    parser.add_argument("--sample-rate", type=int, default=16000)
    args = parser.parse_args()
    import sounddevice as sd
    output = Path("data/wakeword") / args.label
    output.mkdir(parents=True, exist_ok=True)
    print(f"Collecting {args.count} {args.label} samples in {output}. Press Enter for each sample.")
    for index in range(args.count):
        input(f"[{index + 1}/{args.count}] Press Enter, then speak... ")
        recording = sd.rec(int(args.seconds * args.sample_rate), samplerate=args.sample_rate,
                           channels=1, dtype="float32", device=args.device)
        sd.wait()
        path = output / f"{args.label}-{int(time.time() * 1000)}.wav"
        save_wav(path, np.asarray(recording)[:, 0], args.sample_rate)
        print(f"Saved {path}")


if __name__ == "__main__":
    main()

