#!/usr/bin/env python3
from __future__ import annotations

"""Compare generated-runtime behavior with the same modules hosted in PyCrop.

The comparison is performed on exported history CSV files, not source code.
The script can either use already exported traces or run both sides on demand.
"""

import argparse
import csv
import json
import math
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pipeline.path_defaults import resolve_generated_dir, require_generated_package, default_validation_dir
DEFAULT_OUTPUT_DIR = ROOT_DIR / "out" / "outputs" / "validation" / "pycrop_comparison"


@dataclass
class ComparedCell:
    sample: int
    variable: str
    generated_value: str
    pycrop_value: str
    match: bool
    abs_error: float | None = None


@dataclass
class PyCropBehaviorComparisonReport:
    generated_dir: str
    output_dir: str
    generated_trace: str
    pycrop_trace: str
    generated_summary: str | None = None
    pycrop_summary: str | None = None
    compared_variables: list[str] = field(default_factory=list)
    compared_cells: int = 0
    matched_cells: int = 0
    mismatched_cells: int = 0
    max_abs_error: float | None = None
    status: str = "not-run"
    notes: list[str] = field(default_factory=list)


def _split_csv_values(values: list[str] | None) -> list[str] | None:
    if not values:
        return None
    result: list[str] = []
    for item in values:
        for part in item.split(","):
            part = part.strip()
            if part:
                result.append(part)
    return result or None


def _read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    path = Path(path)
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {path}")
        return [dict(row) for row in reader]


def _parse_var_maps(raw_maps: list[str] | None) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in raw_maps or []:
        if "=" not in item:
            raise ValueError(f"Invalid --var-map item: {item!r}. Expected GENERATED=PYCROP")
        generated, pycrop = item.split("=", 1)
        generated = generated.strip()
        pycrop = pycrop.strip()
        if not generated or not pycrop:
            raise ValueError(f"Invalid --var-map item: {item!r}. Expected GENERATED=PYCROP")
        result[generated] = pycrop
    return result


def _parse_shift_maps(raw_maps: list[str] | None) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in raw_maps or []:
        if "=" not in item:
            raise ValueError(f"Invalid shift item: {item!r}. Expected NAME=INTEGER_SHIFT")
        name, shift = item.split("=", 1)
        name = name.strip()
        shift = shift.strip()
        if not name or not shift:
            raise ValueError(f"Invalid shift item: {item!r}. Expected NAME=INTEGER_SHIFT")
        try:
            result[name] = int(shift)
        except ValueError as exc:
            raise ValueError(f"Invalid shift item: {item!r}. Shift must be an integer.") from exc
    return result


def _excluded_columns() -> set[str]:
    return {"sample", "step", "time", "timestep", "event", "target", "fired"}


def _infer_column_map(generated_rows: list[dict[str, str]], pycrop_rows: list[dict[str, str]]) -> dict[str, str]:
    if not generated_rows or not pycrop_rows:
        return {}
    generated_columns = set(generated_rows[0])
    pycrop_columns = set(pycrop_rows[0])
    excluded = _excluded_columns()
    common = sorted(
        column
        for column in generated_columns & pycrop_columns
        if column.lower() not in excluded
    )
    return {column: column for column in common}


def _as_float(value: str) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def _values_match(generated: str, pycrop: str, tolerance: float) -> tuple[bool, float | None]:
    generated_float = _as_float(generated)
    pycrop_float = _as_float(pycrop)
    if generated_float is not None and pycrop_float is not None:
        error = abs(generated_float - pycrop_float)
        return error <= tolerance, error
    return str(generated) == str(pycrop), None


