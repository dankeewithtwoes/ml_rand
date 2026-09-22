# 17 — Local Document Parser with Evidence Tracing

Local-first document parsing: extract structured fields from documents and
**trace every extracted field back to its exact source offsets** — no cloud
OCR, no hosted LLM, no data leaving the machine.

## Problem

Structured extraction from invoices, forms, and scans is usually done by
sending documents to a cloud API — a non-starter for contracts, medical, or
financial data. Running a local LLM instead solves the privacy problem but
creates a trust problem: LLMs hallucinate values, and a wrong "total due" in
a downstream system is indistinguishable from a correct one.

The fix this project demonstrates is **evidence tracing**: every extracted
field carries the exact character offsets and the verbatim quote it was
derived from. A field whose value does not appear in the source text is
flagged `grounded: false` instead of silently passing through, and an
`evidence_coverage` score tells you what fraction of the output is anchored
in the document. Verification becomes a cheap substring check instead of a
manual re-read of the whole document.

## What it does

- **Distinctive capability** (`evidence.py`): for each extracted field,
  locate the value in the source text and attach `{start, end, quote}` plus
  a `grounded` flag; `evidence_coverage()` aggregates the grounded fraction.
- **Main pipeline** (`parse.py`): read a document (PDF via PyMuPDF, local
  Tesseract OCR for image-only pages, or plain text directly), extract
  key-value fields, ground them against the source, and emit a JSON report.
- **Two extraction backends**: a deterministic line-oriented rules extractor
  (`rules.py`, pure stdlib, fully offline) and an optional local LLM via
  Ollama for free-form documents.
- **Batch and benchmark helpers**: `batch_parse.py` parses a directory of
  PDFs; `benchmark_parser.py` scores field accuracy against ground truth.

## Architecture

Stack: Python 3.12, PyMuPDF for PDF rendering, Pillow + pytesseract with an
installed local Tesseract executable for scanned pages, and an optional local
Ollama server for LLM structuring. Text input and rule extraction stay local.

```
 document (.pdf via PyMuPDF  |  .txt/.md read directly)
        |
        v
    raw text -------------------------------------------------.
        |                                                     |
        v                                                     |
  field extraction                                            |
  rules.py (offline, deterministic)  |  local LLM via Ollama  |
        |                                                     |
        v                                                     v
  evidence.py: attach_evidence(fields, source_text)
        |  per field: value, {start, end, quote}, grounded
        v
  JSON report + evidence_coverage (0.0 .. 1.0)
```

Key modules:

| Module | Role |
|---|---|
| `evidence.py` | Distinctive feature: offsets, quotes, grounding, coverage |
| `rules.py` | Deterministic offline `Key: Value` extractor |
| `parse.py` | CLI pipeline: input → extract → ground → JSON |
| `batch_parse.py` | Directory-level PDF batch parsing |
| `benchmark_parser.py` | Field accuracy vs ground truth |

## Quickstart

The offline demo needs **zero installs** — text input, rules extraction, and
evidence tracing are pure standard library:

```bash
cd 17_local_document_parser
python parse.py --input examples/sample_invoice.txt --output examples/demo_output.json --no-llm
# -> [parse] 1 pages -> examples\demo_output.json
```

Optional extras, only when you need them:

```bash
pip install -r requirements.txt   # pinned light deps + PyMuPDF for PDF input
python parse.py --input invoice.pdf --output invoice.json           # PDF + LLM
python parse.py --input invoice.pdf --output invoice.json --no-llm  # PDF + rules
python parse.py --input scan.pdf --output scan.json --no-llm --ocr-language rus+eng
python batch_parse.py --input-dir docs/ --output-dir parsed/ --no-llm
```

`pip` устанавливает Python-обвязку OCR, но сам Tesseract — системная
зависимость. Установите локальный исполняемый файл Tesseract и языковые данные
для значения `--ocr-language` (`rus+eng` по умолчанию). Если движок или язык
не найдены, парсер завершится явной ошибкой и не выдаст пустой текст за
успешный результат. В JSON поле `extraction` для каждой страницы фиксирует
`embedded_text` или `tesseract_ocr`, число символов, язык и DPI.

