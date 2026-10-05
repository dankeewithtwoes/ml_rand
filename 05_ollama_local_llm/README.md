# Сравнение моделей в Ollama

Скрипты сравнивают модели на одинаковом промпте: задержка ответа, число токенов, скорость генерации и необязательная оценка моделью-судьёй. Результаты сохраняются в demo/arena_results.json.

## Запуск

Команды выполняются из этой папки.

```bash
pip install -r requirements.txt
python pull_model.py --model llama3.1
python pull_model.py --model phi3
python arena.py --models llama3.1,phi3 --prompt "Explain RAG."
python arena.py --models llama3.1,phi3 --prompt "Explain RAG." --judge llama3.1
python chat.py --interactive
```

## Ограничения

Нужны работающий Ollama и загруженные модели. Скорость зависит от оборудования и параметров запроса. Оценка моделью-судьёй не заменяет размеченную тестовую выборку; приведённые команды не задают ожидаемых численных результатов.
