# Pipeline benchmark

- CIF: `examples/traffic_light_temporal.cif`
- Generated directory: `/home/bena/Programs/PyCoffee/Step94_Escet_trace_fix/out/generated/traffic_light_temporal`
- Hours per simulation: `24`
- Limits: `[1, 10, 100]`
- Repetitions: `1`

## Pipeline phases

| Phase | Seconds | Peak memory MB |
|---|---:|---:|
| parse | 0.003204 | 15.52 |
| feature_analysis | 0.001901 | 15.52 |
| recorded_feature_analysis | 0.004914 | 15.52 |
| recorded_code_generation | 0.003894 | 15.52 |
| recorded_translation_manifest | 0.010543 | 15.52 |
| recorded_generated_artifacts | 0.002811 | 15.52 |

## Simulation scaling

| Limit | Dynamic modules | Build s | Simulation s | Total s | Limited bindings | Input bindings | Peak memory MB |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 0.001839 | 0.000002 | 0.001841 | 0 | 0 | 15.52 |
| 10 | 1 | 0.000722 | 0.000001 | 0.000723 | 0 | 0 | 15.52 |
| 100 | 1 | 0.001472 | 0.000002 | 0.001474 | 0 | 0 | 15.52 |

## Notes

- Peak memory is measured through resource.getrusage(RUSAGE_SELF).ru_maxrss; it is a process-level estimate.
- Generation is measured once because it is independent from the simulation limit.
- Simulation limit indicates how many instances per dynamic template are instantiated.
- Full manifest bindings: 0

## Interpretation for the thesis

The parsing and generation phases are mostly independent from the number of simulated plants.
The build and simulation phases scale with the number of instantiated modules and bindings.
This provides the quantitative basis for discussing future parallelization or GPU-oriented execution.