"""Report local acceleration choices without requiring CUDA."""

from __future__ import annotations


def main() -> None:
    try:
        import torch
        available = torch.cuda.is_available()
        print(f"PyTorch CUDA available: {'YES' if available else 'NO'}")
        if available:
            print(f"GPU: {torch.cuda.get_device_name(0)}")
            print(f"CUDA: {torch.version.cuda}")
        else:
            print("GPU: CPU fallback")
            print("CUDA: unavailable")
        print(f"Whisper device: {'cuda' if available else 'cpu'}")
        print(f"Speaker model: {'cuda' if available else 'cpu'}")
    except ImportError:
        print("PyTorch CUDA available: NO (PyTorch is not installed)")
        print("Whisper device: cpu")
        print("Speaker model: cpu")


if __name__ == "__main__": main()

