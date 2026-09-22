#!/usr/bin/env python3
"""Benchmark edge cluster throughput and failover."""
import argparse, json, time
from pathlib import Path
import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--orchestrator", default="http://localhost:9090")
    parser.add_argument("--requests", type=int, default=10)
    parser.add_argument("--output", default="demo/cluster_benchmark.json")
    args = parser.parse_args()

    url = f"{args.orchestrator}/v1/chat/completions"
    prompt = "Summarize the benefits of local AI in one sentence."
    results = []
    start = time.time()
    for i in range(args.requests):
        try:
            r_start = time.time()
            resp = requests.post(url, json={"model": "llama3.1", "messages": [{"role": "user", "content": prompt}]}, timeout=30)
            latency = time.time() - r_start
            results.append({"status": resp.status_code, "latency_s": round(latency, 3)})
        except Exception as exc:
            results.append({"status": 0, "error": str(exc)})
    total = time.time() - start

    ok = [r for r in results if r["status"] == 200]
    throughput = len(ok) / total if total else 0.0
    report = {
        "total_requests": args.requests,
        "successful": len(ok),
        "throughput_req_per_s": round(throughput, 2),
        "total_time_s": round(total, 2),
        "details": results,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"[benchmark] throughput={throughput:.2f} req/s -> {args.output}")


if __name__ == "__main__":
    main()
