#!/usr/bin/env python3
from __future__ import annotations

"""
Compare generated Python simulator behavior with an ESCET reference trace.

The script compares behavior traces, not source code.

The ESCET reference trace must be generated beforehand, typically by running
your local ESCET/cifsim workflow manually and exporting a CSV that can be
compared with the generated Python runner history.
"""

import argparse
import csv
import json
import math
import shutil
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


@dataclass
class ComparedCell:
    sample: int
    variable: str
    generated_value: str
    escet_value: str
    match: bool
    abs_error: float | None = None


@dataclass
class BehaviorComparisonReport:
    cif: str
    generated_dir: str
    output_dir: str
    generated_trace: str
    escet_trace: str | None
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
            raise ValueError(f"Invalid --var-map item: {item!r}. Expected GENERATED=ESCET")
        generated, escet = item.split("=", 1)
        generated = generated.strip()
        escet = escet.strip()
        if not generated or not escet:
            raise ValueError(f"Invalid --var-map item: {item!r}. Expected GENERATED=ESCET")
        result[generated] = escet
    return result


def _parse_shift_maps(raw_maps: list[str] | None) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in raw_maps or []:
        if "=" not in item:
            raise ValueError(f"Invalid --shift-generated-var item: {item!r}. Expected GENERATED=INTEGER_SHIFT")
        generated, shift = item.split("=", 1)
        generated = generated.strip()
        shift = shift.strip()
        if not generated or not shift:
            raise ValueError(f"Invalid --shift-generated-var item: {item!r}. Expected GENERATED=INTEGER_SHIFT")
        try:
            result[generated] = int(shift)
        except ValueError as exc:
            raise ValueError(
                f"Invalid --shift-generated-var item: {item!r}. Shift must be an integer."
            ) from exc
    return result


def _excluded_columns() -> set[str]:
    return {
        "sample",
        "step",
        "time",
        "timestep",
        "event",
        "target",
        "fired",
    }


