# Portfolio scorecard and product roadmap

This audit uses five criteria: a real user problem, a distinctive technical thesis, runnable setup, behavioral tests, and visible evidence (benchmark/demo).

## What is already differentiated

- **Local-first thesis:** privacy, cost, and offline operation connect many projects.
- **Measurement mindset:** benchmarks are present across retrieval, serving, routing, safety, and portability.
- **Breadth:** the catalog supports strong interview conversations across ML, LLM apps, inference, and MLOps.

## The credibility gap

Most projects are concise labs, not production tools yet. Compilation is useful but does not prove behavior. Several benchmarks use heuristic labels or expected output rather than published, reproducible results. README claims must stay aligned with that reality.

## Priority roadmap

| Priority | Product direction | Next proof that matters |
|---:|---|---|
| P0 | Skill Forge | isolated capability runner, signed packages, adapters tested against two providers |
| P0 | Knowledge OS | import connectors, deletion/export guarantees, fixed recall dataset, UI demo |
| P1 | Model Router | online feedback loop, budget constraints, Pareto dashboard, real trace dataset |
| P1 | Observability Guard | streaming proxy, redaction rather than block-only behavior, OpenTelemetry export |
| P1 | Red-Team Arena | versioned safe datasets, judge calibration, CI regression budgets |
| P2 | Document Parser | annotated public benchmark and human correction workflow |

## GitHub release checklist

Before promoting any lab to flagship:

- [ ] one-command demo on a clean machine;
- [ ] behavioral tests for the happy path and three failure modes;
- [ ] screenshot or short terminal recording in the README;
- [ ] benchmark fixture, raw results, hardware/software metadata;
- [ ] explicit threat model and data-handling statement;
- [ ] tagged release, changelog, contribution guide, and issue templates;
- [ ] no invented metrics, stars, users, or performance claims.

## Positioning

The strongest public story is not “I built 21 AI apps.” It is:

> I build local-first AI infrastructure and publish the tests, trade-offs, and failure modes—not just the demo.

That positioning is more memorable, more credible to technical reviewers, and creates a coherent reason to follow the repository.
