# ESCET Grid trace workflow

This note documents the helper workflow for comparing `Grid_semplified.cif`
between:

- ESCET / `cifsim`
- the generated Python simulator

## Why two extra helper scripts are needed

For `Grid_semplified.cif`, the generated Python runtime is step-driven and uses
one logical CSV row per logical simulation step.

ESCET, instead, consumes trace-input commands and produces trajectory data.
To compare the two behaviors, the project now provides two dedicated helpers:

- `scripts/csv_to_escet_trace_grid.py`
- `scripts/escet_trajdata_to_csv.py`

These helpers are intentionally documented here as part of the **Grid case
study workflow**. They are useful for validating the current `Grid` /
`Grid_semplified` example against ESCET, but they are **not claimed to be
generic trace-generation utilities for arbitrary CIF models**.

More precisely:

- `scripts/csv_to_escet_trace_grid.py` is **Grid-specific**, because it assumes the
  input columns, step policy and trace-driving policy of the Grid case study.
- `scripts/escet_trajdata_to_csv.py` is more broadly reusable as a trajectory-data
  conversion helper, but in this workflow it is still used in combination with
  the Grid-specific trace plan sidecar.

## 1. Create the ESCET trace file

```bash
python3 scripts/csv_to_escet_trace_grid.py \
  --cif examples/Grid_semplified.cif \
  --input-csv examples/grid_weather_input_48h_repeat.csv \
  --hours 48 
```

This writes:

```text
grid_semplified.trace
grid_semplified.trace.plan.json
grid_semplified.trace.init_args.txt
```

The JSON sidecar records which ESCET trajectory rows correspond to the logical
samples used by the generated Python runtime history.

The helper now follows the corrected core runtime semantics derived from the
ESCET-generated Java code: after `Biomass.day`, the local `Biomass.c` clock is
*not* reset, so the next `Biomass.hour` may become enabled almost immediately.
For this reason the generated 48-hour trace contains `Biomass.day` **and**
`Biomass.hour` in the same logical step after each daily biomass update.

## 2. Run ESCET / cifsim locally

The ESCET trace-input mode accepts option commands, event commands, input assignments and, when explicit time mode is used, the `time` command. In this Grid case-study workflow the helper now generates traces in **implicit time mode**, so no `time` commands are emitted. Event names should use absolute names such as `a.e`, matching the local ESCET/CIF documentation.

A local command for ESCET 11 looks like this:

```bash
cifsim examples/Grid_semplified.cif \
  -i trace \
  --init=T_in:20.0 \
  --init=Rad:300.0 \
  --init=T_mean:21.0 \
  --init=T_daytime_mean:22.0 \
  --trace-input-file=out/outputs/Grid_semplified/validation/escet_grid/Grid_semplified.trace \
  --trajdata=yes \
  --trajdata-file=out/outputs/Grid_semplified/validation/escet_grid/Grid_semplified.trajdata \
  --ask-terminate=off
```

Useful optional additions are, for example:

```bash
--gui=off
--output-mode=normal
```

The helper now auto-detects the full number of `Nodes`, `LAI` and `Biomass` instances from the CIF and generates trace events for **all** of them. This is required for ESCET execution on the full `Grid_semplified.cif`: using only a subset such as `--limit 5` leaves the omitted automata waiting at the same simulation boundary, which leads to deadlock on the next `Biomass_*.hour` event. For this reason, the ESCET trace generator should be run on the full instance set of `Grid_semplified.cif`.

The important detail is that `cifsim` long options use the `--name=value` form.
For instance, writing `--trace-input-file PATH` with a space instead of `=` causes
errors such as `Missing "=" character`.

Also note that the trajectory-data options are named exactly as shown by `cifsim -h`:

```text
--trajdata=BOOL
--trajdata-file=TDFILE
```

They are **not** named `--output-trajectories` or `--output-trajectory-data-file`.

If your local ESCET installation differs, keep `cifsim -h` as the final source of
truth for the invocation on your machine.

A successful run of this corrected workflow should produce a non-empty
`grid_semplified.trajdata` file. In our validation run, ESCET completed the
48-hour scenario and produced readable trajectory data that could then be passed
to `scripts/escet_trajdata_to_csv.py` for conversion and comparison.

## 3. Convert the ESCET trajectory data to CSV

ESCET trajectory data always contains `time` and, by default, state/input/algebraic numeric variables in the standard trajectory output format.

Convert the `.trajdata` file and sample only the logical step boundaries:

> Note: ESCET trajectory files start with a `# time` header cell and use fixed-width spacing between columns. The converter in this package normalizes that header to `time` automatically, so you can request `--columns time ...` without editing the `.trajdata` file by hand.

