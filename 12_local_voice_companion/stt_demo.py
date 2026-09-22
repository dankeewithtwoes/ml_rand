#!/usr/bin/env python3
"""Record or load audio and transcribe it locally with faster-whisper."""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from audio_io import AudioError, record_wav, transcribe_wav


def transcribe(
    audio_path: str | Path,
    model: str = "small",
    device: str = "cpu",
    compute_type: str = "int8",
    language: str | None = None,
) -> str:
    return transcribe_wav(
        audio_path, model=model, device=device, compute_type=compute_type, language=language
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Local faster-whisper STT demo")
    parser.add_argument("--audio", help="Existing WAV/audio file; omit to record the microphone")
    parser.add_argument("--record-seconds", type=float, default=5.0)
    parser.add_argument("--model", default="small", help="Model name or local faster-whisper model path")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8")
    parser.add_argument("--language", default="auto")
    args = parser.parse_args()
    try:
        language = None if args.language.lower() == "auto" else args.language
        if args.audio:
            text = transcribe(args.audio, args.model, args.device, args.compute_type, language)
        else:
            with tempfile.TemporaryDirectory(prefix="stt-demo-") as temp_dir:
                audio_path = Path(temp_dir) / "recording.wav"
                print(f"[mic] recording {args.record_seconds:g}s...", flush=True)
                record_wav(audio_path, args.record_seconds)
                text = transcribe(audio_path, args.model, args.device, args.compute_type, language)
        print(f"[stt] {text}")
        return 0
    except AudioError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
