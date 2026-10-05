# ML-проекты

21 учебный проект на Python: обучение классификаторов, LoRA, RAG, локальный инференс, агенты и обработка данных. В каждом каталоге есть код, зависимости и команды запуска. Проекты запускаются отдельно.

## Веб-интерфейс

Общий интерфейс показывает примеры функций из всех проектов, принимает JSON и сохраняет историю в SQLite. Он запускает отдельные функции; обучение больших моделей и внешние сервисы настраиваются отдельно.

Из корня репозитория:

```bash
python -m venv .venv
```

Активируйте `.venv`: `source .venv/bin/activate` на Linux/macOS или `.venv\Scripts\Activate.ps1` в PowerShell. Затем:

```bash
python -m pip install -r requirements-web.txt
python portfolio_app.py --open
```

Адрес интерфейса — `http://127.0.0.1:8801`. Для Windows есть `Start-Portfolio-Workbench.ps1`.

## Проверка

В активированном окружении:

```bash
python -m pip install jsonschema pytest httpx httpx2
python quality_gate.py
```

Проверка включает наличие файлов в 21 проекте, компиляцию Python и локальные тесты. Она не подтверждает все вызовы моделей, работу на GPU или качество ответов.

[Архитектура](ARCHITECTURE.md) описывает группы проектов, [состояние](PROJECT_SCORECARD.md) — незавершённые части и дальнейшую работу, [PRODUCT_UPGRADES.md](PRODUCT_UPGRADES.md) — проверяемые функции.

## Проекты

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

## Лицензия

Код опубликован под MIT. Модели, датасеты и сторонние библиотеки распространяются по собственным лицензиям.
