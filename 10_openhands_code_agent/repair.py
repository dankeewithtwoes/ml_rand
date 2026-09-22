#!/usr/bin/env python3
"""Simple LLM-driven repair loop with git-diff output."""
import argparse, difflib, os, re, subprocess, sys
from pathlib import Path
from repair_policy import validate_candidate


def run_tests(test_file: str):
    proc = subprocess.run([sys.executable, "-m", "pytest", test_file, "-q"], capture_output=True, text=True)
    return proc.returncode == 0, proc.stdout + proc.stderr


def build_prompt(source: str, test_output: str) -> str:
    return (
        "You are an expert Python engineer. Fix the bugs in the code below so all tests pass.\n"
        "Return ONLY the corrected file content (no markdown fences, no explanations).\n\n"
        f"```python\n{source}\n```\n\n"
        f"Test output:\n{test_output}\n"
    )


def call_llm(prompt: str, model: str = "gpt-4o-mini") -> str:
    try:
        from openai import OpenAI
    except Exception as exc:
        raise RuntimeError(f"openai SDK unavailable: {exc}")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return resp.choices[0].message.content


def extract_code(reply: str) -> str:
    # Try stripping fences
    if "```python" in reply:
        reply = reply.split("```python", 1)[1]
    if "```" in reply:
        reply = reply.split("```", 1)[0]
    return reply.strip()


def generate_diff(path: Path, original_source: str, fixed_source: str) -> str:
    return "\n".join(difflib.unified_diff(
        original_source.splitlines(), fixed_source.splitlines(),
        fromfile=str(path), tofile=f"{path} (proposed)", lineterm=""))


def repair(source_path: Path, test_file: str, max_iterations: int = 3, model: str = "gpt-4o-mini"):
    original = source_path.read_text(encoding="utf-8")
    current = original
    for i in range(max_iterations):
        ok, output = run_tests(test_file)
        if ok:
            print(f"[iter {i}] tests pass")
            return {"success": True, "iterations": i, "source": current}
        prompt = build_prompt(current, output)
        try:
            reply = call_llm(prompt, model=model)
        except Exception as exc:
            print(f"[iter {i}] LLM call failed: {exc}")
            return {"success": False, "iterations": i, "source": current, "error": str(exc)}
        current = extract_code(reply)
        policy = validate_candidate(original, current)
        if not policy["valid"]:
            return {"success": False, "iterations": i, "source": original, "error": "; ".join(policy["errors"])}
        source_path.write_text(current, encoding="utf-8")
        print(f"[iter {i}] applied patch")

    ok, output = run_tests(test_file)
    return {"success": ok, "iterations": max_iterations, "source": current, "test_output": output}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="sample_bug.py")
    parser.add_argument("--tests", default="test_sample_bug.py")
    parser.add_argument("--max-iterations", type=int, default=3)
    parser.add_argument("--model", default="gpt-4o-mini")
    args = parser.parse_args()

    source_path = Path(args.source)
    original = source_path.read_text(encoding="utf-8")
    result = repair(source_path, args.tests, args.max_iterations, args.model)
    diff = generate_diff(source_path, original, result["source"])
    print("\n--- DIFF ---\n")
    print(diff)
    if result["success"]:
        print("\n[success] all tests pass")
    else:
        print("\n[fail] repair did not converge")
        # restore original
        source_path.write_text(original, encoding="utf-8")


if __name__ == "__main__":
    main()
