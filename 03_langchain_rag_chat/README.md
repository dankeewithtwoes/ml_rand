# 03 — Sentence-Grounded Hybrid RAG

Retrieval-augmented generation answers questions over local documents, then checks **which sentences of the answer are actually supported by the retrieved evidence**.

## Problem → why it matters

RAG systems reduce hallucination but do not eliminate it: the model can still blend retrieved facts with plausible-sounding claims that appear nowhere in the source documents. When such a system answers a real user, the failure is silent — the answer reads fluently whether it is grounded or not, so nobody notices the invented sentence until it causes a wrong decision.

The standard fix is an LLM-as-a-judge faithfulness score, which adds cost, latency, another model to trust, and usually a network call. This project takes the cheaper first step: a deterministic, offline, sentence-level grounding check that flags exactly which claims in a generated answer lack support in the retrieved context — so unsupported sentences can be shown to a human, filtered, or logged before the answer is trusted.

## What it does

**Distinctive capability (tested core):** `grounding.py` — sentence-level grounding with no LLM judge. It splits an answer into sentences, measures the share of each sentence's terms that appear in the retrieved evidence, and flags every sentence below the coverage threshold as an unsupported claim. Pure standard library: no model downloads, no GPU, no network.

**Main pipeline (optional, heavy dependencies):** a hybrid retrieval stack — BM25 + dense embeddings (`EnsembleRetriever`) over a persistent Chroma index, cross-encoder reranking (`ms-marco-MiniLM-L-6-v2`), and RAGAS-style proxy metrics (context precision, answer relevancy, faithfulness) in `evaluate_rag.py`. Answers come from any OpenAI-compatible endpoint or a local Ollama model.

## Architecture

| Module | Role | Dependencies |
|---|---|---|
| `grounding.py` | sentence-level evidence coverage (the tested core) | stdlib only |
| `examples/grounding_demo.py` | offline demo → `examples/grounding_report.json` | stdlib only |
| `rag_engine.py` | `HybridRAG`: loaders → chunks → BM25 + Chroma ensemble → rerank → LLM | langchain, chromadb, sentence-transformers |
| `rag_chat.py` | CLI chat over the hybrid engine | pipeline deps |
| `evaluate_rag.py` | proxy metrics: context precision / answer relevancy / faithfulness | pipeline deps + scikit-learn |
| `build_index.py` | build/rebuild the persistent Chroma index | pipeline deps |

```text
documents/*.txt
      │
      ▼
chunking ──► BM25 retriever ──┐
      │                       ├── ensemble ──► cross-encoder rerank ──► LLM answer
      └─► Chroma (dense) ─────┘                                        │
                                                                       ▼
                                          grounding.py: per-sentence coverage vs evidence
                                                                       ▼
                                          grounded flags per sentence + grounded ratio
```

## Quickstart (offline, one command)

```bash
python examples/grounding_demo.py
```

No `pip install` needed — the demo and the tests run on the standard library alone. The demo uses the real project documents as the evidence base, checks three generated answers, prints per-sentence verdicts, and writes the full report to [`examples/grounding_report.json`](examples/grounding_report.json) (a real run artifact, regenerated on every run).

Full hybrid pipeline (not part of the offline quickstart):

```bash
pip install -r requirements.txt   # pulls torch/chromadb — heavy, optional
cp .env.example .env              # or leave empty to fall back to local Ollama
python rag_chat.py "What are the benefits of Product A?"
python evaluate_rag.py            # writes demo/eval_results.json
```

## Verified results

Real run on this machine — command `python examples/grounding_demo.py` (full JSON: [`examples/grounding_report.json`](examples/grounding_report.json)):

```text
[supported answer] grounded ratio: 1.00
  ok  coverage=1.00  Product A is an analytics platform.
  ok  coverage=1.00  Its benefits include real-time dashboards and low-latency queries.
  -> 0 unsupported sentence(s)

[mixed answer with a hallucinated claim] grounded ratio: 0.50
  ok  coverage=0.86  Product B classifies support tickets with language models.
  FLAG coverage=0.25  Product B also offers a free tier with unlimited storage.
  -> 1 unsupported sentence(s)

[answer outside the evidence base] grounded ratio: 0.00
  FLAG coverage=0.25  The platform was founded in 1998 and is headquartered in Oslo.
  -> 1 unsupported sentence(s)
```

Environment: Windows 11 (10.0.26200), Python 3.12.6, 64-bit x86 (Intel64 Family 6 Model 186, 20 logical CPUs), no GPU used.

The full hybrid pipeline was **not** run on this machine: it requires the heavy optional extras (torch via sentence-transformers, chromadb, rank-bm25) plus an LLM endpoint (OpenAI-compatible API or local Ollama). Numbers for `evaluate_rag.py` are therefore not claimed here — only the offline grounding core is verified.

## Tests

```bash
python -m unittest discover -s tests -v
```

12 tests, all passing on the environment above (`Ran 12 tests in 0.001s — OK`). Coverage:

- **Happy path**: supported vs unsupported sentences flagged independently; ratio is the mean of sentence flags; case/punctuation normalization.
- **Failure modes**: empty answer (ratio 0.0), empty context list (every sentence flagged), non-string answer rejected (`TypeError`), a bare string passed as `contexts` rejected instead of silently iterating characters, non-string context element rejected, out-of-range threshold rejected (`ValueError`).
- **Boundary cases**: coverage exactly at the threshold counts as grounded; a termless sentence ("OK.") is neutral; strict threshold 1.0 flags partial coverage.

The portfolio-level proof test `test_03_grounding_flags_unsupported_claim` lives in the repository root (`tests/test_wave1.py`) and exercises this same module via the root quality gate.

## Threat model & data handling

- The grounding check is fully local and deterministic: no network calls, no telemetry, no model downloads, nothing leaves the machine.
- Source documents stay on disk and are only read; the demo writes its report inside the project directory and nowhere else.
- The optional pipeline sends document chunks to whatever `OPENAI_BASE_URL` points at — with no API key configured it falls back to `localhost` (Ollama). Pointing it at a hosted API means your documents leave the machine; that is an explicit operator choice, not a default.
- `OPENAI_API_KEY` is read from a local `.env` (see `.env.example`); keep the real file out of version control.
- What the system does **not** do: it does not verify factual truth, does not detect keyword-stuffed unsupported claims, and does not replace human review for high-stakes answers.

## Limitations

- The grounding score is lexical overlap, not entailment: a sentence that merely repeats evidence keywords can false-pass, and a heavily paraphrased supported sentence can false-flag.
- No stemming or lemmatization — inflected word forms ("dashboard" vs "dashboards" matches, "query" vs "queries" does not) lower measured coverage.
- Sentence splitting is regex-based; abbreviations and decimals can split oddly.
- The default threshold (0.35) is a heuristic and should be tuned per domain.
- Only the grounding core is integration-tested here; the langchain/Chroma/reranker pipeline is exercised by compilation checks and by structure, not by an end-to-end run on this machine.
