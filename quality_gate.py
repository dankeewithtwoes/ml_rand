#!/usr/bin/env python3
"""Single offline quality gate for every portfolio project."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT_SUITES = {
    "01_pytorch_classifier_demo": ["unittest", "discover", "-s", "tests", "-v"],
    "03_langchain_rag_chat": ["unittest", "discover", "-s", "tests", "-v"],
    "04_llamaindex_agent": ["unittest", "test_web_search", "-v"],
    "07_vllm_serving": ["unittest", "test_latency_stats", "-v"],
    "10_openhands_code_agent": ["pytest", "test_repair_policy.py", "-q"],
    "11_local_knowledge_os": ["unittest", "test_knowledge_store", "-v"],
    "12_local_voice_companion": ["unittest", "test_audio_io", "-v"],
    "14_local_model_router": ["unittest", "test_decision", "-v"],
    "16_local_synthetic_data_factory": ["unittest", "test_generate_qa", "-v"],
    "17_local_document_parser": ["unittest", "discover", "-p", "test*.py", "-v"],
    "18_local_ai_observability": ["unittest", "test_policies", "-v"],
    "20_local_redteam_arena": ["unittest", "discover", "-s", "tests", "-v"],
}


def validate_contract() -> dict:
    manifest = json.loads((ROOT / "portfolio_manifest.json").read_text(encoding="utf-8"))
    projects, errors = manifest.get("projects", []), []
    ids = [project.get("id") for project in projects]
    dirs = [project.get("dir") for project in projects]
    if ids != list(range(1, 22)): errors.append("project ids must be exactly 1..21")
    if len(dirs) != len(set(dirs)): errors.append("project directories must be unique")
    tests = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "tests").glob("test_wave*.py"))
    details = []
    for project in projects:
        directory = ROOT / project["dir"]
        missing = [name for name in ("README.md", "requirements.txt", project["feature"]) if not (directory / name).is_file()]
        if project["proof"] not in tests: missing.append(f"proof:{project['proof']}")
        if missing: errors.append(f"{project['dir']}: missing {', '.join(missing)}")
        details.append({"id": project["id"], "project": project["dir"], "valid": not missing, "feature": project["feature"]})
    return {"ok": not errors and len(projects) == 21, "projects": len(projects), "errors": errors, "details": details}


def run(command: list[str], cwd: Path = ROOT) -> dict:
    environment = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        process = subprocess.run(command, cwd=cwd, text=True, encoding="utf-8", errors="replace",
                                 capture_output=True, env=environment, timeout=180)
    except subprocess.TimeoutExpired:
        return {"ok": False, "command": command, "output": "Test process exceeded 180 seconds"}
    return {"ok": process.returncode == 0, "command": command, "output": process.stdout + process.stderr}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--json", action="store_true"); args = parser.parse_args()
    report = {"contract": validate_contract()}
    report["behavior"] = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    report["skillforge"] = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], ROOT / "21_universal_skill_forge")
    report["compilation"] = run([sys.executable, "run_all_smoke_tests.py"])
    suites = {folder: run([sys.executable, "-m", *command], ROOT / folder)
              for folder, command in PROJECT_SUITES.items()}
    report["project_tests"] = {"ok": all(suite["ok"] for suite in suites.values()), "suites": suites}
    report["ok"] = all(section["ok"] for section in (report["contract"], report["behavior"], report["skillforge"], report["compilation"], report["project_tests"]))
    if args.json: print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Quality gate: {'PASS' if report['ok'] else 'FAIL'}")
        print(f"Projects: {report['contract']['projects']}/21")
        print(report["behavior"]["output"].strip())
        print(report["skillforge"]["output"].strip())
        print(report["compilation"]["output"].strip())
        for folder, suite in suites.items():
            print(f"{folder}: {'PASS' if suite['ok'] else 'FAIL'}")
            if not suite["ok"]: print(suite["output"].strip())
        for error in report["contract"]["errors"]: print(f"[contract] {error}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
