from __future__ import annotations

"""
Behavioral validation for the generated Grid/TOMGRO pipeline.

This script does not validate CIF syntax. It validates that the generated
Python modular simulator behaves coherently on the Grid/TOMGRO model:

- generated instance counts are complete;
- generated execution order respects dependency flow;
- Greenhouse input values are propagated to plant modules;
- Nodes, LAI and Biomass produce finite and qualitatively coherent values.
"""

from dataclasses import asdict, dataclass, field
import argparse

import csv
import json
import math
from pathlib import Path
import sys
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pipeline.path_defaults import resolve_generated_dir, require_generated_package, default_validation_dir, default_reports_dir

from pipeline.auto_builder import build_engine_from_generated_package, run_engine_if_possible


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class GridValidationResult:
    cif_path: str
    generated_dir: str
    limit: int
    hours: int
    checks: list[CheckResult]
    metrics: dict[str, Any]

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    def as_dict(self) -> dict[str, Any]:
        return {
            "cif_path": self.cif_path,
            "generated_dir": self.generated_dir,
            "limit": self.limit,
            "hours": self.hours,
            "passed": self.passed,
            "checks": [asdict(check) for check in self.checks],
            "metrics": self.metrics,
        }


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def _last(results: dict[str, list[Any]], key: str) -> Any:
    values = results.get(key, [])
    return values[-1] if values else None


def _first(results: dict[str, list[Any]], key: str) -> Any:
    values = results.get(key, [])
    return values[0] if values else None


def _series_delta(results: dict[str, list[Any]], key: str) -> float | None:
    values = results.get(key, [])
    if len(values) < 2:
        return None
    if not _finite(values[0]) or not _finite(values[-1]):
        return None
    return float(values[-1]) - float(values[0])


def _load_existing_manifest(generated_dir: Path) -> dict[str, Any]:
    report_dir = default_reports_dir(generated_dir=generated_dir, project_root=ROOT_DIR)
    manifest_path = report_dir / "translation_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            "translation_manifest.json not found. "
            "Generate the package once with scripts/cif_to_python.py before running validation."
        )
    return json.loads(manifest_path.read_text())


def _write_csv_summary(path: Path, results: dict[str, list[Any]], limit: int) -> None:
    fields = [
        "index",
        "nodes_initial",
        "nodes_final",
        "lai_initial",
        "lai_final",
        "biomass_initial",
        "biomass_final",
        "greenhouse_t_mean_initial",
        "greenhouse_rad_initial",
    ]

    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()

        for index in range(limit):
            writer.writerow(
                {
                    "index": index,
                    "nodes_initial": _first(results, f"Nodes_{index}_N"),
                    "nodes_final": _last(results, f"Nodes_{index}_N"),
                    "lai_initial": _first(results, f"LAI_{index}_lai"),
                    "lai_final": _last(results, f"LAI_{index}_lai"),
                    "biomass_initial": _first(results, f"Biomass_{index}_w"),
                    "biomass_final": _last(results, f"Biomass_{index}_w"),
                    "greenhouse_t_mean_initial": _first(results, f"Greenhouse_T_sparse_mean_{index}"),
                    "greenhouse_rad_initial": _first(results, f"Greenhouse_Rad_input_{index}"),
                }
            )


def _markdown_report(result: GridValidationResult) -> str:
    lines = [
        "# Grid.cif behavioral validation report",
        "",
        f"Overall result: **{'PASS' if result.passed else 'FAIL'}**",
        "",
        f"- CIF: `{result.cif_path}`",
        f"- Generated package: `{result.generated_dir}`",
        f"- Simulated instances per template: `{result.limit}`",
        f"- Simulated steps/hours: `{result.hours}`",
        "",
        "## Checks",
        "",
        "| Check | Result | Details |",
        "|---|---:|---|",
    ]

    for check in result.checks:
        status = "PASS" if check.passed else "FAIL"
        details = ", ".join(f"{key}={value}" for key, value in check.details.items())
        lines.append(f"| `{check.name}` | {status} | {details} |")

    lines.extend(
        [
            "",
            "## Key metrics",
            "",
            "```json",
            json.dumps(result.metrics, indent=2),
            "```",
            "",
            "## Interpretation",
            "",
            "This validation is behavioral, not a proof of full biological correctness.",
            "It checks that the generated modular Python simulator preserves the expected dependency flow",
            "and produces coherent TOMGRO-style trends for a limited Grid.cif execution.",
        ]
    )

    return "\n".join(lines)


