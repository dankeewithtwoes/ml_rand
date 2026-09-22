#!/usr/bin/env python3
"""Benchmark a repair agent on a dataset of synthetic bugs."""
import argparse, json, shutil, subprocess, sys
from pathlib import Path


BUGS = [
    {
        "name": "total_accumulation",
        "original": "def calculate_total(prices):\n    total = 0\n    for price in prices:\n        total =+ price\n    return total\n",
        "tests": "import sample_bug\ndef test_total():\n    assert sample_bug.calculate_total([10, 20, 30]) == 60\n",
    },
    {
        "name": "even_comparison",
        "original": "def is_even(n):\n    return n % 2\n",
        "tests": "import sample_bug\ndef test_even():\n    assert sample_bug.is_even(4) is True\n    assert sample_bug.is_even(3) is False\n",
    },
    {
        "name": "first_word_index",
        "original": "def get_first_word(text):\n    return text.split(' ')[1]\n",
        "tests": "import sample_bug\ndef test_first_word():\n    assert sample_bug.get_first_word('hello world') == 'hello'\n",
    },
]


def run_one(bug: dict, source_path: Path, test_path: Path, agent_cmd: list):
    source_path.write_text(bug["original"], encoding="utf-8")
    test_path.write_text(bug["tests"], encoding="utf-8")
    proc = subprocess.run(agent_cmd, capture_output=True, text=True)
    # Check if tests pass after agent run
    test_proc = subprocess.run([sys.executable, "-m", "pytest", str(test_path), "-q"], capture_output=True, text=True)
    return {
        "bug": bug["name"],
        "returncode": proc.returncode,
        "tests_pass": test_proc.returncode == 0,
        "stdout": proc.stdout[-1000:],
        "stderr": proc.stderr[-500:],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-cmd", default="python repair.py --source sample_bug.py --tests test_sample_bug.py")
    parser.add_argument("--output", default="demo/repair_benchmark.json")
    args = parser.parse_args()

    workdir = Path("demo_repair_workdir")
    workdir.mkdir(exist_ok=True)
    source_path = workdir / "sample_bug.py"
    test_path = workdir / "test_sample_bug.py"

    results = []
    for bug in BUGS:
        print(f"[benchmark] {bug['name']}")
        res = run_one(bug, source_path, test_path, args.agent_cmd.split())
        results.append(res)
        print(f"  tests_pass={res['tests_pass']}")

    shutil.rmtree(workdir, ignore_errors=True)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
