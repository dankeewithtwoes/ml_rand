# Local-First AI Engineering Portfolio

21 hands-on projects exploring how to build AI systems that remain measurable, private, and useful outside a notebook.

Every project now has a distinct offline capability and a behavioral proof. Run `python quality_gate.py` to validate the complete 21-project contract, execute 21 behavioral tests, and compile every Python entry point.

The portfolio still distinguishes a tested core from external integrations: a green offline gate does not pretend that every model, GPU, API, or operating system has been integration-tested.

See [PRODUCT_UPGRADES.md](./PRODUCT_UPGRADES.md) for the user value and proof added to every project.

## Start here

| Project | Problem it solves | Evidence | Status |
|---|---|---|---|
| [Universal Skill Forge](./21_universal_skill_forge) | Agent tools are tied to one provider and rarely have executable contracts | strict JSON Schema, offline examples, portability contract | Tested core |
| [Local Knowledge OS](./11_local_knowledge_os) | Personal AI memory should stay searchable and user-owned | search, export, deletion, deterministic fallback test | Tested core |
| [Local Model Router](./14_local_model_router) | Not every prompt should leave the machine | explainable privacy/cost/latency constraints | Tested core |
| [AI Observability Guard](./18_local_ai_observability) | LLM traces must not become another privacy leak | content-free trace hashes and local PII redaction | Tested core |
| [Red-Team Arena](./20_local_redteam_arena) | Safety claims need uncertainty and error accounting | confidence intervals and infrastructure-error exclusion | Tested core |
| [Evaluated RAG](./03_langchain_rag_chat) | Generated answers should cite verifiable evidence | sentence-level grounding flags unsupported claims | Tested core |
| [Code repair agent](./10_openhands_code_agent) | AI-generated fixes can be unsafe or over-broad | safety gate blocks dynamic execution and change overruns | Tested core |
| [vLLM serving](./07_vllm_serving) | Small benchmark samples distort tail latency | nearest-rank percentiles with exact small-sample semantics | Tested core |
| [Document parser](./17_local_document_parser) | Extracted fields must trace back to source evidence | evidence offsets with coverage scoring | Tested core |

## One command to verify the portfolio

```bash
python quality_gate.py
cd 21_universal_skill_forge
pip install -r requirements.txt
python -m unittest discover -s tests -v
python skillforge.py doctor
```

The root smoke test checks that all 21 projects compile. Project tests verify behavior. This distinction matters: a green compile check is not presented as product quality.

Every flagship also ships demo artifacts captured from real offline runs — see `examples/` (or `demo/`, `docs/`) inside each project. CI runs the same gate plus the flagship behavioral tests on every push: `.github/workflows/ci.yml`.

## The system story

```text
private knowledge → retrieval → model routing → guarded inference
        ↑                                      ↓
 reusable skills ← evaluation / red teaming ← traces
```

The projects are not meant to be 21 unrelated framework tutorials. Together they explore a local-first AI stack:

1. **Build and adapt** — PyTorch experiments, LoRA fine-tuning, synthetic data.
2. **Retrieve and reason** — evaluated RAG, agents, long-term memory, document parsing.
3. **Run efficiently** — Ollama, GGUF, vLLM, model routing, edge inference.
4. **Operate safely** — observability, private code review, red teaming.
5. **Reuse capabilities** — provider-neutral, contract-tested skills.

See [PROJECT_SCORECARD.md](./PROJECT_SCORECARD.md) for the candid audit and roadmap, and [ARCHITECTURE.md](./ARCHITECTURE.md) for the full map.

## Complete catalog

| # | Project | Core experiment |
|---:|---|---|
| 01 | [PyTorch classifier](./01_pytorch_classifier_demo) | reproducible training, MLflow, ONNX |
| 02 | [Hugging Face tuning](./02_huggingface_finetune_demo) | parameter-efficient LoRA evaluation |
| 03 | [Evaluated RAG](./03_langchain_rag_chat) | hybrid retrieval, reranking, RAG metrics |
| 04 | [LlamaIndex agent](./04_llamaindex_agent) | state, routing, fallback |
| 05 | [Local LLM arena](./05_ollama_local_llm) | latency and model comparison |
| 06 | [GGUF inference](./06_llamacpp_gguf_inference) | quantization trade-offs |
| 07 | [vLLM serving](./07_vllm_serving) | throughput and tail latency |
| 08 | [Dify workflow](./08_dify_workflow_integration) | workflow-as-code |
| 09 | [ComfyUI pipeline](./09_comfyui_image_gen) | reproducible batch generation |
| 10 | [Code repair agent](./10_openhands_code_agent) | test-driven automated repair |
| 11 | [Knowledge OS](./11_local_knowledge_os) | private long-term memory |
| 12 | [Voice companion](./12_local_voice_companion) | offline VAD → STT → LLM → TTS |
| 13 | [Fine-tuning lab](./13_local_finetuning_lab) | consumer-GPU training |
| 14 | [Model router](./14_local_model_router) | privacy/cost/latency routing |
| 15 | [Code reviewer](./15_local_code_reviewer) | local review without source leakage |
| 16 | [Synthetic data factory](./16_local_synthetic_data_factory) | schema coverage and downstream value |
| 17 | [Document parser](./17_local_document_parser) | OCR, layout, structured extraction |
| 18 | [AI observability](./18_local_ai_observability) | policy proxy and local traces |
| 19 | [Edge fleet](./19_local_edge_fleet) | distributed inference and failover |
| 20 | [Red-Team Arena](./20_local_redteam_arena) | adversarial evaluation |
| 21 | [Skill Forge](./21_universal_skill_forge) | portable tools with executable contracts |

## Open-source direction

Useful contributions are welcome: reproducible benchmark fixtures, platform-neutral setup, real-world datasets with safe licenses, failure-case tests, and demo recordings. See [CONTRIBUTING.md](./CONTRIBUTING.md).

## License

Portfolio code is released under the MIT License. Third-party models, datasets, and frameworks retain their own licenses.

