"""Stable fingerprints and SARIF output for CI code scanning."""
import hashlib


def fingerprint(issue: dict) -> str:
    stable = f"{issue.get('file')}:{issue.get('line')}:{issue.get('message')}"
    return hashlib.sha256(stable.encode()).hexdigest()[:16]


def to_sarif(issues: list[dict]) -> dict:
    levels = {"HIGH": "error", "MED": "warning", "LOW": "note"}
    results = [{"ruleId": fingerprint(issue), "level": levels.get(issue.get("severity"), "warning"),
                "message": {"text": issue["message"]},
                "locations": [{"physicalLocation": {"artifactLocation": {"uri": issue["file"]},
                               "region": {"startLine": issue["line"]}}}]} for issue in issues]
    return {"version": "2.1.0", "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "runs": [{"tool": {"driver": {"name": "Local Code Reviewer"}}, "results": results}]}
