# Классификация текста с LoRA

Обучение LoRA-адаптера для DistilBERT через Hugging Face Transformers и PEFT. Примеры из `data.jsonl` оформляются как инструкция и входной текст, но задача модели — классификация, а не генерация ответа. Скрипты оценки рассчитывают accuracy, F1 и classification report. `data_audit.py` проверяет дубликаты и пересечение выборок.

## Запуск

Команды выполняются из этой папки:

```bash
pip install -r requirements.txt
python finetune.py --epochs 10 --lora-rank 8
python evaluate.py --model-dir demo/model/model
python infer.py --text "This product completely exceeded my expectations!"
```

## Данные

Небольшой комплект примеров нужен для проверки обучения. Долю обучаемых параметров выводит `print_trainable_parameters()`. Метрики зависят от данных и запуска; фиксированных значений accuracy и F1 здесь не заявлено. Для оценки на своих данных нужна отдельная репрезентативная тестовая выборка.
