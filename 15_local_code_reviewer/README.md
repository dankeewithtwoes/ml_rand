# 15 — Local Secure Code Reviewer

The tool scans files and git diffs, checks for selected issue classes, and writes a JSON report for CI.

## Возможности

- Анализ git diff и полных файлов.
- Поиск уязвимостей (SQL-injection, path traversal, eval, hardcoded secrets).
- Оценку рисков и explanation.
- Сравнение с semgrep/bandit.
- JSON-отчёт для CI.

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

