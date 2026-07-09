# Project structure

The repository follows a lightweight `src/` layout and separates generated artifacts, reports, and run outputs from the translation core.

```text
project/
  src/
    pipeline/                # translation core, runtime, builders, manifests
    pycrop_adapter/          # PyCrop hosting adapters
  scripts/
    cif_to_python.py         # main user-facing CLI
    pycrop_host_runner.py    # host generated packages inside PyCrop
    csv_to_escet_trace_grid.py
    escet_trajdata_to_csv.py
    run_pipeline.sh          # interactive shell wrapper
  validation/                # behavioral and BLEU-style comparisons
  benchmarks/                # benchmark scripts
  examples/                  # CIF models and scenario CSV files
  docs/                      # technical documentation
  tests/                     # regression and CLI tests
  out/
    generated/               # generated Python packages per CIF model
    outputs/
      <Model>/
        results/             # history CSV/JSON and run outputs
        validation/          # ESCET/PyCrop/grid validation outputs
        benchmarks/          # model-specific benchmark outputs
        pycrop/              # PyCrop-hosted summaries or traces
    reports/
      <Model>/               # feature reports, manifests, generation timing
  ._pycrop/                  # hidden internal PyCrop copy used for adapter work
  requirements.txt
  README.md
```

## Main conventions

- **Source code** lives under `src/`.
- **User-facing entry points** live under `scripts/`.
- **Generated packages** default to `out/generated/<CIF stem>/`.
- **Generation reports** default to `out/reports/<CIF stem>/`.
- **Run outputs** default to `out/outputs/<CIF stem>/...`, split by `results`, `validation`, `benchmarks`, and `pycrop`.

## Typical commands

```bash
python3 scripts/cif_to_python.py examples/Grid.cif
python3 validation/run_grid_validation.py --cif examples/Grid.cif
python3 benchmarks/benchmark_pipeline.py --cif examples/Grid.cif
```

## Why this structure

This structure keeps the translation core stable and readable while avoiding a repository root crowded with generated modules and transient execution artifacts. It also makes the distinction between:

- source code (`src/`),
- runnable tools (`scripts/`, `validation/`, `benchmarks/`),
- input examples (`examples/`),
- generated artifacts (`out/generated/`),
- generation reports (`out/reports/`),
- execution outputs (`out/outputs/`).
