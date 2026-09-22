"""Deterministic, leakage-resistant dataset preparation."""
import hashlib
import json
import random


def fingerprint(item: dict) -> str:
    return hashlib.sha256(json.dumps(item, sort_keys=True, ensure_ascii=False).strip().lower().encode()).hexdigest()


def validate(items: list[dict]) -> dict:
    errors, seen, duplicates = [], set(), []
    for index, item in enumerate(items):
        if not isinstance(item, dict): errors.append({"row": index, "error": "not an object"}); continue
        for field in ("instruction", "output"):
            if not str(item.get(field, "")).strip(): errors.append({"row": index, "error": f"empty {field}"})
        digest = fingerprint(item)
        if digest in seen: duplicates.append(index)
        seen.add(digest)
    return {"valid": not errors and not duplicates, "errors": errors, "duplicates": duplicates}


def deterministic_split(items: list[dict], validation_ratio: float, seed: int = 42):
    if len(items) < 2 or not 0 < validation_ratio < 1: raise ValueError("need 2+ items and split in (0, 1)")
    shuffled = list(items); random.Random(seed).shuffle(shuffled)
    size = max(1, min(len(items) - 1, round(len(items) * validation_ratio)))
    return shuffled[size:], shuffled[:size]
