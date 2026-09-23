# 06 — Quantization Benchmark

The scripts compare GGUF quantizations Q4_K_M, Q5_K_M, and Q6_K by speed and answer quality.

## Возможности

- Скачивание моделей в локальный кэш.
- Замеры **load time**, **generation time**, **tokens/sec**.
- JSON-отчёт для выбора оптимального trade-off скорость/качество.

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

