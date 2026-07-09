# CIF to modular Python simulator pipeline

## Thesis context

Official thesis title:

```text
Automatic translation of CIF models to modular Python simulators
```

All comments, shell prompts, and project documentation in this package are written in English.

## What this project does

The project implements an experimental pipeline that:

```text
accepts a CIF model
->
optionally validates it with ESCET
->
analyzes supported/unsupported constructs
->
generates a modular Python simulator package when the model belongs to the supported subset
->
validates and benchmarks the generated package
```

The pipeline does not claim to translate the full CIF language.

It accepts arbitrary CIF input and translates the models that fit the implemented subset.


A recent reverse-engineering pass against the ESCET-generated Java `cifcode` of
`Grid_semplified.cif` also led to a runtime-core fix: the generated Python
runtime now drains automatic/internal transitions to quiescence inside one
logical step, instead of firing at most one automatic edge per step. This fixes
a semantic lag affecting daily/hourly chains such as `Biomass.day` followed by
`Biomass.hour`.

## Main commands

Generate the Python package:

```bash
python3 scripts/cif_to_python.py examples/Grid.cif
```

Interactive pipeline:

```bash
./scripts/run_pipeline.sh examples/Grid.cif
```

Validate the generated Grid package:

```bash
python3 validation/run_grid_validation.py \
  --cif examples/Grid.cif \
  --reference-root="._pycrop/PyCrop_restrict/PyCrop/Implementations/TOMGRO/"
```

Benchmark the generated Grid package:

```bash
python3 benchmarks/benchmark_pipeline.py \
  --cif examples/Grid.cif \
  --limits 1 10 100 1600 \
  --hours 24
```

## Clean project structure

```text
src/pipeline/                 core CIF -> Python translation pipeline
src/pipeline/core/            generic runtime/engine support code
src/pycrop_adapter/           experimental PyCrop hosting bridge
scripts/                      user-facing CLI wrappers and helper workflows
examples/                     CIF examples and scenario input files
validation/                   behavior and reference comparison tools
benchmarks/                   benchmark tools
docs/                         manual technical documentation
tests/                        regression/development tests
out/generated/<MODEL_NAME>/   generated Python package for each CIF model
out/reports/<MODEL_NAME>/     feature, manifest and generation timing reports
out/outputs/<MODEL_NAME>/     per-model results, validation and benchmark outputs
._pycrop/                     vendored PyCrop reference bundle used only by adapter/benchmarks
```

See:

```text
docs/PROJECT_STRUCTURE.md
```

## Single generation point

Modules are generated only by:

```text
src/pipeline/cif_to_python.py
```

The user-facing entry point is `scripts/cif_to_python.py`, which loads the package code from `src/`.

Validation and benchmark scripts reuse the existing generated package instead of generating modules again.

## Supported subset

See:

```text
docs/SUPPORTED_CIF_SUBSET.md
docs/CIF_SUPPORT_MATRIX.md
```

## Event semantics

See:

```text
docs/EVENT_SEMANTICS.md
```

## Grid validation

See:

```text
docs/GRID_VALIDATION.md
```

The current validation checks:

```text
manifest validity
instance counts
dependency order
Greenhouse input propagation
Nodes monotonicity
LAI monotonicity
Biomass non-negativity
```

## Reference comparison

See:

```text
docs/REFERENCE_COMPARISON.md
```

BLEU-style similarity is used only as a supplementary lexical similarity metric, not as semantic proof.

## Benchmarks

See:

```text
docs/BENCHMARKS.md
```

The benchmark separates translation cost from simulator execution cost.

## Generated package

Generated packages are stored under:

```text
out/generated/<MODEL_NAME>/
```

For example:

```text
out/generated/Grid/
out/generated/Grid_semplified/
out/generated/coffee_machine/
```

A generated package may include files such as:

```text
runtime.py
constants.py
factory.py
run_generated_model.py
source_model.cif
<generated module files>.py
```

The exact module files depend on the CIF model. For example, Grid/TOMGRO models generate modules such as `greenhouse.py`, `nodes.py`, `lai.py`, and `biomass.py`, while event-driven examples such as `coffee_machine.cif` generate their own automaton module.

