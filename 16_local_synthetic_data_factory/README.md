# 16 — Local Synthetic Data Factory

The tool generates records from a schema, checks field coverage and duplicates, and exports JSONL or CSV.

## Возможности

- Задание схемы данных (persona, scenario, QA, JSON).
- Генерацию через локальную LLM.
- Проверку покрытия схемы и дедупликацию.
- Оценку качества через downstream задачу.
- Экспорт в JSONL/CSV.

## Запуск

```bash
pip install -r requirements.txt

# Сгенерировать QA-датасет
python generate_qa.py --schema schemas/customer_support.yaml --count 200

# Проверить качество
python validate_dataset.py --input data/synthetic.jsonl

# Оценить downstream-accuracy
python benchmark_downstream.py --train data/synthetic.jsonl --test data/real.jsonl
```

Генератор работает fail-closed: он принимает только непустые пары
`Q: ... A: ...`, удаляет точные дубликаты и публикует JSONL атомарно лишь
после получения ровно `--count` валидных уникальных строк. Недоступный Ollama,
отсутствующий SDK, пустой или плохо отформатированный ответ завершают CLI с
кодом 2. Пустой/частичный датасет и строки `[skip]` не записываются; уже
существующий output при неудаче остаётся без изменений.

```bash
python -m unittest test_generate_qa.py -v
```

## Ожидаемый результат

```
[generate] 200 samples in 14s
[validate] schema coverage=0.96 diversity=0.82
[benchmark] downstream accuracy=0.79
```

