# Generic runtime vs PyCrop hosting benchmark

This benchmark measures end-to-end CLI execution time for one selected CIF scenario.
It does not translate the CIF model and it does not measure semantic correctness.

| Model | Mode | Runner | Runs | Mean (s) | Median (s) | Min (s) | Max (s) |
|---|---|---:|---:|---:|---:|---:|---:|
| coffee_machine | event-trace | generic_runtime | 1 | 2.160439 | 2.160439 | 2.160439 | 2.160439 |
| coffee_machine | event-trace | pycrop_host | 1 | 2.168054 | 2.168054 | 2.168054 | 2.168054 |

## Commands

### generic_runtime

```bash
/opt/pyvenv/bin/python3 out/generated/coffee_machine/run_generated_model.py --events-csv examples/coffee_machine_events.csv
```

### pycrop_host

```bash
/opt/pyvenv/bin/python3 scripts/pycrop_host_runner.py --pycrop-root ._pycrop/PyCrop_restrict --cif examples/coffee_machine.cif --events-csv examples/coffee_machine_events.csv --seconds 4
```
