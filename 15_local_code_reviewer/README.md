# Проверка кода локальной моделью

review.py анализирует файл или git diff и формирует список замечаний через локальный LLM endpoint. reporting.py создаёт JSON/SARIF для последующей обработки.

## Запуск

Команды выполняются из этой папки.

```bash
pip install -r requirements.txt
python review.py --diff HEAD~1
python review.py --file app.py
```

## Ограничения

Замечания модели требуют проверки. benchmark_vs_static.py использует небольшие синтетические примеры; полноценного сравнения с Semgrep/Bandit в нём нет. Показатели precision и recall без отдельного запуска не заявлены. Код передаётся на настроенный endpoint.
