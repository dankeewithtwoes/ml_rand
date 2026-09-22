#!/usr/bin/env python3
"""Local microphone -> Whisper -> Ollama -> system TTS companion."""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
import time
from pathlib import Path

from audio_io import AudioError, record_wav, speak_text, transcribe_wav
from wake_word import extract_command


class CompanionError(RuntimeError):
    """Raised when the local LLM cannot produce a real answer."""


def query_llm(prompt: str) -> str:
    try:
        from openai import OpenAI
    except (ImportError, OSError) as exc:
        raise CompanionError("the local LLM client requires the openai package") from exc
    try:
        client = OpenAI(
            api_key="ollama",
            base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1"),
        )
        response = client.chat.completions.create(
            model=os.getenv("OLLAMA_MODEL", "llama3.1"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        answer = response.choices[0].message.content
    except Exception as exc:
        raise CompanionError(f"local Ollama client/request failed: {exc}") from exc
    if not isinstance(answer, str) or not answer.strip():
        raise CompanionError("local Ollama returned an empty answer")
    return answer.strip()


def simulate_wake_word(text: str, wake_word: str) -> bool:
    """Compatibility helper for wake-word behavior tests."""
    return extract_command(text, wake_word) is not None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fully local voice companion")
    parser.add_argument("--wake-word", default="компьютер")
    parser.add_argument("--text-input", action="store_true", help="Use a keyboard instead of the microphone")
    parser.add_argument("--record-seconds", type=float, default=5.0)
    parser.add_argument("--stt-model", default="small", help="faster-whisper model name or local model path")
    parser.add_argument("--stt-device", default="cpu")
    parser.add_argument("--compute-type", default="int8")
    parser.add_argument("--language", default="ru", help="Whisper language code; use 'auto' to detect")
    parser.add_argument("--no-tts", action="store_true", help="Print the answer without speaking it")
    parser.add_argument("--voice-id")
    parser.add_argument("--speech-rate", type=int)
    return parser


def run(args: argparse.Namespace) -> int:
    print(f"[companion] local wake word: {args.wake_word}")
    with tempfile.TemporaryDirectory(prefix="voice-companion-") as temp_dir:
        turn = 0
        while True:
            try:
                if args.text_input:
                    user_text = input("> ").strip()
                    if not user_text:
                        return 0
                else:
                    turn += 1
                    audio_path = Path(temp_dir) / f"turn-{turn}.wav"
                    print(f"[mic] recording {args.record_seconds:g}s...", flush=True)
                    record_wav(audio_path, args.record_seconds)
                    language = None if args.language.lower() == "auto" else args.language
                    user_text = transcribe_wav(
                        audio_path,
                        model=args.stt_model,
                        device=args.stt_device,
                        compute_type=args.compute_type,
                        language=language,
                    )
                    print(f"[stt] {user_text}")

                command = extract_command(user_text, args.wake_word)
                if command is None:
                    continue
                if not command:
                    print("[wake] say a command after the wake word")
                    continue
                started = time.perf_counter()
                answer = query_llm(command)
                print(f"[llm] {answer}")
                if not args.no_tts:
                    tts_seconds = speak_text(answer, voice_id=args.voice_id, rate=args.speech_rate)
                    print(f"[tts] played in {tts_seconds:.2f}s")
                print(f"[end-to-end] {time.perf_counter() - started:.2f}s")
            except (AudioError, CompanionError) as exc:
                print(f"[error] {exc}", file=sys.stderr)
                return 2
            except (EOFError, KeyboardInterrupt):
                return 0


def main() -> int:
    return run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