def _infer_column_map(generated_rows: list[dict[str, str]], escet_rows: list[dict[str, str]]) -> dict[str, str]:
    if not generated_rows or not escet_rows:
        return {}

    generated_columns = set(generated_rows[0])
    escet_columns = set(escet_rows[0])
    excluded = _excluded_columns()

    common = sorted(
        column
        for column in generated_columns & escet_columns
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


def _values_match(generated: str, escet: str, tolerance: float) -> tuple[bool, float | None]:
    generated_float = _as_float(generated)
    escet_float = _as_float(escet)

    if generated_float is not None and escet_float is not None:
        error = abs(generated_float - escet_float)
        return error <= tolerance, error

    return str(generated) == str(escet), None


def compare_traces(
    generated_trace: str | Path,
    escet_trace: str | Path,
    output_dir: str | Path,
    variable_map: dict[str, str] | None = None,
    tolerance: float = 1e-9,
    generated_shifts: dict[str, int] | None = None,
) -> BehaviorComparisonReport:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_trace = Path(generated_trace)
    escet_trace = Path(escet_trace)

    generated_rows = _read_csv_rows(generated_trace)
    escet_rows = _read_csv_rows(escet_trace)

    variable_map = variable_map or _infer_column_map(generated_rows, escet_rows)
    generated_shifts = generated_shifts or {}
    if not variable_map:
        raise ValueError(
            "No comparable variables found. Use --var-map GENERATED=ESCET to define mappings."
        )

    sample_count = min(len(generated_rows), len(escet_rows))
    compared: list[ComparedCell] = []
    skipped_cells = 0

    for sample_index in range(sample_count):
        escet_row = escet_rows[sample_index]

        for generated_column, escet_column in variable_map.items():
            shift = generated_shifts.get(generated_column, 0)
            generated_index = sample_index + shift
            if generated_index < 0 or generated_index >= len(generated_rows):
                skipped_cells += 1
                continue

            generated_row = generated_rows[generated_index]
            generated_value = generated_row.get(generated_column, "")
            escet_value = escet_row.get(escet_column, "")
            match, abs_error = _values_match(generated_value, escet_value, tolerance)
            compared.append(
                ComparedCell(
                    sample=sample_index,
                    variable=generated_column,
                    generated_value=generated_value,
                    escet_value=escet_value,
                    match=match,
                    abs_error=abs_error,
                )
            )

    matched = sum(1 for item in compared if item.match)
    mismatched = len(compared) - matched
    numeric_errors = [
        item.abs_error
        for item in compared
        if item.abs_error is not None
    ]

    report = BehaviorComparisonReport(
        cif="",
        generated_dir="",
        output_dir=str(output_dir),
        generated_trace=str(generated_trace),
        escet_trace=str(escet_trace),
        compared_variables=list(variable_map),
        compared_cells=len(compared),
        matched_cells=matched,
        mismatched_cells=mismatched,
        max_abs_error=max(numeric_errors) if numeric_errors else None,
        status="pass" if mismatched == 0 else "fail",
        notes=[
            f"Compared {sample_count} aligned samples.",
            "Comparison is behavioral trace comparison, not source-code comparison.",
        ],
    )

    if generated_shifts:
        report.notes.append(
            "Generated trace shifts applied: "
            + ", ".join(f"{name}={shift}" for name, shift in sorted(generated_shifts.items()))
        )
    if skipped_cells:
        report.notes.append(f"Skipped {skipped_cells} shifted cells outside the available sample range.")

    _write_comparison_outputs(report, compared, output_dir)
    return report


def _write_comparison_outputs(
    report: BehaviorComparisonReport,
    compared: list[ComparedCell],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "escet_vs_generated_behavior.json").write_text(
        json.dumps(
            {
                "report": asdict(report),
                "cells": [asdict(item) for item in compared],
            },
            indent=2,
        )
    )

    with (output_dir / "escet_vs_generated_behavior.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "sample",
                "variable",
                "generated_value",
                "escet_value",
                "match",
                "abs_error",
            ],
        )
        writer.writeheader()
        for item in compared:
            writer.writerow(asdict(item))

    lines = [
        "# ESCET vs generated behavior comparison",
        "",
        f"- status: **{report.status.upper()}**",
        f"- generated trace: `{report.generated_trace}`",
        f"- ESCET trace: `{report.escet_trace}`",
        f"- compared variables: `{', '.join(report.compared_variables)}`",
        f"- compared cells: `{report.compared_cells}`",
        f"- matched cells: `{report.matched_cells}`",
        f"- mismatched cells: `{report.mismatched_cells}`",
        f"- max absolute error: `{report.max_abs_error}`",
        "",
        "## Notes",
        "",
    ]

    for note in report.notes:
        lines.append(f"- {note}")

    if report.mismatched_cells:
        lines.extend(["", "## First mismatches", ""])
        for item in compared:
            if not item.match:
                lines.append(
                    f"- sample `{item.sample}`, variable `{item.variable}`: "
                    f"generated=`{item.generated_value}`, escet=`{item.escet_value}`, "
                    f"abs_error=`{item.abs_error}`"
                )
                if len(lines) > 40:
                    break

    (output_dir / "escet_vs_generated_behavior.md").write_text("\n".join(lines) + "\n")