The associated generation reports are stored separately under `out/reports/<MODEL_NAME>/`, not inside the generated package.

## Report format policy

Generated reports now use only:

```text
JSON -> machine-readable reports
MD   -> human-readable reports
CSV  -> tabular data
```

Plain `.txt` reports are no longer generated.

See:

```text
docs/REPORT_FORMAT_POLICY.md
```


## Scenario inputs

The generated runner supports external simulation scenarios without manual module bindings.

Event-driven scenario:

```bash
python3 out/generated/CoffeeMachine/run_generated_model.py \
  --events-csv examples/coffee_machine_events.csv
```

Data-driven scenario:

```bash
python3 out/generated/Grid/run_generated_model.py \
  --input-csv examples/grid_weather_input.csv \
  --limit 100
```

Event-trace temporal example:

```bash
python3 out/generated/traffic_light_temporal/run_generated_model.py \
  --events-csv examples/traffic_light_temporal_events.csv
```

Event-trace guarded counter example:

```bash
python3 out/generated/ship-counter-optimized/run_generated_model.py \
  --events-csv examples/ship-counter-optimized_events.csv
```

See:

```text
docs/SCENARIO_INPUTS.md
```


## Simulation history export

The generated runner can optionally write the in-memory simulation history to CSV or JSON.

When using `scripts/run_pipeline.sh`, the verification simulation follows the repository output policy and always writes the history CSV to `out/outputs/<MODEL_NAME>/results/history.csv`. The wrapper does not ask for a custom history output path.

Example:

```bash
python3 out/generated/Grid/run_generated_model.py \
  --input-csv examples/grid_weather_input.csv \
  --limit 10 \
  --save-every 1 \
  --history-csv out/outputs/Grid/results/history.csv \
  --history-vars Nodes_0_N LAI_0_lai Biomass_0_w
```

See:

```text
docs/HISTORY_EXPORT.md
```


## ESCET behavior comparison

The project includes behavior-comparison tools against ESCET references.
For event-trace models, use the dedicated wrapper after generating the package:

```bash
./scripts/run_pipeline.sh examples/coffee_machine.cif
./scripts/run_event_trace_behavior_comparison.sh
```

The wrapper converts the events CSV to an ESCET `.trace`, runs `cifsim` when available, converts the `cifsim` log to `escet_reference.csv`, and then calls `validation/compare_with_escet_behavior.py`.

See:

```text
docs/ESCET_BEHAVIOR_COMPARISON.md
docs/EVENT_TRACE_BEHAVIOR_COMPARISON.md
```

For event-trace models, the repository includes:

```text
docs/EVENT_TRACE_BEHAVIOR_COMPARISON.md
examples/traffic_light_temporal.cif
examples/traffic_light_temporal_events.csv
examples/ship-counter-optimized.cif
examples/ship-counter-optimized_events.csv
```


## Feature report format

The Markdown feature report is concise and omits raw analyzer diagnostics.

Detailed analyzer diagnostics are preserved in:

```text
feature_report.json
```

The generated package still keeps `source_model.cif` for traceability and reproducibility.

## ESCET Grid helper scripts

This version also includes two helper scripts for the `Grid_semplified.cif` ESCET comparison workflow:

```text
scripts/csv_to_escet_trace_grid.py
scripts/escet_trajdata_to_csv.py
```

For event-trace models, the event comparison workflow also includes:

```text
scripts/events_csv_to_escet_trace.py
scripts/cifsim_event_log_to_csv.py
scripts/run_event_trace_behavior_comparison.sh
```

See `docs/ESCET_GRID_TRACE_WORKFLOW.md` for the full workflow.

Canonical `Grid_semplified` validation workflows now use the 48-hour climate scenario in `examples/grid_weather_input_48h_repeat.csv`. The earlier 6-hour run remains useful only as a short smoke test.


## Real literals in ESCET trace input

