"""Sentence-level evidence coverage metrics that work without an LLM judge.

The core check is deliberately dependency-free (stdlib only): it splits a
generated answer into sentences and measures how much of each sentence's
vocabulary is backed by the retrieved evidence. Sentences whose term coverage
falls below ``threshold`` are flagged as unsupported claims.

Semantics worth knowing before relying on the output:

- Terms are word tokens longer than two characters, lowercased; punctuation,
  case and hyphenated words are normalized away.
- A sentence with no usable terms (e.g. "OK.") is treated as neutral and
  counts as grounded — there is no claim to support.
- This is a lexical proxy, not an entailment model: a sentence that merely
  repeats evidence keywords can score as grounded (see README limitations).
"""
from __future__ import annotations

import re


def _terms(text: str) -> set[str]:
    return {word.lower() for word in re.findall(r"[\w-]+", text, flags=re.UNICODE) if len(word) > 2}


def sentence_grounding(answer: str, contexts: list[str], threshold: float = 0.35) -> dict:
    """Flag answer sentences that are not covered by the retrieved contexts.

    Returns a report with the ratio of grounded sentences and per-sentence
    coverage details. Raises ``TypeError`` for non-string input (a bare string
    passed as ``contexts`` would silently be treated as an iterable of
    characters) and ``ValueError`` for a threshold outside ``[0.0, 1.0]``.
    """
    if not isinstance(answer, str):
        raise TypeError(f"answer must be a string, got {type(answer).__name__}")
    if isinstance(contexts, str) or not isinstance(contexts, (list, tuple)):
        raise TypeError("contexts must be a list of context strings")
    for context in contexts:
        if not isinstance(context, str):
            raise TypeError(f"each context must be a string, got {type(context).__name__}")
    if not 0.0 <= threshold <= 1.0:
        raise ValueError(f"threshold must be within [0.0, 1.0], got {threshold}")

    evidence = _terms(" ".join(contexts))
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", answer) if part.strip()]
    details = []
    for sentence in sentences:
        terms = _terms(sentence)
        coverage = len(terms & evidence) / len(terms) if terms else 1.0
        details.append({"sentence": sentence, "coverage": coverage, "grounded": coverage >= threshold})
    score = sum(item["grounded"] for item in details) / len(details) if details else 0.0
    return {"grounded_sentence_ratio": score, "threshold": threshold, "sentences": details}
