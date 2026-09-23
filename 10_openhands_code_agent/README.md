# 10 — Test-Driven Repair Agent with a Safety Gate

The repair loop asks an LLM to address failing pytest cases. Before a patch is written, `repair_policy.py` checks its syntax, calls, and change size.

## Problem

Automated patches can contain invalid syntax, dangerous calls, or unrelated edits. The policy checks each candidate before writing it and leaves the source unchanged when a check fails.

## Implementation

- **Repair policy:**
  `repair_policy.validate_candidate(original, candidate, max_changed_lines=80)`
  checks every proposed patch for
  1. **syntax validity** — the candidate must parse as Python (`ast.parse`);
  2. **dangerous calls** — any `eval` / `exec` / `compile` / `__import__` call,
     including ones hidden inside nested functions or class bodies, blocks the patch;
  3. **change budget** — a unified-diff line count above the budget (default 80)
     blocks over-broad rewrites;
  4. **empty output** — blank candidates are rejected.
- **Test-driven repair loop** (`repair.py`): runs pytest, feeds failures to an
  OpenAI-compatible LLM, gates the reply through the policy, applies it, and retries
  up to N iterations. Produces a real unified diff for review and restores the
  original file on failure.
- **Benchmark harness** (`benchmark.py`): replays the agent against a small dataset
  of synthetic bugs and writes a pass/fail scoreboard JSON.

## Architecture

Pure Python 3.12 standard library for the core gate; `pytest` for the test runner;
the optional `openai` SDK (with `python-dotenv`) only for the LLM loop. Any
OpenAI-compatible endpoint works (OpenAI API, or local Ollama via `OPENAI_BASE_URL`).

| Module | Role |
|---|---|
| `repair_policy.py` | Safety gate: AST syntax check, blocked-call scan, diff budget. Stdlib only. |
| `repair.py` | Repair loop: pytest → prompt → LLM → policy gate → apply → diff. |
| `agent.py` | Minimal OpenHands-style single-shot variant (backup/restore around apply). |
| `benchmark.py` | Dataset-of-bugs runner producing a JSON scoreboard. |
| `demo_policy_gate.py` | Offline demo of the gate (no LLM, no network). |
| `sample_bug.py` / `test_sample_bug.py` | Intentionally buggy fixture and its failing suite. |

```
            ┌────────────┐   failures   ┌─────────┐  candidate patch  ┌───────────────┐
 pytest ──▶ │ repair.py  │ ───────────▶ │   LLM   │ ────────────────▶ │ repair_policy │
            │  (loop)    │ ◀─────────── │ (opt.)  │                   │     gate      │
            └─────┬──────┘   apply only └─────────┘                   └──────┬────────┘
                  │        if gate ACCEPTS                                    │ verdict
                  ▼                                                           ▼
         source file + unified diff                              block: eval/exec,
                                                          syntax errors, over-broad diffs
```

## Quickstart (offline, verified)

```bash
pip install -r requirements.txt
python demo_policy_gate.py
```

The demo runs the buggy sample's failing tests, then pushes four realistic
LLM-style candidates through the safety gate and writes
[`demo/policy_gate_report.json`](./demo/policy_gate_report.json). No API key,
no network, no GPU. The raw terminal output is captured in
[`demo/demo_run.log`](./demo/demo_run.log).

## Verified results

Actual output of `python demo_policy_gate.py` on this machine
(Windows 11 10.0.26200, Python 3.12.6, Intel64 Family 6 Model 186 — see the
`environment` block in the JSON report):

```
Baseline: 3 failed in 0.22s (expected: buggy sample fails)
[ACCEPTED] correct_minimal_fix: changed_lines=6 errors=[]
[BLOCKED] fix_with_eval_injection: changed_lines=4 errors=['blocked call introduced: eval']
[BLOCKED] overbroad_rewrite: changed_lines=133 errors=['change budget exceeded: 133 > 80']
[BLOCKED] broken_syntax_reply: changed_lines=0 errors=['syntax error: invalid syntax']
Summary: 1 accepted, 3 blocked out of 4 candidates
```

The LLM repair loop (`repair.py`, `agent.py`, `benchmark.py`) was **not run here**:
this machine has no `OPENAI_API_KEY` configured and no Ollama server on
`localhost:11434`. It requires either an OpenAI-compatible API key or a local
Ollama instance (see `.env.example`).

## Tests

```bash
python -m pytest test_repair_policy.py -q   # 8 passed
```

`test_repair_policy.py` covers the gate's happy path (minimal fix accepted,
identical candidate accepted, exact-budget boundary accepted) and its failure
modes: syntax errors, each of the four blocked dynamic-execution calls, blocked
calls hidden in nested functions/class bodies (bypass attempt), over-budget
rewrites, and empty candidates. Note that `test_sample_bug.py` **fails by
design** — it is the buggy fixture the repair loop works on, not a project test.

## Threat model & data handling

- The gate treats all LLM output as untrusted: a rejected candidate is never
  written to disk, and `repair.py` restores the original file when a repair
  does not converge.
- Source code and pytest output are sent to the configured LLM endpoint when
  the repair loop runs — point `OPENAI_BASE_URL` at a local Ollama instance to
  keep code on the machine. The gate, tests, and demo send nothing anywhere.
- The gate is a static pre-write filter; it does **not** sandbox execution.
  A patch that passes the gate is still ordinary Python running with your
  permissions.
- No telemetry, no logging of file contents outside the local `demo/` artifacts.

## Limitations

- The blocked-call scan matches direct name calls only. Obfuscated dynamic
  execution (`getattr(__builtins__, 'eval')`, `importlib`, `os.system`) is not
  detected — the gate is a first line of defense, not a security boundary.
- The change budget counts raw unified-diff lines; it cannot tell a semantically
  small refactor from a large one.
- The gate validates Python syntax, not test correctness — a gated patch can
  still be wrong; the pytest loop is the second check.
- Repair quality depends entirely on the backing LLM; the benchmark dataset is
  three synthetic bugs, illustrative rather than representative.

