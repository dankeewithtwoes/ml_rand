# Локальное хранилище заметок

`KnowledgeStore` хранит заметки и метаданные в SQLite. При наличии Chroma подключается векторный поиск; без неё остаётся поиск по тексту. Есть экспорт JSON и удаление записей. `ask.py` добавляет ответ Ollama поверх найденного контекста.

## Запуск

Демонстрация добавления, поиска, экспорта и удаления, из этой папки:

```bash
python examples/demo_lifecycle.py
python -m unittest test_knowledge_store -v
```

CLI для заметок и ответов:

```bash
pip install -r requirements.txt
python ingest.py --note "Meeting with Artem: router deadline is Friday" --tags work,meetings
python ask.py "when is the router deadline"
python compress_memory.py --days 30
python benchmark_recall.py
```

## Хранение и ограничения

Пример вывода: [demo_lifecycle_output.txt](examples/demo_lifecycle_output.txt). Записи и индексы хранятся локально. SQLite не шифруется; удаление строки не гарантирует стирание резервных копий или свободных страниц файла. Ошибки Chroma требуют отдельной проверки согласованности индекса с SQLite.

Тесты хранилища не подтверждают качество ответов LLM. Для слоя генерации нужен работающий Ollama; отправляемый контекст определяется настройкой endpoint.
