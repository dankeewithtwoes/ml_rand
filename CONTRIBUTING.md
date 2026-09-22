# Contributing

Thanks for improving the local-first AI portfolio.

1. Pick one project and describe the user problem in the issue.
2. Keep optional heavyweight dependencies isolated to that project.
3. Add a deterministic test or benchmark fixture for every behavior change.
4. Record commands, environment, model version, and hardware for performance claims.
5. Never commit API keys, private documents, model weights, or generated personal data.

Run before opening a pull request:

```bash
python run_all_smoke_tests.py
cd 21_universal_skill_forge
python -m unittest discover -s tests -v
```

Small, evidence-backed pull requests are preferred over broad framework rewrites.
