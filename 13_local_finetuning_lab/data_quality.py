"""Deterministic, leakage-resistant dataset preparation."""
import hashlib
import json
import random


def fingerprint(item: dict) -> str:
    content = {key: " ".join(str(item.get(key, "")).split()).casefold()
               for key in ("instruction", "input", "output")}
    return hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def format_record(item: dict) -> str:
    text = f"### Instruction:\n{item['instruction']}"
    if item.get("input"):
        text += f"\n\n### Input:\n{item['input']}"
    return text + f"\n\n### Response:\n{item['output']}"


def validate(items: list[dict]) -> dict:
    errors, seen, duplicates = [], set(), []
    for index, item in enumerate(items):
        if not isinstance(item, dict): errors.append({"row": index, "error": "not an object"}); continue
        for field in ("instruction", "output"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append({"row": index, "error": f"{field} must be a non-empty string"})
        if "input" in item and not isinstance(item["input"], str):
            errors.append({"row": index, "error": "input must be a string"})
        digest = fingerprint(item)
        if digest in seen: duplicates.append(index)
        seen.add(digest)
    return {"valid": not errors and not duplicates, "errors": errors, "duplicates": duplicates}


def deterministic_split(items: list[dict], validation_ratio: float, seed: int = 42):
    if len(items) < 2 or not 0 < validation_ratio < 1: raise ValueError("need 2+ items and split in (0, 1)")
    shuffled = list(items); random.Random(seed).shuffle(shuffled)
    size = max(1, min(len(items) - 1, round(len(items) * validation_ratio)))
    return shuffled[size:], shuffled[:size]
