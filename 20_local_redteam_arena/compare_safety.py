#!/usr/bin/env python3
"""Compare safety scores across multiple local models."""
import argparse, json, subprocess
from pathlib import Path
from safety_metrics import wilson_interval


def run_redteam(model: str) -> dict:
    result = subprocess.run(
        ["python", "redteam.py", "--model", model, "--count", "6", "--output", f"demo/redteam_{model.replace('/', '_')}.json"],
        capture_output=True, text=True,
    )
    path = Path(f"demo/redteam_{model.replace('/', '_')}.json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8")).get("summary", {})
    return {}


def safety_score(summary: dict) -> float:
    scores = []
    for attack, metrics in summary.items():
        scores.append(1 - metrics.get("success_rate", 0.0))
    return sum(scores) / len(scores) if scores else 0.0


def safety_score_with_uncertainty(summary: dict, samples_per_attack: int = 1) -> dict:
    rates = [metrics.get("success_rate", 0.0) for metrics in summary.values()]
    total = len(rates) * samples_per_attack
    attacks = round(sum(rates) * samples_per_attack)
    low, high = wilson_interval(attacks, total)
    return {"safety_score": 1 - attacks / total if total else 0.0,
            "safety_ci95": [1 - high, 1 - low], "samples": total}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", default="llama3.1,phi3,qwen2.5")
    parser.add_argument("--output", default="demo/safety_comparison.json")
    args = parser.parse_args()

    models = [m.strip() for m in args.models.split(",")]
    comparison = []
    for model in models:
        print(f"[compare] {model}")
        summary = run_redteam(model)
        score = safety_score(summary)
        comparison.append({"model": model, "safety_score": round(score, 2), "summary": summary})

    comparison.sort(key=lambda x: x["safety_score"], reverse=True)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(comparison, indent=2, ensure_ascii=False))
    print(f"[compare] winner: {comparison[0]['model']} ({comparison[0]['safety_score']})")


if __name__ == "__main__":
    main()
