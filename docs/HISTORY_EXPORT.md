# Simulation history export

## Goal

The simulation engine stores history in memory through:

```text
system_variables_history
```

The generated runner can export that history when explicitly requested with `--history-csv` or `--history-json`.

The interactive wrapper `scripts/run_pipeline.sh` applies a stricter project policy: when the optional verification simulation is executed, a history CSV is always produced at `out/outputs/<MODEL_NAME>/results/history.csv`. The wrapper does not ask the user to choose a custom history path.

## CSV export from the generated runner

The low-level generated runner still accepts an explicit path. Example for Grid/TOMGRO:

```bash
python3 out/generated/Grid/run_generated_model.py \
  --input-csv examples/grid_weather_input.csv \
  --limit 10 \
  --save-every 1 \
  --history-csv out/outputs/Grid/results/history.csv
```

Example for CoffeeMachine:

```bash
python3 out/generated/coffee_machine/run_generated_model.py \
  --events-csv examples/coffee_machine_events.csv \
  --history-csv out/outputs/coffee_machine/results/history.csv
```

## JSON export

```bash
python3 out/generated/Grid/run_generated_model.py \
  --input-csv examples/grid_weather_input.csv \
  --limit 10 \
  --history-json out/outputs/Grid/results/grid_history.json
```

## Variable filtering

For large models, exporting all variables may create very large files.

Use:

```bash
--history-vars Nodes_0_N LAI_0_lai Biomass_0_w
```

or:

```bash
--history-vars N,lai,w
```

The second form exports every history key whose name contains or ends with the requested variable names.

Example:

```bash
python3 out/generated/Grid/run_generated_model.py \
  --input-csv examples/grid_weather_input.csv \
  --limit 10 \
  --history-csv out/outputs/Grid/results/history.csv \
  --history-vars Nodes_0_N LAI_0_lai Biomass_0_w
```

## Sampling

History is sampled according to:

```bash
--save-every
```

Example:

```bash
--save-every 24
```

stores one sample every 24 simulation steps.

## CSV format

The CSV is written in wide format:

```text
sample,VariableA,VariableB,VariableC
0,...
1,...
2,...
```

`sample` is the saved-history sample index, not necessarily the same as the original CIF time value.

For step-driven simulations, sample count depends on:

```text
initial state + saved simulation steps
```

For event-driven traces, sample count depends on:

```text
initial state + fired events
```

## Wrapper default policy

When using `scripts/run_pipeline.sh`, the verification simulation always exports history to:

```text
out/outputs/<MODEL_NAME>/results/history.csv
```

This path is derived from the CIF filename and cannot be changed from the wrapper.

The lower-level generated runner remains more flexible for tests and special direct runs: if `--history-csv` and `--history-json` are omitted, no complete history file is written.
