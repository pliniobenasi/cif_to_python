# Pipeline benchmark

- CIF: `examples/Grid.cif`
- Generated directory: `./out/generated/Grid`
- Hours per simulation: `48`
- Limits: `[1, 10, 100]`
- Repetitions: `1`

## Pipeline phases

| Phase | Seconds | Peak memory MB |
|---|---:|---:|
| parse | 0.229356 | 23.23 |
| feature_analysis | 0.420912 | 29.53 |
| recorded_escet_validation | 75.728535 | 29.53 |
| recorded_feature_analysis | 0.935772 | 29.53 |
| recorded_code_generation | 1.139256 | 29.53 |
| recorded_translation_manifest | 1.765403 | 29.53 |
| recorded_generated_artifacts | 0.001326 | 29.53 |

## Simulation scaling

| Limit | Dynamic modules | Build s | Simulation s | Total s | Limited bindings | Input bindings | Peak memory MB |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 3 | 0.463450 | 0.015809 | 0.479259 | 9 | 1 | 29.53 |
| 10 | 30 | 0.435403 | 0.122988 | 0.558391 | 90 | 10 | 29.53 |
| 100 | 300 | 0.491528 | 1.241031 | 1.732559 | 900 | 100 | 29.53 |

## Notes

- Peak memory is measured through resource.getrusage(RUSAGE_SELF).ru_maxrss; it is a process-level estimate.
- Generation is measured once because it is independent from the simulation limit.
- Simulation limit indicates how many instances per dynamic template are instantiated.
- Full manifest bindings: 14400

## Interpretation for the thesis

The parsing and generation phases are mostly independent from the number of simulated plants.
The build and simulation phases scale with the number of instantiated modules and bindings.
This provides the quantitative basis for discussing future parallelization or GPU-oriented execution.
