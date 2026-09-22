#!/usr/bin/env python3
"""Run lightweight smoke tests across all rezume_git projects.

This script does NOT download models, start servers, or call paid APIs.
It only checks that Python files compile and that project structure is valid.
"""

import importlib.util
import os
import subprocess
import sys
from pathlib import Path


PROJECTS = [
    "01_pytorch_classifier_demo",
    "02_huggingface_finetune_demo",
    "03_langchain_rag_chat",
    "04_llamaindex_agent",
    "05_ollama_local_llm",
    "06_llamacpp_gguf_inference",
    "07_vllm_serving",
    "08_dify_workflow_integration",
    "09_comfyui_image_gen",
    "10_openhands_code_agent",
    "11_local_knowledge_os",
    "12_local_voice_companion",
    "13_local_finetuning_lab",
    "14_local_model_router",
    "15_local_code_reviewer",
    "16_local_synthetic_data_factory",
    "17_local_document_parser",
    "18_local_ai_observability",
    "19_local_edge_fleet",
    "20_local_redteam_arena",
    "21_universal_skill_forge",
]


def check_file_exists(project: Path, filename: str) -> bool:
    return (project / filename).is_file()


def compile_python_files(project: Path) -> tuple[bool, str]:
    py_files = list(project.rglob("*.py"))
    if not py_files:
        return True, "no Python files"
    cmd = [sys.executable, "-m", "py_compile"] + [str(f) for f in py_files]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stderr or "OK"


def run_project_test(project_name: str) -> dict:
    project = Path(project_name)
    result = {"name": project_name, "ok": True, "messages": []}

    for required in ["README.md", "requirements.txt"]:
        if not check_file_exists(project, required):
            result["ok"] = False
            result["messages"].append(f"missing {required}")

    ok, msg = compile_python_files(project)
    if not ok:
        result["ok"] = False
        result["messages"].append(f"compile error: {msg}")

    return result


def main():
    os.chdir(Path(__file__).parent)
    print("Running rezume_git smoke tests...\n")

    failed = []
    for project in PROJECTS:
        result = run_project_test(project)
        status = "PASS" if result["ok"] else "FAIL"
        print(f"[{status}] {project}")
        for msg in result["messages"]:
            print(f"       - {msg}")
        if not result["ok"]:
            failed.append(project)

    print(f"\n{'=' * 50}")
    print(f"Passed: {len(PROJECTS) - len(failed)}/{len(PROJECTS)}")
    if failed:
        print(f"Failed: {', '.join(failed)}")
        sys.exit(1)
    print("All smoke tests passed.")


if __name__ == "__main__":
    main()
