# Event-trace behavior comparison

This document describes a configurable validation workflow for CIF models whose simulation scenario can be represented as an ordered trace of external events.

The goal is to compare the observable behavior of the same CIF model in up to three contexts:

1. an ESCET/cifsim observable reference scenario;
2. the generated modular Python simulator executed by the project `GenericSimulationEngine`;
3. the same generated module hosted inside PyCrop through the adapter layer, when `._pycrop/PyCrop_restrict` is available.

`CoffeeMachine` is used as the default repository example, but the workflow itself is not named after it. It can be reused for other compatible event-trace CIF models by overriding the environment variables accepted by the wrapper script.

## Responsibility boundary

`scripts/run_event_trace_behavior_comparison.sh` is a validation/comparison workflow only.

It does **not** translate the CIF model and it does **not** refresh the generated Python package. Translation remains the responsibility of:

```bash
./scripts/run_pipeline.sh MODEL.cif
```

The event-trace comparison script expects an already generated package at the deterministic project path:

```text
out/generated/<MODEL_NAME>/
```

`<MODEL_NAME>` is always derived from the CIF filename. The Bash wrapper does not expose a free generated-package path; it always checks `out/generated/<MODEL_NAME>/`. The lower-level Python validators still accept `--generated-dir` for special cases, but only after checking that the selected package already exists.

If the generated package is missing, the script stops with an error and asks the user to run `scripts/run_pipeline.sh` first. This keeps the repository structure clearer:

```text
run_pipeline.sh                         -> CIF -> generated Python package
run_event_trace_behavior_comparison.sh  -> generated package + event scenario -> behavior comparison
```

## Scope

This workflow targets models where the input scenario is an ordered list of events. It is suitable when:

- the scenario can be stored as an events CSV;
- each CSV row identifies one external CIF event;
- event names are either top-level/global CIF events, absolute events such as `Automaton.event`, or automaton-local events that can be made absolute through a `target` column or `DEFAULT_TARGET`;
- the generated runner supports `--events-csv`;
- the observable variable to compare, typically a location variable or a discrete state variable, is exported in the generated history;
- `cifsim` can execute the generated ESCET `.trace` file and its observable log can be converted to a reference CSV.

This is not a universal validation workflow for every CIF model. Models with numeric input variables, automatic/internal time chains, or case-specific sampling requirements may need a different scenario generator. `Grid_semplified.cif`, for example, is handled by the separate Grid-specific workflow.

## Main files

- `scripts/events_csv_to_escet_trace.py`: converts an event CSV into an ESCET/cifsim `.trace` file.
- `scripts/run_event_trace_behavior_comparison.sh`: validation wrapper for event-trace behavior comparison.
- `scripts/cifsim_event_log_to_csv.py`: converts the `cifsim` event-trace console log to an observable CSV for event-trace models. It supports location histories such as `CoffeeMachine_0_location` and simple discrete-variable histories such as `ShipCounter_0_count`.
- `validation/compare_with_escet_behavior.py`: compares the generated runtime history with the ESCET observable reference CSV produced from the `cifsim` run.
- `validation/compare_with_pycrop_behavior.py`: optionally compares the generated runtime history with the PyCrop-hosted execution.

Default example files:

- `examples/coffee_machine.cif`: example source CIF model.
- `out/generated/coffee_machine/`: generated Python package for the default example, when already produced by the translation pipeline.
- `examples/coffee_machine_events.csv`: example event scenario.
- `examples/coffee_machine_escet_trace_sample.csv`: offline fallback example, useful only when `cifsim` is not available in the current environment.

## Run the default example

If the generated package is missing or outdated, first run the translation pipeline:

```bash
./scripts/run_pipeline.sh examples/coffee_machine.cif
```

Then run the event-trace comparison workflow:

```bash
./scripts/run_event_trace_behavior_comparison.sh
```

The default validation run performs the following steps:

```text
existing out/generated/coffee_machine package
-> examples/coffee_machine_events.csv
-> scripts/events_csv_to_escet_trace.py
-> event trace for cifsim
-> cifsim trace-mode execution
-> conversion of the cifsim log to escet_reference.csv
-> generated Python runtime history produced during comparison
-> ESCET reference CSV comparison
-> optional PyCrop-hosted comparison
```

If `cifsim` is available in `PATH`, the script runs the generated `.trace` file and then converts the resulting `cifsim` log into `escet_reference.csv`. This CSV is the ESCET-side observable reference passed to `compare_with_escet_behavior.py`.

A pre-existing CSV reference is no longer required as the normal workflow. The optional `ESCET_REFERENCE_CSV_FALLBACK` variable exists only for offline smoke tests or environments where `cifsim` is not available.

## Run another compatible event-trace model

First generate the package:

```bash
./scripts/run_pipeline.sh examples/my_model.cif
```

Then run the comparison:

```bash
CIF_PATH=examples/my_model.cif \
EVENTS_CSV=examples/my_model_events.csv \
HISTORY_VAR=MyAutomaton_0_location \
DEFAULT_TARGET=MyAutomaton \
./scripts/run_event_trace_behavior_comparison.sh
```

By default the converter runs with `EVENT_RESOLUTION=auto`. In this mode it also receives `CIF_PATH` and inspects the CIF declarations to decide whether a relative event is global or automaton-local. This matters because top-level CIF events must be written in the ESCET trace without an automaton prefix.

