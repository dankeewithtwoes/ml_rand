# Local Red-Team Arena

A local red-team runner for OpenAI-compatible endpoints. Reports attack success rates with Wilson confidence intervals and counts endpoint errors separately.

## Problem

Small prompt sets make safety rates uncertain, and endpoint failures should not count as safe refusals. This project runs against a local OpenAI-compatible endpoint, reports Wilson confidence intervals, and tracks infrastructure errors separately.

## Implementation

In safety_metrics.py: given raw red-team records, it

- drops every record whose response starts with `[error` (infrastructure failure) into a separate `excluded_errors` count — never into the success/failure denominator;
- reports the attack success rate over **valid** records only, with a Wilson score 95% confidence interval (`attack_success_ci95`), so a claim always carries its sample size and uncertainty;
- returns a zero report (`evaluated=0`) instead of a misleading `0.0` success rate when there is nothing valid to measure.

Pipeline around it:

1. `redteam.py` — built-in attack template library (jailbreak / toxicity / fuzzing), sends prompts to any OpenAI-compatible endpoint, classifies responses with local refusal/toxicity heuristics, writes raw JSON records.
2. `safety_metrics.py` — calibrated statistics over those records.
3. `compare_safety.py` — runs several local models and ranks them with uncertainty-aware safety scores.
4. `report.py` — renders a run into a human-readable Markdown safety report.

## Architecture

Pure Python 3.12; the statistics core is standard-library only (`math`). `requests` is used for endpoint calls. No GPU, no cloud API, no telemetry.

```text
attack templates (jailbreak / toxicity / fuzzing)
      │  redteam.py — one request per prompt to a local OpenAI-compatible endpoint
      ▼
raw records {attack, prompt, response, refused, toxic_output, success}
      │  local heuristics (refusal phrases, toxic terms); failures become "[error ...]"
      ▼
safety_metrics.evaluate
      ├─► "[error" records → excluded_errors (counted, never scored)
      └─► valid records → attack_success_rate + Wilson 95% CI
      ▼
JSON report ──► report.py (Markdown) / compare_safety.py (multi-model ranking)
```

## Quickstart (offline, verified)

```bash
pip install -r requirements.txt
python examples/run_offline_demo.py
```

The demo runs fully offline in two parts and writes `examples/offline_safety_report.json`:

- **Part A** points the real `redteam.py` at a dead localhost endpoint. The naive per-attack summary reports `success_rate 0.0` everywhere — which looks like a perfectly safe model — while `safety_metrics.evaluate()` reports `evaluated=0, excluded_errors=3`: no valid measurements, no claim.
- **Part B** evaluates a small synthetic fixture (`examples/sample_redteam_results.json`, exact `redteam.py` record format) for two fictional models and prints Wilson intervals.

Run the tests:

```bash
python -m unittest discover -s tests -v
```

Optional live run against a real local model (requires a running server such as Ollama; **not part of the offline verification**):

```bash
python redteam.py --model llama3.1 --attacks jailbreak,toxicity,fuzzing --count 30
python compare_safety.py --models llama3.1,phi3,qwen2.5
python report.py --input demo/redteam.json
```

## Verified results

Executed on this machine: Windows 11 (10.0.26200), Python 3.12.6, AMD64 (Intel64 Family 6 Model 186), `requests` 2.34.2. Real output of `python examples/run_offline_demo.py` (~7 s, no network):

```text
[part A] dead endpoint probe (real redteam.py run, no server listening)
  redteam.py naive summary implies success_rate 0.0 for every attack type
  safety_metrics: evaluated=0 excluded_errors=3 -> no valid measurements, nothing claimed
[part B] synthetic fixture, Wilson 95% CI per model
  model-a-synthetic: attack_success_rate=0.2857  ci95=[0.1172, 0.5465]  (4/14 evaluated, 1 excluded)
  model-b-synthetic: attack_success_rate=0.5000  ci95=[0.2538, 0.7462]  (6/12 evaluated, 3 excluded)
[saved] examples\offline_safety_report.json
```

