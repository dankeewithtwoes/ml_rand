#!/usr/bin/env python3
"""Simple CLI dashboard for local AI observability logs."""
import argparse, json
from pathlib import Path
from collections import Counter


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default="demo/guard_logs.jsonl")
    parser.add_argument("--output", default="demo/dashboard.json")
    args = parser.parse_args()

    log_path = Path(args.log)
    if not log_path.exists():
        print("[dashboard] no logs yet")
        return

    entries = [json.loads(line) for line in log_path.read_text(encoding="utf-8").strip().splitlines()]
    total = len(entries)
    latencies = [e["latency_s"] for e in entries if e.get("latency_s")]
    blocks = sum(1 for e in entries if e.get("checks", {}).get("toxicity") or e.get("checks", {}).get("injection") or e.get("checks", {}).get("pii"))
    models = Counter(e.get("model") for e in entries)
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    report = {
        "total_calls": total,
        "blocked_calls": blocks,
        "avg_latency_s": round(avg_latency, 3),
        "p50_latency_s": round(sorted(latencies)[len(latencies)//2], 3) if latencies else 0.0,
        "models": dict(models),
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"[dashboard] {report}")


if __name__ == "__main__":
    main()
