"""Deterministic offline field extraction from plain text.

Fallback extractor used when no LLM is available (`--no-llm`): parses
line-oriented ``Key: Value`` pairs with no model, no PDF library, and no
network access. Extraction is a heuristic — every returned field is later
grounded against the source text by ``evidence.attach_evidence``.
"""


def extract_fields(text: str) -> dict:
    """Extract ``Key: Value`` pairs from plain-text lines.

    The first occurrence of a key wins, keys are lower-cased and
    whitespace-normalized, and values are stripped. Lines without a colon,
    empty keys/values, and keys longer than 40 characters are ignored.
    """
    fields: dict[str, str] = {}
    for line in text.splitlines():
        key, sep, value = line.partition(":")
        if not sep:
            continue
        key = " ".join(key.split()).strip().lower()
        value = value.strip()
        if not key or not value or len(key) > 40:
            continue
        fields.setdefault(key, value)
    return fields
