"""Privacy and diversity gates for synthetic instruction data."""
import hashlib
import re

PII = {"email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
       "phone": re.compile(r"(?<!\d)(?:\+?\d[\d ()-]{7,}\d)(?!\d)"),
       "api_key": re.compile(r"\b(?:sk-|api[_-]?key[=: ]+)[A-Za-z0-9_-]{12,}\b", re.I)}


def normalize(text: str) -> str: return " ".join(text.lower().split())


def audit(items: list[dict]) -> dict:
    seen, duplicates, pii = set(), [], []
    for index, item in enumerate(items):
        text = f"{item.get('instruction', '')} {item.get('output', '')}"
        digest = hashlib.sha256(normalize(text).encode()).hexdigest()
        if digest in seen: duplicates.append(index)
        seen.add(digest)
        found = [name for name, pattern in PII.items() if pattern.search(text)]
        if found: pii.append({"row": index, "types": found})
    return {"valid": not duplicates and not pii, "duplicates": duplicates, "pii": pii, "unique_ratio": len(seen) / len(items) if items else 0.0}
