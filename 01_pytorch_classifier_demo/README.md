# PyTorch Classifier with Calibration Reporting

A reproducible two-moons classifier training harness whose real subject is not accuracy but **confidence quality**: a calibration report (Brier score + expected calibration error) that tells you when a model is confidently wrong.

## Problem — why it matters

A classifier that reports 99% accuracy can still be dangerous if its probabilities are meaningless. In any downstream system that thresholds, routes, or abstains on confidence — fraud queues, medical triage, agent tool-use — an overconfident wrong prediction is worse than no prediction, because it suppresses human review exactly where review is needed.

Accuracy alone cannot detect this. A model can be 99% accurate and still assign 0.99 probability to the wrong class on the 1% it misses. Calibration metrics (Brier score, expected calibration error over confidence bins) measure the gap between *how sure the model says it is* and *how often it is actually right*, which is the number a reliability-minded engineer needs before shipping a threshold.

## What it does

- **Distinctive capability:** `src/reliability.py` — a dependency-free (stdlib-only) calibration report for binary classifiers. Given predicted probabilities and true labels it returns the Brier score, the expected calibration error (ECE), and per-bin confidence/accuracy buckets. It validates its input loudly (empty input, length mismatch, out-of-range probabilities, non-binary labels, non-positive bin counts are all rejected) instead of producing a silently misleading number.
- **Main pipeline:** config-driven PyTorch training on a synthetic two-moons dataset with seeded reproducibility, a held-out stratified validation split, per-epoch metrics, decision-boundary plots, classification reports, one-off inference, and optional ONNX export / MLflow tracking.

## Architecture

Stack: Python 3.12, PyTorch (CPU is enough), Hydra/OmegaConf for config, scikit-learn for reporting, matplotlib for plots. Optional: MLflow, ONNX.

```text
configs/config.yaml ──► train.py ──► src/data.py   make_moons → seeded shuffle → stratified split
                       │           src/model.py   TwoLayerNet (2 → 16 → 2, ReLU)
                       │           src/utils.py   set_seed (random/numpy/torch)
                       ▼
              demo/model.pt + decision_boundary.png
                       │
                       ▼
   evaluate.py / infer.py / examples/run_calibration_demo.py
                       │
                       ▼
        src/reliability.py  calibration_report(probabilities, labels)
                       │
                       ▼
        examples/calibration_report.json  (Brier, ECE, per-bin buckets)
```

Key modules:

| File | Role |
|---|---|
| `src/reliability.py` | Calibration report — the tested core. Pure stdlib, no torch needed. |
| `src/data.py` | Two-moons generator; shuffles with the run seed *before* splitting (an ordered split would put a single class in validation — see Limitations). |
| `src/model.py` | `TwoLayerNet`: two linear layers with ReLU. |
| `train.py` | Hydra entry point; trains, checkpoints, plots, logs to MLflow if installed. |
| `evaluate.py` / `infer.py` | Classification report on the validation split / single-point inference. |
| `examples/run_calibration_demo.py` | Offline demo below. |

## Quickstart

One-command demo, zero dependencies beyond the Python standard library — it exercises the calibration report on synthetic edge cases:

```bash
python examples/run_calibration_demo.py
```

Full pipeline (installs pinned light deps plus the CPU PyTorch wheel):

```bash
pip install -r requirements.txt
python train.py                                                    # 50 epochs, seed 42
python examples/run_calibration_demo.py --model demo/model.pt      # calibration of the trained model
python evaluate.py                                                 # sklearn classification report
python infer.py --input "0.5,-0.3"                                 # one-off inference
```

Hydra overrides work as usual, e.g. `python train.py training.epochs=100 training.lr=0.005`.

## Verified results

Everything below was run on this machine — no invented numbers:

- **Environment:** Windows 11 (10.0.26200), AMD64, Intel64 Family 6 Model 186, Python 3.12.6, torch 2.10.0+cpu, **CPU-only, no GPU**.
- **Training** (`python train.py`, default config): final validation accuracy **0.9925**, best **0.9950** over 50 epochs (~seconds on CPU).
- **Calibration of the trained model** (`python examples/run_calibration_demo.py --model demo/model.pt`, 400 validation samples, 10 bins): **Brier 0.005497, ECE 0.011445, val_acc 0.9925** — well calibrated on this easy synthetic task.
- **The failure this project exists to detect:** on confidently-wrong synthetic predictions the same report returns **Brier 0.856250, ECE 0.925000**; on perfect predictions, exactly **0.0 / 0.0**.
- **Evaluation** (`python evaluate.py`): 0.99 accuracy, 214/186 class support on the stratified validation split.

Raw artifacts from these exact runs are committed:

- [`examples/calibration_report.json`](examples/calibration_report.json) — machine-readable report with environment metadata embedded;
- [`examples/demo_terminal_output.txt`](examples/demo_terminal_output.txt) — terminal log of the full run;
- [`examples/demo_terminal_output_stdlib.txt`](examples/demo_terminal_output_stdlib.txt) — terminal log of the zero-dependency quickstart run.

Not run here (marked honestly rather than implied): ONNX export (`onnx` not installed in this environment) and MLflow UI (`mlflow` not installed; `train.py` auto-skips tracking when it is absent).

## Tests

```bash
python -m unittest discover -s tests -v
```

13 tests, all passing on the environment above. Coverage of the calibration report:

- **Happy path:** perfect predictions score exactly 0; hand-computed Brier/ECE on small cases; exact per-bin counts, confidences, and accuracies; single-sample input.
- **Edge cases:** a probability of exactly `1.0` lands in the last (half-open) bin instead of vanishing; empty bins are skipped.
- **Failure modes (all rejected with `ValueError`):** empty input, mismatched lengths, probability > 1, probability < 0, non-binary labels, `bins=0`.

The portfolio-level proof test `test_01_calibration_perfect_predictions` lives in the root `tests/` suite and is exercised by `python quality_gate.py`.

## Threat model & data handling

- **Fully local and offline:** the dataset is synthetic (generated in-process); no data is downloaded, uploaded, or sent to any API.
- **No secrets, no PII:** inputs are 2-D Gaussian-noise moons and probability lists; there is nothing sensitive to leak.
- **What it does NOT do:** no network calls, no file writes outside the project directory, no execution of external code, no persistence of anything beyond run artifacts (`demo/`, `examples/`, Hydra `outputs/`).
- **Trust boundary:** checkpoints are loaded with `weights_only=True`; still, only load `demo/model.pt` files you produced or reviewed — a `.pt` file is a pickle container.
- **MLflow/ONNX are opt-in integrations**, not part of the tested core; enabling MLflow writes tracking files under the configured local directory only.

## Limitations

- Binary classification only; the calibration report is not a multiclass or regression metric.
- ECE is bin-sensitive: with few samples per bin it is noisy (the 400-sample validation run above is near the practical floor for 10 bins).
- Two-moons is a toy task. The pipeline demonstrates *method* (seeded splits, calibration gates), not state-of-the-art accuracy on real data.
- An earlier version of `src/data.py` split without shuffling, which put a single class in validation and made accuracy/calibration numbers meaningless; the split is now seeded-shuffled, but the lesson stands — verify your split before trusting your metrics.
- `train.py` checkpoints the final epoch to `demo/model.pt`; the best-epoch checkpoint goes to Hydra's `outputs/` run directory. On a diverging run those can differ.

## Tested core vs. integrations

Per the portfolio positioning: the **tested core** is `src/reliability.py` plus the training/evaluation pipeline verified above on CPU. **External integrations** (MLflow tracking, ONNX export) are optional layers that were not exercised in this environment and are not claimed as tested.
