"""Dependency-light reliability metrics for binary classifiers."""
from __future__ import annotations


def calibration_report(probabilities: list[float], labels: list[int], bins: int = 10) -> dict:
    if len(probabilities) != len(labels) or not probabilities:
        raise ValueError("probabilities and labels must have the same non-zero length")
    if bins < 1 or any(not 0 <= p <= 1 for p in probabilities):
        raise ValueError("bins must be positive and probabilities must be in [0, 1]")
    if any(label not in (0, 1) for label in labels):
        raise ValueError("labels must be binary")

    brier = sum((p - y) ** 2 for p, y in zip(probabilities, labels)) / len(labels)
    buckets = []
    ece = 0.0
    for index in range(bins):
        low, high = index / bins, (index + 1) / bins
        members = [(p, y) for p, y in zip(probabilities, labels) if low <= p < high or (index == bins - 1 and p == 1)]
        if not members:
            continue
        confidence = sum(p for p, _ in members) / len(members)
        accuracy = sum(y for _, y in members) / len(members)
        ece += len(members) / len(labels) * abs(accuracy - confidence)
        buckets.append({"range": [low, high], "count": len(members), "confidence": confidence, "accuracy": accuracy})
    return {"brier_score": brier, "expected_calibration_error": ece, "bins": buckets}
