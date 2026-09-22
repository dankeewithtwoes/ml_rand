"""Dependency-free local redaction and policy decisions."""
import hashlib
import re

PATTERNS = {"EMAIL": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
            "PHONE": re.compile(r"(?<!\d)(?:\+?\d[\d ()-]{7,}\d)(?!\d)"),
            "API_KEY": re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b")}


def redact(text: str) -> tuple[str, list[dict]]:
    findings = []
    for kind, pattern in PATTERNS.items():
        def replace(match):
            findings.append({"type": kind, "start": match.start(), "end": match.end()})
            return f"[{kind}_REDACTED]"
        text = pattern.sub(replace, text)
    return text, findings


def trace_summary(text: str) -> dict:
    return {"characters": len(text), "sha256": hashlib.sha256(text.encode()).hexdigest()}
