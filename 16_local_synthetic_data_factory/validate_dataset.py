#!/usr/bin/env python3
"""Validate synthetic dataset: schema coverage and diversity."""
import argparse, json
from pathlib import Path
from collections import Counter
from quality import audit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/synthetic.jsonl")
    parser.add_argument("--output", default="demo/validation.json")
    args = parser.parse_args()

    items = [json.loads(line) for line in Path(args.input).read_text(encoding="utf-8").strip().splitlines()]
    total = len(items)
    has_instruction = sum(1 for i in items if "instruction" in i)
    has_output = sum(1 for i in items if "output" in i)
    schema_coverage = (has_instruction + has_output) / (total * 2) if total else 0.0

    # Simple diversity: unique trigrams ratio
    all_text = " ".join(i.get("instruction", "") + " " + i.get("output", "") for i in items)
    words = all_text.lower().split()
    trigrams = set(zip(words, words[1:], words[2:]))
    diversity = len(trigrams) / max(1, len(words))

    report = {
        "total_samples": total,
        "schema_coverage": round(schema_coverage, 2),
        "diversity": round(diversity, 2),
        "avg_output_length": round(sum(len(i.get("output", "")) for i in items) / max(1, total), 1),
        "quality_gate": audit(items),
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"[validate] {report}")


if __name__ == "__main__":
    main()