def validate_grid_behavior(
    cif_path: str | Path,
    generated_dir: str | Path,
    output_dir: str | Path,
    limit: int = 5,
    hours: int = 72,
    save_every: int = 1,
) -> GridValidationResult:
    cif_path = Path(cif_path)
    generated_dir = Path(generated_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_dir = require_generated_package(generated_dir, cif_path)

    manifest = _load_existing_manifest(generated_dir)

    build = build_engine_from_generated_package(
        generated_dir,
        cif_path=cif_path,
        limit=limit,
        hours=hours,
    )
    run_result = run_engine_if_possible(build, save_every=save_every)
    results = build.engine.get_results()

    checks: list[CheckResult] = []

    checks.append(
        CheckResult(
            "manifest_valid",
            bool(manifest.get('valid', False)),
            {
                "dynamic_templates": ",".join(manifest.get("dynamic_templates", [])),
                "input_templates": ",".join(manifest.get("algebraic_input_templates", [])),
                "resolved_bindings": manifest.get('resolved_bindings_count', 0),
            },
        )
    )

    expected_counts = {"Nodes": 1600, "LAI": 1600, "Biomass": 1600, "Greenhouse_template": 1}
    counts_ok = all(manifest.get('expected_instance_counts', {}).get(key) == value for key, value in expected_counts.items())
    checks.append(
        CheckResult(
            "grid_instance_counts",
            counts_ok,
            {key: manifest.get('expected_instance_counts', {}).get(key) for key in expected_counts},
        )
    )

    order = build.execution_order
    order_ok = (
        all(name.startswith("Nodes_") for name in order[:limit])
        and all(name.startswith("LAI_") for name in order[limit:limit * 2])
        and all(name.startswith("Biomass_") for name in order[limit * 2:limit * 3])
    )
    checks.append(
        CheckResult(
            "dependency_order_nodes_lai_biomass",
            order_ok,
            {"execution_order_sample": order[: min(len(order), limit * 3)]},
        )
    )

    greenhouse_ok = True
    greenhouse_details: dict[str, Any] = {}
    for index in range(limit):
        # The engine stores an initial state before the first step. Dynamic modules
        # receive input values during the step, so propagation is checked on the
        # final saved state rather than on the pre-step initial snapshot.
        t_mean = _last(results, f"Greenhouse_T_sparse_mean_{index}")
        rad = _last(results, f"Greenhouse_Rad_input_{index}")
        biomass_t = _last(results, f"Biomass_{index}_T_mean")
        biomass_rad = _last(results, f"Biomass_{index}_Rad")
        greenhouse_ok = greenhouse_ok and _finite(t_mean) and _finite(rad)
        greenhouse_ok = greenhouse_ok and abs(float(t_mean) - float(biomass_t)) < 1e-9
        greenhouse_ok = greenhouse_ok and abs(float(rad) - float(biomass_rad)) < 1e-9
        greenhouse_details[f"plant_{index}_T_mean_final"] = t_mean
        greenhouse_details[f"plant_{index}_Rad_final"] = rad

    checks.append(
        CheckResult(
            "greenhouse_input_propagation_to_biomass",
            greenhouse_ok,
            greenhouse_details,
        )
    )

    nodes_ok = True
    lai_ok = True
    biomass_ok = True
    trend_details: dict[str, Any] = {}

    for index in range(limit):
        n_initial = _first(results, f"Nodes_{index}_N")
        n_final = _last(results, f"Nodes_{index}_N")
        lai_initial = _first(results, f"LAI_{index}_lai")
        lai_final = _last(results, f"LAI_{index}_lai")
        w_initial = _first(results, f"Biomass_{index}_w")
        w_final = _last(results, f"Biomass_{index}_w")

        nodes_ok = nodes_ok and _finite(n_initial) and _finite(n_final) and float(n_final) >= float(n_initial)
        lai_ok = lai_ok and _finite(lai_initial) and _finite(lai_final) and float(lai_final) >= float(lai_initial)
        biomass_ok = biomass_ok and _finite(w_initial) and _finite(w_final) and float(w_final) >= 0.0

        trend_details[f"plant_{index}_nodes_delta"] = _series_delta(results, f"Nodes_{index}_N")
        trend_details[f"plant_{index}_lai_delta"] = _series_delta(results, f"LAI_{index}_lai")
        trend_details[f"plant_{index}_biomass_final"] = w_final

    checks.append(CheckResult("nodes_non_decreasing", nodes_ok, trend_details))
    checks.append(CheckResult("lai_non_decreasing", lai_ok, trend_details))
    checks.append(CheckResult("biomass_non_negative", biomass_ok, trend_details))

    metrics = {
        "run_mode": run_result["mode"],
        "steps": run_result.get("steps"),
        "input_modules": build.input_modules,
        "dynamic_templates": build.dynamic_templates,
        "dynamic_modules_instantiated": len(build.dynamic_modules),
        "resolved_bindings_for_limited_run": len(getattr(build.engine, "ir_bindings", [])),
        "global_input_bindings_for_limited_run": len(getattr(build.engine, "global_input_bindings", [])),
        "manifest_resolved_bindings_full_model": manifest.get('resolved_bindings_count', 0),
    }

    result = GridValidationResult(
        cif_path=str(cif_path),
        generated_dir=str(generated_dir),
        limit=limit,
        hours=hours,
        checks=checks,
        metrics=metrics,
    )

    (output_dir / "grid_behavior_validation.json").write_text(json.dumps(result.as_dict(), indent=2))
    (output_dir / "grid_behavior_validation.md").write_text(_markdown_report(result))
    _write_csv_summary(output_dir / "grid_behavior_summary.csv", results, limit)

    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cif", default=str(ROOT_DIR / "examples" / "Grid.cif"))
    parser.add_argument("--generated-dir", default=None, help="Generated package directory (default: out/generated/<CIF stem>)")
    parser.add_argument('--output-dir', default=None)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--hours", type=int, default=72)
    parser.add_argument("--save-every", type=int, default=1)
    args = parser.parse_args()

    resolved_generated_dir = require_generated_package(resolve_generated_dir(args.generated_dir, args.cif, ROOT_DIR), args.cif)
    model_name = resolved_generated_dir.name
    result = validate_grid_behavior(
        args.cif,
        str(resolved_generated_dir),
        str(Path(args.output_dir) if args.output_dir else (default_validation_dir(project_root=ROOT_DIR, model_name=model_name) / 'grid_behavior')),
        limit=args.limit,
        hours=args.hours,
        save_every=args.save_every,
    )

    print(f"Grid behavior validation: {'PASS' if result.passed else 'FAIL'}")
    resolved_output_dir = Path(args.output_dir) if args.output_dir else (default_validation_dir(project_root=ROOT_DIR, model_name=model_name) / 'grid_behavior')
    print(f"Report: {resolved_output_dir / 'grid_behavior_validation.md'}")
    if not result.passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
