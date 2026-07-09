# Interactive Bash pipeline

## Goal

`scripts/run_pipeline.sh` is an interactive wrapper around the Python CLI.

It does not replace the actual translation pipeline and it does not allow a custom generated-package destination. The generated package is always written to `out/generated/<MODEL_NAME>/`, where `<MODEL_NAME>` is derived from the CIF filename.

When the optional verification simulation is executed, the history CSV path is also fixed by convention and is not requested from the user:

```text
out/outputs/<MODEL_NAME>/results/history.csv
```

## Usage

```bash
./scripts/run_pipeline.sh MODEL.cif
```

The generated package path is fixed by convention:

```text
out/generated/<MODEL_NAME>/
```

The verification history CSV path is fixed by convention:

```text
out/outputs/<MODEL_NAME>/results/history.csv
```

Example:

```bash
./scripts/run_pipeline.sh examples/Grid.cif
```

## Flow

```text
CIF input
->
optional ESCET validation prompt
->
ESCET validation, if requested
->
internal supported-subset diagnostics
->
Python module generation
->
feature report
->
translation manifest
->
optional verification simulation prompt
->
GenericSimulationEngine
```

## ESCET command

The ESCET command is optional and configurable.

Example:

```bash
export ESCET_CIF_CHECK_CMD='cif2cif {cif_abs} --output-mode=error'
export ESCET_TIMEOUT=900
./scripts/run_pipeline.sh examples/Grid.cif
```

## ESCET timeout

Large CIF files such as `Grid.cif` can require more than 60 seconds.

A timeout means only that the external ESCET command did not finish within the configured limit. It does not prove that the CIF file is invalid.

## Simulation modes

Step-driven mode:

```text
limit
hours
save_every
optional history variable filters
```

Event-driven mode:

```text
explicit event sequence
```

The user can choose the scenario and optional variable filters, but cannot choose the history CSV path. The wrapper always exports verification history to `out/outputs/<MODEL_NAME>/results/history.csv`.


## Scenario CSV inputs

For event-driven verification, the wrapper can use:

```text
--events-csv
```

For step-driven verification, the wrapper can use:

```text
--input-csv
```

This keeps external simulation scenarios separate from the CIF model.