```bash
python3 scripts/escet_trajdata_to_csv.py \
  --trajdata out/outputs/Grid_semplified/validation/escet_grid/Grid_semplified.trajdata \
  --trace-plan out/outputs/Grid_semplified/validation/escet_grid/Grid_semplified.trace.plan.json \
  --output-csv out/outputs/Grid_semplified/validation/escet_grid/Grid_semplified_escet_trace.csv
```

Optional explicit column filter:

```bash
python3 scripts/escet_trajdata_to_csv.py \
  --trajdata out/outputs/Grid_semplified/validation/escet_grid/Grid_semplified.trajdata \
  --trace-plan out/outputs/Grid_semplified/validation/escet_grid/Grid_semplified.trace.plan.json \
  --columns time Rad Nodes_0.N LAI_0.lai Biomass_0.w \
  --output-csv out/outputs/Grid_semplified/validation/escet_grid/Grid_semplified_escet_trace.csv
```

## 4. Compare with the generated Python trace

The final Grid case-study comparison requires an explicit one-sample shift for
`Greenhouse_Rad`, because the generated Python history logs that input in a
pre-step convention while the sampled ESCET trajectory reflects the value at
the next post-step boundary.

Use:

```bash
python3 validation/compare_with_escet_behavior.py   --cif examples/Grid_semplified.cif     --input-csv examples/grid_weather_input_48h_repeat.csv   --limit 5   --hours 48   --history-vars Greenhouse_Rad Nodes_0_N LAI_0_lai Biomass_0_w   --escet-trace out/outputs/Grid_semplified/validation/escet_grid/grid_semplified_escet_trace.csv   --var-map Greenhouse_Rad=Rad   --var-map Nodes_0_N=Nodes_0.N   --var-map LAI_0_lai=LAI_0.lai   --var-map Biomass_0_w=Biomass_0.w   --shift-generated-var Greenhouse_Rad=1   --output-dir out/outputs/Grid_semplified/validation/escet_comparison/grid_semplified
```

Expected result for the validated 48-hour scenario:

```text
status: pass
mismatched cells: 0
```

The exact number of compared cells depends on the selected variables and on whether a one-sample shift is applied to `Greenhouse_Rad`.

## Important note on semantics

The generated `.trace` file is intentionally aligned with the **current
step-driven runtime policy** of the generated Python target.

That means it is a practical helper for behavioral comparison with the current
prototype. It is **not** a claim that the trace enumerates all possible CIF
behaviors of the model.

A practical lesson from the ESCET validation work is that **explicit time mode**
was not a good fit for this Grid case study. In ESCET trace mode, the `time`
command only *allows* time passage; it does not force it, and delay selection is
left to ESCET. The current helper therefore uses **implicit time mode**, so that
ESCET delays by the least amount necessary to enable the next event in the trace.
This avoids the spurious deadlocks we observed when the trace still contained
explicit `time` commands before `Biomass_*.hour` events.

## Important note about initial input variables

For `Grid` / `Grid_semplified`, ESCET initializes the model **before** processing the trace commands. Therefore, the first scenario row must be provided on the `cifsim` command line with `--init=NAME:VALUE` for each top-level input variable. The `.trace` file only changes input values *after* initialization. This workflow is specific to the Grid case study and is the reason the helper also writes a companion `.init_args.txt` file.


## Real literals in ESCET trace input

For `Grid/Grid_semplified`, ESCET treats inputs such as `Rad` as `real`. In the trace file, update commands must therefore use real literals like `310.0`, not integer-looking literals like `310`. The helper `scripts/csv_to_escet_trace_grid.py` now forces a decimal point for whole-number values when generating both `--init` arguments and `input ... = ...` trace commands.


## Important note about instance count

When the CIF model contains 100 plant instances, the ESCET trace must also drive all 100 `Nodes`, `LAI` and `Biomass` automata. A reduced trace such as `--limit 5` is not a valid execution trace for the full model and causes deadlock, because many automata remain at the current time boundary without receiving their required transitions.


Note on `.trajdata` conversion: ESCET may repeat the trajectory header block inside long `.trajdata` files, and the raw plan indexes may not match the number of persisted trajectory rows. The converter therefore normalizes repeated `# time` headers and, when needed, falls back to time-based sampling using the logical steps recorded in the trace plan.


## Final status of the validated Grid workflow

With the corrected helper scripts and the comparison shift above, the full
workflow now completes successfully for the 48-hour `Grid_semplified.cif` case:

```text
input CSV -> ESCET trace -> cifsim -> .trajdata -> sampled ESCET CSV -> comparison report
```

This means the Grid case-study validation against ESCET is now reproducible from
command line with the files included in this package.
