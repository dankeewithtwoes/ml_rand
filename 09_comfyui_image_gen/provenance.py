"""Reproducible provenance records for generated media."""
import hashlib
import json
from pathlib import Path


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""): digest.update(chunk)
    return digest.hexdigest()


def generation_record(prompt: dict, images: list[Path], engine: str = "comfyui") -> dict:
    canonical = json.dumps(prompt, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return {"engine": engine, "workflow_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
            "images": [{"path": str(path), "sha256": file_sha256(path), "bytes": path.stat().st_size} for path in images]}
