# Генерация изображений через ComfyUI

Python-клиент отправляет workflow в ComfyUI, получает изображения и собирает сетку вариантов. provenance.py записывает хеши workflow и выходных файлов для сопоставления запуска с результатом.

## Запуск

Команды выполняются из этой папки.

```bash
pip install -r requirements.txt
python generate.py --prompt "a robot reading a book, digital art" \
  --server http://127.0.0.1:8188 --output-dir outputs
python batch_grid.py --server http://127.0.0.1:8188 --output-dir outputs --grid outputs/grid.jpg
```

## Ограничения

Нужны работающий ComfyUI, веса и узлы из workflow_api.json. Хеши подтверждают совпадение файлов, но не качество изображений. Время генерации зависит от оборудования и workflow.
