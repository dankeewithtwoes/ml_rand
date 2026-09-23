# Local-First AI Engineering Portfolio

This repository contains 21 projects covering local ML and LLM workflows: training, retrieval, inference, routing, evaluation, and privacy. Some demos depend on external APIs, models, or hardware; the offline checks do not validate those integrations.

## Start here

| Project | Focus | Check |
|---|---|---|
| [Universal Skill Forge](./21_universal_skill_forge) | Portable tool schemas for agents | Offline schema and portability checks |
| [Local Knowledge OS](./11_local_knowledge_os) | Searchable local memory | Search, export, and deletion tests |
| [Local Model Router](./14_local_model_router) | Privacy, cost, and latency rules | Selection and rejection reasons |
| [AI Observability Guard](./18_local_ai_observability) | Traces without raw prompt text | Redaction and trace tests |
| [Red-Team Arena](./20_local_redteam_arena) | Safety evaluation | Confidence intervals and error accounting |
| [Evaluated RAG](./03_langchain_rag_chat) | Evidence checks for generated answers | Sentence-level grounding test |
| [Code repair agent](./10_openhands_code_agent) | Guarded automated code changes | Patch safety checks |
| [vLLM serving](./07_vllm_serving) | Small-sample latency statistics | Nearest-rank percentile tests |
| [Document parser](./17_local_document_parser) | Source references for extracted fields | Evidence offset tests |

## Run the offline checks

From the repository root:

    python quality_gate.py
    cd 21_universal_skill_forge
    pip install -r requirements.txt
    python -m unittest discover -s tests -v
    python skillforge.py doctor

The root gate checks the 21 local contracts, compiles Python entry points, and runs the portfolio tests. It does not test every model, API, GPU, or operating system integration.

Demo files are kept in each project's demo/, examples/, or docs/ directory. The GitHub Actions workflow runs the root gate and selected project tests on pushes.

## Project groups

1. **Train and adapt:** PyTorch, LoRA fine-tuning, and synthetic data.
2. **Retrieve and process:** RAG, agents, local memory, and document parsing.
3. **Run models:** Ollama, GGUF, vLLM, model routing, and edge inference.
4. **Evaluate and protect:** observability, code review, and red-team testing.
5. **Reuse tools:** provider-neutral skills with executable contracts.

See [PROJECT_SCORECARD.md](./PROJECT_SCORECARD.md) for current limitations and next steps, and [ARCHITECTURE.md](./ARCHITECTURE.md) for the project map.

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

## License

Portfolio code is released under the MIT License. Third-party models, datasets, and frameworks retain their own licenses.

