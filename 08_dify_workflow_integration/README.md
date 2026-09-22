# 08 — Dify Workflow-as-Code

> **Уникальный угол**: интеграция с Dify не через клики, а через **CLI + версионирование workflow JSON** в Git.

## Что демонстрирует

- Чат с Dify Chatbot API.
- Запуск Workflow app с параметрами.
- Экспорт/импорт workflow DSL для версионирования.

## Почему это отличается от туториала

| Обычный туториал | Этот проект |
|------------------|-------------|
| UI-конфигурация | CLI + код |
| Workflow живёт только в Dify | Workflow версионируется в Git |
| Нет интеграции с CI | JSON-экспорт пригоден для code review |

## Запуск

```bash
pip install -r requirements.txt

# Chat
python chat.py --base-url http://localhost/v1 --api-key $DIFY_API_KEY \
  --query "Summarize the report."

# Workflow run
python workflow.py --base-url http://localhost/v1 --api-key $DIFY_API_KEY \
  --input topic=AI --input tone=professional

# Export workflow для Git
python export_workflow.py --base-url http://localhost/v1 --api-key $DIFY_API_KEY \
  --output workflow_api.json

# Import workflow
python export_workflow.py --base-url http://localhost/v1 --api-key $DIFY_API_KEY \
  --import-file workflow_api.json
```

## Ожидаемый результат

```
{
  "answer": "...",
  "workflow_run_id": "..."
}
```
