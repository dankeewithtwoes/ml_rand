# 19 — Local Edge AI Fleet

> **Уникальный угол**: распределённый inference на нескольких локальных/edge-устройствах с load balancing и failover, а не один мощный сервер.

## Что демонстрирует

- Регистрацию edge-нод (ПК, Jetson, Raspberry Pi).
- Health-check и выбор ноды по загрузке.
- Распределение запросов (round-robin / least-load).
- Failover при падении ноды.
- Метрики кластера.

## Почему это отличается от туториала

| Обычный туториал | Этот проект |
|------------------|-------------|
| Один инстанс | Кластер edge-устройств |
| Ручное переключение | Авто-failover |
| Нет мониторинга | device utilization, cluster throughput |

## Запуск

```bash
pip install -r requirements.txt

# Запустить ноду
python node.py --name jetson-1 --port 9001 --model http://localhost:11434

# Запустить оркестратор
python orchestrator.py --nodes nodes.yaml --port 9090

# Отправить запрос в кластер
python client.py --url http://localhost:9090 --prompt "Explain quantization."

# Бенчмарк failover
python benchmark_cluster.py
```

## Ожидаемый результат

```
[orchestrator] 3 nodes registered
[route] -> jetson-2 (load=0.3)
[failover] jetson-1 down, switched to jetson-3 in 0.4s
[benchmark] cluster throughput: 28 tok/s
```
