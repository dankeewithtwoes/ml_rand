"""Behavioral tests for the repair safety gate (repair_policy.validate_candidate).

Covers the happy path (a small, safe fix is accepted) and the failure modes
the gate exists for: syntax errors, dynamic-execution calls (including ones
hidden inside nested scopes), over-broad rewrites, and empty candidates.
"""
import repair_policy


ORIGINAL = (
    "def calculate_total(prices):\n"
    "    total = 0\n"
    "    for price in prices:\n"
    "        total =+ price\n"
    "    return total\n"
)

GOOD_FIX = ORIGINAL.replace("total =+ price", "total += price")


def test_happy_path_small_fix_is_accepted():
    result = repair_policy.validate_candidate(ORIGINAL, GOOD_FIX)
    assert result["valid"] is True
    assert result["errors"] == []
    # one line removed, one line added
    assert result["changed_lines"] == 2


def test_happy_path_identical_candidate_is_accepted():
    result = repair_policy.validate_candidate(ORIGINAL, ORIGINAL)
    assert result["valid"] is True
    assert result["changed_lines"] == 0


def test_failure_syntax_error_is_rejected():
    result = repair_policy.validate_candidate(ORIGINAL, "def broken(:\n")
    assert result["valid"] is False
    assert any("syntax error" in e for e in result["errors"])
    assert result["changed_lines"] == 0


def test_failure_dynamic_execution_calls_are_rejected():
    for call in ("eval('1+1')", "exec('x=1')", "compile('x','<s>','eval')", "__import__('os')"):
        candidate = ORIGINAL + f"\nresult = {call}\n"
        result = repair_policy.validate_candidate(ORIGINAL, candidate)
        assert result["valid"] is False, call
        assert any("blocked call" in e for e in result["errors"]), call


def test_failure_blocked_call_hidden_in_nested_scope_is_caught():
    # Bypass attempt: bury eval inside a helper function and a class method.
    candidate = ORIGINAL + (
        "\ndef helper():\n"
        "    return eval('1 + 1')\n"
        "\nclass Wrapper:\n"
        "    def run(self):\n"
        "        exec('pass')\n"
    )
    result = repair_policy.validate_candidate(ORIGINAL, candidate)
    assert result["valid"] is False
    blocked = [e for e in result["errors"] if "blocked call" in e]
    assert len(blocked) == 2


def test_failure_change_budget_exceeded_is_rejected():
    big_rewrite = "\n".join(f"x_{i} = {i}" for i in range(50)) + "\n"
    result = repair_policy.validate_candidate(ORIGINAL, big_rewrite, max_changed_lines=20)
    assert result["valid"] is False
    assert any("change budget exceeded" in e for e in result["errors"])


def test_boundary_exactly_at_budget_is_accepted():
    # 4 changed lines (2 removed + 2 added) with a budget of 4 must pass.
    candidate = (
        "def calculate_total(prices):\n"
        "    total = 0\n"
        "    for p in prices:\n"
        "        total += p\n"
        "    return total\n"
    )
    result = repair_policy.validate_candidate(ORIGINAL, candidate, max_changed_lines=4)
    assert result["changed_lines"] == 4
    assert result["valid"] is True


def test_failure_empty_candidate_is_rejected():
    for empty in ("", "   \n  \n"):
        result = repair_policy.validate_candidate(ORIGINAL, empty)
        assert result["valid"] is False
        assert "candidate is empty" in result["errors"]
