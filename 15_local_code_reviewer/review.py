#!/usr/bin/env python3
"""Local-only code review agent for diffs and files."""
import argparse, os, re, subprocess, sys
from pathlib import Path
from reporting import to_sarif


PATTERNS = [
    ("HIGH", r"eval\s*\(", "possible code injection via eval()"),
    ("HIGH", r"exec\s*\(", "possible code injection via exec()"),
    ("HIGH", r"subprocess\.call\s*\([^)]*shell\s*=\s*True", "shell=True with subprocess can lead to command injection"),
    ("HIGH", r"os\.system\s*\(", "os.system is dangerous, use subprocess securely"),
    ("MED", r"SELECT\s+.*FROM\s+.*\+\s*", "possible SQL injection"),
    ("MED", r"api[_-]?key\s*=\s*[\"'][^\"']+[\"']", "possible hardcoded API key"),
    ("MED", r"password\s*=\s*[\"'][^\"']+[\"']", "possible hardcoded password"),
    ("LOW", r"TODO|FIXME|XXX", "leftover TODO/FIXME marker"),
]


def review_text(text: str, filename: str = "code") -> list:
    issues = []
    for severity, pattern, message in PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            line = text[:match.start()].count("\n") + 1
            issues.append({
                "file": filename,
                "line": line,
                "severity": severity,
                "message": message,
                "match": match.group(0)[:40],
            })
    return issues


def get_diff(ref: str) -> str:
    result = subprocess.run(
        ["git", "diff", ref],
        capture_output=True, text=True,
    )
    return result.stdout


def call_llm_for_review(code: str) -> str:
    prompt = (
        "You are a security-focused code reviewer. Find bugs and vulnerabilities in the code below. "
        "Return a short bullet list.\n\n```python\n" + code + "\n```"
    )
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "ollama"), base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1"))
        model = os.getenv("OLLAMA_MODEL", "llama3.1") if not os.getenv("OPENAI_API_KEY") else os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        resp = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}], temperature=0.2)
        return resp.choices[0].message.content
    except Exception as exc:
        return f"[skip] LLM unavailable: {exc}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--diff", default="HEAD~1")
    parser.add_argument("--file")
    parser.add_argument("--llm", action="store_true")
    parser.add_argument("--sarif", help="write GitHub Code Scanning compatible SARIF")
    args = parser.parse_args()

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
        filename = args.file
    else:
        text = get_diff(args.diff)
        filename = f"diff({args.diff})"

    issues = review_text(text, filename)
    print(f"[review] {len(issues)} static issues found")
    for issue in issues:
        print(f"  {issue['severity']:5} {issue['file']}:{issue['line']} {issue['message']}")
    if args.sarif:
        import json
        Path(args.sarif).write_text(json.dumps(to_sarif(issues), indent=2), encoding="utf-8")

    if args.llm:
        print("\n[llm review]")
        print(call_llm_for_review(text[:4000]))


if __name__ == "__main__":
    main()
