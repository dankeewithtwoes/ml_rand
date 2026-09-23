# 09 — ComfyUI Batch Grid

The script sends prompt variations to ComfyUI, assembles the outputs into a grid, and records generation settings in JSON.

## Возможности

- Вызов ComfyUI API из Python.
- Параметрические вариации prompt.
- Сборка grid и метаданных JSON.

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

