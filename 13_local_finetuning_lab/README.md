# 13 — Local Fine-tuning Lab

The pipeline covers data preparation, LoRA training, evaluation, GGUF export, and local inference.

## Возможности

- Загрузку и валидацию собственных данных.
- Авто-подбор LoRA rank/learning rate.
- Обучение с валидацией и логированием.
- Merge adapter + квантование GGUF.
- Локальный деплой через llama.cpp.

## Запуск

```bash
pip install -r requirements.txt

# Подготовить данные
python prepare_data.py --input data/my_prompts.jsonl --output data/train.jsonl

# Запустить лабораторию
python lab.py --data data/train.jsonl --base-model Qwen/Qwen2.5-1.5B-Instruct --auto-tune

# Оценить и смержить
python eval.py --adapter outputs/lora
python merge_and_quant.py --adapter outputs/lora --quant q4_k_m

# Бенчмарк ресурсов
python benchmark_training.py
```

## Ожидаемый результат

```
[lab] best lr=2e-4 rank=32
[lab] val_loss=0.87 perplexity=2.39 peak_vram=6.2GB
[quant] saved outputs/merged-q4_k_m.gguf
```

