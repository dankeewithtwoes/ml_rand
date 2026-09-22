# 05 — Local LLM Arena

> **Уникальный угол**: не просто чат с одной моделью, а **арена для сравнения локальных LLM**: один prompt прогоняется через несколько моделей, измеряется latency, tokens/sec и (опционально) judge-оценка качества.

## Что демонстрирует

- Параллельное тестирование нескольких локальных моделей.
- Измерение **latency**, **throughput** и **judge score**.
- Экспорт результатов в JSON для дальнейшего анализа.

## Почему это отличается от туториала

| Обычный туториал | Этот проект |
|------------------|-------------|
| Чат с одной моделью | Сравнение N моделей на одном prompt |
| Нет метрик | latency, tokens/sec, judge score |
| Ручная проверка ответов | JSON-отчёт с результатами |

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
