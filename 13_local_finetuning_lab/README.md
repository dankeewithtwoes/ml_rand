# Обучение LoRA-адаптера

Подготовка JSONL, разбиение данных, обучение адаптера и оценка на отложенной выборке. Дубликаты проверяются по содержимому, без служебных полей вроде ID. Обучение и оценка используют одинаковый формат instruction/input/output.

## Запуск

Из этой папки:

```bash
pip install -r requirements.txt
python prepare_data.py --input data/my_prompts.jsonl --output data/train.jsonl
python lab.py --data data/train.jsonl --base-model Qwen/Qwen2.5-1.5B-Instruct --output-dir outputs/lora
python eval.py --adapter outputs/lora --val-data data/train_val.jsonl
python merge_and_quant.py --adapter outputs/lora
```

Для перебора rank/learning rate добавьте `--auto-tune` к `lab.py`. Веса каждого кандидата сохраняются отдельно, лучший адаптер копируется в `--output-dir`. Данные должны содержать непустые строки `instruction` и `output`; `input` необязателен. Нужны отдельные train и validation без пересечения.

## Проверка и ограничения

Проверены обучение на CPU, сохранение и повторная загрузка небольшого локального Qwen2-адаптера, loss и perplexity на отложенных примерах. Использовалась случайно инициализированная модель для проверки кода, поэтому эти числа не оценивают качество предобученного Qwen.

`eval.py` считает средний loss с весом по числу токенов и perplexity; это не оценка полезности ответа человеком. При отсутствии зависимостей, данных или весов скрипты завершаются с ошибкой. `merge_and_quant.py` сохраняет объединённые веса Hugging Face; перевод в GGUF и квантование выполняются отдельно инструментами llama.cpp.
