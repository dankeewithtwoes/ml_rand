# Маршрутизация между узлами инференса

Flask-сервисы предоставляют общий endpoint для нескольких узлов. Оркестратор проверяет здоровье, использует round-robin или нагрузку с весами и учитывает cooldown после ошибок. При сетевом сбое или HTTP 5xx он пробует другой доступный узел. HTTP 4xx передаётся клиенту без повторного запроса.

## Запуск

Из этой папки, при работающем Ollama:

```bash
pip install -r requirements.txt
python node.py --name node-1 --port 9001 --model-url http://localhost:11434/v1
```

Укажите адреса запущенных узлов в `nodes.yaml`. В других терминалах:

```bash
python orchestrator.py --nodes nodes.yaml --port 9090 --policy least-load
python client.py --url http://localhost:9090 --prompt "Explain quantization."
python benchmark_cluster.py
```

## Ограничения

Имя модели и параметры генерации передаются выбранному серверу. Потоковые ответы пока не поддерживаются. Проверки HTTP-связок используют локальный тестовый сервер; запуск физического кластера с моделями требует отдельной проверки. Названия Jetson/Raspberry Pi не подтверждают запуск на таком оборудовании. Бенчмарк считает запросы в секунду, а не tokens/sec.
