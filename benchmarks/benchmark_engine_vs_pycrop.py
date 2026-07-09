#!/usr/bin/env python3
"""Benchmark one generated CIF package in the generic runtime and in PyCrop hosting mode.

The script is intentionally a validation/benchmark consumer: it never generates
Python packages. The package must already exist under out/generated/<MODEL_NAME>/
or be supplied explicitly through the low-level --generated-dir option.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pipeline.path_defaults import (
    default_benchmarks_dir,
    resolve_generated_dir,
    require_generated_package,
)


def _project_path(path: str | Path, root: Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else root / p


def _command_for_report(cmd: list[str], root: Path) -> str:
    parts = []
    for item in cmd:
        try:
            path = Path(item)
            if path.is_absolute():
                try:
                    parts.append(str(path.relative_to(root)))
                    continue
                except ValueError:
                    pass
        except Exception:
            pass
        parts.append(item)
    return " ".join(parts)


def _run_command(cmd: list[str], cwd: Path) -> float:
    start = time.perf_counter()
    completed = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    elapsed = time.perf_counter() - start
    if completed.returncode != 0:
        raise RuntimeError(
            "Benchmark command failed.\n"
            f"Command: {_command_for_report(cmd, cwd)}\n"
            f"Exit code: {completed.returncode}\n"
            f"STDOUT:\n{completed.stdout}\n"
            f"STDERR:\n{completed.stderr}"
        )
    return elapsed


def _count_csv_rows(path: Path) -> int:
    with path.open("r", newline="") as f:
        reader = csv.reader(f)
        rows = [row for row in reader if row and any(cell.strip() for cell in row)]
    if not rows:
        return 0
    # All project scenario CSVs currently have headers. Keeping the rule explicit
    # makes the inferred data-driven duration deterministic and easy to explain.
    return max(0, len(rows) - 1)


def _infer_event_seconds(path: Path) -> int:
    with path.open("r", newline="") as f:
        sample = f.read(2048)
        f.seek(0)
        try:
            has_header = csv.Sniffer().has_header(sample)
        except csv.Error:
            has_header = True

        if has_header:
            reader = csv.DictReader(f)
            max_step = -1
            rows = 0
            for row in reader:
                if not row or not any((value or "").strip() for value in row.values()):
                    continue
                rows += 1
                lowered = {str(k).strip().lower(): (v or "").strip() for k, v in row.items() if k is not None}
                for key in ("step", "timestep", "time"):
                    if key in lowered and lowered[key] != "":
                        max_step = max(max_step, int(lowered[key]))
                        break
            return max_step + 1 if max_step >= 0 else rows

        reader = csv.reader(f)
        max_step = -1
        rows = 0
        for row in reader:
            if not row or not any(cell.strip() for cell in row):
                continue
            rows += 1
            try:
                max_step = max(max_step, int(row[0].strip()))
            except (ValueError, IndexError):
                pass
        return max_step + 1 if max_step >= 0 else rows


def _build_commands(args: argparse.Namespace, root: Path) -> tuple[str, Path, list[tuple[str, list[str]]]]:
    cif_path = _project_path(args.cif, root).resolve()
    if cif_path.name == "source_model.cif" and "out/generated" in str(cif_path):
        raise ValueError(
            "Do not pass out/generated/<MODEL_NAME>/source_model.cif as --cif. "
            "Use the original CIF path, for example examples/coffee_machine.cif."
        )

    generated_dir = require_generated_package(
        resolve_generated_dir(args.generated_dir, cif_path, root),
        cif_path,
    ).resolve()
    model_name = cif_path.stem

    pycrop_root = _project_path(args.pycrop_root, root).resolve()
    if not pycrop_root.exists():
        raise FileNotFoundError(
            f"PyCrop root not found: {pycrop_root}\n"
            "Pass --pycrop-root or keep the default ._pycrop/PyCrop_restrict directory."
        )

    if bool(args.events_csv) == bool(args.input_csv):
        raise ValueError("Choose exactly one scenario type: --events-csv or --input-csv.")

    common_generated_cmd = [sys.executable, str(generated_dir / "run_generated_model.py")]
    common_pycrop_cmd = [
        sys.executable,
        str(root / "scripts" / "pycrop_host_runner.py"),
        "--pycrop-root",
        str(pycrop_root),
        "--cif",
        str(cif_path),
    ]

    if args.limit is not None:
        common_generated_cmd += ["--limit", str(args.limit)]
        common_pycrop_cmd += ["--limit", str(args.limit)]

    if args.events_csv:
        events_csv = _project_path(args.events_csv, root).resolve()
        if not events_csv.exists():
            raise FileNotFoundError(f"Events CSV not found: {events_csv}")
        seconds = args.seconds if args.seconds is not None else max(1, _infer_event_seconds(events_csv))
        mode = "event-trace"
        generated_cmd = common_generated_cmd + ["--events-csv", str(events_csv)]
        pycrop_cmd = common_pycrop_cmd + ["--events-csv", str(events_csv), "--seconds", str(seconds)]
    else:
        input_csv = _project_path(args.input_csv, root).resolve()
        if not input_csv.exists():
            raise FileNotFoundError(f"Input CSV not found: {input_csv}")
        hours = args.hours if args.hours is not None else max(1, _count_csv_rows(input_csv))
        mode = "data-driven"
        generated_cmd = common_generated_cmd + ["--input-csv", str(input_csv), "--hours", str(hours)]
        pycrop_cmd = common_pycrop_cmd + ["--input-csv", str(input_csv), "--hours", str(hours)]

    commands = [
        ("generic_runtime", generated_cmd),
        ("pycrop_host", pycrop_cmd),
    ]
    return mode, cif_path, commands


def benchmark(args: argparse.Namespace, root: Path) -> tuple[str, Path, list[dict[str, Any]]]:
    mode, cif_path, commands = _build_commands(args, root)
    rows: list[dict[str, Any]] = []
    for runner, cmd in commands:
        times = [_run_command(cmd, root) for _ in range(args.runs)]
        rows.append(
            {
                "model": cif_path.stem,
                "mode": mode,
                "runner": runner,
                "runs": args.runs,
                "mean_seconds": sum(times) / len(times),
                "median_seconds": statistics.median(times),
                "min_seconds": min(times),
                "max_seconds": max(times),
                "command": _command_for_report(cmd, root),
            }
        )
    return mode, cif_path, rows


def _write_markdown(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Generic runtime vs PyCrop hosting benchmark",
        "",
        "This benchmark measures end-to-end CLI execution time for one selected CIF scenario.",
        "It does not translate the CIF model and it does not measure semantic correctness.",
        "",
        "| Model | Mode | Runner | Runs | Mean (s) | Median (s) | Min (s) | Max (s) |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['model']} | {row['mode']} | {row['runner']} | {row['runs']} | "
            f"{row['mean_seconds']:.6f} | {row['median_seconds']:.6f} | "
            f"{row['min_seconds']:.6f} | {row['max_seconds']:.6f} |"
        )
    lines.extend(["", "## Commands", ""])
    for row in rows:
        lines.append(f"### {row['runner']}")
        lines.append("")
        lines.append("```bash")
        lines.append(row["command"])
        lines.append("```")
        lines.append("")
    path.write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark one generated CIF package in the generic runtime vs PyCrop hosting mode."
    )
    parser.add_argument("--cif", required=True, help="Original CIF model path. Used to resolve out/generated/<MODEL_NAME>/.")
    parser.add_argument("--events-csv", help="Event trace CSV scenario for event-driven models")
    parser.add_argument("--input-csv", help="Numeric input CSV scenario for data-driven models")
    parser.add_argument("--hours", type=int, default=None, help="Hours for data-driven mode. Default: number of data rows in --input-csv")
    parser.add_argument("--seconds", type=int, default=None, help="Seconds/steps for event-trace PyCrop mode. Default: inferred from --events-csv")
    parser.add_argument("--limit", type=int, default=None, help="Optional per-template instance limit")
    parser.add_argument("--runs", type=int, default=3, help="Number of repetitions per runner")
    parser.add_argument("--pycrop-root", default="._pycrop/PyCrop_restrict", help="Path to extracted PyCrop_restrict root")
    parser.add_argument("--generated-dir", default=None, help="Low-level override for generated package directory. Default: out/generated/<CIF stem>")
    parser.add_argument("--output-dir", default=None, help="Low-level override for benchmark output directory. Default: out/outputs/<MODEL_NAME>/benchmarks/engine_vs_pycrop")
    args = parser.parse_args()

    if args.runs < 1:
        raise ValueError("--runs must be >= 1")

    root = Path.cwd().resolve()
    _, cif_path, rows = benchmark(args, root)

    output_dir = Path(args.output_dir).resolve() if args.output_dir else default_benchmarks_dir(cif_path=cif_path, project_root=root) / "engine_vs_pycrop"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "engine_vs_pycrop_benchmark.csv"
    json_path = output_dir / "engine_vs_pycrop_benchmark.json"
    md_path = output_dir / "engine_vs_pycrop_benchmark.md"

    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps(rows, indent=2))
    _write_markdown(md_path, rows)

    print(json.dumps({"csv": str(csv_path), "json": str(json_path), "markdown": str(md_path), "rows": rows}, indent=2))


if __name__ == "__main__":
    main()
