# 08 — Dify Workflow-as-Code

The CLI calls the Dify Chatbot and Workflow APIs; workflow JSON can be versioned and reviewed in Git.

## Возможности

- Чат с Dify Chatbot API.
- Запуск Workflow app с параметрами.
- Экспорт/импорт workflow DSL для версионирования.

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

