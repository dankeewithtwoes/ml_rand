# Извлечение полей из документов

Парсер читает текст и PDF, извлекает поля правилами или через LLM и сохраняет JSON. Для сканированных страниц используется OCR. `evidence.py` сопоставляет извлечённые поля с фрагментами исходного текста и их смещениями.

## Запуск

Текстовый пример без модели, из этой папки:

```bash
python parse.py --input examples/sample_invoice.txt --output examples/demo_output.json --no-llm
```

PDF, сканы и пакетная обработка:

```bash
pip install -r requirements.txt
python parse.py --input invoice.pdf --output invoice.json --no-llm
python parse.py --input scan.pdf --output scan.json --no-llm --ocr-language rus+eng
python batch_parse.py --input-dir docs/ --output-dir parsed/ --no-llm
```

Для LLM-извлечения уберите `--no-llm` и настройте endpoint. Для OCR нужны Tesseract и языковые пакеты.

```bash
python -m unittest discover -p "test*.py" -v
```

## Ограничения

Вывод текстового примера находится в [demo_output.json](examples/demo_output.json). Правила рассчитаны на ограниченный набор форматов; переносы, таблицы и OCR-ошибки могут мешать извлечению. Совпадение цитаты с исходником подтверждает её наличие, а не правильность всего поля. Незнакомые макеты требуют отдельной оценки на размеченных документах. LLM-путь передаёт текст на настроенный endpoint и не покрывается проверкой режима `--no-llm`.
