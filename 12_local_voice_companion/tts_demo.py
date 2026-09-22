#!/usr/bin/env python3
"""Synthesize a verified WAV with the local operating-system speech engine."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from audio_io import AudioError, synthesize_wav


def synthesize(
    text: str,
    output: Path,
    voice_id: str | None = None,
    rate: int | None = None,
) -> float:
    return synthesize_wav(text, output, voice_id=voice_id, rate=rate)


def main() -> int:
    parser = argparse.ArgumentParser(description="Local pyttsx3 TTS demo")
    parser.add_argument("--text", default="Привет, я локальный ассистент.")
    parser.add_argument("--output", default="demo/tts_output.wav")
    parser.add_argument("--voice-id")
    parser.add_argument("--rate", type=int)
    args = parser.parse_args()
    try:
        output = Path(args.output)
        latency = synthesize(args.text, output, args.voice_id, args.rate)
        print(f"[tts] saved verified WAV {output} in {latency * 1000:.0f}ms")
        return 0
    except AudioError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
