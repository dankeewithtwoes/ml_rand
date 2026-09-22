"""Transparent multi-objective scoring for local model benchmark results."""
from __future__ import annotations


def rank_results(results: list[dict], quality_weight: float = 0.6, speed_weight: float = 0.4) -> list[dict]:
    if not results:
        return []
    if quality_weight < 0 or speed_weight < 0 or quality_weight + speed_weight == 0:
        raise ValueError("weights must be non-negative and not both zero")
    max_speed = max(float(item.get("tokens_per_sec", 0)) for item in results) or 1.0
    ranked = []
    for item in results:
        quality = float(item.get("judge_score", 0)) / 5
        speed = float(item.get("tokens_per_sec", 0)) / max_speed
        score = (quality_weight * quality + speed_weight * speed) / (quality_weight + speed_weight)
        ranked.append({**item, "arena_score": round(score, 4),
                       "score_components": {"quality": quality, "relative_speed": speed}})
    return sorted(ranked, key=lambda item: (-item["arena_score"], item["model"]))
