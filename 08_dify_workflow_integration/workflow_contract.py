"""Version and review Dify workflows without leaking credentials."""
import hashlib
import json

SECRET_KEYS = {"api_key", "apikey", "authorization", "password", "secret", "token"}


def redact(value):
    if isinstance(value, dict):
        return {key: ("***REDACTED***" if key.lower() in SECRET_KEYS else redact(item)) for key, item in value.items()}
    if isinstance(value, list): return [redact(item) for item in value]
    return value


def fingerprint(workflow: dict) -> str:
    canonical = json.dumps(redact(workflow), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def contract_diff(before: dict, after: dict) -> dict:
    old_inputs = set(before.get("inputs", {})); new_inputs = set(after.get("inputs", {}))
    return {"breaking": bool(old_inputs - new_inputs), "removed_inputs": sorted(old_inputs - new_inputs),
            "added_inputs": sorted(new_inputs - old_inputs), "changed": fingerprint(before) != fingerprint(after)}