def compare_traces(
    generated_trace: str | Path,
    pycrop_trace: str | Path,
    output_dir: str | Path,
    variable_map: dict[str, str] | None = None,
    tolerance: float = 1e-9,
    generated_shifts: dict[str, int] | None = None,
    pycrop_shifts: dict[str, int] | None = None,
) -> PyCropBehaviorComparisonReport:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_trace = Path(generated_trace)
    pycrop_trace = Path(pycrop_trace)
    generated_rows = _read_csv_rows(generated_trace)
    pycrop_rows = _read_csv_rows(pycrop_trace)

    variable_map = variable_map or _infer_column_map(generated_rows, pycrop_rows)
    generated_shifts = generated_shifts or {}
    pycrop_shifts = pycrop_shifts or {}
    if not variable_map:
        raise ValueError("No comparable variables found. Use --var-map GENERATED=PYCROP to define mappings.")

    sample_count = min(len(generated_rows), len(pycrop_rows))
    compared: list[ComparedCell] = []
    skipped_cells = 0

    for sample_index in range(sample_count):
        for generated_column, pycrop_column in variable_map.items():
            generated_index = sample_index + generated_shifts.get(generated_column, 0)
            pycrop_index = sample_index + pycrop_shifts.get(pycrop_column, 0)
            if generated_index < 0 or generated_index >= len(generated_rows):
                skipped_cells += 1
                continue
            if pycrop_index < 0 or pycrop_index >= len(pycrop_rows):
                skipped_cells += 1
                continue

            generated_value = generated_rows[generated_index].get(generated_column, "")
            pycrop_value = pycrop_rows[pycrop_index].get(pycrop_column, "")
            match, abs_error = _values_match(generated_value, pycrop_value, tolerance)
            compared.append(
                ComparedCell(
                    sample=sample_index,
                    variable=generated_column,
                    generated_value=generated_value,
                    pycrop_value=pycrop_value,
                    match=match,
                    abs_error=abs_error,
                )
            )

    matched = sum(1 for item in compared if item.match)
    mismatched = len(compared) - matched
    numeric_errors = [item.abs_error for item in compared if item.abs_error is not None]

    report = PyCropBehaviorComparisonReport(
        generated_dir="",
        output_dir=str(output_dir),
        generated_trace=str(generated_trace),
        pycrop_trace=str(pycrop_trace),
        compared_variables=list(variable_map),
        compared_cells=len(compared),
        matched_cells=matched,
        mismatched_cells=mismatched,
        max_abs_error=max(numeric_errors) if numeric_errors else None,
        status="pass" if mismatched == 0 else "fail",
        notes=[
            f"Compared {sample_count} aligned samples.",
            "Comparison is behavioral history comparison, not source-code comparison.",
        ],
    )
    if len(generated_rows) != len(pycrop_rows):
        report.notes.append(
            f"Trace lengths differ (generated={len(generated_rows)}, pycrop={len(pycrop_rows)}); comparison used the common aligned prefix."
        )
    if generated_shifts:
        report.notes.append(
            "Generated trace shifts applied: " + ", ".join(f"{n}={s}" for n, s in sorted(generated_shifts.items()))
        )
    if pycrop_shifts:
        report.notes.append(
            "PyCrop trace shifts applied: " + ", ".join(f"{n}={s}" for n, s in sorted(pycrop_shifts.items()))
        )
    if skipped_cells:
        report.notes.append(f"Skipped {skipped_cells} shifted cells outside the available sample range.")

    _write_comparison_outputs(report, compared, output_dir)
    return report


def _write_comparison_outputs(report: PyCropBehaviorComparisonReport, compared: list[ComparedCell], output_dir: Path) -> None:
    csv_path = output_dir / "generated_vs_pycrop_behavior.csv"
    md_path = output_dir / "generated_vs_pycrop_behavior.md"
    json_path = output_dir / "generated_vs_pycrop_behavior.json"

    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["sample", "variable", "generated_value", "pycrop_value", "match", "abs_error"],
        )
        writer.writeheader()
        for item in compared:
            writer.writerow(asdict(item))

    lines = [
        "# Generated runtime vs PyCrop behavior comparison",
        "",
        f"- status: **{report.status}**",
        f"- compared cells: {report.compared_cells}",
        f"- mismatched cells: {report.mismatched_cells}",
        f"- generated trace: `{report.generated_trace}`",
        f"- pycrop trace: `{report.pycrop_trace}`",
        "",
        "## Notes",
        "",
    ]
    for note in report.notes:
        lines.append(f"- {note}")
    lines.extend(["", "## First mismatches", ""])
    mismatches = [item for item in compared if not item.match][:20]
    if not mismatches:
        lines.append("No mismatches detected.")
    else:
        lines.append("| sample | variable | generated | pycrop | abs_error |")
        lines.append("|---:|---|---:|---:|---:|")
        for item in mismatches:
            error = "" if item.abs_error is None else f"{item.abs_error:.12g}"
            lines.append(
                f"| {item.sample} | {item.variable} | {item.generated_value} | {item.pycrop_value} | {error} |"
            )

    md_path.write_text("\n".join(lines) + "\n")
    json_path.write_text(json.dumps(asdict(report), indent=2))


