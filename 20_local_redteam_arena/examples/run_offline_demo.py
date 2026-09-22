#!/usr/bin/env python3
"""Offline demo of the red-team safety statistics pipeline.

Runs fully offline in two parts:

A. Infrastructure-error accounting with the real attack pipeline.
   redteam.py is pointed at a dead localhost endpoint (127.0.0.1:9), so
   every request fails. The naive per-attack summary printed by redteam.py
   reports success_rate 0.0, which looks like a perfectly safe model.
   safety_metrics.evaluate() instead excludes all three records as
   infrastructure errors and reports that zero attacks were evaluated.

B. Calibrated statistics on recorded results.
   A small synthetic fixture (sample_redteam_results.json, in the exact
   per-record format written by redteam.py) is evaluated per model,
   producing Wilson score confidence intervals for the attack success
   rate and showing how much (or how little) the sample supports.

Writes offline_safety_report.json next to this script and prints the
same numbers to stdout. No network, no GPU, no API keys.
"""
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from safety_metrics import evaluate, wilson_interval

DEAD_ENDPOINT = "http://127.0.0.1:9/v1"  # nothing listens here; requests fail fast
EXAMPLES = Path(__file__).resolve().parent


def run_dead_endpoint_probe() -> dict:
    raw_path = EXAMPLES / "dead_endpoint_raw.json"
    command = [
        sys.executable, str(PROJECT / "redteam.py"),
        "--endpoint", DEAD_ENDPOINT,
        "--count", "3",
        "--output", str(raw_path),
    ]
    completed = subprocess.run(command, cwd=PROJECT, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"redteam.py failed: {completed.stderr.strip()}")
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    stats = evaluate(raw["details"])
    return {
        "command": f"python redteam.py --endpoint {DEAD_ENDPOINT} --count 3 --output {raw_path.name}",
        "redteam_stdout": completed.stdout.strip(),
        "naive_summary_from_redteam_py": raw["summary"],
        "safety_metrics_verdict": stats,
        "raw_output_file": raw_path.name,
    }


def evaluate_fixture() -> dict:
    fixture = json.loads((EXAMPLES / "sample_redteam_results.json").read_text(encoding="utf-8"))
    by_model: dict[str, list[dict]] = {}
    for record in fixture["results"]:
        by_model.setdefault(record["model"], []).append(record)
    per_model = {}
    for model, records in by_model.items():
        stats = evaluate(records)
        successes = round(stats["attack_success_rate"] * stats["evaluated"])
        low, high = stats["attack_success_ci95"]
        per_model[model] = {
            **stats,
            "safety_score": round(1 - stats["attack_success_rate"], 4),
            "safety_score_ci95": [round(1 - high, 4), round(1 - low, 4)],
            "successful_attacks": successes,
        }
    return per_model


def main() -> None:
    part_a = run_dead_endpoint_probe()
    part_b = evaluate_fixture()

    report = {
        "demo": "offline safety statistics for red-team results",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "environment": {
            "os": platform.platform(),
            "python": platform.python_version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "part_a_dead_endpoint": part_a,
        "part_b_fixture_evaluation": part_b,
    }
    out_path = EXAMPLES / "offline_safety_report.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    verdict = part_a["safety_metrics_verdict"]
    print("[part A] dead endpoint probe (real redteam.py run, no server listening)")
    print(f"  redteam.py naive summary implies success_rate 0.0 for every attack type")
    print(f"  safety_metrics: evaluated={verdict['evaluated']} excluded_errors={verdict['excluded_errors']}"
          f" -> no valid measurements, nothing claimed")
    print("[part B] synthetic fixture, Wilson 95% CI per model")
    for model, stats in part_b.items():
        low, high = stats["attack_success_ci95"]
        print(f"  {model}: attack_success_rate={stats['attack_success_rate']:.4f}"
              f"  ci95=[{low:.4f}, {high:.4f}]"
              f"  ({stats['successful_attacks']}/{stats['evaluated']} evaluated,"
              f" {stats['excluded_errors']} excluded)")
    print(f"[saved] {out_path.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
