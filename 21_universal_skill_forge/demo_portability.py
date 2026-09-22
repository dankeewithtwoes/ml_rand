#!/usr/bin/env python3
"""Offline demo: run the portability contract for every discovered skill.

No model is called and no network is used. The report is written to
examples/portability_report.json and printed to stdout.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from portability import contract_report
from skill import discover_skills

PROVIDERS = ["ollama", "openai"]


def main() -> int:
    skills = discover_skills(ROOT / "skills")
    reports = [contract_report(skill, PROVIDERS) for skill in skills]
    report = {
        "offline": True,
        "providers": PROVIDERS,
        "skills_checked": len(reports),
        "skills_portable": sum(1 for entry in reports if entry["portable"]),
        "reports": reports,
    }
    out = ROOT / "examples" / "portability_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\n[demo] report written to {out.relative_to(ROOT)}")
    return 0 if all(entry["portable"] for entry in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