Artifacts: [`examples/offline_safety_report.json`](examples/offline_safety_report.json) (full report with environment metadata) and [`examples/dead_endpoint_raw.json`](examples/dead_endpoint_raw.json) (raw `redteam.py` output from the dead-endpoint probe).

Note what the fixture numbers say: model B's point estimate (0.50) is worse than model A's (0.29), but the intervals overlap on [0.25, 0.55]. At this sample size the honest conclusion is "B looks weaker, not yet proven" — which is exactly the claim discipline this project exists to enforce. The synthetic fixture is illustrative input, not a model benchmark.

Live multi-model benchmarks against Ollama were **not run here** (no model server on this machine); they require a local OpenAI-compatible endpoint and are marked optional above.

## Tests

```bash
python -m unittest discover -s tests -v     # 13 tests, all passing on the machine above
```

Coverage of the metric checks (`tests/test_safety_metrics.py`):

- **Happy path** — mixed refused/penetrated/error records: correct `evaluated`/`excluded_errors` counts, rate over valid records only, point estimate bracketed by the CI; Wilson interval matches the textbook reference value for 50/100 ([0.4038, 0.5962]).
- **Failure modes** — empty input returns a zero report without raising; an all-infrastructure-error run reports `evaluated=0` instead of a fake-perfect 0.0 success rate; non-positive totals return a degenerate `(0.0, 0.0)` interval; interval bounds stay clamped to [0, 1] at 0% and 100% success.
- **Contract boundaries** — the `[error` prefix rule (prefix match excludes, mid-string does not), missing `success`/`response` keys, interval narrowing as samples grow, `compare_safety.safety_score_with_uncertainty` including the empty-summary case.

The portfolio-level proof test `test_20_safety_metrics_report_uncertainty_and_errors` lives in `../tests/test_wave3.py` and is enforced by the root `quality_gate.py`.

## Tested core vs external integrations

- **Tested offline here:** `safety_metrics.py` statistics (13 unit tests + portfolio proof test), the demo's dead-endpoint error-accounting path through the real `redteam.py` CLI, and compilation of every entry point (root smoke test).
- **External, not exercised in this verification:** live model traffic (`redteam.py` / `compare_safety.py` against Ollama or any other OpenAI-compatible server). Refusal/toxicity classification quality against real model outputs requires a running local model and is not claimed here.

## Threat model & data handling

- Attack prompts and model responses (truncated to 200 characters) are written to local JSON files only; nothing leaves the machine unless you deliberately point `--endpoint` at a remote server.
- The tool intentionally generates adversarial prompts (jailbreak, toxicity elicitation, fuzzing). Run it only against models you own or are authorized to evaluate.
- No API key is needed for the demo or tests; live runs read `OPENAI_API_KEY`/`OPENAI_BASE_URL` and send the key only to the configured endpoint.
- Scoring heuristics are substring lists run locally — prompts and responses are never sent to a third-party judge.
- All files under `examples/` are synthetic; no real user or benchmark data is shipped.

## Limitations

- The built-in template library is small (3 attack families, a handful of templates) — a starting point, not the coverage of dedicated frameworks like garak or PyRIT.
- Refusal/toxicity heuristics misclassify in both directions; the Wilson interval quantifies sampling uncertainty, not classifier error. A calibrated model-based judge is on the roadmap.
- The `[error` prefix contract can hide a genuine model response that happens to start with `[error`.
- Intervals assume independent samples, but attacks cycle through a small template set, so effective prompt diversity is limited — treat the CI as a lower bound on true uncertainty.
- `compare_safety.py` aggregates rounded per-attack rates; for rigorous comparison, evaluate record-level details with `safety_metrics.evaluate` directly.

## License

MIT (see repository root).

