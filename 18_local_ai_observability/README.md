# 18 — Local AI Observability & Guardrails

A self-hosted proxy that sits between your applications and a local LLM,
enforces guardrails (PII, toxicity, prompt injection), and produces
**content-free traces**: the log stores only the prompt's length and SHA-256
hash, never the raw text.

## Problem

Storing full prompts in logs can expose private data. This proxy keeps request metadata while omitting raw prompt text from its trace records.

## Implementation

The proxy writes traces (`policies.py`):

- `redact(text)` replaces emails, phone numbers, and API keys with typed
  placeholders (`[EMAIL_REDACTED]`, ...) and returns findings with offsets —
  detection exists so traffic can be blocked or audited, not stored.
- `trace_summary(text)` reduces any prompt to `{characters, sha256}` — enough
  to deduplicate and correlate calls, useless to anyone who steals the log.

Main pipeline (`guard_proxy.py`): an HTTP proxy in front of any
OpenAI-compatible endpoint. Every request is checked for PII, toxicity, and
prompt-injection markers. Violating calls are blocked with HTTP 400 and the
finding types; allowed calls are forwarded. Either way, only the content-free
trace summary, model name, latency, and check results are appended to a
JSONL log. `dashboard.py` aggregates the log into call counts, block counts,
and latency stats. PII detection uses Presidio if installed and degrades
gracefully to the built-in regex heuristics when it is not.

## Architecture

Stack: Python 3.12, Flask (proxy), requests, stdlib `re`/`hashlib` for the
tested core. Optional: presidio-analyzer (heavy, spaCy-based; commented out in
`requirements.txt`, uncomment to enable) for ML PII detection, openai client
for the example app.

```
client ──► guard_proxy.py ──► checks: pii / toxicity / injection
              │                        │
              │ pass                   │ violation
              ▼                        ▼
      forward to target LLM      HTTP 400 + finding types
      (Ollama / mock / vLLM)           │
              │                        │
              └──────────┬─────────────┘
                         ▼
              demo/guard_logs.jsonl   (content-free: length + sha256 only)
                         ▼
              dashboard.py ──► demo/dashboard.json
```

Key modules:

- `policies.py` — dependency-free redaction and trace summaries (tested core).
- `guard_proxy.py` — Flask proxy: guardrail checks, blocking, content-free logging.
- `dashboard.py` — CLI aggregation of the JSONL log.
- `benchmark_guardrails.py` — heuristic detection check on a synthetic fixture.
- `run_demo.py` — one-command offline demo (mock LLM + proxy + dashboard).

## Quickstart

One command, fully offline (starts a mock LLM, runs safe/PII/injection
prompts through the proxy, aggregates the log):

```bash
pip install -r requirements.txt
python run_demo.py
```

Verified on this machine — see the captured transcript in
[docs/demo_output.txt](docs/demo_output.txt) and the generated
`demo/dashboard.json`.

Against a real local model instead of the mock:

```bash
python guard_proxy.py --target http://localhost:11434/v1 --port 11435  # needs Ollama running
python example_client.py --prompt "Hello"
python dashboard.py
```

## Verified results

Run on Windows 11 (10.0.26200), Python 3.12.6, AMD64
(Intel64 Family 6 Model 186, 20 logical cores), no GPU, no network.
Presidio was **not** installed, so all results below use the regex-heuristic
fallback — the shipped default.

`python run_demo.py` (full transcript: [docs/demo_output.txt](docs/demo_output.txt)):

```
[demo] safe prompt (allowed): HTTP 200 -> [mock-llm reply] What is the capital of France?
[demo] PII prompt (blocked): HTTP 400 -> guardrail blocked {'pii': [{'end': 30, 'start': 12, 'type': 'EMAIL'}], ...}
[demo] injection prompt (blocked): HTTP 400 -> guardrail blocked {'injection': True, 'pii': [], 'toxicity': False}
[demo] verified: raw prompt text never appears in guard_logs.jsonl
[dashboard] {'total_calls': 3, 'blocked_calls': 2, 'avg_latency_s': 0.028, 'p50_latency_s': 0.028, 'models': {'mock-llm': 3}}
```

The log line for the blocked PII call — note the prompt is length + hash only:

```json
{"model": "mock-llm", "latency_s": 0.0, "prompt": {"characters": 44, "sha256": "e32f8b05af38..."}, "checks": {"pii": [{"type": "EMAIL", "start": 12, "end": 30}], ...}}
```

`python benchmark_guardrails.py` scored **4/4 (accuracy 1.00)** on its
synthetic fixture — raw output in `demo/guardrail_benchmark.json`. Read this
honestly: the fixture is four hand-picked prompts exercising the heuristics,
not a measured detection rate on real traffic. A proper detection benchmark
against a labeled PII dataset was **not run here** — it would require
presidio-analyzer plus a downloaded spaCy model and an external dataset.

## Tests

```bash
python -m unittest test_policies -v   # 8 tests, all passing in this environment
```

Coverage (`test_policies.py`, unittest, matching the repo's root test style):

- Happy path: email/phone/API-key redaction, finding offsets matching the
  original text, trace summary contains exactly `{characters, sha256}`.
- Failure modes: empty input yields no findings; non-string input fails
  loudly (`TypeError`); API-key pattern boundary (12 chars redacted, 11 not);
  safe text passes unchanged.
- Policy-bypass resistance: `guard_proxy.log_call` is fed a prompt containing
  an email and the written JSONL line is asserted to contain no raw content —
  only the trace summary.

The portfolio-level proof test
(`test_18_observability_redacts_instead_of_logging_content` in the root
`tests/`) also exercises `policies.py` and stays untouched.

## Threat model & data handling

- **Guarantee:** raw prompt text is never written to disk — log entries carry
  only length, SHA-256, model, latency, and finding types/offsets.
- SHA-256 of a prompt is a fingerprint, not encryption: it enables
  correlation and offline dictionary checks against known prompts.
- Blocked requests are rejected before reaching the LLM; allowed requests are
  forwarded to the configured target over whatever channel that target uses
  (loopback HTTP by default — no TLS termination here).
- The proxy does **not** inspect or log response bodies.
- No telemetry, no outbound calls: all processing is local; Presidio, if
  installed, also runs locally.

## Limitations

- Heuristic detectors have both false negatives (obfuscated PII like
  `person [at] example.com` is missed) and false positives (the word list in
  `detect_toxicity` is five words); the benchmark fixture is too small to
  quantify either.
- Detection is pre-forward only: there is no streaming support and no
  response-side guardrails.
- Single-process Flask dev server — a demo topology, not a production
  deployment story (no auth on the proxy port, no backpressure).
- Regex heuristics are English-centric.

## Tested core vs. integrations

The tested, offline core is `policies.py` plus the proxy/logging pipeline
exercised against a mock target (`run_demo.py`, `test_policies.py`). The
integration layer — pointing the proxy at a real Ollama/vLLM endpoint and
using Presidio for ML-based PII detection — is optional, requires those
services/packages installed, and was not part of the verified runs above.

