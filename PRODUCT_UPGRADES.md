# Tested product capabilities

Each project owns one distinctive, dependency-light capability that can be verified without downloading a model or using a paid API. Heavy integrations remain optional layers above this tested core.

| # | Useful capability | Why it is different | Behavioral proof |
|---:|---|---|---|
| 01 | classifier calibration report | measures confidence quality, not accuracy alone | perfect predictions have zero Brier/ECE |
| 02 | tuning-data leakage audit | hashes normalized full examples across splits | duplicates and validation leakage are detected |
| 03 | sentence-level grounding | exposes which answer claims lack retrieved evidence | unsupported claim is flagged independently |
| 04 | bounded agent arithmetic | AST interpreter instead of `eval` | Python execution payload is rejected |
| 05 | explainable local model ranking | separates quality and relative speed components | quality/speed trade-off is reproducible |
| 06 | GGUF artifact integrity | benchmark binds results to size and SHA-256 | correct and incorrect checksums are tested |
| 07 | nearest-rank tail latency | correct p95/p99 for small samples | known latency series has exact percentile |
| 08 | secret-safe workflow contracts | redacted fingerprint plus breaking input diff | removed workflow input is detected |
| 09 | generated-media provenance | workflow and outputs receive content hashes | record is stable and complete |
| 10 | AI repair safety gate | syntax, dangerous calls, and change budget checked before write | dynamic execution is blocked; diff is real |
| 11 | user-owned AI memory | search, export, and deletion work without vectors | lifecycle is tested against SQLite |
| 12 | boundary-aware wake word | prevents activation inside larger words | command preserved; substring rejected |
| 13 | deterministic tuning split | seeded split plus empty/duplicate gate | repeatability and duplicate rejection tested |
| 14 | constrained model routing | returns selection and rejection reasons | cloud model rejected for private prompt |
| 15 | local SARIF reporting | private scanner connects to GitHub Code Scanning | stable rule id and SARIF 2.1 output tested |
| 16 | synthetic-data privacy gate | blocks PII and normalized duplicates | email and repeated row rejected |
| 17 | extraction evidence offsets | each field points back to an exact source quote | coverage and quote tested |
| 18 | privacy-preserving traces | stores only length/hash while supporting redaction | raw prompt and email never reach trace |
| 19 | edge circuit breaker | cooldown plus capacity-weighted load selection | failed node opens and later recovers |
| 20 | calibrated safety statistics | reports CI and excludes infrastructure failures | sample count and Wilson interval tested |
| 21 | offline skill portability | checks provider-safe names and schema subset | two-provider contract verified offline |

## Verification boundary

`quality_gate.py` proves local contracts, failure cases, compilation, and documentation presence. It does not fabricate integration evidence. GPU throughput, model quality, OCR accuracy, provider compatibility, and end-to-end latency must be published only with raw result files plus hardware, model, dataset, and software versions.