For example, in `examples/coffee_machine.cif` the events are declared globally, before `automaton CoffeeMachine:`. Therefore the generated ESCET trace must contain:

```text
event input_coffee
event heat_water
event add_water
event deliver_cup
```

and not:

```text
event CoffeeMachine.input_coffee
```

`DEFAULT_TARGET` is still useful for models with automaton-local events, or when no CIF model is supplied to the converter. If the events CSV already contains absolute event names, they are emitted unchanged.

## Missing generated package behavior

When the selected generated package does not exist, the script intentionally fails instead of calling the translator automatically. The expected message is similar to:

```text
Error: generated Python package not found:
  out/generated/my_model

This script only performs event-trace behavior comparison.
Generate the Python package first, for example:
  ./scripts/run_pipeline.sh examples/my_model.cif
```

This behavior is intentional: it prevents hidden regeneration, keeps generated packages in the repository-standard location, and makes validation runs reproducible.

## Expected result for the default example

For the default `CoffeeMachine` event sequence:

```text
input_coffee -> heat_water -> add_water -> deliver_cup
```

the observable location history is expected to be:

```text
WaitingOrder -> GrindingCoffee -> HeatingWater -> ExtractingCoffee -> WaitingOrder
```

The expected comparison result is therefore `PASS` for:

- ESCET reference vs generated runtime;
- generated runtime vs PyCrop-hosted execution, when PyCrop is available.

## Methodological role

This workflow does not replace the larger `Grid_semplified.cif` case study. It has a different role:

- event-trace workflow: validates simple event-driven CIF models with discrete locations and external events;
- Grid-specific workflow: validates a larger data-driven/template-based model with input variables, automatic/internal transitions and numeric state variables.

Together, they help separate two classes of validation scenarios:

```text
event-trace CIF models -> event-driven trace comparison
Grid_semplified        -> data-driven modular case-study comparison
```

This distinction is useful for explaining that the translation pipeline is general over the supported CIF subset, while each behavioral validation scenario still requires an explicit and coherent input scenario.

## TrafficLight temporal example

The repository also includes `examples/traffic_light_temporal.cif`, a small cyclic event-trace model with a global `tick` event:

```text
Red --tick--> Green --tick--> Yellow --tick--> Red
```

Although the model contains a `granularity = 3600` discrete variable, `tick` is still a CIF event and must be supplied explicitly in the event scenario. The event trace used for validation is:

```text
examples/traffic_light_temporal_events.csv
```

The generated ESCET `.trace` therefore contains global events:

```text
event tick
event tick
event tick
```

and not automaton-prefixed events such as `event TrafficLight.tick`, because `tick` is declared at CIF top level.

The comparison workflow can be run as follows after generating the package:

```bash
./scripts/run_pipeline.sh examples/traffic_light_temporal.cif

CIF_PATH=examples/traffic_light_temporal.cif \
EVENTS_CSV=examples/traffic_light_temporal_events.csv \
HISTORY_VAR=TrafficLight_0_location \
DEFAULT_TARGET=TrafficLight \
./scripts/run_event_trace_behavior_comparison.sh
```

The expected location history is:

```text
Red -> Green -> Yellow -> Red -> Green -> Yellow -> Red
```

In the current validation run, the generated runtime and the PyCrop-hosted execution both match this expected event-trace behavior with zero mismatches. When `cifsim` is available, the event-trace wrapper derives the ESCET reference CSV from the actual `cifsim` execution log rather than from a hand-written sample CSV.


## ShipCounter guarded counter example

The repository also includes `examples/ship-counter-optimized.cif`, a compact event-trace model used to validate guards and discrete updates in isolation.

The model contains one automaton, `ShipCounter`, with a discrete counter variable:

```text
count = 0
ship_enters is enabled when count < 5 and increments count
ship_leaves is enabled when count > 0 and decrements count
```

Unlike `CoffeeMachine` and `traffic_light_temporal`, the interesting observable is not the location, which remains `Counter`, but the discrete variable:

```text
ShipCounter_0_count
```

The normal validation scenario intentionally contains only enabled events:

```text
ship_enters x 5, then ship_leaves x 5
```

The expected count history is:

```text
0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 4 -> 3 -> 2 -> 1 -> 0
```

This is important because ESCET trace-input mode treats a requested but disabled event as an invalid trace item, not as a no-op. The generated runtime follows the same strict event-trace rule: if the CSV asks for `ship_enters` when `count = 5`, or `ship_leaves` when `count = 0`, the run fails instead of silently keeping the old value.

Run it after generating the package:

```bash
./scripts/run_pipeline.sh examples/ship-counter-optimized.cif

CIF_PATH=examples/ship-counter-optimized.cif \
EVENTS_CSV=examples/ship-counter-optimized_events.csv \
HISTORY_VAR=ShipCounter_0_count \
DEFAULT_TARGET=ShipCounter \
./scripts/run_event_trace_behavior_comparison.sh
```

With `EVENT_RESOLUTION=auto`, the generated ESCET trace uses automaton-qualified event names because `ship_enters` and `ship_leaves` are declared inside `automaton ShipCounter`:

```text
event ShipCounter.ship_enters
event ShipCounter.ship_leaves
```

In the current validation run, the generated runtime and the PyCrop-hosted execution match the expected counter behavior with zero mismatches. When `cifsim` is available, the ESCET reference CSV is generated from the actual `cifsim` log; the bundled sample CSV is only an offline fallback.

