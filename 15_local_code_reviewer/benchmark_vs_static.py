#!/usr/bin/env python3
"""Compare local LLM reviewer against semgrep/bandit on synthetic code."""
import json, subprocess, sys
from pathlib import Path
from review import review_text


SAMPLES = [
    ("def login(user_input):\n    query = 'SELECT * FROM users WHERE name = ' + user_input\n", ["SQL injection"]),
    ("API_KEY = 'sk-1234567890abcdef'\n", ["hardcoded secret"]),
    ("os.system(user_input)\n", ["command injection"]),
    ("def add(a, b):\n    return a + b\n", []),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="demo/review_benchmark.json")
    args = parser.parse_args()

    tp = fp = fn = 0
    results = []
    for code, expected in SAMPLES:
        issues = review_text(code)
        predicted = len(issues) > 0
        actual = len(expected) > 0
        if predicted and actual:
            tp += 1
        elif predicted and not actual:
            fp += 1
        elif not predicted and actual:
            fn += 1
        results.append({"code": code.strip(), "issues": issues, "expected": expected})

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    summary = {
        "precision": round(precision, 2),
        "recall": round(recall, 2),
        "samples": results,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"[benchmark] precision={precision:.2f} recall={recall:.2f} -> {args.output}")


if __name__ == "__main__":
    main()
