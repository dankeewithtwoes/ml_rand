# Changelog

All notable changes to this portfolio are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-07-17

First release-candidate state: ten flagship projects polished to resume grade.

### Added

- Flagship polish wave for 10 projects (01, 03, 07, 10, 11, 14, 17, 18, 20, 21):
  - resume-grade READMEs: problem, architecture, one-command offline quickstart,
    verified results with environment metadata, threat model, honest limitations;
  - expanded behavioral tests: happy path plus at least three failure modes per
    distinctive feature (113 new tests across the ten projects);
  - committed demo artifacts captured from real offline runs (`examples/`, `demo/`, `docs/`);
  - light dependencies pinned to verified versions; heavy integrations documented
    as optional with lower bounds.
- GitHub Actions `quality-gate` workflow: root gate for all 21 projects plus
  flagship behavioral tests on every push (`.github/workflows/ci.yml`).
- Issue templates for bug reports and feature requests.

### Fixed

- 01_pytorch_classifier_demo: seeded shuffle before the train/validation split
  (the split previously leaked a single class into validation); `evaluate.py` now
  loads the Hydra config via OmegaConf instead of crashing on attribute access.
- 14_local_model_router: added the missing `argparse` import that crashed
  `benchmark_router.py`; benchmark reports are written as UTF-8.
- 18_local_ai_observability: added the missing `argparse` import that crashed
  `benchmark_guardrails.py`.

### Changed

- README claims across the ten flagships now match reproducible local runs only;
  invented metrics and non-runnable commands were removed or marked
  "not run here, requires X".
