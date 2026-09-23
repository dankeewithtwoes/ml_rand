# 11 — Local Knowledge OS

A local memory store backed by SQLite. It supports search, JSON export, and deletion; an optional vector backend can be enabled separately.

## Problem

Memory is stored in a local SQLite database. The store supports search, full JSON export, and deletion; tests cover these operations with and without the optional vector backend.

## Implementation

The test suite covers the search, export, and deletion operations.

- `add` — store a note with tags and a timestamp; empty content is rejected.
- `query(question, top_k)` — semantic search via ChromaDB when installed, with an
  automatic deterministic keyword fallback over SQLite when it is not (no network,
  no embeddings download). `top_k` is validated and strictly enforced.
- `export()` — the entire memory as versioned, portable JSON (`knowledge-os-export` v1).
- `delete(id)` — removes the episode from SQLite **and** from the vector index;
  idempotent (second delete returns `False`), verified to disappear from both
  export and subsequent search results.
- `summarize_old(days)` — compresses old episodes into a single summary record
  (memory compaction for long-running use).

## Architecture

Stack: Python 3.12, SQLite (stdlib `sqlite3`) as the source of truth.
Optional extras: ChromaDB + sentence-transformers for vector search, any
OpenAI-compatible local endpoint (Ollama by default) for the QA answer layer.
Everything optional degrades gracefully — the lifecycle core never leaves the stdlib.

| Module | Role |
|---|---|
| `knowledge_store.py` | Core `KnowledgeStore`: SQLite lifecycle, keyword fallback, export/delete, compaction |
| `ingest.py` | CLI: add a note with tags |
| `ask.py` | CLI: retrieve top-k context, then ask a local LLM (skips cleanly if none is reachable) |
| `compress_memory.py` | CLI: summarize old episodes |
| `benchmark_recall.py` | recall@k on a fixed personal-facts dataset |
| `examples/demo_lifecycle.py` | End-to-end offline demo of search → export → delete |

```
note ──▶ KnowledgeStore.add ──▶ SQLite (metadata.db)  ←── source of truth
              │                        ▲   │
              └─▶ ChromaDB (optional) ─┘   │ delete removes from BOTH
                                           │
question ─▶ query(top_k) ─▶ vector search ─┤──▶ top-k context ─▶ local LLM (optional)
                           └ keyword fallback (offline, default here)

export() ─▶ knowledge-os-export v1 JSON (all episodes, portable)
```

## Quickstart

Offline-first: the core demo needs **zero installs** — Python 3.10+ stdlib only.

```bash
# One-command end-to-end demo: ingest → search → export JSON → permanent delete
python examples/demo_lifecycle.py
```

This writes a real export to `examples/export_before_delete.json` and prints the
full lifecycle log. Captured real output: [`examples/demo_lifecycle_output.txt`](examples/demo_lifecycle_output.txt).

CLI usage (equally offline; creates `demo/knowledge/` on first write):

```bash
python ingest.py --note "Meeting with Artem: AI router deadline is Friday" --tags work,meetings
python ask.py "when is the router deadline"     # retrieval works offline; the LLM
                                                # answer layer needs Ollama on :11434
python compress_memory.py --days 30
python benchmark_recall.py
```

`pip install -r requirements.txt` is only needed for the optional vector path
(chromadb, sentence-transformers — heavy) and pulls the two pinned light packages.
The quickstart above works without it.

## Verified results

All outputs below are real runs on the dev machine — no fabricated metrics.

Environment: Windows 11 (10.0.26200), Python 3.12.6, AMD64
(Intel64 Family 6 Model 186). chromadb / sentence-transformers **not installed** —
all results are the SQLite keyword-fallback path. No GPU, no network, no API keys.

- `python examples/demo_lifecycle.py` — 4 notes ingested, both queries returned the
  correct episode at rank 1, export contained all 4 episodes, delete removed the
  episode from export and search (asserted in the script). Full log:
  [`examples/demo_lifecycle_output.txt`](examples/demo_lifecycle_output.txt);
  real export artifact: [`examples/export_before_delete.json`](examples/export_before_delete.json).
- `python benchmark_recall.py` — **recall@3 = 0.75** (3/4 FOUND, 1 MISS) on the
  fixed 4-fact dataset with keyword fallback. The miss is an exact-substring
  artifact ("паста" vs "пасты") — a known limitation of keyword matching without
  stemming; the vector path is expected to do better. Log:
  [`examples/cli_demo_output.txt`](examples/cli_demo_output.txt).
- `python -m unittest test_knowledge_store -v` — **9 tests, OK** in ~0.12 s.
- `ask.py` LLM layer: **not run here** — requires a local Ollama endpoint or
  `OPENAI_API_KEY`. Verified instead that it degrades gracefully
  (`[skip] LLM call failed` → `[LLM unavailable]`) while retrieval still works.
- Vector path (ChromaDB): **not run here** — optional heavy dependency, not
  installed; the fallback it replaces is what all numbers above measure.

## Tests

```bash
python -m unittest test_knowledge_store -v     # from this directory
```

`test_knowledge_store.py` (9 tests, unittest — same style as the portfolio root
suite) covers search, export, and deletion:

- Happy path: add → query with `top_k` → export → delete, including search-hit
  ordering, `top_k` enforcement, and a deleted episode disappearing from both
  search results and subsequent exports.
- Failure modes: empty/blank content rejected (`ValueError`); non-positive
  `top_k` rejected (`ValueError`); delete is idempotent and unknown IDs return
  `False` instead of raising; empty store queries and exports safely; queries
  with no matching words return `[]`; `top_k` larger than the corpus returns
  only what actually matches.

The portfolio-level proof test (`test_11_memory_export_delete_and_top_k`, in the
root `tests/`) exercises the same lifecycle through the root quality gate and is
unchanged.

## Threat model & data handling

- All data lives in one directory (`<store-dir>/metadata.db`, plus `chroma_db/`
  when the optional vector backend is used). Nothing is sent anywhere by the
  core store — there is no network code in `knowledge_store.py`.
- Export is a **complete** plaintext JSON dump of memory: treat it as sensitive
  as the store itself. The tool does not encrypt at rest — use OS-level disk
  encryption if the machine is shared.
- Delete is real: the row is removed from SQLite and the entry from the vector
  index. It is not a soft-delete flag, and tests assert the episode is gone from
  both search and export. (As with any SQLite delete, forensic recovery from
  free pages is possible until vacuum — see Limitations.)
- `ask.py` sends retrieved context to an LLM endpoint — by default local Ollama.
  If `OPENAI_BASE_URL` is pointed at a cloud API, your notes leave the machine;
  that is an explicit operator choice, not a default.
- What the system does **not** do: no telemetry, no background sync, no account
  system, no hidden retention of deleted episodes, no third-party calls in the
  storage path.

## Limitations

- Keyword fallback is exact substring matching without stemming or ranking
  sophistication — inflected word forms miss (measured above: recall@3 = 0.75 on
  the small Russian fixture). Install the optional vector extras for semantic recall.
- `summarize_old` produces a tag/count digest, not an LLM-written summary; the
  digest text is currently Russian-only.
- Deleted rows are not cryptographically erased — no `VACUUM`/secure-wipe is run,
  so do not rely on `delete` against a forensic adversary.
- Single-user, single-process design: SQLite handles concurrent reads, but the
  store is not a multi-tenant service and has no access control.
- Export format is versioned (v1) but there is no import/merge tool yet —
  export is a one-way portability guarantee today.

