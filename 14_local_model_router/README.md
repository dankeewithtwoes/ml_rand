# Маршрутизация запросов между моделями

Реестр хранит тип модели, URL, стоимость, задержку и подходящие задачи. `decision.py` применяет ограничения приватности, бюджета и задержки, выбирает модель и возвращает причины отклонения остальных вариантов. `route.py` определяет тип запроса по ключевым словам и может вызвать выбранный endpoint.

## Проверка выбора

Из этой папки:

```bash
python route.py --prompt "Rotate my database password and restart the service" --registry examples/registry.json
python benchmark_router.py --registry examples/registry.json --output examples/router_benchmark.json
python -m unittest test_decision -v
```

Регистрация модели:

```bash
python register_model.py --name mistral-7b --type local --url http://localhost:11434/v1 --latency 500 --strengths general,fast --registry examples/registry.json
```

Для сетевых вызовов установите `requirements.txt` и запустите соответствующий сервер модели.

## Ограничения

Причины выбора и данные проверки находятся в [router_benchmark.json](examples/router_benchmark.json). Классификатор использует английские ключевые слова; русские запросы могут попадать в `general`. Комплект из четырёх размеченных запросов слишком мал для оценки качества классификации.

Стоимость и задержки в реестре задаются вручную. Ограничение приватности опирается на правильно указанный тип `local`; ошибочно зарегистрированный облачный URL оно не обнаружит. Детектор чувствительных слов — эвристика. Локальные тесты не проверяют реальные задержки endpoint и качество ответов.
