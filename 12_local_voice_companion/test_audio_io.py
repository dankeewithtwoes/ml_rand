"""Behavior tests for real audio boundaries without requiring test hardware."""
from __future__ import annotations

import sys
import tempfile
import types
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audio_io import (
    AudioDependencyError,
    AudioRuntimeError,
    record_wav,
    synthesize_wav,
    transcribe_wav,
)


def _write_wav(path: Path, frames: int = 100) -> None:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16_000)
        wav_file.writeframes(b"\x00\x00" * frames)


class AudioIoTests(unittest.TestCase):
    def test_microphone_bytes_become_a_real_wav(self):
        class Stream:
            def __init__(self, **_kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self, frames):
                return b"\x01\x00" * frames, False

        fake = types.SimpleNamespace(RawInputStream=Stream)
        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(sys.modules, {"sounddevice": fake}):
            output = Path(temp_dir) / "mic.wav"
            record_wav(output, 0.01, sample_rate=1_000, block_frames=4)
            with wave.open(str(output), "rb") as wav_file:
                self.assertEqual(10, wav_file.getnframes())
                self.assertEqual(1_000, wav_file.getframerate())

    def test_missing_microphone_dependency_is_explicit(self):
        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(sys.modules, {"sounddevice": None}):
            with self.assertRaisesRegex(AudioDependencyError, "sounddevice"):
                record_wav(Path(temp_dir) / "mic.wav", 0.01)

    def test_local_whisper_transcript_is_returned(self):
        class Segment:
            def __init__(self, text):
                self.text = text

        class Model:
            def __init__(self, *_args, **_kwargs):
                pass

            def transcribe(self, *_args, **_kwargs):
                return iter([Segment(" hello "), Segment("world")]), object()

        fake = types.SimpleNamespace(WhisperModel=Model)
        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(sys.modules, {"faster_whisper": fake}):
            source = Path(temp_dir) / "speech.wav"
            _write_wav(source)
            self.assertEqual("hello world", transcribe_wav(source))

    def test_missing_stt_dependency_is_explicit(self):
        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(
            sys.modules, {"faster_whisper": None}
        ):
            source = Path(temp_dir) / "speech.wav"
            _write_wav(source)
            with self.assertRaisesRegex(AudioDependencyError, "faster-whisper"):
                transcribe_wav(source)

    def test_empty_transcript_is_an_error(self):
        class Model:
            def __init__(self, *_args, **_kwargs):
                pass

            def transcribe(self, *_args, **_kwargs):
                return iter(()), object()

        fake = types.SimpleNamespace(WhisperModel=Model)
        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(sys.modules, {"faster_whisper": fake}):
            source = Path(temp_dir) / "silence.wav"
            _write_wav(source)
            with self.assertRaisesRegex(AudioRuntimeError, "empty transcript"):
                transcribe_wav(source)

    def test_tts_publishes_only_a_valid_wav(self):
        class Engine:
            def save_to_file(self, _text, path):
                self.path = Path(path)

            def runAndWait(self):
                _write_wav(self.path)

            def setProperty(self, *_args):
                pass

        fake = types.SimpleNamespace(init=lambda: Engine())
        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(sys.modules, {"pyttsx3": fake}):
            output = Path(temp_dir) / "speech.wav"
            synthesize_wav("hello", output)
            with wave.open(str(output), "rb") as wav_file:
                self.assertGreater(wav_file.getnframes(), 0)

    def test_missing_tts_dependency_is_explicit_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(
            sys.modules, {"pyttsx3": None}
        ):
            output = Path(temp_dir) / "speech.wav"
            with self.assertRaisesRegex(AudioDependencyError, "pyttsx3"):
                synthesize_wav("hello", output)
            self.assertFalse(output.exists())

    def test_tts_failure_never_writes_text_disguised_as_wav(self):
        class Engine:
            def save_to_file(self, text, path):
                self.path = Path(path)
                self.text = text

            def runAndWait(self):
                self.path.write_text(self.text, encoding="utf-8")

            def setProperty(self, *_args):
                pass

        fake = types.SimpleNamespace(init=lambda: Engine())
        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(sys.modules, {"pyttsx3": fake}):
            output = Path(temp_dir) / "speech.wav"
            with self.assertRaisesRegex(AudioRuntimeError, "valid WAV"):
                synthesize_wav("this must not become a fake WAV", output)
            self.assertFalse(output.exists())
            self.assertEqual([], list(Path(temp_dir).glob("*.partial.wav")))


if __name__ == "__main__":
    unittest.main()
