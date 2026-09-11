"""Interactively collect owner or negative speaker recordings."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np

from audio.utils import save_wav


PROMPTS = [
    "Hey Nova, please open my editor", "Today I am testing my personal assistant",
    "สวัสดีโนวา เปิดโปรแกรมให้หน่อย", "ช่วยบอกเวลาตอนนี้ให้หน่อย",
    "The quick brown fox jumps over the lazy dog", "เพิ่มเสียงเป็นห้าสิบเปอร์เซ็นต์",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", choices=["owner", "negatives"], default="owner")
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--seconds", type=float, default=4.0)
    parser.add_argument("--device", default=None)
    parser.add_argument("--sample-rate", type=int, default=16000)
    args = parser.parse_args()
    import sounddevice as sd
    output = Path("data/speakers") / args.label
    output.mkdir(parents=True, exist_ok=True)
    print("Vary speaking pace, distance, and volume. Record in several sessions if possible.")
    for index in range(args.count):
        prompt = PROMPTS[index % len(PROMPTS)]
        input(f"[{index + 1}/{args.count}] Press Enter then say: {prompt}\n")
        recording = sd.rec(int(args.seconds * args.sample_rate), samplerate=args.sample_rate,
                           channels=1, dtype="float32", device=args.device)
        sd.wait()
        path = output / f"{args.label}-{int(time.time() * 1000)}.wav"
        save_wav(path, np.asarray(recording)[:, 0], args.sample_rate)
        print(f"Saved {path}")


if __name__ == "__main__": main()

