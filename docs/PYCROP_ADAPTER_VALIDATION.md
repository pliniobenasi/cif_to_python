# PyCrop adapter validation notes

This note summarizes the validation performed after introducing the PyCrop hosting bridge.

## 1. CoffeeMachine event history

The event adapter was corrected so that a scenario CSV target such as `CoffeeMachine` is accepted for the generated instance `CoffeeMachine_0`.

The adapter now accepts template-level and instance-level aliases and disables automatic extra stepping for purely event-driven models.

### Verified history

Both the generic runtime and the PyCrop-hosted bridge produce the same observed location history for `examples/coffee_machine_events.csv`:

| sample | location |
|---|---|
| 0 | WaitingOrder |
| 1 | GrindingCoffee |
| 2 | HeatingWater |
| 3 | ExtractingCoffee |
| 4 | WaitingOrder |

The PyCrop-hosted run keeps the location at `WaitingOrder` for the remaining idle samples because no additional events are injected after the end of the scenario.

## 2. Grid_semplified longer runs

To make biomass growth visible, the 24-hour weather profile was also repeated to 48 hours in `examples/grid_weather_input_48h_repeat.csv`.

### Generic runtime observations (`--limit 5`)

- **24h**: `Nodes_0_N` and `LAI_0_lai` increase at the day boundary, while `Biomass_0_w` is still `0`.
- **48h**: `Biomass_0_w` becomes positive immediately after the first full day.

Representative values:

- sample 24: `Nodes_0_N = 5.509732142857143`, `LAI_0_lai = 0.01588629145205231`, `Biomass_0_w = 0`
- sample 25: `Biomass_0_w = 0.626947444196308`
- sample 48: `Nodes_0_N = 6.019464285714285`, `LAI_0_lai = 0.01700028362834248`, `Biomass_0_w = 0.626947444196308`

### PyCrop-hosted bridge observations (`--limit 5`)

- **24h**: `Nodes_0_N` increases at the first day boundary; `Biomass_0_w` is still `0` as expected.
- **48h**: `Biomass_0_w` becomes positive as well, showing that the bridge does not stall on longer runs.

Representative values:

- sample 24: `Nodes_0_N = 5.509732142857143`, `LAI_0_lai = 0.015`, `Biomass_0_w = 0`
- sample 25: `Biomass_0_w = 0.6240745027468977`
- sample 48: `Nodes_0_N = 6.019464285714285`, `LAI_0_lai = 0.01588629145205231`, `Biomass_0_w = 0.6240745027468977`

### Interpretation

The PyCrop bridge is therefore **correctly executable** and shows biomass growth on longer runs, but it is **not fully behavior-identical** to the generic runtime on the day-boundary-sensitive variables. The most likely reason is the original single-pass scheduling policy of the PyCrop `SimulationEngine`, which makes downstream modules observe upstream values one cycle later.

## 3. Benchmark

A lightweight CLI-level benchmark is provided in:

- `benchmarks/benchmark_engine_vs_pycrop.py`

If the benchmark is launched with `--output-dir out/outputs/benchmark_suite/benchmarks`, results are written to:

- `out/outputs/benchmark_suite/benchmarks/engine_hosting_benchmark.csv`
- `out/outputs/benchmark_suite/benchmarks/engine_hosting_benchmark.json`

These timings are useful as a project-level comparison, but they include Python process startup and package loading, so they should not be interpreted as low-level micro-benchmarks.

## 4. Direct generic-runtime vs PyCrop history comparison

The package now includes `validation/compare_with_pycrop_behavior.py`, which exports the history from both hosts and compares them sample-by-sample.

Current checked outcomes:

- `coffee_machine`: **pass**, `mismatched cells: 0`
- `Grid_semplified` 24h: **fail**, `mismatched cells: 1` (first day-boundary LAI update)
- `Grid_semplified` 48h: **fail**, `mismatched cells: 49`

The `Grid_semplified` mismatches are therefore no longer anecdotal observations from manual CSV inspection; they are now reproducible through a dedicated comparison workflow. This strengthens the interpretation that the current difference belongs to the host scheduling policy of PyCrop rather than to the adapter's ability to execute the generated modules.
