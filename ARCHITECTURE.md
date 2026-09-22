# Архитектура rezume_git

Это не просто набор туториалов. Проекты спроектированы как цепочка **«от эксперимента к production»**: каждый следующий решает задачу, которую предыдущий оставил нерешённой.

## Карта связей

```
[01 PyTorch harness] ──→ эксперименты + reproducibility
         │
         ▼
[02 HF LoRA tuning] ──→ адаптация модели под домен
         │
         ▼
[03 Evaluated RAG] ──→ модель + знания + метрики качества
         │
         ▼
[04 Stateful agent] ──→ долгая память, выбор инструментов
         │
         ▼
[05 Local LLM arena] ──→ выбор локальной модели под задачу
         │
         ▼
[06 GGUF benchmark] ──→ оптимизация размера/скорости локальной модели
         │
         ▼
[07 vLLM serving] ──→ production-сервинг с бенчмарками
         │
         ▼
[08 Dify workflow] ──→ low-code оркестрация
         │
         ▼
[09 ComfyUI batch] ──→ генеративный pipeline
         │
         ▼
[10 OpenHands agent] ──→ автоматизация разработки
         │
         ▼
[11 Knowledge OS] ──→ персональная долгосрочная память
         │
         ▼
[12 Voice companion] ──→ оффлайн мультимодальный интерфейс
         │
         ▼
[13 Fine-tuning Lab] ──→ дообучение под себя на своём железе
         │
         ▼
[14 Model Router] ──→ умный выбор локальной/облачной модели
         │
         ▼
[15 Secure Code Reviewer] ──→ приватный code review
         │
         ▼
[16 Synthetic Data Factory] ──→ генерация данных без утечки
         │
         ▼
[17 Document Parser] ──→ локальное понимание документов
         │
         ▼
[18 AI Observability] ──→ self-hosted мониторинг + guardrails
         │
         ▼
[19 Edge Fleet] ──→ распределённый inference
         │
         ▼
[20 Red-Team Arena] ──→ локальная оценка безопасности
         │
         ▼
[21 Universal Skill Forge] ──→ универсальные скиллы для любых моделей
```

## Чем каждый проект отличается от туториала

| Проект | Типичный туториал | Этот проект |
|--------|-------------------|-------------|
| 01 PyTorch | `train()` на two-moons | Reproducible MLOps harness с Hydra + MLflow |
| 02 Hugging Face | Full fine-tune sentiment | LoRA instruction tuning на кастомном домене |
| 03 LangChain RAG | Базовый RetrievalQA | Hybrid search + reranker + RAGAS evaluation |
| 04 LlamaIndex | Одношаговый агент | Stateful router agent с памятью и fallback |
| 05 Ollama | Простой чат | Local LLM arena сравнения моделей |
| 06 llama.cpp | `Llama()` инференс | Quantization benchmark: speed (tokens/sec, load/gen time) |
| 07 vLLM | `api_server` + client | Нагрузочное тестирование с percentile latency |
| 08 Dify | HTTP-запросы | Workflow-as-code CLI с import/export |
| 09 ComfyUI | Одна генерация | Batch pipeline с grid-визуализацией |
| 10 OpenHands | Один фикс одного файла | Test-driven repair benchmark на 5 багах |
| 11 Knowledge OS | RAG над папкой | Долгосрочная персональная память с компрессией |
| 12 Voice Companion | Текстовый чат | Оффлайн VAD→STT→LLM→TTS pipeline |
| 13 Fine-tuning Lab | Jupyter ноутбук | Автоматизированная LoRA lab с quant/deploy |
| 14 Model Router | Хардкод одной модели | Автовыбор локальной/облачной модели по задаче |
| 15 Code Reviewer | LLM-запрос | Локальный code review pipeline с precision/recall |
| 16 Synthetic Data | Пара примеров | Фабрика с контролем coverage и downstream accuracy |
| 17 Document Parser | Только OCR | OCR + layout + LLM-структурирование |
| 18 Observability | Нет мониторинга | Self-hosted guardrails + dashboard |
| 19 Edge Fleet | Один инстанс | Распределённый inference с failover |
| 20 Red-Team | Один prompt | Систематическое adversarial тестирование |
| 21 Skill Forge | Skill под один фреймворк | Универсальный skill + cross-model portability |

## Как читать портфолио

1. Если вы HR/рекрутер — смотрите `README.md` каждого проекта и раздел **«Почему этот проект отличается»**.
2. Если вы техлид — смотрите код, метрики и `run_all_smoke_tests.py`.
3. Если вы изучаете — идите по порядку 01 → 21, каждый проект добавляет один production-слой.
