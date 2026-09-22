# 02 — Parameter-Efficient Instruction Tuning (LoRA)

> **Уникальный угол**: fine-tuning не всей модели, а только LoRA-адаптеров в instruction-формате. Показывает, как адаптировать большую модель под узкий домен, экономя память и время.

## Что демонстрирует

- **PEFT / LoRA** для `AutoModelForSequenceClassification`.
- **Instruction format** (`### Instruction`, `### Input`, `### Response`).
- Оценку через **accuracy / F1 / classification report**.
- Сравнение обучаемых параметров (`model.print_trainable_parameters()`).

## Почему это отличается от туториала

| Обычный туториал | Этот проект |
|------------------|-------------|
| Full fine-tuning на sentiment | LoRA adapter, обучается <1% параметров |
| CSV без формата | JSONL в instruction-формате |
| Только accuracy | accuracy + F1 + classification report |

## Запуск

```bash
pip install -r requirements.txt

# Обучение LoRA-адаптера
python finetune.py --epochs 10 --lora-rank 8

# Оценка
python evaluate.py --model-dir demo/model/model

# Инференс
python infer.py --text "This product completely exceeded my expectations!"
```

## Ожидаемый результат

- Обучается только ~0.6% параметров модели.
- На 10 примерах accuracy/F1 ~0.8–1.0 (зависит от сходимости).
- Для production качества замените `data.jsonl` на полноценный доменный датасет.

## Структура

```
02_huggingface_finetune_demo/
├── data.jsonl              # instruction-формат
├── finetune.py             # LoRA fine-tuning
├── evaluate.py             # оценка
├── infer.py                # инференс
└── demo/model/             # сохранённый адаптер
```
