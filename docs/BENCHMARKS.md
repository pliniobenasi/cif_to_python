# Final pipeline benchmarks

## Goal

Benchmarks measure the cost of the final pipeline by separating:

```text
parsing
feature analysis
recorded code-generation timing
engine build
simulation
```

This distinction is useful because:

```text
parsing/generation = translation cost
build/simulation = generated simulator execution cost
```

## Script

```bash
python3 benchmarks/benchmark_pipeline.py \
  --cif examples/Grid.cif \
  --limits 1 10 100 1600 \
  --hours 24 \
  --repetitions 1 \
  --save-every 24
```

## Outputs

```text
out/outputs/Grid/benchmarks/pipeline/
  pipeline_benchmark.md
  pipeline_benchmark.json
  pipeline_benchmark.csv
```

## Collected metrics

| Metric | Meaning |
|---|---|
| `parse` | CIF parsing time |
| `feature_analysis` | supported-feature diagnostic time |
| `recorded_code_generation` | code-generation time recorded by `scripts/cif_to_python.py` |
| `build_seconds_mean` | engine/module/binding instantiation time |
| `simulation_seconds_mean` | simulation time |
| `dynamic_modules_instantiated` | number of dynamic modules created |
| `resolved_bindings_limited` | bindings reconstructed for the simulated subset |
| `peak_memory_mb_after_run` | process peak-memory estimate |

## Grid limits

For `Grid.cif`, `limit` indicates how many instances per template are simulated.

```text
limit=1    -> 1 Nodes, 1 LAI, 1 Biomass
limit=10   -> 10 Nodes, 10 LAI, 10 Biomass
limit=100  -> 100 Nodes, 100 LAI, 100 Biomass
limit=1600 -> 1600 Nodes, 1600 LAI, 1600 Biomass
```

Therefore:

```text
dynamic_modules = limit * 3
```

## Link to parallelization / GPU

The benchmark separates:

```text
translation cost
simulation cost
engine build cost
binding-management cost
```

If simulation dominates for many independent plant instances, future work may evaluate:

```text
multiprocessing
vectorization
per-plant parallelization
GPU execution
```

GPU execution is therefore not introduced as an initial requirement, but as a possible future development motivated by benchmark results.


## Generated package policy

Benchmark scripts do not generate or refresh Python packages. They benchmark packages already created by `scripts/run_pipeline.sh`. By default, the generated package is resolved from the CIF path as:

```text
out/generated/<MODEL_NAME>/
```

If the package is missing, the benchmark stops with an explicit error. Low-level `--generated-dir` options, where available, are intended only for controlled experiments and must point to an existing generated package.


## Generic runtime vs PyCrop hosting benchmark

`benchmarks/benchmark_engine_vs_pycrop.py` compares one selected scenario executed in two ways:

```text
generated package in the generic runtime
generated package hosted through the PyCrop adapter bridge
```

The script no longer runs a hardcoded multi-scenario suite. The model and scenario must be selected explicitly, for example:

```bash
python3 benchmarks/benchmark_engine_vs_pycrop.py \
  --cif examples/coffee_machine.cif \
  --events-csv examples/coffee_machine_events.csv \
  --runs 3
```

or:

```bash
python3 benchmarks/benchmark_engine_vs_pycrop.py \
  --cif examples/Grid_semplified.cif \
  --input-csv examples/grid_weather_input_48h_repeat.csv \
  --hours 48 \
  --limit 5 \
  --runs 3
```

The benchmark measures end-to-end CLI time and is useful mainly to estimate the overhead of the PyCrop hosting adapter compared with the direct generic runtime. It is not a semantic validation metric and it is not a pure inner-loop microbenchmark.
