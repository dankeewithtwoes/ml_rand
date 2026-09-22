"""Local microphone, speech-to-text, and text-to-speech primitives.

All optional native dependencies are imported at the point of use.  Missing
drivers/models therefore produce actionable errors, never fake transcripts or
files containing text with a ``.wav`` extension.
"""
from __future__ import annotations

import math
import time
import uuid
import wave
from pathlib import Path


class AudioError(RuntimeError):
    """Base class for local audio failures."""


class AudioDependencyError(AudioError):
    """Raised when an installed local audio component is missing."""


class AudioRuntimeError(AudioError):
    """Raised when a device, model, or local speech engine fails."""


def _validate_wav(path: Path) -> int:
    """Return frame count when *path* is a non-empty PCM WAV."""
    try:
        with wave.open(str(path), "rb") as wav_file:
            frames = wav_file.getnframes()
            if frames <= 0 or wav_file.getnchannels() <= 0 or wav_file.getframerate() <= 0:
                raise AudioRuntimeError(f"WAV contains no playable audio frames: {path}")
            return frames
    except AudioRuntimeError:
        raise
    except (OSError, EOFError, wave.Error) as exc:
        raise AudioRuntimeError(f"not a valid WAV file: {path}: {exc}") from exc


def _temporary_wav(output: Path) -> Path:
    return output.with_name(f".{output.stem}.{uuid.uuid4().hex}.partial.wav")


def record_wav(
    output: Path | str,
    seconds: float,
    *,
    sample_rate: int = 16_000,
    channels: int = 1,
    block_frames: int = 1_024,
) -> Path:
    """Record signed 16-bit microphone samples to an atomic WAV output."""
    if seconds <= 0:
        raise AudioRuntimeError("recording duration must be positive")
    if sample_rate <= 0 or channels <= 0 or block_frames <= 0:
        raise AudioRuntimeError("sample rate, channels, and block size must be positive")
    try:
        import sounddevice as sd
    except (ImportError, OSError) as exc:
        raise AudioDependencyError(
            "microphone recording requires sounddevice and a working PortAudio driver"
        ) from exc

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = _temporary_wav(output)
    total_frames = math.ceil(seconds * sample_rate)
    captured: list[bytes] = []
    try:
        with sd.RawInputStream(
            samplerate=sample_rate,
            channels=channels,
            dtype="int16",
            blocksize=min(block_frames, total_frames),
        ) as stream:
            remaining = total_frames
            while remaining:
                frames_to_read = min(block_frames, remaining)
                data, overflowed = stream.read(frames_to_read)
                if overflowed:
                    raise AudioRuntimeError("microphone input overflowed; recording was discarded")
                captured.append(bytes(data))
                remaining -= frames_to_read

        with wave.open(str(partial), "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b"".join(captured))
        _validate_wav(partial)
        partial.replace(output)
        return output
    except AudioError:
        partial.unlink(missing_ok=True)
        raise
    except Exception as exc:
        partial.unlink(missing_ok=True)
        raise AudioRuntimeError(f"microphone recording failed: {exc}") from exc


def transcribe_wav(
    audio_path: Path | str,
    *,
    model: str = "small",
    device: str = "cpu",
    compute_type: str = "int8",
    language: str | None = None,
) -> str:
    """Transcribe audio locally with faster-whisper."""
    audio_path = Path(audio_path)
    if not audio_path.is_file():
        raise AudioRuntimeError(f"audio file does not exist: {audio_path}")
    if audio_path.suffix.lower() == ".wav":
        _validate_wav(audio_path)
    try:
        from faster_whisper import WhisperModel
    except (ImportError, OSError) as exc:
        raise AudioDependencyError(
            "speech recognition requires faster-whisper (pip install -r requirements.txt)"
        ) from exc
    try:
        whisper = WhisperModel(model, device=device, compute_type=compute_type)
        segments, _info = whisper.transcribe(
            str(audio_path), language=language, vad_filter=True, beam_size=5
        )
        transcript = " ".join(
            str(segment.text).strip() for segment in segments if str(segment.text).strip()
        ).strip()
    except Exception as exc:
        raise AudioRuntimeError(f"local Whisper transcription failed: {exc}") from exc
    if not transcript:
        raise AudioRuntimeError("local Whisper returned an empty transcript")
    return transcript


def _configure_tts(engine, voice_id: str | None, rate: int | None) -> None:
    if voice_id:
        engine.setProperty("voice", voice_id)
    if rate is not None:
        if rate <= 0:
            raise AudioRuntimeError("speech rate must be positive")
        engine.setProperty("rate", rate)


def _tts_engine():
    try:
        import pyttsx3
    except (ImportError, OSError) as exc:
        raise AudioDependencyError(
            "text-to-speech requires pyttsx3 and a local system speech engine"
        ) from exc
    try:
        return pyttsx3.init()
    except Exception as exc:
        raise AudioRuntimeError(f"local text-to-speech engine failed to initialize: {exc}") from exc


def synthesize_wav(
    text: str,
    output: Path | str,
    *,
    voice_id: str | None = None,
    rate: int | None = None,
) -> float:
    """Synthesize speech locally and atomically publish a verified WAV."""
    if not text.strip():
        raise AudioRuntimeError("text-to-speech input cannot be empty")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = _temporary_wav(output)
    started = time.perf_counter()
    try:
        engine = _tts_engine()
        _configure_tts(engine, voice_id, rate)
        engine.save_to_file(text, str(partial))
        engine.runAndWait()
        _validate_wav(partial)
        partial.replace(output)
        return time.perf_counter() - started
    except AudioError:
        partial.unlink(missing_ok=True)
        raise
    except Exception as exc:
        partial.unlink(missing_ok=True)
        raise AudioRuntimeError(f"local text-to-speech synthesis failed: {exc}") from exc


def speak_text(text: str, *, voice_id: str | None = None, rate: int | None = None) -> float:
    """Speak text through the local system output device."""
    if not text.strip():
        raise AudioRuntimeError("text-to-speech input cannot be empty")
    started = time.perf_counter()
    try:
        engine = _tts_engine()
        _configure_tts(engine, voice_id, rate)
        engine.say(text)
        engine.runAndWait()
        return time.perf_counter() - started
    except AudioError:
        raise
    except Exception as exc:
        raise AudioRuntimeError(f"local speech playback failed: {exc}") from exc
