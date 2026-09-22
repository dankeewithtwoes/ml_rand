# 09 — ComfyUI Batch Grid

> **Уникальный угол**: не ручная генерация в UI, а **пакетная генерация с вариациями prompt и автоматическая сборка grid-изображения**.

## Что демонстрирует

- Вызов ComfyUI API из Python.
- Параметрические вариации prompt.
- Сборка grid и метаданных JSON.

## Почему это отличается от туториала

| Обычный туториал | Этот проект |
|------------------|-------------|
| Одна картинка вручную | Batch + grid |
| Параметры в UI | Параметры в CLI/коде |
| Нет метаданных | JSON с prompt и путями |

## Запуск

```bash
pip install -r requirements.txt

# Убедитесь, что ComfyUI запущен (по умолчанию http://127.0.0.1:8188)

# Одна генерация
python generate.py --prompt "a robot reading a book, digital art" \
  --server http://127.0.0.1:8188 --output-dir outputs

# Batch grid
python batch_grid.py --server http://127.0.0.1:8188 --output-dir outputs --grid outputs/grid.jpg
```

## Ожидаемый результат

```
Saved outputs/ComfyUI_00001_.png
Saved outputs/ComfyUI_00002_.png
...
Grid saved outputs/grid.jpg
```
