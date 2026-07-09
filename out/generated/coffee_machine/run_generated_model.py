#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any


PACKAGE_DIR = Path(__file__).resolve().parent
BAKED_PIPELINE_ROOT = Path("/home/bena/GitHub_PB/cif_to_python/src")

candidate_roots = [
    Path.cwd(),
    PACKAGE_DIR.parent,
    PACKAGE_DIR.parents[2] if len(PACKAGE_DIR.parents) > 2 else PACKAGE_DIR.parent,
    BAKED_PIPELINE_ROOT,
]

for candidate in candidate_roots:
    candidate = candidate.resolve()

    # Case 1: candidate is the project root.
    if (candidate / "src" / "pipeline" / "auto_builder.py").exists() and (candidate / "src" / "pipeline" / "core").exists():
        PIPELINE_ROOT = candidate / "src"
        break

    # Case 2: candidate is the src directory itself.
    if (candidate / "pipeline" / "auto_builder.py").exists() and (candidate / "pipeline" / "core").exists() and candidate.name == "src":
        PIPELINE_ROOT = candidate
        break

    # Case 3: candidate is the pipeline package directory itself.
    if (candidate / "auto_builder.py").exists() and (candidate / "core").exists() and candidate.name == "pipeline":
        PIPELINE_ROOT = candidate.parent
        break
else:
    raise SystemExit(
        "Cannot locate CIF -> Python pipeline support files. "
        "Run from the pipeline root or regenerate this package."
    )

if str(PIPELINE_ROOT) not in sys.path:
    sys.path.insert(0, str(PIPELINE_ROOT))


from pipeline.auto_builder import build_engine_from_generated_package, compact_module_summary, run_engine_if_possible
from pipeline.scenario_inputs import read_event_trace_csv, read_input_series_csv
from pipeline.result_exports import export_history_csv, export_history_json, parse_history_variables


def _parse_input_value(raw: str) -> tuple[str, Any]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError("input values must use NAME=VALUE syntax")

    name, value = raw.split("=", 1)
    name = name.strip()
    value = value.strip()

    if "," in value:
        return name, [float(item.strip()) for item in value.split(",") if item.strip()]

    return name, float(value)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run this generated CIF -> Python package."
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--hours", type=int, default=None)
    parser.add_argument("--save-every", type=int, default=1)
    parser.add_argument("--events", nargs="*", default=None)
    parser.add_argument(
        "--events-csv",
        default=None,
        help="CSV event trace with columns such as step,event,target",
    )
    parser.add_argument(
        "--input-csv",
        default=None,
        help="CSV data trace that overrides generated input-module numeric series",
    )
    parser.add_argument(
        "--input",
        action="append",
        type=_parse_input_value,
        default=[],
        help="Input override NAME=VALUE or NAME=v1,v2,...",
    )
    parser.add_argument(
        "--history-csv",
        default=None,
        help="Write engine history to a CSV file after the run",
    )
    parser.add_argument(
        "--history-json",
        default=None,
        help="Write engine history to a JSON file after the run",
    )
    parser.add_argument(
        "--history-vars",
        nargs="*",
        default=None,
        help="Optional variable-name filters for history export, e.g. N lai w or Nodes_0_N,LAI_0_lai",
    )
    args = parser.parse_args()

    source_cif = PACKAGE_DIR / "source_model.cif"

    input_values: dict[str, Any] = {}
    input_csv_rows: int | None = None
    if args.input_csv:
        csv_values, input_csv_rows = read_input_series_csv(args.input_csv)
        input_values.update(csv_values)

    input_values.update(dict(args.input))
    hours = args.hours if args.hours is not None else (input_csv_rows or 48)

    event_trace = read_event_trace_csv(args.events_csv) if args.events_csv else None

    build_result = build_engine_from_generated_package(
        PACKAGE_DIR,
        cif_path=source_cif,
        limit=args.limit,
        hours=hours,
        input_values=input_values,
    )

    run_result = run_engine_if_possible(
        build_result,
        events=args.events,
        event_trace=event_trace,
        save_every=args.save_every,
    )

    history_variables = parse_history_variables(args.history_vars)
    history = build_result.engine.get_results()

    if args.history_csv:
        path = export_history_csv(history, args.history_csv, variables=history_variables)
        print(f"history CSV: {path}")

    if args.history_json:
        path = export_history_json(history, args.history_json, variables=history_variables)
        print(f"history JSON: {path}")

    print("Generated package run summary")
    print(f"package: {PACKAGE_DIR}")
    print(f"source CIF: {source_cif}")
    print(f"mode: {run_result['mode']}")
    print(f"input modules: {build_result.input_modules}")
    print(f"dynamic templates: {build_result.dynamic_templates}")
    print(f"dynamic modules instantiated: {len(build_result.dynamic_modules)}")
    print(f"execution order sample: {build_result.execution_order[:10]}")
    print(f"resolved CIF bindings: {len(getattr(build_result.engine, 'ir_bindings', []))}")
    print(f"global input bindings: {len(getattr(build_result.engine, 'global_input_bindings', []))}")

    if run_result["mode"] in {"event-driven", "event-trace"}:
        for item in run_result["events"]:
            variables = item["variables"]
            prefix = f"step={item.get('step')} target={item.get('target')} " if run_result["mode"] == "event-trace" else ""
            print(
                f"{prefix}{item['event']}: "
                f"fired={item['fired']} "
                f"location={variables.get('location')}"
            )
        return

    if run_result["mode"] == "step-driven":
        print(f"steps: {run_result['steps']}")
        print("final module snapshots:")
        for item in compact_module_summary(build_result.engine, max_modules=5):
            variables = item["variables"]
            compact = {key: variables[key] for key in list(variables.keys())[:8]}
            print(f"  - {item['module']}: {compact}")
        return

    print(run_result.get("reason", "No run performed."))


if __name__ == "__main__":
    main()
