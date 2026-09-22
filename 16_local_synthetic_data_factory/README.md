# 16 — Local Synthetic Data Factory

> **Уникальный угол**: генерация синтетических датасетов **полностью локально** по схеме, с контролем diversity и coverage, без утечки данных в API.

## Что демонстрирует

- Задание схемы данных (persona, scenario, QA, JSON).
- Генерацию через локальную LLM.
- Проверку покрытия схемы и дедупликацию.
- Оценку качества через downstream задачу.
- Экспорт в JSONL/CSV.

## Почему это отличается от туториала

| Обычный туториал | Этот проект |
|------------------|-------------|
| Пара примеров | Фабрика с контролем качества |
| Нет метрик | schema coverage, diversity, downstream accuracy |
| Ручная генерация | CLI pipeline |

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
