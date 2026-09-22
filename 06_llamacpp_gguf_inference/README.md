# 06 — Quantization Benchmark

> **Уникальный угол**: не инференс ради инференса, а **сравнительный бенчмарк квантизаций GGUF** (Q4_K_M, Q5_K_M, Q6_K) по скорости и качеству ответа.

## Что демонстрирует

- Скачивание моделей в локальный кэш.
- Замеры **load time**, **generation time**, **tokens/sec**.
- JSON-отчёт для выбора оптимального trade-off скорость/качество.

## Почему это отличается от туториала

| Обычный туториал | Этот проект |
|------------------|-------------|
| Один запуск одной модели | Сравнение нескольких квантизаций |
| Нет метрик | tokens/sec, load/gen time |
| Субъективная оценка | JSON-отчёт |

## Запуск

```bash
pip install -r requirements.txt

# Скачать несколько квантизаций
python download_model.py --model qwen2.5-1.5b-q4 --cache-dir models
python download_model.py --model qwen2.5-1.5b-q5 --cache-dir models
python download_model.py --model qwen2.5-1.5b-q6 --cache-dir models

# Бенчмарк
python benchmark_quant.py --models-dir models --max-tokens 128
```

## Ожидаемый результат

```
[bench] qwen2.5-1.5b-instruct-q4_k_m.gguf
  tokens/sec=45.12 load=1.2s gen=2.8s
[bench] qwen2.5-1.5b-instruct-q5_k_m.gguf
  tokens/sec=38.50 load=1.3s gen=3.2s
...
Saved demo/benchmark_quant.json
```
