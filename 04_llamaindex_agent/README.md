# 04 — Stateful Router Agent (LlamaIndex)

The agent keeps chat context, selects a tool for each request, and falls back to search when no tool matches.

## Возможности

- **ReAct agent** с несколькими function tools.
- **ChatMemoryBuffer** для многоходовых диалогов.
- **Router**: LLM сам выбирает между company_docs, inventory, calculator, fallback.
- **Graceful degradation**: нет подходящего инструмента → живой поиск или явная ошибка провайдера.

## Запуск

```bash
pip install -r requirements.txt
cp .env.example .env  # или оставьте пустым для Ollama

# Один вопрос
python agent.py "What is the total value of inventory?"

# Интерактив
python agent.py --interactive
```

## Примеры многоходовых вопросов

```
You: What products do we sell?
You: How many Widget Pro are in stock?
You: What is the total inventory value?
You: What is the weather today?   # → fallback
```

## Структура

```
04_llamaindex_agent/
├── documents/company.txt
├── agent.py              # stateful router agent
└── README.md
```

## Реальный внешний поиск

Fallback-инструмент выполняет живой keyless-запрос к DuckDuckGo Instant
Answer и возвращает URL, фрагменты ответа и блок `provenance` с провайдером,
адресом запроса и UTC-временем получения. API-ключ не нужен. Это
instant-answer API, а не полный индекс поисковой выдачи: если сеть недоступна
или провайдер не нашёл содержательного результата, инструмент возвращает
явный `WEB_SEARCH_ERROR` и не придумывает ответ.

Проверка без обращения к сети (HTTP-ответы подменяются в тестах):

```bash
python -m unittest test_web_search.py -v
```

