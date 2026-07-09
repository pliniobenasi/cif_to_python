#!/usr/bin/env python3
from __future__ import annotations

"""
Single generic CLI for the experimental CIF -> modular Python pipeline.

Usage examples:
    python3 scripts/cif_to_python.py model.cif --run --limit 3 --hours 48
    python3 scripts/cif_to_python.py automaton.cif --run --events event1 event2

Project-level runs should prefer scripts/run_pipeline.sh, which fixes the
generated package destination to out/generated/<MODEL_NAME>. The --output
option is kept only for low-level testing and special cases.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

SRC_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SRC_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pipeline.auto_builder import build_engine_from_generated_package, compact_module_summary, run_engine_if_possible
from pipeline.feature_analyzer import analyze_file
from pipeline.python_generator_general import generate_general_from_cif
from pipeline.translation_manifest import write_manifest
from pipeline.generated_artifacts import write_generated_artifacts
from pipeline.escet_validator import validate_with_escet
from pipeline.scenario_inputs import read_event_trace_csv, read_input_series_csv
from pipeline.result_exports import export_history_csv, export_history_json, parse_history_variables
from pipeline.path_defaults import default_generated_dir, default_reports_dir, default_results_dir


def _parse_input_value(raw: str) -> tuple[str, Any]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError("input values must use NAME=VALUE syntax")
    name, value = raw.split("=", 1)
    name = name.strip()
    value = value.strip()
    if not name:
        raise argparse.ArgumentTypeError("input value name cannot be empty")

    if "," in value:
        return name, [float(item.strip()) for item in value.split(",") if item.strip()]
    return name, float(value)


def _write_report(report_dir: Path, report) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "feature_report.json").write_text(json.dumps(report.as_dict(), indent=2))
    (report_dir / "feature_report.md").write_text(
        "# Feature compatibility report\n\n"
        "```text\n"
        f"{report.to_text()}\n"
        "```\n"
    )


def _time_call(timings: list[dict[str, Any]], name: str, func):
    start = time.perf_counter()
    result = func()
    seconds = time.perf_counter() - start
    timings.append({"name": name, "seconds": seconds})
    return result


def _write_timing_report(report_dir: Path, timings: list[dict[str, Any]]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "note": "Timing report for the single code-generation point cif_to_python.py",
        "phases": timings,
        "total_seconds": sum(item["seconds"] for item in timings),
    }
    (report_dir / "pipeline_generation_timing.json").write_text(json.dumps(data, indent=2))

    lines = [
        "Pipeline generation timing",
        "",
        "This report is written by cif_to_python.py, the only entry point that generates modules.",
        "",
    ]
    for item in timings:
        lines.append(f"- {item['name']}: {item['seconds']:.6f} s")
    lines.append("")
    lines.append(f"Total: {data['total_seconds']:.6f} s")
    (report_dir / "pipeline_generation_timing.md").write_text("\n".join(["# Pipeline generation timing", ""] + lines[2:]) + "\n")


def _print_escet_result(result) -> None:
    print(result.to_text())


def _print_generation_summary(output_dir: Path, report) -> None:
    print(f"Generated package: {output_dir}")
    print(f"Supported by current pipeline: {report.supported}")
    print("Dynamic automata/templates:", ", ".join(report.dynamic_automata) or "none")
    print("Algebraic/input automata/templates:", ", ".join(report.algebraic_input_automata) or "none")
    if report.instance_counts:
        print("Instance counts:")
        for name, count in sorted(report.instance_counts.items()):
            print(f"  - {name}: {count}")
    if report.warnings:
        print("Warnings:")
        for warning in report.warnings:
            print(f"  - {warning}")


def _print_manifest_summary(manifest) -> None:
    print("Translation manifest:")
    print(f"  valid: {manifest.valid}")
    print(f"  generated dynamic templates: {', '.join(manifest.dynamic_templates) or 'none'}")
    print(f"  generated input templates: {', '.join(manifest.algebraic_input_templates) or 'none'}")
    print(f"  resolved bindings: {manifest.resolved_bindings_count}")
    if manifest.validation_errors:
        print("  validation errors:")
        for error in manifest.validation_errors:
            print(f"    - {error}")


def _print_run_summary(run_result: dict[str, Any], build_result) -> None:
    print()
    print("Run summary")
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
            location = variables.get("location")
            prefix = f"step={item.get('step')} target={item.get('target')} " if run_result["mode"] == "event-trace" else ""
            print(f"{prefix}{item['event']}: fired={item['fired']} location={location}")
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Generic CIF -> modular Python pipeline")
    parser.add_argument("cif", help="Input CIF file")
    parser.add_argument("--output", "-o", default=None, help="Output generated Python package directory (default: out/generated/<CIF stem>)")
    parser.add_argument("--analyze-only", action="store_true", help="Only analyze the CIF file, do not generate code")
    parser.add_argument("--run", action="store_true", help="Run the generated model after generation when possible")
    parser.add_argument("--limit", type=int, default=None, help="Limit instantiated modules per template for execution")
    parser.add_argument("--hours", type=int, default=None, help="Input-module time horizon for step-driven simulations")
    parser.add_argument("--save-every", type=int, default=1, help="History sampling frequency")
    parser.add_argument("--events", nargs="*", default=None, help="Manual events for event-driven models without input modules")
    parser.add_argument("--events-csv", default=None, help="CSV event trace with columns such as step,event,target")
    parser.add_argument("--input-csv", default=None, help="CSV data trace that overrides generated input-module numeric series")
    parser.add_argument("--input", action="append", type=_parse_input_value, default=[], help="Input override NAME=VALUE or NAME=v1,v2,...")
    parser.add_argument("--history-csv", default=None, help="Write engine history to a CSV file after --run")
    parser.add_argument("--history-json", default=None, help="Write engine history to a JSON file after --run")
    parser.add_argument("--history-vars", nargs="*", default=None, help="Optional variable-name filters for history export")
    parser.add_argument("--json-report", action="store_true", help="Print feature report as JSON")
    parser.add_argument("--strict", action="store_true", help="Fail also on warnings, not only unsupported features")
    parser.add_argument("--escet-check", action="store_true", help="Run external ESCET validation pre-check before generation")
    parser.add_argument("--escet-cmd", default=None, help="ESCET command template, e.g. cif2cif {cif_abs} /tmp/out.cif")
    parser.add_argument("--require-escet", action="store_true", help="Fail if ESCET validation is skipped or fails")
    parser.add_argument("--escet-timeout", type=int, default=60, help="ESCET validation timeout in seconds")
    args = parser.parse_args()

    cif_path = Path(args.cif)
    output_dir = Path(args.output) if args.output else default_generated_dir(cif_path, PROJECT_ROOT)
    report_dir = default_reports_dir(cif_path=cif_path, project_root=PROJECT_ROOT)
    timings: list[dict[str, Any]] = []

    if args.escet_check or args.escet_cmd or args.require_escet:
        escet_result = _time_call(
            timings,
            "escet_validation",
            lambda: validate_with_escet(
                cif_path,
                command_template=args.escet_cmd,
                timeout=args.escet_timeout,
                required=args.require_escet,
            ),
        )
        _print_escet_result(escet_result)
        if escet_result.status == "failed":
            raise SystemExit("ESCET validation pre-check failed.")

    report = _time_call(timings, "feature_analysis", lambda: analyze_file(cif_path))

    if args.json_report:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(report.to_text())

    if args.analyze_only:
        return

    if not report.supported:
        raise SystemExit("Input CIF is outside the currently supported subset.")

    if args.strict and report.warnings:
        raise SystemExit("Input CIF produced warnings and --strict was enabled.")

    report = _time_call(timings, "code_generation", lambda: generate_general_from_cif(cif_path, output_dir))
    _write_report(report_dir, report)
    _print_generation_summary(output_dir, report)

    manifest = _time_call(timings, "translation_manifest", lambda: write_manifest(cif_path, output_dir, report=report, report_dir=report_dir))
    _print_manifest_summary(manifest)
    print(f'Report directory: {report_dir}')

    artifacts = _time_call(timings, "generated_artifacts", lambda: write_generated_artifacts(cif_path, output_dir, pipeline_root=PROJECT_ROOT / "src"))
    print("Generated usability artifacts:")
    print(f"  source CIF copy: {artifacts['source_cif']}")
    print(f"  runner: {artifacts['runner']}")
    print(f"  README: {artifacts['readme']}")

    _write_timing_report(report_dir, timings)
    print(f"Timing report: {output_dir / 'pipeline_generation_timing.md'}")

    if not manifest.valid:
        raise SystemExit("Generated package did not pass manifest validation.")

    if args.run:
        input_values: dict[str, Any] = {}
        input_csv_rows: int | None = None
        if args.input_csv:
            csv_values, input_csv_rows = read_input_series_csv(args.input_csv)
            input_values.update(csv_values)

        input_values.update(dict(args.input))
        hours = args.hours if args.hours is not None else (input_csv_rows or 48)
        event_trace = read_event_trace_csv(args.events_csv) if args.events_csv else None

        build_result = build_engine_from_generated_package(
            output_dir,
            cif_path=cif_path,
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

        _print_run_summary(run_result, build_result)


if __name__ == "__main__":
    main()
