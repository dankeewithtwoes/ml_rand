#!/usr/bin/env python3
"""Measure the real local STT -> Ollama -> TTS pipeline."""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

from audio_io import AudioError, synthesize_wav, transcribe_wav
from companion import CompanionError, query_llm


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark real local voice components")
    parser.add_argument("--audio", required=True, help="Recorded speech file for the STT stage")
    parser.add_argument("--model", default="small")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8")
    parser.add_argument("--language", default="auto")
    parser.add_argument("--output", default="demo/latency.json")
    args = parser.parse_args()
    try:
        language = None if args.language.lower() == "auto" else args.language
        started = time.perf_counter()
        transcript = transcribe_wav(
            args.audio,
            model=args.model,
            device=args.device,
            compute_type=args.compute_type,
            language=language,
        )
        stt_seconds = time.perf_counter() - started

        started = time.perf_counter()
        answer = query_llm(transcript)
        llm_seconds = time.perf_counter() - started

        with tempfile.TemporaryDirectory(prefix="voice-benchmark-") as temp_dir:
            tts_seconds = synthesize_wav(answer, Path(temp_dir) / "answer.wav")

        report = {
            "stt_seconds": round(stt_seconds, 4),
            "llm_seconds": round(llm_seconds, 4),
            "tts_seconds": round(tts_seconds, 4),
            "total_seconds": round(stt_seconds + llm_seconds + tts_seconds, 4),
            "transcript_characters": len(transcript),
            "answer_characters": len(answer),
            "stt_model": args.model,
            "stt_device": args.device,
        }
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False))
        return 0
    except (AudioError, CompanionError) as exc:
        print(f"[error] benchmark could not complete: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
