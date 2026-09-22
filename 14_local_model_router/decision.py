"""Explainable constrained routing for local and cloud models."""
PRIVATE_MARKERS = {"password", "secret", "token", "ssn", "passport", "confidential", "private key"}


def contains_sensitive_data(prompt: str) -> bool:
    lower = prompt.lower()
    return any(marker in lower for marker in PRIVATE_MARKERS)


def choose(models: list[dict], intent: str, private: bool = False, max_cost: float | None = None,
           max_latency_ms: float | None = None) -> dict:
    candidates, rejected = [], []
    for model in models:
        reasons = []
        if private and model.get("type") != "local": reasons.append("privacy requires local execution")
        if max_cost is not None and model.get("cost_per_1k_tokens", 0) > max_cost: reasons.append("over cost budget")
        if max_latency_ms is not None and model.get("avg_latency_ms", float("inf")) > max_latency_ms: reasons.append("over latency budget")
        if reasons: rejected.append({"model": model.get("name"), "reasons": reasons}); continue
        match = intent in model.get("strengths", [])
        score = (1.0 if match else 0.0) - model.get("avg_latency_ms", 500) / 10000 - model.get("cost_per_1k_tokens", 0) * 100
        candidates.append((score, model, match))
    if not candidates: raise ValueError("no model satisfies routing constraints")
    score, model, match = max(candidates, key=lambda item: (item[0], item[1].get("name", "")))
    return {"model": model, "intent": intent, "score": round(score, 4), "privacy_required": private,
            "reasons": ["matched model strength" if match else "best available trade-off"], "rejected": rejected}
