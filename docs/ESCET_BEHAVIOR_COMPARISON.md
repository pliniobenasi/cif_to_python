# ESCET behavior comparison

## Goal

The comparison with ESCET is a behavior comparison, not a source-code comparison.

The same CIF model and the same simulation scenario are executed through:

```text
ESCET reference execution
generated Python execution
```

The resulting traces are then compared variable by variable.

This is useful because ESCET is the official CIF reference toolchain, while the generated Python package is the experimental target of this project.

## Important distinction

The pipeline still does not claim to support the full CIF language.

For models outside the supported subset, the expected result is:

```text
ESCET may accept the CIF
the pipeline rejects it with diagnostics
```

For models inside the supported subset, the expected validation is:

```text
ESCET trace
generated Python trace
behavior comparison report
```


## Generated package resolution

The comparison script does not translate the CIF model. Before running it, generate the package with:

```bash
./scripts/run_pipeline.sh MODEL.cif
```

When `--generated-dir` is omitted, the script looks for the package at:

```text
out/generated/<MODEL_NAME>/
```

If the package or its `run_generated_model.py` runner is missing, the script stops and asks the user to run `run_pipeline.sh` first.

## Low-level comparison script

```bash
python3 validation/compare_with_escet_behavior.py \
  --cif examples/coffee_machine.cif \
  --events-csv examples/coffee_machine_events.csv \
  --escet-trace out/outputs/coffee_machine/validation/event_trace_behavior_comparison/escet_reference.csv \
  --var-map CoffeeMachine_0_location=CoffeeMachine_0_location 
```

## ESCET reference production

`validation/compare_with_escet_behavior.py` remains a low-level comparator: it expects an already produced ESCET-side CSV through `--escet-trace` and does not translate the model or run the generated package setup.

For data-driven models such as `Grid_semplified`, producing the ESCET-side CSV is still a separate case-study workflow: CSV scenario -> ESCET `.trace` -> `cifsim` `.trajdata` -> CSV conversion.

For event-trace models such as `CoffeeMachine`, `traffic_light_temporal`, or `ship-counter-optimized`, the dedicated wrapper can automate this reference-production step:

```bash
./scripts/run_event_trace_behavior_comparison.sh
```

That wrapper converts the events CSV into an ESCET `.trace`, runs `cifsim` when available, converts the `cifsim` event log into `escet_reference.csv`, and then calls `compare_with_escet_behavior.py`. The low-level comparator therefore stays focused on comparing two CSV traces, while the wrapper handles the event-trace ESCET reference generation.

For ESCET 11 specifically, trajectory-data output is enabled with options such as:

```bash
--trajdata=yes \
--trajdata-file=... \
--trace-input-file=...
```

and not with `--output-trajectories` / `--output-trajectory-data-file`.

## Generated trace

The script always generates the Python-side trace automatically by running:

```text
generated_dir/run_generated_model.py
```

with:

```text
--history-csv generated_trace.csv
```

## Existing ESCET trace mode

The comparator can still consume an existing ESCET observable CSV directly:

```bash
python3 validation/compare_with_escet_behavior.py \
  --cif examples/coffee_machine.cif \
  --events-csv examples/coffee_machine_events.csv \
  --escet-trace path/to/escet_reference.csv \
  --var-map CoffeeMachine_0_location=CoffeeMachine_0_location
```

This is useful for offline debugging, but the event-trace wrapper should normally produce `escet_reference.csv` from the local `cifsim` run.

## Output

The script writes:

```text
escet_vs_generated_behavior.md
escet_vs_generated_behavior.json
escet_vs_generated_behavior.csv
generated_trace.csv
escet_trace.csv
```

under the selected output directory.

## Variable mapping

If the generated trace and the ESCET trace use the same column names, no mapping is needed.

If column names differ, use:

```bash
--var-map GENERATED_COLUMN=ESCET_COLUMN
```

Example:

```bash
--var-map CoffeeMachine_0_location=CoffeeMachine.location
```

Multiple mappings can be supplied:

```bash
--var-map Nodes_0_N=Nodes_0.N \
--var-map LAI_0_lai=LAI_0.lai \
--var-map Biomass_0_w=Biomass_0.w
```

## Numeric tolerance

For numeric variables, use:

```bash
--tolerance 1e-6
```

String variables, such as locations, are compared exactly. Discrete numeric variables, such as `ShipCounter_0_count`, are compared using the configured numeric tolerance.

## Recommended workflow

Step 1: generate the Python package.

```bash
./scripts/run_pipeline.sh examples/coffee_machine.cif
```

This writes the generated package to the deterministic path:

```text
out/generated/coffee_machine/
```

Step 2: for event-trace models, run the event-trace wrapper. It produces the ESCET `.trace`, runs `cifsim`, converts the `cifsim` log to `escet_reference.csv`, and then invokes the comparator.

```bash
./scripts/run_event_trace_behavior_comparison.sh
```

Step 3: inspect:

```text
out/outputs/coffee_machine/validation/escet_comparison/coffee/escet_vs_generated_behavior.md
```

## Interpretation

