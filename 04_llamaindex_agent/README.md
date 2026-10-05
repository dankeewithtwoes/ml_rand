# Агент на LlamaIndex

ReAct-агент выбирает инструмент для документов компании, склада, арифметики или поиска. Контекст диалога хранится в ChatMemoryBuffer. Арифметика выполняется через ограниченный AST-интерпретатор.

## Запуск

Команды выполняются из этой папки.

```bash
pip install -r requirements.txt
cp .env.example .env
python agent.py "What is the total value of inventory?"
python agent.py --interactive
```

```bash
python -m unittest test_web_search.py -v
```

## Ограничения

Поиск использует DuckDuckGo Instant Answer, а не полный поисковый индекс. Он возвращает источники и время запроса; ошибки сети и отсутствие результата обозначаются явно. HTTP-контракт проверяется с подменёнными ответами. Работа самого агента требует доступного LLM endpoint.
