#!/usr/bin/env python3
"""Generate a human-readable safety report from red-team JSON."""
import argparse, json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="demo/redteam.json")
    parser.add_argument("--output", default="demo/safety_report.md")
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    lines = [
        f"# Safety Report: {data['model']}",
        "",
        "## Summary",
        "",
    ]
    for attack, metrics in data.get("summary", {}).items():
        lines.append(f"- **{attack}**: success_rate={metrics['success_rate']}, refusal_rate={metrics['refusal_rate']}, toxic_pass_through={metrics['toxic_pass_through']}")
    lines.extend(["", "## Sample Findings", ""])
    for r in data.get("details", [])[:5]:
        lines.append(f"- [{r['attack']}] {'REFUSED' if r['refused'] else 'PENETRATED'}: {r['prompt'][:60]}...")

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text("\n".join(lines), encoding="utf-8")
    print(f"[report] saved {args.output}")


if __name__ == "__main__":
    main()
