# Генерация QA-датасетов

Генератор получает пары вопрос–ответ от локальной LLM, проверяет формат и удаляет точные дубликаты. JSONL публикуется только после получения указанного числа записей; при ошибке прежний файл сохраняется. Отдельные модули проверяют данные и запускают TF-IDF-классификатор на размеченной выборке.

## Запуск

Команды выполняются из этой папки.

```bash
pip install -r requirements.txt
python generate_qa.py --schema schemas/customer_support.yaml --count 200
python validate_dataset.py --input data/synthetic.jsonl
python benchmark_downstream.py --train data/synthetic.jsonl --test data/real.jsonl
```

```bash
python -m unittest test_generate_qa.py -v
```

## Ограничения

Нужен работающий Ollama. Формат и отсутствие точных дубликатов не гарантируют достоверность ответов. Для downstream-оценки нужны метки label в train/test данных и независимая тестовая выборка.
