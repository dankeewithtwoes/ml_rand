#!/usr/bin/env python3
"""A minimal OpenHands-style agent: read code, ask LLM to fix, apply, test."""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


SYSTEM_PROMPT = """You are a coding assistant. Given a Python file with bugs and the test failures, produce a corrected version of the ENTIRE file.
Output ONLY the corrected Python code inside a markdown code block:
```python
# corrected code here
```
Do not add explanations outside the code block."""


def get_llm_client():
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    if api_key:
        return OpenAI(api_key=api_key, base_url=base_url)
    print("OPENAI_API_KEY not set; falling back to local Ollama (llama3.1)")
    return OpenAI(api_key="ollama", base_url="http://localhost:11434/v1")


def run_tests(test_path: Path) -> tuple[bool, str]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_path), "-v"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, result.stdout + result.stderr


def extract_code(reply: str) -> str:
    match = re.search(r"```python\n(.*?)\n```", reply, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Fallback: return everything if no block found
    return reply.strip()


def main(source_file: Path, test_file: Path, output_file: Path, model: str):
    client = get_llm_client()
    source_code = source_file.read_text(encoding="utf-8")

    print("Running tests before fix...")
    ok, output = run_tests(test_file)
    if ok:
        print("Tests already pass; nothing to fix.")
        return

    print("Tests failed. Asking LLM for a fix...")
    user_prompt = (
        f"Here is the buggy file `{source_file}`:\n\n"
        f"```python\n{source_code}\n```\n\n"
        f"Here are the test failures:\n```\n{output}\n```\n\n"
        "Please provide the fully corrected Python code."
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    fixed_code = extract_code(response.choices[0].message.content)
    output_file.write_text(fixed_code, encoding="utf-8")
    print(f"Fixed code written to {output_file}")

    # Run tests against the fixed file by temporarily replacing it
    backup = source_file.with_suffix(source_file.suffix + ".bak")
    source_file.rename(backup)
    try:
        output_file.rename(source_file)
        print("Running tests after fix...")
        ok, output = run_tests(test_file)
        print(output)
        if ok:
            print("✅ All tests pass.")
        else:
            print("❌ Tests still fail.")
    finally:
        # Restore original
        source_file.rename(output_file)
        backup.rename(source_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, default="sample_bug.py")
    parser.add_argument("--tests", type=Path, default="test_sample_bug.py")
    parser.add_argument("--output", type=Path, default="sample_bug_fixed.py")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    args = parser.parse_args()
    main(args.file, args.tests, args.output, args.model)
