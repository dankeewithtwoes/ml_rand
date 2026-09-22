"""Correct nearest-rank percentiles and benchmark summaries."""
import math
import statistics


def percentile(values: list[float], quantile: float) -> float:
    if not values: return 0.0
    if not 0 <= quantile <= 1: raise ValueError("quantile must be in [0, 1]")
    ordered = sorted(values)
    return ordered[max(0, math.ceil(quantile * len(ordered)) - 1)]


def summarize(latencies: list[float]) -> dict:
    return {"count": len(latencies), "mean": statistics.mean(latencies) if latencies else 0.0,
            "p50": percentile(latencies, 0.50), "p95": percentile(latencies, 0.95),
            "p99": percentile(latencies, 0.99), "max": max(latencies, default=0.0)}
