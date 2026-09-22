# Skill Forge

Provider-neutral, testable Python tools for AI agents. A skill is a tiny local package — a semantic-versioned manifest, a JSON Schema input contract, deterministic examples, and a handler — that you write once, validate offline, and then expose to Ollama or any OpenAI-compatible provider.

## The problem

Giving an LLM agent a new tool today usually means editing framework-specific glue code and then discovering at call time — after paying for tokens — that the model rejected the tool schema, the name violated the provider's naming rules, or the arguments failed validation. The feedback loop is slow, costs money per iteration, and differs across providers, so a tool that works against one endpoint silently breaks against another.

Skill Forge moves that feedback loop entirely offline. Schemas are validated against JSON Schema Draft 2020-12 before any model is involved, every skill ships executable examples that run as unit tests, and a portability contract checks each tool definition against the constraints that OpenAI-compatible providers actually enforce — without a single network call or paid token.

## What it does

The distinctive capability: **an offline two-provider portability contract** (`portability.py`). For each skill it verifies, without calling any model, that:

- the tool name matches the published OpenAI function-name pattern (`^[a-zA-Z0-9_-]{1,64}$`) — the same rules Ollama's OpenAI-compatible endpoint applies;
- the input schema is a JSON object, as function-calling APIs require;
- the schema uses only the keyword subset (`$schema`, `type`, `properties`, `required`, `additionalProperties`, `description`) that providers accept, flagging anything likely to be rejected or silently dropped.

The report is per-provider and machine-readable, so it gates CI before any paid call happens.

The main pipeline around it:

```text
create ──▶ validate package ──▶ run example tests ──▶ portability contract ──▶ (optional) expose to provider
 scaffold    manifest + schema    deterministic in→out     offline, per-provider      OpenAI/Ollama tool format
```

- `python skillforge.py create <name>` scaffolds a contract-complete skill package.
- `Skill.run()` validates full inputs with JSON Schema and rejects unknown fields when the schema requests it.
- `python skillforge.py test <skill>` executes the skill's `examples.json` as deterministic in→out cases.
- Every CLI command emits JSON, so CI pipelines and other agents can consume it.

## Architecture

Pure Python 3.12, one hard dependency (`jsonschema`). No network, no GPU, no model downloads for package validation and portability checks. The bundled `weather` handler opens the network only when that skill is explicitly run.

| Module | Role |
|---|---|
| `skill.py` | `Skill` package loader: manifest/schema validation, discovery, sandboxed-per-process handler import |
| `skillforge.py` | CLI: `create`, `list`, `inspect`, `test`, `run`, `doctor` — all JSON-emitting |
| `portability.py` | Offline two-provider portability contract (the distinctive feature) |
| `runtime.py` | Optional adapters: converts skills to OpenAI function-tool format, calls Ollama/OpenAI-compatible endpoints |
| `benchmark_portability.py` | Optional benchmark across live model endpoints (requires a running provider) |
| `demo_portability.py` | One-command offline demo; writes `examples/portability_report.json` |
| `skills/` | Local skill registry (`calculator`, `weather`; empty dirs are ignored) |

Data flow:

```text
skills/<name>/ ──▶ Skill loader ──▶ JSON Schema validation ──▶ handler.handle(args)
manifest.json          │                                              │
schema.json            ▼                                              ▼
examples.json    portability.contract_report ◀── schema + name    deterministic
handler.py             │                                            examples
                       ▼
              per-provider report (ollama, openai) — offline
```

## Quickstart (offline, verified)

```bash
pip install -r requirements.txt
python skillforge.py doctor
python skillforge.py test skills/calculator
python skillforge.py run skills/calculator --input '{"expression":"2 + 3 * 4"}'
python demo_portability.py
```

Live keyless weather (sends the requested city to Open-Meteo):

```bash
python skillforge.py run skills/weather --input '{"city":"Волгоград","language":"ru"}'
```

