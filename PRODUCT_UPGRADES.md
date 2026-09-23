# Offline behavior checks

Each project has at least one behavior that can be checked locally without downloading a model or calling a paid API. These checks cover selected parts of each project; they do not validate every external integration.

| # | Capability | Implementation | Test |
|---:|---|---|---|
| 01 | classifier calibration report | Brier score, ECE, and confidence bins | perfect predictions have zero Brier/ECE |
| 02 | tuning-data leakage audit | hashes normalized examples across splits | duplicate and validation leakage detection |
| 03 | sentence-level grounding | checks answer claims against retrieved text | unsupported sentence is flagged |
| 04 | bounded agent arithmetic | AST interpreter without eval | Python execution payload is rejected |
| 05 | local model ranking | scores quality and relative speed | ranking trade-off is reproducible |
| 06 | GGUF artifact integrity | records size and SHA-256 | valid and invalid checksums are tested |
| 07 | nearest-rank tail latency | calculates p95/p99 from observations | known sample has exact percentiles |
| 08 | workflow contract checks | redacted fingerprint and input diff | removed input is detected |
| 09 | generated-media provenance | hashes workflow and output files | provenance record is stable |
| 10 | repair safety gate | checks syntax, dangerous calls, and change size | dynamic execution is blocked |
| 11 | local memory lifecycle | search, export, and deletion with SQLite | stored records can be retrieved and removed |
| 12 | wake-word boundaries | detects complete wake words | substring match is rejected |
| 13 | deterministic tuning split | seeded split and duplicate checks | repeatability and leakage checks |
| 14 | constrained model routing | records selection and rejection reasons | private prompt excludes cloud models |
| 15 | local SARIF reporting | emits GitHub Code Scanning format | rule IDs and SARIF output are stable |
| 16 | synthetic-data checks | detects PII and repeated rows | email and duplicate rows are rejected |
| 17 | extraction evidence offsets | links fields to source text | quote and coverage are checked |
| 18 | private traces | stores prompt length and hash | raw prompt text is absent |
| 19 | edge circuit breaker | tracks cooldown and weighted load | failed node recovers after cooldown |
| 20 | safety statistics | reports confidence intervals and errors | infrastructure errors are excluded |
| 21 | skill portability | checks tool names and schema subset | provider contract runs offline |

## What the checks cover

quality_gate.py runs local contract checks, failure cases, compilation, and documentation checks. It does not measure GPU throughput, model quality, OCR accuracy, provider compatibility, or end-to-end latency. Publish those results with raw output and the relevant hardware, model, dataset, and software versions.

