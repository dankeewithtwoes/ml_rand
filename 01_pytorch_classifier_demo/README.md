# Классификатор на PyTorch

Двухслойная сеть классифицирует точки синтетического датасета two-moons. Конфигурация задаётся через Hydra; обучение сохраняет веса, метрики и график границы решений. В `src/reliability.py` отдельно рассчитываются Brier score, ECE и точность по интервалам уверенности.

## Запуск

Из этой папки, после установки зависимостей:

```bash
pip install -r requirements.txt
python train.py
python evaluate.py
python infer.py --input "0.5,-0.3"
python examples/run_calibration_demo.py --model demo/model.pt
```

Для проверки калибровки без PyTorch:

```bash
python examples/run_calibration_demo.py
python -m unittest discover -s tests -v
```

## Результаты и ограничения

В сохранённом CPU-запуске точность на валидации составила 0.9925, Brier score — 0.005497, ECE — 0.011445. Конфигурация и вывод находятся в [отчёте](examples/calibration_report.json) и [логе](examples/demo_terminal_output.txt). Это результат на синтетических данных, его нельзя переносить на прикладные задачи.

Метрики калибровки рассчитаны для бинарной классификации; ECE зависит от числа интервалов. `demo/model.pt` содержит последнюю эпоху, лучший checkpoint сохраняется в каталоге Hydra. MLflow и ONNX — отдельные интеграции, не проверенные в сохранённом запуске. Загружайте только доверенные веса.
