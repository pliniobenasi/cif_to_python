# Report format policy

## Decision

The project keeps generated reports in three formats only:

```text
JSON -> machine-readable reports
MD   -> human-readable reports
CSV  -> tabular data for benchmarks and validation summaries
```

Plain `.txt` reports are no longer generated.

## Reason

The previous output layout duplicated the same information in both `.txt` and `.json` files.

The cleaned policy is:

```text
JSON for scripts, tests, automation, and reproducibility
MD for humans, documentation, and thesis material
CSV for tables, plots, and spreadsheet-style analysis
```

## Generated package reports

Generation reports are written under `out/reports/<Model>/`. For example, the Grid package uses `out/reports/Grid/`:

```text
feature_report.json
feature_report.md
translation_manifest.json
translation_manifest.md
pipeline_generation_timing.json
pipeline_generation_timing.md
```

## Validation and benchmark reports

Validation and benchmark outputs use:

```text
*.json
*.md
*.csv
```

where CSV is used only when the report contains tabular data.


## Feature report diagnostics

`feature_report.md` is intentionally concise and user-facing.

Detailed analyzer diagnostics are kept in:

```text
feature_report.json
```

This keeps the Markdown report readable while preserving complete machine-readable diagnostic information.