For `Grid/Grid_semplified`, ESCET treats inputs such as `Rad` as `real`. In the trace file, update commands must therefore use real literals like `310.0`, not integer-looking literals like `310`. The helper `csv_to_escet_trace_grid.py` now forces a decimal point for whole-number values when generating both `--init` arguments and `input ... = ...` trace commands.


## ESCET Grid case-study note

For `Grid_semplified.cif`, the ESCET helper workflow is case-study-specific. The generated trace must drive **all** detected plant instances of the CIF, and the first input row must be passed to `cifsim` via `--init=...` arguments listed in the companion `.init_args.txt` file.

- the `.trajdata` converter handles ESCET's `# time` header and fixed-width spacing automatically.


Note on `.trajdata` conversion: ESCET may repeat the trajectory header block inside long `.trajdata` files, and the raw plan indexes may not match the number of persisted trajectory rows. The converter therefore normalizes repeated `# time` headers and, when needed, falls back to time-based sampling using the logical steps recorded in the trace plan.


Note on `Greenhouse_Rad` comparison: the generated runner currently exports input-module history with a one-sample lag relative to the post-step ESCET trajectory samples. State variables such as `Nodes_0.N`, `LAI_0.lai`, and `Biomass_0.w` can still match exactly. For mixed comparisons that include `Greenhouse_Rad`, use `--shift-generated-var Greenhouse_Rad=1` in `compare_with_escet_behavior.py`.


## Experimental PyCrop hosting bridge

All direct PyCrop imports are intentionally confined to `src/pycrop_adapter/`. The main CIF -> Python translation path and the generated runtime no longer require the vendored PyCrop bundle.


The package now also includes an experimental compatibility layer to host generated CIF modules inside the **original PyCrop `SimulationEngine`**.

See:

- `docs/PYCROP_ADAPTER_INTEGRATION.md`
- `scripts/pycrop_host_runner.py`
- `src/pycrop_adapter/pycrop_host_runner.py`

Supported integration modes currently validated:

- `CoffeeMachine` inside PyCrop through an event CSV trace;
- `Grid_semplified` inside PyCrop through generated greenhouse input modules and generic binding reconstruction from the CIF model.


## PyCrop hosting extras

The package now also contains:

- `examples/grid_weather_input_48h_repeat.csv` for longer Grid/TOMGRO runs;
- `benchmarks/benchmark_engine_vs_pycrop.py` for scenario-based CLI-level benchmarking between the generic runtime and PyCrop hosting mode;
- updated PyCrop adapter documentation, including the CoffeeMachine event-history fix and the 24h/48h Grid observations.

Note: `pycrop_host_runner.py` now creates parent directories automatically for `--output-json` before writing the summary file.

The PyCrop bridge also supports direct history export through `--history-csv` / `--history-json`, and the package now includes a dedicated behavioral comparison workflow between the generic runtime and PyCrop hosting:

- `validation/compare_with_pycrop_behavior.py`
- `docs/PYCROP_BEHAVIOR_COMPARISON.md`

This makes it possible to compare the same generated package in two hosts:

- generic runtime vs PyCrop for `CoffeeMachine` (current result: pass)
- generic runtime vs PyCrop for `traffic_light_temporal` (current result: pass)
- generic runtime vs PyCrop for `ship-counter-optimized` (current result: pass on `ShipCounter_0_count`)
- generic runtime vs PyCrop for `Grid_semplified` (current result: informative fail on day-boundary-sensitive variables)

Internal support material that is not part of the main user-facing workflow is kept under hidden directories when bundled, such as `._pycrop/` for the vendored PyCrop reference bundle. Python cache directories like `__pycache__/` are excluded from the distributed package.


### ShipCounter event trace note

`examples/ship-counter-optimized_events.csv` intentionally contains only events that are enabled in ESCET trace mode: five `ship_enters` events followed by five `ship_leaves` events. This validates discrete variable updates and guards along an executable trace. A separate negative scenario, `examples/ship-counter-optimized_invalid_guard_events.csv`, requests one extra `ship_enters` event after `count` has reached 5; ESCET and the generated runtime both reject it because event-trace inputs are strict and disabled events are not silent no-ops.
