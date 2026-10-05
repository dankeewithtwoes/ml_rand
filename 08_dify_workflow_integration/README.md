# Вызов Dify из Python

CLI обращается к Chatbot и Workflow API Dify. Скрипт export_workflow.py содержит команды экспорта и импорта; workflow_contract.py сравнивает входные поля и формирует отпечаток конфигурации с маскированием выбранных данных.

## Запуск

Команды выполняются из этой папки.

```bash
pip install -r requirements.txt
python chat.py --base-url http://localhost/v1 --api-key $DIFY_API_KEY \
  --query "Summarize the report."
python workflow.py --base-url http://localhost/v1 --api-key $DIFY_API_KEY \
  --input topic=AI --input tone=professional
python export_workflow.py --base-url http://localhost/v1 --api-key $DIFY_API_KEY \
  --output workflow_api.json
python export_workflow.py --base-url http://localhost/v1 --api-key $DIFY_API_KEY \
  --import-file workflow_api.json
```

## Ограничения

Нужны запущенный Dify и ключ приложения. Доступность маршрутов экспорта и импорта зависит от версии сервера. Локальная проверка контракта не проверяет выполнение workflow на сервере.
