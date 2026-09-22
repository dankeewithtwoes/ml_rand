"""Safety gate for AI-generated Python repairs."""
import ast
import difflib

BLOCKED_CALLS = {"eval", "exec", "compile", "__import__"}


def validate_candidate(original: str, candidate: str, max_changed_lines: int = 80) -> dict:
    errors = []
    try: tree = ast.parse(candidate)
    except SyntaxError as exc: return {"valid": False, "errors": [f"syntax error: {exc.msg}"], "changed_lines": 0}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in BLOCKED_CALLS:
            errors.append(f"blocked call introduced: {node.func.id}")
    diff = list(difflib.unified_diff(original.splitlines(), candidate.splitlines()))
    changed = sum(1 for line in diff if line.startswith(("+", "-")) and not line.startswith(("+++", "---")))
    if changed > max_changed_lines: errors.append(f"change budget exceeded: {changed} > {max_changed_lines}")
    if not candidate.strip(): errors.append("candidate is empty")
    return {"valid": not errors, "errors": errors, "changed_lines": changed}