LLM structuring expects a local Ollama server (`OPENAI_BASE_URL`,
`OLLAMA_MODEL` env vars); it is never required for the demo or the tests.

## Verified results

Run on this machine: **Windows 11 (10.0.26200), Python 3.12.6, Intel64
Family 6 Model 186 (x86-64)**. Full terminal log: `examples/demo_run.log`.

Demo command above (real output in `examples/demo_output.json`):

- 7 fields extracted from `examples/sample_invoice.txt` by the rules backend
- 7/7 fields grounded with exact offsets, e.g. `"total due": "$1,204.50"`
  → `{start: 130, end: 139, quote: "$1,204.50"}`
- `evidence_coverage: 1.0`

Test suite (`python -m unittest discover -p "test*.py"`):

```
Ran 15 tests in 0.103s
OK
```

An additional end-to-end check generated an image-only PDF, parsed it with
PyMuPDF 1.28.0 + the installed Tesseract 5.5.1 (`--ocr-language eng`), and
returned `method: tesseract_ocr`, text `INVOICE / Total due: 42 USD`, and
`evidence_coverage: 1.0`. This proves the local scanned-PDF path executes; it
is not an OCR-accuracy benchmark.

**Not run here** (marked honestly, no invented numbers): local-LLM structuring
(needs a running Ollama server), Russian OCR (the machine has `eng`/`osd` but
not the `rus` Tesseract language pack), and the ground-truth benchmark (needs
a labeled corpus of representative scans).

## Tests

```bash
cd 17_local_document_parser
python -m unittest discover -p "test*.py" -v
```

Covered:

- **Happy path** — fields grounded with exact offsets, offsets slice the
  original source back to the value; case-insensitive matching preserves the
  original-cased quote; non-string values coerced.
- **Failure modes** — hallucinated value absent from the source →
  `grounded: false`, `evidence: null`; empty source → everything ungrounded,
  coverage 0.0; empty/whitespace value never grounded (guards the
  `find("") == 0` false positive); empty field set → vacuous coverage 1.0.
- **Rules extractor** — key-value lines, empty input, malformed lines,
  duplicate keys.
- **End-to-end CLI** — `parse.py --no-llm` on a temp document produces a
  report whose evidence offsets slice the emitted text correctly.
- **OCR routing** — image-only pages are rendered and sent to Tesseract,
  text-layer pages bypass OCR, extraction provenance is emitted, and missing
  or empty OCR results fail explicitly.

The portfolio-level proof test
`test_17_extracted_fields_include_source_evidence` (root `tests/test_wave3.py`)
is unchanged and green via the root `quality_gate.py`.

## Threat model & data handling

- Documents are read from local disk and written to local disk; nothing is
  sent anywhere by the offline path.
- The optional LLM backend talks only to a user-configured local server
  (default `http://localhost:11434`); no cloud keys exist in the project.
- Evidence quotes are verbatim slices of the source — the output JSON
  contains the document text, so treat reports as sensitive as the input.
- The system does **not** verify semantics: grounding proves a value appears
  in the document, not that it is the *right* value.
- The system does **not** redact, encrypt, or retain anything beyond the
  output file you ask for.

## Limitations

- Grounding is substring matching: a value appearing only as part of a
  larger token (e.g. `42` inside `4207`) can still be flagged grounded.
- The rules extractor only sees line-oriented `Key: Value` pairs; free-form
  prose needs the LLM backend (not run on the verification machine).
- PDF input requires PyMuPDF; scanned pages additionally require the local
  Tesseract executable and the requested language packs. OCR quality depends
  on scan resolution, skew, typography, and installed language data.
- Matching is case-insensitive but literal — paraphrased or reformatted
  values (e.g. `$1,204.50` vs `1204.5`) will not ground.