A passing comparison means:

```text
for the selected scenario
and for the selected observable variables
the generated Python simulator produced the same trace as the ESCET reference
within the configured tolerance
```

For the current Grid case study, the final validated run reaches:

```text
status: pass
compared cells: 27
mismatched cells: 0
```

It is not a mathematical proof for all possible traces.


## Local fallback sample trace

For offline smoke tests, the package still includes fallback sample CSV files such as:

```text
examples/coffee_machine_escet_trace_sample.csv
examples/traffic_light_temporal_escet_trace_sample.csv
examples/ship-counter-optimized_escet_trace_sample.csv
```

This file mimics the expected ESCET reference trace format for the CoffeeMachine scenario. It is useful only when `cifsim` is not available, for example with:

```bash
ESCET_REFERENCE_CSV_FALLBACK=examples/coffee_machine_escet_trace_sample.csv \
RUN_CIFSIM=no \
./scripts/run_event_trace_behavior_comparison.sh
```

It is not a replacement for a real ESCET run in the normal validation workflow.

## Grid helper workflow

For `Grid_semplified.cif`, the package now also includes two helper scripts at the project root:

```text
scripts/csv_to_escet_trace_grid.py
scripts/escet_trajdata_to_csv.py
```

They are documented in:

```text
docs/ESCET_GRID_TRACE_WORKFLOW.md
```

Use them to convert `grid_weather_input.csv` into an ESCET `.trace` file, convert the resulting `.trajdata` file back to CSV, and then feed that CSV into `validation/compare_with_escet_behavior.py`.

These helpers are documented as **case-study helpers for `Grid` / `Grid_semplified`**. They do not redefine the general scope of the thesis or of the translation pipeline: the translation backend remains the generic part, while this workflow is a practical validation path for the tomato-field case study.


## Important note about initial input variables

For `Grid` / `Grid_semplified`, ESCET initializes the model **before** processing the trace commands. Therefore, the first scenario row must be provided on the `cifsim` command line with `--init=NAME:VALUE` for each top-level input variable. The `.trace` file only changes input values *after* initialization. This workflow is specific to the Grid case study and is the reason the helper also writes a companion `.init_args.txt` file.


## Real literals in ESCET trace input

For `Grid/Grid_semplified`, ESCET treats inputs such as `Rad` as `real`. In the trace file, update commands must therefore use real literals like `310.0`, not integer-looking literals like `310`. The helper `scripts/csv_to_escet_trace_grid.py` now forces a decimal point for whole-number values when generating both `--init` arguments and `input ... = ...` trace commands.


## Grid case-study caveat

For the full `Grid_semplified.cif`, the ESCET trace must include all plant instances detected in the model. A partial trace that drives only the first few `Biomass`/`Nodes`/`LAI` automata is not behaviorally valid for the full CIF and leads to deadlock in `cifsim`.


## Important practical notes from the Grid case study

For `Grid_semplified.cif`, the ESCET-side trace generation is part of the case-study validation workflow and is not a generic facility of the translator. During validation, four concrete adjustments were necessary: (1) pass the first input row via `--init=...` because ESCET initializes the model before processing the trace, (2) emit explicit real literals such as `310.0` for `real` inputs, (3) use `option time implicit` instead of explicit `time` commands to avoid spurious deadlocks, and (4) drive all `Nodes`, `LAI` and `Biomass` instances of the reduced 100-plant model rather than only a subset. With these corrections, `cifsim` produced a valid `.trajdata` file for the 48-hour validation scenario, enabling the final conversion-to-CSV step and the behavioral comparison against the generated Python simulator. A final parser fix was then needed on the Python side: ESCET writes trajectory headers using a leading `# time` cell and aligned spacing, so `scripts/escet_trajdata_to_csv.py` now normalizes that header to `time` and splits fixed-width columns robustly.


Note on `.trajdata` conversion: ESCET may repeat the trajectory header block inside long `.trajdata` files, and the raw plan indexes may not match the number of persisted trajectory rows. The converter therefore normalizes repeated `# time` headers and, when needed, falls back to time-based sampling using the logical steps recorded in the trace plan.


Note on `Greenhouse_Rad` comparison: the generated runner currently exports input-module history with a one-sample lag relative to the post-step ESCET trajectory samples. State variables such as `Nodes_0.N`, `LAI_0.lai`, and `Biomass_0.w` can still match exactly. For mixed comparisons that include `Greenhouse_Rad`, use `--shift-generated-var Greenhouse_Rad=1` in `compare_with_escet_behavior.py`.

## Core semantic fix discovered during ESCET comparison

The 48-hour `Grid_semplified` comparison uncovered a runtime-core issue rather
than a case-study-only trace bug. Reverse-engineering the ESCET Java `cifcode`
showed that `Biomass.day` does not reset the local clock `c`, which allows an
additional automatic `Biomass.hour` transition to follow almost immediately.

The generated Python runtime was updated accordingly to drain automatic edges
until quiescence within one logical step. The Grid-specific ESCET trace helper
was also updated so that the daily biomass step emits `day + hour` in the same
logical sample where needed.
