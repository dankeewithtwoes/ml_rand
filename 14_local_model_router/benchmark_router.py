#!/usr/bin/env python3
"""Benchmark routing accuracy and cost savings on labeled samples."""
import argparse
import json
from pathlib import Path
from registry import ModelRegistry
from route import classify_intent, select_model


SAMPLES = [
    ("Переведи договор на английский", "legal", True),
    ("Напиши функцию сортировки на Python", "code", False),
    ("Расскажи сказку на ночь", "creative", False),
    ("Мой пароль от банка 1234", "private", True),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="demo/registry.json")
    parser.add_argument("--output", default="demo/router_benchmark.json")
    args = parser.parse_args()

    reg = ModelRegistry(Path(args.registry))
    correct = 0
    cloud_only_cost = 0.0
    routed_cost = 0.0
    results = []
    for prompt, expected_intent, private in SAMPLES:
        intent = classify_intent(prompt)
        model = select_model(reg, prompt, private)
        hit = intent == expected_intent
        correct += int(hit)
        cloud_only_cost += 0.00015  # assume ~1k tokens
        routed_cost += model.get("cost_per_1k_tokens", 0.0)
        results.append({
            "prompt": prompt,
            "expected_intent": expected_intent,
            "predicted_intent": intent,
            "selected_model": model["name"],
            "private": private,
        })

    accuracy = correct / len(SAMPLES)
    savings = cloud_only_cost - routed_cost
    summary = {
        "routing_accuracy": round(accuracy, 2),
        "cloud_only_cost": round(cloud_only_cost, 5),
        "routed_cost": round(routed_cost, 5),
        "cost_saved": round(savings, 5),
        "details": results,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[benchmark] accuracy={accuracy:.2f} cost_saved=${savings:.5f} -> {args.output}")


if __name__ == "__main__":
    main()
