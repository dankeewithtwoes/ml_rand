# Обслуживание моделей через vLLM

Скрипты запускают OpenAI-совместимый сервер и измеряют задержки запросов при заданной параллельности. `latency_stats.py` рассчитывает p50, p95 и p99 методом nearest rank.

## Проверка статистики

Из этой папки, без модели и GPU:

```bash
python demo_tail_latency.py
python -m unittest test_latency_stats -v
```

Пример отчёта: [tail_latency_report.json](demo/tail_latency_report.json). Данные демонстрации синтетические.

## Запуск сервера

Для пути с vLLM нужна совместимая среда Linux/CUDA и установленные зависимости:

```bash
pip install -r requirements.txt
python serve.py --model Qwen/Qwen2.5-1.5B-Instruct --port 8000 --wait
python client.py --base-url http://localhost:8000/v1
python benchmark.py --base-url http://localhost:8000/v1 --concurrency 4 --rounds 5 --max-tokens 128
```

## Ограничения

Локальные тесты проверяют расчёт статистики, а не работу vLLM на GPU. На маленькой выборке p99 часто совпадает с максимумом. Для сравнения производительности нужны одинаковые модели, параметры генерации, оборудование и число запросов. Промпты отправляются на указанный endpoint.
