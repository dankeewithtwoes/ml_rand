"""Trace structured fields back to source text offsets."""


def attach_evidence(fields: dict, source: str) -> dict:
    lower = source.lower(); result = {}
    for key, value in fields.items():
        needle = str(value).strip(); start = lower.find(needle.lower()) if needle else -1
        result[key] = {"value": value, "evidence": None if start < 0 else {"start": start, "end": start + len(needle), "quote": source[start:start + len(needle)]},
                       "grounded": start >= 0}
    return result


def evidence_coverage(fields: dict) -> float:
    return sum(bool(item.get("grounded")) for item in fields.values()) / len(fields) if fields else 1.0
