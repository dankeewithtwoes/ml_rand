# 05 — Local LLM Arena

The script compares local models on the same prompts by latency, generation speed, and optional quality score.

## Возможности

- Параллельное тестирование нескольких локальных моделей.
- Измерение **latency**, **throughput** и **judge score**.
- Экспорт результатов в JSON для дальнейшего анализа.

## Запуск

```bash
pip install -r requirements.txt

# Скачать модели
python pull_model.py --model llama3.1
python pull_model.py --model phi3

# Арена (без judge)
python arena.py --models llama3.1,phi3 --prompt "Explain RAG."

# Арена с judge-оценкой
python arena.py --models llama3.1,phi3 --prompt "Explain RAG." --judge llama3.1

# Интерактивный чат
python chat.py --interactive
```

## Ожидаемый результат

```
Model: llama3.1
Latency: 2.3s | Tokens: 85 | Speed: 36.96 tok/s
Answer: ...

Model: phi3
Latency: 1.8s | Tokens: 92 | Speed: 51.11 tok/s
Answer: ...
```

Результаты сохраняются в `demo/arena_results.json`.

