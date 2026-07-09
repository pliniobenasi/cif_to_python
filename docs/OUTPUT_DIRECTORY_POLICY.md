# Output directory policy

The project separates executable artifacts from derived outputs.

## Default locations

- Generated packages: `out/generated/<Model>/`
- Generation reports: `out/reports/<Model>/`
- Execution outputs: `out/outputs/<Model>/results/`
- Validation outputs: `out/outputs/<Model>/validation/`
- Benchmark outputs: `out/outputs/<Model>/benchmarks/`
- PyCrop-hosted outputs: `out/outputs/<Model>/pycrop/`

In validation and benchmark CLIs, the `<Model>` component is inferred from `--cif` whenever possible. The default generated package path is therefore `out/generated/<Model>/`. Low-level Python CLIs may still expose `--generated-dir` for testing and special cases, but they check that the selected package already exists and they never regenerate it implicitly. The interactive/project-level Bash wrappers use deterministic paths only and do not expose a custom generated-package destination.


## Interactive wrapper policy

`scripts/run_pipeline.sh` does not accept a custom generated-package output directory. The destination is always `out/generated/<MODEL_NAME>/`, with `<MODEL_NAME>` derived from the CIF filename. This keeps generated packages, validation workflows, and report paths aligned.


## Verification history policy

When `scripts/run_pipeline.sh` runs the optional verification simulation, the history CSV is always exported to:

```text
out/outputs/<MODEL_NAME>/results/history.csv
```

The user cannot override this path from the wrapper. This keeps the generated package, execution results, validation scripts, and documentation aligned around the same model-name convention.


## Validation and benchmark package checks

Validation and benchmark scripts are consumers of generated packages. They expect the package to have already been produced by:

```bash
./scripts/run_pipeline.sh MODEL.cif
```

When `--generated-dir` is omitted, these scripts resolve the generated package from the CIF path:

```text
out/generated/<MODEL_NAME>/
```

If that directory, or the expected generated runner, is missing, the script stops with a clear error instead of launching the translator internally. This keeps the translation step and the validation/benchmark steps separate and reproducible.
