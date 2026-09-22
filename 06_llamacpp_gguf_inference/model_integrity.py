"""Streaming model-file integrity checks for reproducible GGUF benchmarks."""
import hashlib
from pathlib import Path


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_file(path: Path, expected_sha256: str | None = None, minimum_bytes: int = 1) -> dict:
    if not path.is_file():
        return {"valid": False, "error": "file not found", "path": str(path)}
    size = path.stat().st_size
    actual = sha256_file(path)
    valid = size >= minimum_bytes and (expected_sha256 is None or actual.lower() == expected_sha256.lower())
    return {"valid": valid, "path": str(path), "bytes": size, "sha256": actual,
            "error": None if valid else "size or checksum mismatch"}
