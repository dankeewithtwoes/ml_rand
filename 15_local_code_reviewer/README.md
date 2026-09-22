# 15 — Local Secure Code Reviewer

> **Уникальный угол**: code-review агент, который **не отправляет исходники в облако**: ищет баги, уязвимости, антипаттерны и генерирует отчёт локально.

## Что демонстрирует

- Анализ git diff и полных файлов.
- Поиск уязвимостей (SQL-injection, path traversal, eval, hardcoded secrets).
- Оценку рисков и explanation.
- Сравнение с semgrep/bandit.
- JSON-отчёт для CI.

## Почему это отличается от туториала

| Обычный туториал | Этот проект |
|------------------|-------------|
| Пример LLM-запроса | Полный local-only review pipeline |
| Нет бенчмарка | precision/recall vs статическими анализаторами |
| Ручная проверка | CI-ready JSON-отчёт |

## Запуск

```bash
pip install -r requirements.txt

# Проверить diff
python review.py --diff HEAD~1

# Проверить файл
python review.py --file app.py

# Сравнить с semgrep
python benchmark_vs_static.py --target src/
```

## Ожидаемый результат

```
[review] 3 issues found
  HIGH: possible SQL injection in login() at line 42
  MED: hardcoded API key at line 18
[benchmark] precision=0.84 recall=0.71 vs semgrep
```
