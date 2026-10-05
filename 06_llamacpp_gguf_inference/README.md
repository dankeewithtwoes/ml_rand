# Инференс и сравнение GGUF-моделей

Скрипты загружают модели GGUF и измеряют время загрузки, время генерации и tokens/sec через llama-cpp-python. Ответы сохраняются для сравнения. model_integrity.py рассчитывает SHA-256 и проверяет размер файла.

## Запуск

Команды выполняются из этой папки.

```bash
pip install -r requirements.txt
python download_model.py --model qwen2.5-1.5b-q4 --cache-dir models
python download_model.py --model qwen2.5-1.5b-q5 --cache-dir models
python download_model.py --model qwen2.5-1.5b-q6 --cache-dir models
python benchmark_quant.py --models-dir models --max-tokens 128
```

## Ограничения

Нужны веса моделей и совместимая сборка llama-cpp-python. Скрипт сохраняет тексты ответов, но не вычисляет независимую оценку их качества. Проверка контрольной суммы не подтверждает производительность или корректность модели.