The handler resolves coordinates through the official [Open-Meteo Geocoding
API](https://open-meteo.com/en/docs/geocoding-api), then requests current
conditions from the [Forecast API](https://open-meteo.com/en/docs). It needs
no API key and returns both request URLs, attribution, and retrieval time in
`provenance`; an unavailable network or unknown city is an explicit error.

The last command is the one-command demo: it runs the portability contract for every discovered skill against two providers, fully offline, and writes the report to `examples/portability_report.json`. Real captured output of the offline quickstart commands is in [`examples/quickstart_log.txt`](examples/quickstart_log.txt).

Create your own skill:

```bash
python skillforge.py create summarize --skills-dir skills
python skillforge.py test skills/summarize
```

## Verified results

Measured on this machine: Windows 11 (AMD64), Python 3.12.6, CPU `Intel64 Family 6 Model 186 Stepping 2, GenuineIntel`. No GPU, no network, no paid API involved.

- `python demo_portability.py` → exit 0; **2/2 skills** (`calculator`, `weather`) pass the portability contract for both `ollama` and `openai` provider rules. Full report: [`examples/portability_report.json`](examples/portability_report.json) (generated, not hand-written).
- `python -m unittest discover -s tests` → **18 tests**, including mocked HTTP contracts for weather.
- `python skillforge.py test skills/calculator` → both deterministic examples pass (`2 + 2 * 5 → 12`, `(10 - 4) / 2 → 3.0`).
- A live Open-Meteo invocation for `Волгоград` on 2026-07-19 resolved the city to `48.71378, 44.4976` and returned model current conditions plus both request URLs and UTC retrieval time. Live values are intentionally not used as exact test fixtures.

Not run here: `benchmark_portability.py` requires a live model endpoint (a local Ollama server or an OpenAI API key) and measures model behavior, not this codebase's logic. It is optional; everything above runs offline.

## Tests

```bash
python -m unittest discover -s tests -v
```

18 tests (unittest, no pytest needed) covering the happy path and failure modes:

- **Portability contract** (`tests/test_portability.py`): valid skill passes for both providers; real `calculator` package passes; non-portable names (spaces, punctuation, >64 chars, empty, non-ASCII) are rejected per provider; non-object schemas are rejected; unsupported schema keywords (`$defs`, `patternProperties`) are listed by name; empty provider list is a valid boundary; multiple violations accumulate in one report. The root portfolio suite additionally pins this feature as `test_21_portability_contract_is_offline`.
- **Skill core** (`tests/test_skillforge.py`): discovery ignores empty directories; strict schema validation rejects wrong types and unknown fields; a code-execution attempt (`__import__('os')`) against the calculator fails; scaffolding refuses to overwrite a non-empty directory; a malformed manifest produces an actionable error.
- **Live weather boundary** (`tests/test_weather.py`): values are taken from mocked Open-Meteo responses (not constants), UTF-8 city names are encoded, provenance is present, and network/unknown-city errors fail explicitly.

## Threat model & data handling

- Handlers are **trusted local Python code**. Schema validation protects the handler boundary, but `import` is not a sandbox — do not install unreviewed skill packages.
- Package create/discover/validate/test and portability checks never open a network connection. Running a handler executes its declared behavior: the bundled weather skill sends the city name plus ordinary HTTP metadata/IP address to Open-Meteo, but sends no document, prompt, API key, or credential.
- No telemetry, no environment scraping, no credential access. Provider adapters read `OPENAI_API_KEY`/`OPENAI_BASE_URL` only when you explicitly call a provider.
- The `calculator` handler evaluates arithmetic via a whitelisted AST walker — no `eval`, no names/attributes/calls — and caps exponents; the test suite verifies a code-injection attempt fails.
- Schema validation rejects unknown fields at the boundary, so prompt-injected extra arguments never reach a handler.

## Limitations

- The portability contract is a **necessary, not sufficient** check: it validates names and the schema keyword subset against published provider rules, but cannot prove a specific model will actually emit a valid tool call — that needs the live benchmark above.
- Only OpenAI-compatible tool format is supported (`runtime.py`); Anthropic-style or other formats would need a new adapter.
- Handlers run in-process: no resource limits, no isolation. A production runner should use a separate process/container, explicit capabilities, and signed packages.
- `examples.json` compares outputs with exact equality; fuzzy or statistical matching is out of scope.
- The weather skill depends on Open-Meteo availability and model coverage. Its “current” values are weather-model data, not measurements from a guaranteed nearby station; geocoding selects the first match, so ambiguous city names should include a region/country.

## Tested core vs external integrations

Tested offline and covered by the suite: skill packaging, discovery, schema validation, deterministic example tests, the CLI, the two-provider portability contract, and the weather HTTP parsing/error contract with mocked responses. Live Open-Meteo availability and live Ollama/OpenAI calls are external integrations and are not asserted by the offline suite.
