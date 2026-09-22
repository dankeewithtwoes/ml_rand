# 07 — vLLM Serving Benchmark: Correct Tail Latency Under Small Samples

Load-testing harness for a vLLM OpenAI-compatible endpoint, built around one
correctness rule: **reported tail latencies must be values that were actually
observed**, even when the benchmark only ran a dozen requests.

## Problem

Latency benchmarks for LLM servers are usually run with small samples — 10 to 50
requests — because each request is expensive. The standard percentile helpers
(NumPy's default, `statistics.quantiles`) answer with *linear interpolation*:
they invent values between observed data points. On a 12-request sample that
means the reported p99 is a number no request ever experienced, and it is
systematically *lower* than the real worst case. Sizing a deployment on an
under-reported tail is how you end up with SLO violations in production that
"never happened in the benchmark."

The other extreme — taking `max()` — is honest but unlabelled and jittery. The
useful middle ground for small samples is the **nearest-rank** method: the p99
of n samples is the `ceil(0.99 * n)`-th ordered observation. Every reported
number is a latency some real request actually had.

## What it does

- **Distinctive capability (tested core, stdlib-only):** `latency_stats.py`
  implements nearest-rank percentiles and a `summarize()` report
  (count/mean/p50/p95/p99/max). Wrong quantiles raise, empty samples degrade to
  a documented `0.0` sentinel instead of crashing a benchmark report.
- **Main pipeline:** `serve.py` launches a vLLM OpenAI-compatible server,
  `client.py` runs a single sanity request, `benchmark.py` fires concurrent
  load (`ThreadPoolExecutor`, concurrency × rounds tasks), and every run is
  summarized through `latency_stats.summarize()` into a JSON report.
- `demo_tail_latency.py` is the offline proof: a fixed 12-request latency
  series where nearest-rank and interpolation visibly disagree.

## Architecture

Stack: Python 3.12 stdlib (statistics, concurrent.futures, argparse) for the
tested core; `openai` SDK for the benchmark client; `vllm` (optional, heavy,
Linux+CUDA only) for the server under test.

```
 serve.py ── launches ──▶ vllm.entrypoints.openai.api_server (GPU, optional)
                                 ▲
 client.py ── 1 request ────────┤ chat.completions + usage
                                 │
 benchmark.py ── concurrency × rounds prompts (ThreadPoolExecutor)
        │
        ▼ latencies_s[]
 latency_stats.summarize()   ← nearest-rank p50/p95/p99, stdlib only
        │
        ▼
 demo/benchmark.json         ← machine-readable report
```

## Quickstart (offline, no GPU, no dependencies)

```bash
cd 07_vllm_serving
python demo_tail_latency.py
```

This writes `demo/tail_latency_report.json` and prints the summary line shown
below. Verified on this machine (Windows 11, Python 3.12.6).

The full GPU pipeline (requires Linux + NVIDIA CUDA; **not runnable on this
Windows machine** — vLLM publishes no Windows wheels):

```bash
pip install openai==2.31.0          # benchmark client (vllm only on Linux+CUDA)
python serve.py --model Qwen/Qwen2.5-1.5B-Instruct --port 8000 --wait
python client.py --base-url http://localhost:8000/v1
python benchmark.py --base-url http://localhost:8000/v1 --concurrency 4 --rounds 5 --max-tokens 128
```

## Verified results

Run on: Windows 11 (10.0.26200), Python 3.12.6, 13th Gen Intel Core i9-13900H,
AMD64. Full report with environment metadata:
[`demo/tail_latency_report.json`](demo/tail_latency_report.json).

`python demo_tail_latency.py` output:

```
n=12 | nearest-rank p99=1.214s (observed max) vs interpolated p99=1.1869s | saved demo/tail_latency_report.json
```

From the saved report — same 12-request sample, two methods:

| metric | nearest-rank (this project) | linear interpolation | delta |
|---|---:|---:|---:|
| p95 | 1.214 s | 1.0787 s | interpolation under-reports by 0.1353 s |
| p99 | 1.214 s | 1.1869 s | interpolation under-reports by 0.0271 s |

Both interpolated values are latencies **no request ever had**; the
nearest-rank values are the observed worst request (1.214 s). Mean was 0.5305 s,
so the tail is ~2.3× the mean — exactly what a small benchmark must not hide.

GPU throughput numbers (tok/s, req/s against a live vLLM server) are **not
published here**: they were not run on this machine. They require an NVIDIA GPU
with Linux/CUDA vLLM wheels, and per this portfolio's rules may only be
published with raw result files plus hardware/model/software metadata.

## Tests

```bash
cd 07_vllm_serving
python -m unittest test_latency_stats -v     # 7 tests
```

Verified on this machine: `Ran 7 tests in 0.000s — OK`.

Coverage of `latency_stats.py`:

- **Happy path:** nearest-rank result on a known series; unsorted input is
  ordered first; `summarize()` report shape, and every reported percentile is
  an observed value.
- **Failure modes:** quantiles outside `[0, 1]` raise `ValueError`; empty input
  returns the documented `0.0` sentinel (count=0, no crash); single-sample and
  quantile-0/1 boundaries; regression guard that small-sample p95/p99 equal the
  observed max and strictly beat linear interpolation.

The portfolio-level proof `test_07_percentile_uses_nearest_rank` lives in the
root `tests/` suite and is exercised by `python quality_gate.py` from the
repository root.

## Threat model & data handling

- `benchmark.py` sends only the fixed, non-sensitive prompt strings shipped in
  this repository; it collects no user data.
- Prompts go exclusively to `--base-url` (default `http://localhost:8000/v1`).
  Pointing it at a remote endpoint sends prompts off-machine — treat the flag
  as a trust decision.
- The API key defaults to the literal `"dummy"` for local servers; if
  `OPENAI_API_KEY` is set it is used for requests but never written to reports.
- Reports persist only latency/token-count statistics — never prompt or
  completion text.
- The tool writes nothing outside the `--output` path and does not modify the
  server or model under test.

## Limitations

- The GPU serving path requires Linux + NVIDIA CUDA; on Windows only the
  stdlib core, tests, and offline demo run. vLLM is kept as an optional,
  lower-bounded dependency for this reason.
- Nearest-rank is exact but coarse on tiny samples: with n ≤ 100, p99 equals
  the observed max. That is the intended honest behavior, not a bug — but there
  is no tail granularity beyond observed ranks.
- Client-side load generation (`ThreadPoolExecutor`) measures client-observed
  latency including thread-scheduling overhead; for high-concurrency production
  load use dedicated tooling.
- `summarize()` signals empty input with `0.0` sentinels rather than raising —
  callers must check `count`.
- Benchmark requests have no timeout/retry; a hung server fails the whole run.
