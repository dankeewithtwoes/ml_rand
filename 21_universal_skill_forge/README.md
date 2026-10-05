# Инструменты для LLM-агентов

Skill Forge загружает Python-инструменты из локального каталога. Пакет содержит `manifest.json`, `schema.json`, `handler.py` и необязательные примеры `examples.json`. CLI проверяет манифест и входные данные, запускает примеры и возвращает JSON.

`portability.py` проверяет имена инструментов и подмножество JSON Schema для Ollama и OpenAI-совместимого формата. `runtime.py` подключает их к endpoint модели.

## Запуск

Из этой папки:

```bash
pip install -r requirements.txt
python skillforge.py doctor
python skillforge.py test skills/calculator
python skillforge.py run skills/calculator --input '{"expression":"2 + 3 * 4"}'
python demo_portability.py
python -m unittest discover -s tests -v
```

Создание нового пакета:

```bash
python skillforge.py create summarize --skills-dir skills
python skillforge.py test skills/summarize
```

Погодный инструмент обращается к Open-Meteo без API-ключа:

```bash
python skillforge.py run skills/weather --input '{"city":"Волгоград","language":"ru"}'
```

Он использует [геокодирование](https://open-meteo.com/en/docs/geocoding-api) и [прогноз погоды](https://open-meteo.com/en/docs), возвращая адреса запросов и время получения данных.

## Ограничения

Пример проверки двух пакетов для двух провайдеров: [portability_report.json](examples/portability_report.json). Совместимая схема не гарантирует правильного вызова конкретной моделью — это проверяется отдельно через `benchmark_portability.py`.

Обработчики — доверенный Python-код, выполняемый в процессе приложения. Проверка схемы не изолирует их и не ограничивает ресурсы. Примеры сравниваются по точному равенству. Погодный инструмент передаёт имя города Open-Meteo и зависит от доступности сервиса; первое совпадение геокодирования может быть неоднозначным. Адаптеры поддерживают только OpenAI-совместимый формат.
