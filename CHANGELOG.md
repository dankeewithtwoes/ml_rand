# Changelog

## 1.0.0 — 2026-07-17

### Added

- Offline behavior checks for the portfolio projects.
- GitHub Actions workflow for the root quality gate and selected project tests.
- Issue templates for bug reports and feature requests.
- Demo outputs and setup notes for the featured projects.

### Fixed

- 01 PyTorch classifier: seeded shuffle before the train/validation split; evaluate.py loads Hydra configuration through OmegaConf.
- 14 Model Router: added the missing argparse import and UTF-8 benchmark reports.
- 18 AI Observability: added the missing argparse import in the benchmark script.

### Documentation

- Updated setup instructions and documented optional integrations and unverified runs.

