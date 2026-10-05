# Подготовка данных и эксперименты с LoRA

prepare_data.py готовит JSONL, data_quality.py проверяет разбиение и дубликаты, lab.py содержит обучение и перебор LoRA rank/learning rate. merge_and_quant.py объединяет адаптер с базовой моделью.

## Запуск

Команды выполняются из этой папки.

```bash
pip install -r requirements.txt
python prepare_data.py --input data/my_prompts.jsonl --output data/train.jsonl
python lab.py --data data/train.jsonl --base-model Qwen/Qwen2.5-1.5B-Instruct --auto-tune
```

## Ограничения

Это незавершённый прототип. В опубликованном eval.py perplexity пока остаётся null: скрипт не рассчитывает качество адаптера. merge_and_quant.py сохраняет объединённую модель и печатает инструкции для llama.cpp; GGUF автоматически не создаётся. Команды ниже описывают интерфейс скриптов, а не подтверждённый сквозной запуск.
