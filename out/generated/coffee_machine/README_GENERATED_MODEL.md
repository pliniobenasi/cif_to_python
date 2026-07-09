# Generated CIF -> Python package

This folder was produced automatically by the generic CIF -> modular Python pipeline.

## Contents

```text
source_model.cif
        run_generated_model.py
*.py generated modules
factory.py
runtime.py
constants.py
```

## Run

Step-driven models with generated input modules:

```bash
python3 run_generated_model.py --limit 3 --hours 48
```

Event-driven models without input modules:

```bash
python3 run_generated_model.py --events event1 event2 event3
```

Event trace CSV scenarios:

```bash
python3 run_generated_model.py --events-csv ../../examples/coffee_machine_events.csv
```

Data trace CSV scenarios:

```bash
python3 run_generated_model.py --input-csv ../../examples/grid_weather_input.csv --limit 100
```

Export simulation history:

```bash
python3 run_generated_model.py --input-csv ../examples/grid_weather_input.csv           --limit 10           --save-every 1           --history-csv ../../outputs/Grid/results/grid_history.csv
```

## Reports

Generation reports are written outside the package under `out/reports/<Model>/`, keeping the generated package focused on executable artifacts.

## Notes

The runner expects to be executed inside the pipeline directory or from a generated
folder whose ancestor project root contains the pipeline support package under `src/pipeline/`.
