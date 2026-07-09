# Generic runtime vs PyCrop hosting benchmark

This benchmark measures end-to-end CLI execution time for one selected CIF scenario.
It does not translate the CIF model and it does not measure semantic correctness.

| Model | Mode | Runner | Runs | Mean (s) | Median (s) | Min (s) | Max (s) |
|---|---|---:|---:|---:|---:|---:|---:|
| traffic_light_temporal | event-trace | generic_runtime | 10 | 0.064364 | 0.062796 | 0.060047 | 0.075067 |
| traffic_light_temporal | event-trace | pycrop_host | 10 | 0.043961 | 0.043993 | 0.040538 | 0.046632 |

## Commands

### generic_runtime

```bash
/usr/bin/python3 out/generated/traffic_light_temporal/run_generated_model.py --events-csv examples/traffic_light_temporal_events.csv
```

### pycrop_host

```bash
/usr/bin/python3 scripts/pycrop_host_runner.py --pycrop-root ._pycrop/PyCrop_restrict --cif examples/traffic_light_temporal.cif --events-csv examples/traffic_light_temporal_events.csv --seconds 6
```
