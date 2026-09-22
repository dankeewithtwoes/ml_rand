#!/usr/bin/env python3
"""Offline demo: nearest-rank vs interpolated tail latency on a small sample.

Runs without a GPU, server, or network. Uses a fixed latency series so the
output is reproducible, and writes a JSON report to demo/tail_latency_report.json.
"""
import argparse
import json
import platform
import statistics
from datetime import datetime, timezone
from pathlib import Path

from latency_stats import percentile, summarize

# Fixed sample of 12 request latencies (seconds), as a small benchmark would
# record them: ten typical requests and two tail spikes.
SAMPLE_LATENCIES_S = [
    0.412, 0.389, 0.401, 0.376, 0.455, 0.398,
    0.421, 0.387, 0.512, 0.433, 0.968, 1.214,
]


def interpolated_percentile(values: list[float], quantile: float) -> float:
    """Linear-interpolation percentile (numpy/statistics 'inclusive' method)."""
    cuts = statistics.quantiles(sorted(values), n=100, method="inclusive")
    return cuts[max(0, round(quantile * 100) - 1)]


def build_report() -> dict:
    nearest_rank = summarize(SAMPLE_LATENCIES_S)
    interp_p95 = round(interpolated_percentile(SAMPLE_LATENCIES_S, 0.95), 4)
    interp_p99 = round(interpolated_percentile(SAMPLE_LATENCIES_S, 0.99), 4)
    return {
        "scenario": "small-sample tail latency (n=12 requests)",
        "latencies_s": SAMPLE_LATENCIES_S,
        "nearest_rank": {
            "count": nearest_rank["count"],
            "mean_s": round(nearest_rank["mean"], 4),
            "p50_s": round(nearest_rank["p50"], 4),
            "p95_s": round(nearest_rank["p95"], 4),
            "p99_s": round(nearest_rank["p99"], 4),
            "max_s": round(nearest_rank["max"], 4),
        },
        "linear_interpolation": {
            "p95_s": interp_p95,
            "p99_s": interp_p99,
        },
        "under_reported_by_interpolation_s": {
            "p95": round(nearest_rank["p95"] - interp_p95, 4),
            "p99": round(nearest_rank["p99"] - interp_p99, 4),
        },
        "environment": {
            "os": f"{platform.system()} {platform.release()}",
            "python": platform.python_version(),
            "cpu": platform.processor() or "unknown",
            "machine": platform.machine(),
            "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="demo/tail_latency_report.json")
    args = parser.parse_args()

    report = build_report()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    nr = report["nearest_rank"]
    li = report["linear_interpolation"]
    print(f"n={nr['count']} | nearest-rank p99={nr['p99_s']}s (observed max) "
          f"vs interpolated p99={li['p99_s']}s | saved {args.output}")


if __name__ == "__main__":
    main()
