# Pipeline benchmark

- CIF: `examples/coffee_machine.cif`
- Generated directory: `/mnt/data/proj_step90/out/generated/coffee_machine`
- Hours per simulation: `1`
- Limits: `[1]`
- Repetitions: `1`

## Pipeline phases

| Phase | Seconds | Peak memory MB |
|---|---:|---:|
| parse | 0.003422 | 301.66 |
| feature_analysis | 0.002983 | 301.66 |
| recorded_escet_validation | 6.832013 | 301.66 |
| recorded_feature_analysis | 0.028287 | 301.66 |
| recorded_code_generation | 0.010186 | 301.66 |
| recorded_translation_manifest | 0.027005 | 301.66 |
| recorded_generated_artifacts | 0.002226 | 301.66 |

## Simulation scaling

| Limit | Dynamic modules | Build s | Simulation s | Total s | Limited bindings | Input bindings | Peak memory MB |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 0.004248 | 0.000004 | 0.004252 | 0 | 0 | 301.66 |

## Notes

- Peak memory is measured through resource.getrusage(RUSAGE_SELF).ru_maxrss; it is a process-level estimate.
- Generation is measured once because it is independent from the simulation limit.
- Simulation limit indicates how many instances per dynamic template are instantiated.
- Full manifest bindings: 0

## Interpretation for the thesis

The parsing and generation phases are mostly independent from the number of simulated plants.
The build and simulation phases scale with the number of instantiated modules and bindings.
This provides the quantitative basis for discussing future parallelization or GPU-oriented execution.