def _run_generated_trace(
    generated_dir: Path,
    output_dir: Path,
    events_csv: str | None,
    input_csv: str | None,
    limit: int | None,
    hours: int | None,
    save_every: int,
    history_vars: list[str] | None,
) -> Path:
    generated_trace = output_dir / "generated_trace.csv"

    cmd = [
        "python3",
        str(generated_dir / "run_generated_model.py"),
        "--save-every",
        str(save_every),
        "--history-csv",
        str(generated_trace),
    ]

    if events_csv:
        cmd.extend(["--events-csv", events_csv])

    if input_csv:
        cmd.extend(["--input-csv", input_csv])

    if limit is not None:
        cmd.extend(["--limit", str(limit)])

    if hours is not None:
        cmd.extend(["--hours", str(hours)])

    if history_vars:
        cmd.append("--history-vars")
        cmd.extend(history_vars)

    proc = subprocess.run(
        cmd,
        cwd=ROOT_DIR,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=600,
    )

    if proc.returncode != 0:
        raise RuntimeError(
            "Generated runner failed while producing the generated trace:\n"
            + proc.stdout
        )

    return generated_trace


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare generated Python behavior with an ESCET reference trace."
    )
    parser.add_argument("--cif", required=True)
    parser.add_argument("--generated-dir", default=None, help="Generated package directory (default: out/generated/<CIF stem>)")
    parser.add_argument('--output-dir', default=None)

    scenario = parser.add_mutually_exclusive_group()
    scenario.add_argument("--events-csv", default=None)
    scenario.add_argument("--input-csv", default=None)

    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--hours", type=int, default=None)
    parser.add_argument("--save-every", type=int, default=1)
    parser.add_argument("--history-vars", nargs="*", default=None)

    parser.add_argument(
        "--escet-trace",
        required=True,
        help="CSV trace exported from ESCET and aligned with the comparison scenario.",
    )
    parser.add_argument(
        "--var-map",
        action="append",
        default=[],
        help="Map generated history column to ESCET trace column: GENERATED=ESCET",
    )
    parser.add_argument("--tolerance", type=float, default=1e-9)
    parser.add_argument(
        "--shift-generated-var",
        action="append",
        default=[],
        help="Optional generated-trace sample shift for specific variables: GENERATED=INTEGER_SHIFT",
    )

    args = parser.parse_args()

    cif = Path(args.cif)
    generated_dir = require_generated_package(resolve_generated_dir(args.generated_dir, args.cif, ROOT_DIR), args.cif)
    model_name = generated_dir.name
    output_dir = Path(args.output_dir) if args.output_dir else (default_validation_dir(project_root=ROOT_DIR, model_name=model_name) / 'escet_comparison')
    output_dir.mkdir(parents=True, exist_ok=True)

    history_vars = _split_csv_values(args.history_vars)
    variable_map = _parse_var_maps(args.var_map)
    generated_shifts = _parse_shift_maps(args.shift_generated_var)

    generated_trace = _run_generated_trace(
        generated_dir=generated_dir,
        output_dir=output_dir,
        events_csv=args.events_csv,
        input_csv=args.input_csv,
        limit=args.limit,
        hours=args.hours,
        save_every=args.save_every,
        history_vars=history_vars,
    )

    escet_trace = output_dir / "escet_trace.csv"
    source_escet_trace = Path(args.escet_trace)
    if not source_escet_trace.exists():
        raise FileNotFoundError(
            f"ESCET trace CSV not found: {source_escet_trace}. "
            "Generate it first with your local ESCET workflow and then pass it via --escet-trace."
        )
    shutil.copy(source_escet_trace, escet_trace)

    report = compare_traces(
        generated_trace=generated_trace,
        escet_trace=escet_trace,
        output_dir=output_dir,
        variable_map=variable_map or None,
        tolerance=args.tolerance,
        generated_shifts=generated_shifts,
    )

    report.cif = str(cif)
    report.generated_dir = str(generated_dir)
    _write_comparison_outputs(
        report,
        [
            ComparedCell(**row)
            for row in json.loads((output_dir / "escet_vs_generated_behavior.json").read_text())["cells"]
        ],
        output_dir,
    )

    print(f"ESCET comparison report: {output_dir / 'escet_vs_generated_behavior.md'}")
    print(f"status: {report.status}")
    print(f"compared cells: {report.compared_cells}")
    print(f"mismatched cells: {report.mismatched_cells}")


if __name__ == "__main__":
    main()
