# Local Model Router — explainable local/cloud routing with rejection reasons

## Problem

The router evaluates local and cloud model candidates using prompt intent, privacy constraints, cost, and latency metadata. It returns the selected model and the reasons other candidates were rejected.

## Implementation

Given a registry of models described by metadata (`type`, `cost_per_1k_tokens`,
`avg_latency_ms`, `strengths`), the router:

1. classifies the prompt intent (keyword rules: `private`, `code`, `legal`,
   `creative`, fallback `general`);
2. auto-detects sensitive markers (`password`, `secret`, `token`, `ssn`, ...) and
   escalates the request to `private` even when the caller forgot the flag;
3. applies **hard constraints** — `private` → local-only, `max_cost`,
   `max_latency_ms` — and rejects every model that violates one, **recording the
   reason per model**;
4. scores the survivors (strength match, latency, cost) and returns the winner
   together with the full rejection list;
5. optionally performs the live call through any OpenAI-compatible endpoint —
   and degrades gracefully to a `[skip]` message when no endpoint is reachable.

The selection and rejection explanations are produced in step 3–4: `decision.py:choose()` returns
`{"model", "reasons", "rejected": [{"model", "reasons"}]}`, so every routing
decision can answer both "why this model?" and "why not that one?".

## Architecture

Pure-Python, standard-library-only core (Python 3.12). The `openai` SDK is
imported lazily and only used for the optional live-call layer.

| Module | Role |
|---|---|
| `decision.py` | Constraint engine: privacy/cost/latency filters + explainable selection |
| `route.py` | CLI: intent keywords, sensitive-marker detection, optional live call |
| `registry.py` | JSON model zoo with auto-seeded defaults (llama3.1, qwen2.5-1.5b, gpt-4o-mini) |
| `register_model.py` | CLI to add models to the zoo |
| `benchmark_router.py` | Labeled 4-sample fixture: intent accuracy + cost saved vs cloud-only |
| `test_decision.py` | Behavioral tests for the routing engine |

```text
prompt ──► classify_intent ──► contains_sensitive_data ──► decision.choose()
                                                              │ hard constraints:
                                                              │  private → local only
                                                              │  max_cost / max_latency
                                                              ▼
                                          ┌────────────────────────────────────┐
                                          │ selected model + per-model         │
                                          │ rejection reasons (audit trail)    │
                                          └────────────────────────────────────┘
                                                              │
                                          optional live call (OpenAI-compatible
                                          endpoint: Ollama / vLLM / cloud API)
```

## Quickstart

Offline-first: the routing engine, registry, benchmark, and tests need no model
downloads, no GPU, and no API keys. Verified on this machine:

```bash
pip install -r requirements.txt   # optional: the routing logic uses the standard library

# One-command demo: seeds a default registry, classifies, routes, explains
python route.py --prompt "Rotate my database password and restart the service" --registry examples/registry.json

# Benchmark on the built-in labeled fixture, writes a JSON report
python benchmark_router.py --registry examples/registry.json --output examples/router_benchmark.json
```

To register your own model:

```bash
python register_model.py --name mistral-7b --type local --url http://localhost:11434/v1 --latency 500 --strengths general,fast --registry examples/registry.json
```

## Verified results

Real output captured on the development machine (full log:
[examples/demo_terminal.log](./examples/demo_terminal.log), machine-readable
report: [examples/router_benchmark.json](./examples/router_benchmark.json)):

```text
$ python route.py --prompt "Rotate my database password and restart the service" --registry examples/registry.json
[intent] private
[router] -> qwen2.5-1.5b (local)
[answer] [skip] model call failed: Connection error.

$ python benchmark_router.py --registry examples/registry.json --output examples/router_benchmark.json
[benchmark] accuracy=0.25 cost_saved=$0.00060 -> examples/router_benchmark.json
```

- The `password` marker escalated the first prompt to `private`, and the cloud
  model was rejected before any network call — exactly the auditable behavior
  the project exists for.
- No model endpoint was running on this machine, so the live call degraded to
  `[skip] ... Connection error.` — routing still completed. Live-call quality is
  **not claimed here**: it requires a running Ollama/vLLM endpoint or a cloud key.
- `accuracy=0.25` is the honest score on the built-in 4-sample fixture: the three
  Russian prompts miss the English-only keyword rules and fall back to `general`
  (see Limitations). The privacy routing itself is unaffected — sensitive prompts
  still stay local.
- `cost_saved=$0.00060` is the fixture arithmetic: 4 samples × $0.00015/1k tokens
  cloud-only vs $0 for the all-local routing the privacy policy produced.

Environment: Windows 11 (10.0.26200), Python 3.12.6, AMD64,
CPU `Intel64 Family 6 Model 186 Stepping 2, GenuineIntel`.

## Tests

```bash
python -m unittest test_decision -v
```

Last run on the environment above: **12 tests, OK** (~0.03 s).

Happy path: strength match wins; private prompt rejects the cloud model *with the
recorded reason*; cost and latency budgets each reject the violating models;
sensitive markers force local routing even without the `--private` flag.

Failure modes: no model satisfies the constraints → `ValueError`; empty registry
→ `ValueError`; a cloud model **named** `local-llama` is still rejected (policy is
keyed on the declared `type`, not the name — a spoofed name cannot bypass privacy);
unknown intent falls back to a declared `best available trade-off`; models with
missing metadata fields are handled via defaults.

The portfolio-level proof test `test_14_router_explains_privacy_rejections`
(`../tests/test_wave2.py`) is kept green by the root `quality_gate.py`.

## Threat model & data handling

- With `private=True` or detected sensitive markers, non-local models are
  rejected **before** any network call — private prompts never leave the machine
  through this router.
- The registry stores only model metadata (name, type, URL, cost, latency,
  strengths). Prompts and responses are never persisted by the router.
- Marker detection is a heuristic safety net, not DLP: it matches a fixed set of
  English keywords and will miss paraphrased or non-English secrets.
- The privacy guarantee trusts the declared `type` field of each registry entry;
  a misregistered endpoint (cloud API declared as `local`) is out of scope.
- The router does not encrypt traffic, sandbox the model, or keep an audit log;
  it is a routing layer, not a security boundary around the model itself.

## Limitations

- The intent classifier is English-keyword based. The built-in fixture proves the
  cost: Russian prompts fall back to `general`, hence `accuracy=0.25` on 4
  samples. A real deployment should plug in a proper classifier (a scikit-learn
  slot is reserved in `requirements.txt` but not yet wired).
- Latency and cost figures in the registry are hand-entered estimates, not
  measurements from the actual endpoints.
- The benchmark fixture is 4 hand-labeled samples — a smoke check, not a
  published benchmark. No real trace dataset yet (see the P1 roadmap in
  `../PROJECT_SCORECARD.md`).
- Live calls require an OpenAI-compatible endpoint and were not
  integration-tested on this machine.

## Tested core vs external integrations

Tested offline here: the constraint engine (`decision.py`), the registry, intent
classification, sensitive-marker detection, and the benchmark fixture — all
covered by `test_decision.py` without network access.

External integration layer: live model calls via the `openai` SDK against
Ollama/vLLM/OpenAI-compatible endpoints. This layer is optional, is not covered
by the offline tests, and was not exercised against a running endpoint on this
machine — no claims are made about end-to-end latency or answer quality.

