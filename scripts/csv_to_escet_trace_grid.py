#!/usr/bin/env python3
from __future__ import annotations

"""
Create an ESCET trace-input file for Grid/Grid_semplified scenarios.

Purpose
-------
The generated Python runtime for the Grid case uses a step-driven policy:
- one logical CSV row per logical simulation step;
- at most one automatic transition per module per step;
- module execution order Nodes -> LAI -> Biomass.

This helper generates a `.trace` file that is intentionally aligned with that
runtime policy, so that ESCET can be used as a behavioral reference for the
same logical scenario. The generated trace uses ESCET trace-input *implicit*
time mode, letting ESCET choose the least amount of time passage needed before
each event.

The produced trace is not meant to enumerate every possible ESCET/CIF behavior.
It is a practical trace recipe for comparing the current generated Python target
with an ESCET run on the same Grid-like model.
"""

import argparse
import csv
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pipeline.path_defaults import default_validation_dir

DEFAULT_CIF = ROOT_DIR / "examples" / "Grid_semplified.cif"
DEFAULT_INPUT_CSV = ROOT_DIR / "examples" / "grid_weather_input.csv"

INPUT_COLUMNS = ["T_in", "Rad", "T_mean", "T_daytime_mean"]


@dataclass
class LogicalStepPlan:
    sample_index: int
    logical_step: int | None
    input_row: int
    biomass_event: str | None
    node_day_count: int
    lai_day_count: int
    biomass_event_count: int
    command_rows_after_sample: int


@dataclass
class TracePlan:
    cif: str
    input_csv: str
    output_trace: str
    hours: int
    limit: int
    initial_inputs: dict[str, str]
    recommended_cifsim_init_args: list[str]
    sample_row_indexes: list[int]
    compared_templates: dict[str, int]
    recommended_var_maps: dict[str, str]
    logical_steps: list[LogicalStepPlan]


def _read_input_rows(path: str | Path) -> list[dict[str, str]]:
    path = Path(path)
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {path}")
        rows = [dict(row) for row in reader]

    if not rows:
        raise ValueError(f"Input CSV contains no rows: {path}")

    missing = [column for column in INPUT_COLUMNS if column not in rows[0]]
    if missing:
        raise ValueError(
            f"Input CSV must contain columns {INPUT_COLUMNS}. Missing: {missing}"
        )
    return rows


def _find_instance_names(cif_text: str, template_name: str) -> list[str]:
    pattern = re.compile(rf"^\s*([A-Za-z_]\w*)\s*:\s*{re.escape(template_name)}\s*\(", re.MULTILINE)
    names = pattern.findall(cif_text)

    def sort_key(name: str) -> tuple[int, str]:
        match = re.search(r"_(\d+)$", name)
        return (int(match.group(1)) if match else 10**9, name)

    names.sort(key=sort_key)
    return names


def _literal_value(raw: str) -> str:
    raw = str(raw).strip()
    if raw == "":
        raise ValueError("Empty input value is not allowed in ESCET trace generation")
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"Invalid numeric value for ESCET trace: {raw!r}") from exc

    # ESCET input variables declared as `real` reject integer-looking literals like
    # `310` in trace assignments. Keep a stable representation, but force a decimal
    # point for whole numbers such as 300 -> 300.0.
    literal = format(value, ".15g")
    lower = literal.lower()
    if "." not in literal and "e" not in lower:
        literal = f"{literal}.0"
    return literal


def _write_inputs(lines: list[str], row: dict[str, str]) -> int:
    for column in INPUT_COLUMNS:
        lines.append(f"input {column} = {_literal_value(row[column])}")
    return len(INPUT_COLUMNS)


def _node_day_due(step_number: int) -> bool:
    return step_number % 24 == 0


def _lai_day_due(step_number: int) -> bool:
    return step_number % 24 == 0


