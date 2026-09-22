#!/usr/bin/env python3
"""Offline demo of sentence-level grounding.

Uses the project documents as the evidence base (the same text the hybrid
retriever would return) and checks three generated answers against it:

1. a supported answer paraphrased from the documents,
2. a mixed answer with one hallucinated claim,
3. an answer on a topic the documents never mention.

Requires no third-party packages, no model downloads and no network.
Writes the full report to examples/grounding_report.json.
"""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from grounding import sentence_grounding

CASES = [
    {
        "label": "supported answer",
        "answer": (
            "Product A is an analytics platform. "
            "Its benefits include real-time dashboards and low-latency queries."
        ),
    },
    {
        "label": "mixed answer with a hallucinated claim",
        "answer": (
            "Product B classifies support tickets with language models. "
            "Product B also offers a free tier with unlimited storage."
        ),
    },
    {
        "label": "answer outside the evidence base",
        "answer": "The platform was founded in 1998 and is headquartered in Oslo.",
    },
]


def main() -> None:
    contexts = [
        path.read_text(encoding="utf-8")
        for path in sorted((PROJECT_ROOT / "documents").glob("*.txt"))
    ]
    report = {
        "evidence_sources": [p.name for p in sorted((PROJECT_ROOT / "documents").glob("*.txt"))],
        "cases": [],
    }
    for case in CASES:
        result = sentence_grounding(case["answer"], contexts)
        report["cases"].append({"label": case["label"], "answer": case["answer"], **result})

        flagged = [s for s in result["sentences"] if not s["grounded"]]
        print(f"[{case['label']}] grounded ratio: {result['grounded_sentence_ratio']:.2f}")
        for item in result["sentences"]:
            mark = "ok " if item["grounded"] else "FLAG"
            print(f"  {mark} coverage={item['coverage']:.2f}  {item['sentence']}")
        print(f"  -> {len(flagged)} unsupported sentence(s)\n")

    out = PROJECT_ROOT / "examples" / "grounding_report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Full report written to {out.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
