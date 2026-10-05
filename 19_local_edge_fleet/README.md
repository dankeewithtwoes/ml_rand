# Маршрутизация между узлами инференса

FastAPI-сервисы описывают узлы и оркестратор запросов. scheduler.py учитывает нагрузку и cooldown после сбоя; клиент обращается к общему endpoint. benchmark_cluster.py измеряет статусы, задержки и успешные запросы в секунду.

## Запуск

Команды выполняются из этой папки.

```bash
pip install -r requirements.txt
python node.py --name jetson-1 --port 9001 --model http://localhost:11434
python orchestrator.py --nodes nodes.yaml --port 9090
python client.py --url http://localhost:9090 --prompt "Explain quantization."
python benchmark_cluster.py
```

## Ограничения

Нужны доступные узлы, корректный nodes.yaml и серверы моделей. Названия Jetson/Raspberry Pi в примерах не подтверждают запуск на таком оборудовании. Тесты планировщика не проверяют физический кластер; benchmark_cluster.py не измеряет tokens/sec.