def _biomass_events_for_step(step_number: int) -> list[str]:
    """
    Return the Biomass automatic events for one logical step.

    ESCET/Java semantics show that after a Biomass.day transition the local
    clock ``c`` is *not* reset. As a consequence, the next Biomass.hour can
    become enabled almost immediately and must be allowed in the same logical
    Python step when draining automatic transitions to quiescence.

    With hourly base step ``H`` this yields the repeating pattern:
    - steps 1..23: hour
    - step 24: hour (while Nodes/LAI also perform day)
    - step 25: day + hour
    - repeat every 24 logical hours thereafter
    """
    if step_number > 1 and (step_number - 1) % 24 == 0:
        return ["day", "hour"]
    return ["hour"]


def _emit_events(lines: list[str], module_names: Iterable[str], event_name: str) -> int:
    count = 0
    for module_name in module_names:
        lines.append(f"event {module_name}.{event_name}")
        count += 1
    return count


def build_trace_and_plan(
    cif_path: str | Path,
    input_csv: str | Path,
    output_trace: str | Path,
    hours: int | None = None,
    limit: int | None = None,
) -> tuple[list[str], TracePlan]:
    cif_path = Path(cif_path)
    input_csv = Path(input_csv)
    output_trace = Path(output_trace)

    cif_text = cif_path.read_text()
    rows = _read_input_rows(input_csv)

    hours = len(rows) if hours is None else min(int(hours), len(rows))
    if hours <= 0:
        raise ValueError("hours must be greater than zero")

    nodes = _find_instance_names(cif_text, "Nodes")
    lais = _find_instance_names(cif_text, "LAI")
    biomasses = _find_instance_names(cif_text, "Biomass")

    if not nodes or not lais or not biomasses:
        raise ValueError(
            "Could not detect Nodes/LAI/Biomass instances from the CIF file. "
            "This helper is intended for Grid-like CIF models."
        )

    full_limit = min(len(nodes), len(lais), len(biomasses))
    requested_limit = full_limit if limit is None else min(int(limit), full_limit)
    if requested_limit <= 0:
        raise ValueError("limit must be greater than zero")

    if requested_limit != full_limit:
        raise ValueError(
            "For ESCET execution on a Grid-like CIF, the trace must drive all detected "
            f"instances (expected {full_limit}, got {requested_limit}). "
            "Using only a subset causes deadlock because the omitted automata remain "
            "at the current time boundary waiting for their own transitions. "
            "Use --limit equal to the full instance count or omit --limit."
        )

    limit = full_limit
    nodes = nodes[:limit]
    lais = lais[:limit]
    biomasses = biomasses[:limit]

    lines: list[str] = [
        "# ESCET trace generated to mirror the current generated Python runtime policy",
        "# Grid-like step-driven scenario: inputs per logical step + automatic events in runtime order",
        "# IMPORTANT: initial input values must be provided to cifsim via --init=... options.",
        "# The trace file only changes inputs after initialization has completed.",
        "option strict off",
        "option time implicit",
    ]

    command_rows = 0
    sample_row_indexes = [0]
    logical_steps: list[LogicalStepPlan] = [
        LogicalStepPlan(
            sample_index=0,
            logical_step=None,
            input_row=0,
            biomass_event=None,
            node_day_count=0,
            lai_day_count=0,
            biomass_event_count=0,
            command_rows_after_sample=command_rows,
        )
    ]

    for step_zero_based in range(hours):
        step_number = step_zero_based + 1
        row = rows[step_zero_based]

        lines.append("")
        lines.append(f"# logical step {step_number} using CSV row {step_zero_based}")

        if step_zero_based > 0:
            command_rows += _write_inputs(lines, row)

        # No explicit `time` command is written. In implicit time mode ESCET
        # delays by the least amount necessary to enable the next event from
        # the trace, which matches the current step-driven Python runtime
        # policy better than explicit time mode for this Grid case study.
        node_day_count = 0
        if _node_day_due(step_number):
            node_day_count = _emit_events(lines, nodes, "day")
            command_rows += node_day_count

        lai_day_count = 0
        if _lai_day_due(step_number):
            lai_day_count = _emit_events(lines, lais, "day")
            command_rows += lai_day_count

        biomass_events = _biomass_events_for_step(step_number)
        biomass_event_count = 0
        for biomass_event in biomass_events:
            biomass_event_count += _emit_events(lines, biomasses, biomass_event)
        command_rows += biomass_event_count

        sample_row_indexes.append(command_rows)
        logical_steps.append(
            LogicalStepPlan(
                sample_index=step_number,
                logical_step=step_number,
                input_row=step_zero_based,
                biomass_event="+".join(biomass_events),
                node_day_count=node_day_count,
                lai_day_count=lai_day_count,
                biomass_event_count=biomass_event_count,
                command_rows_after_sample=command_rows,
            )
        )

    initial_inputs = {column: _literal_value(rows[0][column]) for column in INPUT_COLUMNS}

    plan = TracePlan(
        cif=str(cif_path),
        input_csv=str(input_csv),
        output_trace=str(output_trace),
        hours=hours,
        limit=limit,
        initial_inputs=initial_inputs,
        recommended_cifsim_init_args=[f"--init={name}:{value}" for name, value in initial_inputs.items()],
        sample_row_indexes=sample_row_indexes,
        compared_templates={
            "Nodes": limit,
            "LAI": limit,
            "Biomass": limit,
        },
        recommended_var_maps={
            "Greenhouse_Rad": "Rad",
            "Nodes_0_N": "Nodes_0.N",
            "LAI_0_lai": "LAI_0.lai",
            "Biomass_0_w": "Biomass_0.w",
        },
        logical_steps=logical_steps,
    )
    return lines, plan


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate an ESCET .trace file for Grid/Grid_semplified CSV scenarios."
    )
    parser.add_argument("--cif", default=str(DEFAULT_CIF), help="Grid-like CIF file to target")
    parser.add_argument("--input-csv", default=str(DEFAULT_INPUT_CSV), help="Scenario CSV used by the generated Python runner")
    parser.add_argument('--output-trace', default=None, help='Path of the ESCET .trace file to write')
    parser.add_argument("--hours", type=int, default=None, help="Logical steps/hours to export. Defaults to all CSV rows")
    parser.add_argument("--limit", type=int, default=None, help="Number of Nodes/LAI/Biomass instances to include. For ESCET runs this must match the full model size; omit the option to auto-detect it.")
    parser.add_argument(
        "--plan-json",
        default=None,
        help="Optional JSON sidecar. Defaults to OUTPUT_TRACE with .plan.json suffix",
    )
    parser.add_argument(
        "--init-args-file",
        default=None,
        help="Optional text file containing one suggested --init=NAME:VALUE argument per line. Defaults to OUTPUT_TRACE with .init_args.txt suffix",
    )
    args = parser.parse_args()

    output_trace = Path(args.output_trace) if args.output_trace else (default_validation_dir(cif_path=args.cif, project_root=ROOT_DIR) / 'escet_grid' / f'{Path(args.cif).stem}.trace')
    plan_json = Path(args.plan_json) if args.plan_json else output_trace.with_suffix(output_trace.suffix + ".plan.json")
    init_args_file = Path(args.init_args_file) if args.init_args_file else output_trace.with_suffix(output_trace.suffix + ".init_args.txt")

    lines, plan = build_trace_and_plan(
        cif_path=args.cif,
        input_csv=args.input_csv,
        output_trace=output_trace,
        hours=args.hours,
        limit=args.limit,
    )

    output_trace.parent.mkdir(parents=True, exist_ok=True)
    output_trace.write_text("\n".join(lines) + "\n")
    plan_json.write_text(
        json.dumps(
            {
                **asdict(plan),
                "logical_steps": [asdict(item) for item in plan.logical_steps],
            },
            indent=2,
        )
    )
    init_args_file.write_text("\n".join(plan.recommended_cifsim_init_args) + "\n")

    print(f"ESCET trace: {output_trace}")
    print(f"ESCET trace plan: {plan_json}")
    print(f"ESCET init args: {init_args_file}")
    print(f"hours exported: {plan.hours}")
    print(f"instance limit: {plan.limit}")
    print(f"sample row indexes: {plan.sample_row_indexes[:10]}{'...' if len(plan.sample_row_indexes) > 10 else ''}")


if __name__ == "__main__":
    main()
