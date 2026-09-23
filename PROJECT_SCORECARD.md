# Portfolio status and next steps

## Current scope

The repository contains 21 small AI engineering projects. They are prototypes and labs, not production services. Most focus on local execution, measurable behavior, or data privacy.

The offline checks cover selected behavior in the router, memory store, observability, red-team, RAG, document parsing, and Skill Forge projects. External model and service integrations still need reproducible runs on documented hardware and software.

## Gaps

- Several demos need a clean-machine setup and short recording.
- Benchmarks need raw outputs plus model, dataset, hardware, and software versions.
- Some heuristic evaluations need comparison with labeled data or a calibrated judge.
- Public releases need tagged versions and a clear issue and contribution workflow.

## Next steps

| Priority | Project | Next validation |
|---:|---|---|
| P0 | Skill Forge | Run the same tool contract against two providers |
| P0 | Knowledge OS | Add import connectors, a fixed recall dataset, and a UI demo |
| P1 | Model Router | Add budget constraints and evaluate against recorded traces |
| P1 | Observability Guard | Add streaming proxy support and OpenTelemetry export |
| P1 | Red-Team Arena | Add versioned datasets and judge calibration |
| P2 | Document Parser | Evaluate against an annotated public dataset |

## Before tagging a release

- Run the demo on a clean machine.
- Test the main path and common failures.
- Add a screenshot or short recording.
- Publish raw benchmark data and environment details.
- Document data handling and known limits.
- Add a changelog and GitHub release.