def _run_command(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def _build_generated_run_command(args: argparse.Namespace, history_csv: Path) -> list[str]:
    generated_dir = Path(args.generated_dir)
    cmd = [sys.executable, str(generated_dir / "run_generated_model.py")]
    if args.events_csv:
        cmd.extend(["--events-csv", args.events_csv])
    else:
        cmd.extend(["--input-csv", args.input_csv, "--hours", str(args.hours)])
        if args.limit is not None:
            cmd.extend(["--limit", str(args.limit)])
        cmd.extend(["--save-every", str(args.save_every)])
    cmd.extend(["--history-csv", str(history_csv)])
    if args.history_vars:
        cmd.extend(["--history-vars", *args.history_vars])
    return cmd


def _build_pycrop_run_command(args: argparse.Namespace, history_csv: Path, summary_json: Path) -> list[str]:
    cmd = [
        sys.executable,
        str(ROOT_DIR / 'scripts' / 'pycrop_host_runner.py'),
        "--pycrop-root",
        args.pycrop_root,
        "--history-csv",
        str(history_csv),
        "--output-json",
        str(summary_json),
    ]
    if args.generated_dir:
        cmd.extend(["--generated-dir", args.generated_dir])
    elif args.cif:
        cmd.extend(["--cif", args.cif])
    if args.events_csv:
        cmd.extend(["--events-csv", args.events_csv, "--seconds", str(args.seconds)])
    else:
        cmd.extend(["--input-csv", args.input_csv, "--hours", str(args.hours)])
        if args.limit is not None:
            cmd.extend(["--limit", str(args.limit)])
    if args.history_vars:
        cmd.extend(["--history-vars", *args.history_vars])
    return cmd


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Compare generated-runtime behavior with the same modules hosted in PyCrop.")
    parser.add_argument('--generated-dir', default=None, help='Generated package directory (default: out/generated/<CIF stem>)')
    parser.add_argument("--cif", default=None, help="Optional CIF path used to infer --generated-dir when omitted")
    parser.add_argument("--pycrop-root", required=True, help="Path to extracted PyCrop_restrict root")
    parser.add_argument("--input-csv", help="Numeric scenario CSV for data-driven models")
    parser.add_argument("--events-csv", help="Event scenario CSV for event-driven models")
    parser.add_argument("--hours", type=int, default=48, help="Hours to simulate in data-driven mode")
    parser.add_argument("--seconds", type=int, default=6, help="Seconds/steps to simulate in event-driven mode")
    parser.add_argument("--limit", type=int, default=None, help="Optional per-template instance limit")
    parser.add_argument("--save-every", type=int, default=1, help="Sampling period for the generated runtime")
    parser.add_argument("--history-vars", nargs="*", default=None, help="Optional variable filters for both histories")
    parser.add_argument("--generated-trace", help="Reuse an existing generated-runtime history CSV")
    parser.add_argument("--pycrop-trace", help="Reuse an existing PyCrop-hosted history CSV")
    parser.add_argument("--var-map", action="append", default=None, help="Map GENERATED=PYCROP when column names differ")
    parser.add_argument("--shift-generated-var", action="append", default=None, help="Optional generated trace shift NAME=INT")
    parser.add_argument("--shift-pycrop-var", action="append", default=None, help="Optional PyCrop trace shift NAME=INT")
    parser.add_argument("--tolerance", type=float, default=1e-9)
    parser.add_argument("--output-dir", default=None, help="Directory for traces and comparison report")
    args = parser.parse_args(argv)

    if not args.input_csv and not args.events_csv and not (args.generated_trace and args.pycrop_trace):
        raise ValueError("Provide either --input-csv, --events-csv, or both --generated-trace and --pycrop-trace.")

    resolved_generated_dir = None
    if args.generated_dir or args.cif:
        resolved_generated_dir = require_generated_package(resolve_generated_dir(args.generated_dir, args.cif, ROOT_DIR), args.cif)
    elif not (args.generated_trace and args.pycrop_trace):
        raise ValueError("Provide --cif so out/generated/<MODEL_NAME> can be used, or pass --generated-dir in low-level mode. If both traces are passed explicitly, no generated package is required.")

    model_name = resolved_generated_dir.name if resolved_generated_dir else 'ad_hoc_trace_compare'
    output_dir = Path(args.output_dir) if args.output_dir else (default_validation_dir(project_root=ROOT_DIR, model_name=model_name) / 'pycrop_comparison')
    output_dir.mkdir(parents=True, exist_ok=True)

    if resolved_generated_dir is not None:
        args.generated_dir = str(resolved_generated_dir)
    generated_trace = Path(args.generated_trace) if args.generated_trace else output_dir / "generated_trace.csv"
    pycrop_trace = Path(args.pycrop_trace) if args.pycrop_trace else output_dir / "pycrop_trace.csv"
    pycrop_summary = output_dir / "pycrop_summary.json"

    root = ROOT_DIR.resolve()
    if not args.generated_trace:
        _run_command(_build_generated_run_command(args, generated_trace), root)
    if not args.pycrop_trace:
        _run_command(_build_pycrop_run_command(args, pycrop_trace, pycrop_summary), root)

    report = compare_traces(
        generated_trace=generated_trace,
        pycrop_trace=pycrop_trace,
        output_dir=output_dir,
        variable_map=_parse_var_maps(args.var_map),
        tolerance=args.tolerance,
        generated_shifts=_parse_shift_maps(args.shift_generated_var),
        pycrop_shifts=_parse_shift_maps(args.shift_pycrop_var),
    )
    report.generated_dir = args.generated_dir
    report.generated_summary = None
    report.pycrop_summary = str(pycrop_summary) if pycrop_summary.exists() else None
    (output_dir / "generated_vs_pycrop_behavior.json").write_text(json.dumps(asdict(report), indent=2))
    print(f"PyCrop comparison report: {output_dir / 'generated_vs_pycrop_behavior.md'}")
    print(f"status: {report.status}")
    print(f"compared cells: {report.compared_cells}")
    print(f"mismatched cells: {report.mismatched_cells}")


if __name__ == "__main__":
    main()
