"""Audit instruction-tuning JSONL data before expensive training starts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def normalized_fingerprint(item: dict) -> str:
    canonical = json.dumps(item, sort_keys=True, ensure_ascii=False).strip().lower()
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def audit_records(records: list[dict], required: tuple[str, ...] = ("instruction", "output")) -> dict:
    fingerprints: dict[str, int] = {}
    missing, empty = [], []
    for index, item in enumerate(records):
        absent = [field for field in required if field not in item]
        blank = [field for field in required if field in item and not str(item[field]).strip()]
        if absent: missing.append({"row": index, "fields": absent})
        if blank: empty.append({"row": index, "fields": blank})
        digest = normalized_fingerprint(item)
        fingerprints[digest] = fingerprints.get(digest, 0) + 1
    duplicates = sum(count - 1 for count in fingerprints.values() if count > 1)
    return {"records": len(records), "missing": missing, "empty": empty, "duplicates": duplicates,
            "valid": not missing and not empty and duplicates == 0}


def leakage_between(train: list[dict], validation: list[dict]) -> dict:
    train_hashes = {normalized_fingerprint(item) for item in train}
    leaked = [index for index, item in enumerate(validation) if normalized_fingerprint(item) in train_hashes]
    return {"overlap_count": len(leaked), "validation_rows": leaked, "valid": not leaked}
