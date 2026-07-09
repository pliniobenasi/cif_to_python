# PyCrop adapter integration for generated CIF modules

This document describes the experimental compatibility layer that allows the **generated modules produced by the CIF -> modular Python translator** to run inside the **original PyCrop `SimulationEngine`**.

## Scope

This adapter layer is **not** the main backend of the thesis. The main backend remains the generated ESCET-style/runtime-generic simulator. The PyCrop adapter is a secondary integration layer that demonstrates executable compatibility with PyCrop for the main families of models already explored during the project:

- **event-driven** models such as `CoffeeMachine`;
- **data-driven modular** models such as `Grid_semplified` / `Grid`.

## Design

The integration is split into three reusable parts:

1. `GeneratedModulePyCropAdapter`
   - wraps a generated dynamic module and exposes the PyCrop crop-module interface;
   - supports two modes:
     - `data` for ordinary numeric inputs;
     - `event` for event traces routed through `fire(event)`.

2. `GeneratedInputModulePyCropAdapter`
   - wraps generated algebraic/input modules such as the generated `Greenhouse_template` input module;
   - makes them acceptable to the original PyCrop `SimulationEngine` as regular input modules.

3. `GeneratedEventsCsvInputModule`
   - provides an event-input bridge for generated event-driven models hosted in PyCrop;
   - supports both:
     - generic generated scenario CSV files (`step,event,target`);
     - older distributed coffee-style event CSV rows (`timestep,row,col,event`).

A single CLI runner is provided:

- `src/pycrop_adapter/pycrop_host_runner.py`

This runner auto-selects the execution style depending on the provided input arguments.

---

## Running `CoffeeMachine` inside PyCrop

Prerequisites:

- extract `PyCrop_restrict_new.zip`;
- use an already generated package such as `out/generated/coffee_machine/`; generate it first with `scripts/run_pipeline.sh` when missing.

Example:

```bash
python3 scripts/cif_to_python.py examples/coffee_machine.cif

python3 scripts/pycrop_host_runner.py \
  --pycrop-root ._pycrop/PyCrop_restrict \
  --cif examples/coffee_machine.cif \
  --events-csv examples/coffee_machine_events.csv \
  --seconds 6 \
  --output-json out/outputs/coffee_machine/pycrop/coffee_summary.json
```

Expected behavior:

- the generated module is hosted by the original PyCrop `SimulationEngine`;
- events from the scenario CSV are routed through the adapter to `fire(event)`;
- the final location/state is reported in the JSON summary.

Optional history export:

```bash
python3 scripts/pycrop_host_runner.py \
  --pycrop-root ._pycrop/PyCrop_restrict \
  --cif examples/coffee_machine.cif \
  --events-csv examples/coffee_machine_events.csv \
  --seconds 6 \
  --history-csv out/outputs/coffee_machine/pycrop/coffee_history.csv \
  --history-vars CoffeeMachine_0_location
```

---

## Running `Grid_semplified` inside PyCrop

Example:

```bash
python3 scripts/pycrop_host_runner.py \
  --pycrop-root ._pycrop/PyCrop_restrict \
  --cif examples/Grid_semplified.cif \
  --input-csv examples/grid_weather_input_48h_repeat.csv \
  --hours 48 \
  --limit 5 \
  --output-json out/outputs/Grid_semplified/pycrop/grid_summary.json
```

Expected behavior:

- the generated `Greenhouse_template` input module is wrapped as a PyCrop input module;
- `Nodes`, `LAI`, and `Biomass` generated modules are wrapped as PyCrop crop modules;
- bindings are reconstructed generically from the CIF model and applied through the original PyCrop engine.

Optional history export:

```bash
python3 scripts/pycrop_host_runner.py \
  --pycrop-root ._pycrop/PyCrop_restrict \
  --cif examples/Grid_semplified.cif \
  --input-csv examples/grid_weather_input_48h_repeat.csv \
  --hours 48 \
  --limit 5 \
  --history-csv out/outputs/Grid_semplified/pycrop/grid_history.csv \
  --history-vars Greenhouse_Rad Nodes_0_N LAI_0_lai Biomass_0_w
```

---

## What is generic and what is not

### Generic part

The adapter layer is intentionally generic at the **module-hosting** level:

- a single crop-module adapter;
- a single generated-input adapter;
- a single event-input adapter;
- a single CLI runner.

### Still model-dependent part

The integration still depends on the **execution policy** of the model family:

- event-driven models require event input;
- data-driven models require numeric input series and reconstructed bindings.

Therefore the correct claim is:

> The current adapter framework provides a common PyCrop compatibility layer for the main classes of models already supported by the translator, rather than a one-click universal bridge for every possible CIF model.

This distinction is important for the thesis and remains consistent with the stated scope of the supported CIF subset.


---

## Verified event-driven history for `CoffeeMachine`

After fixing the event-target dispatch in `GeneratedModulePyCropAdapter`, the PyCrop-hosted execution now accepts both the concrete instance name (`CoffeeMachine_0`) and the template-level alias (`CoffeeMachine`) used by the scenario CSV.

In addition, the adapter was switched to **non-automatic stepping** for purely event-driven models, so a PyCrop step only forwards external events to `fire(event)` and does not trigger an extra automatic `step([])` afterwards.

With `examples/coffee_machine_events.csv`, the exported history is now coherent and matches the generated package run:

- sample 0: `WaitingOrder`
- sample 1: `GrindingCoffee`
- sample 2: `HeatingWater`
- sample 3: `ExtractingCoffee`
- sample 4: `WaitingOrder`

This confirms that the bridge is now correct for the `CoffeeMachine` event trace used in the project.

## Longer `Grid_semplified` runs (24h / 48h)

To make biomass growth visible, the Grid/TOMGRO scenario was extended from the initial short validation run to:

- a **24-hour** run using `examples/grid_weather_input.csv`;
- a **48-hour** run using `examples/grid_weather_input_48h_repeat.csv`, obtained by repeating the 24-hour climate profile for a second day.

### Generated runtime (generic engine)

For `--limit 5`:

- after **24h**, `Nodes_0_N` and `LAI_0_lai` have already increased, while `Biomass_0_w` is still `0`;
- after **48h**, `Biomass_0_w` becomes positive (first visible increase right after the day boundary), confirming that the generated biomass module does not update `w` during hourly transitions but only after the daily transition has completed.

### PyCrop-hosted bridge

The PyCrop-hosted execution also shows biomass growth on the 48-hour scenario, so the bridge does not stall. However, the exported history is **not fully identical** to the generic runtime on the day-boundary dependent variables:

- `Nodes_0_N` remains aligned;
- `LAI_0_lai` is delayed by one cycle at the first day boundary;
- `Biomass_0_w` also differs slightly in value after day 1.

This is consistent with the original PyCrop `SimulationEngine` update policy: modules are stepped in a single pass and downstream modules observe upstream values through the engine-level variable store, which is refreshed only after modules finish their step. In practice, this means that the PyCrop-hosted bridge is excellent for **executability** and for short validations, but for tightly chained daily updates the main generic runtime remains the more semantically faithful reference.

Note: `pycrop_host_runner.py` now creates parent directories automatically for `--output-json` before writing the summary file.

## Direct behavioral comparison against the generic runtime

A dedicated helper script is also provided to compare the same generated package in the two hosts:

- `validation/compare_with_pycrop_behavior.py`

See `docs/PYCROP_BEHAVIOR_COMPARISON.md` for the complete workflow and the current observed results for `CoffeeMachine` and `Grid_semplified`.
