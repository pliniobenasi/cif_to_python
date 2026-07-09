from __future__ import annotations

"""
Benchmark for the final CIF -> modular Python simulator pipeline.

The benchmark measures:
- parsing time;
- feature analysis time;
- previously recorded code-generation timing, if available in the generated package;
- engine build time for several grid sizes;
- simulation time for several grid sizes;
- process peak memory estimate, when available.

The benchmark is designed for Grid.cif but does not hardcode generated module names
inside the core pipeline. Grid sizes are expressed as the number of instances per
template to instantiate during the simulation phase.
"""

from dataclasses import asdict, dataclass, field
import argparse
import csv
import gc
import json
import resource
import shutil
import statistics
import time
from pathlib import Path
import sys
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pipeline.path_defaults import resolve_generated_dir, require_generated_package, default_benchmarks_dir, default_reports_dir

from pipeline.auto_builder import build_engine_from_generated_package, run_engine_if_possible
from pipeline.cif_parser import parse_file
from pipeline.feature_analyzer import analyze_file


@dataclass
class PhaseTiming:
    name: str
    seconds: float
    peak_memory_mb: float | None = None


@dataclass
class SimulationBenchmark:
    limit: int
    hours: int
    repetitions: int
    build_seconds_mean: float
    build_seconds_min: float
    build_seconds_max: float
    simulation_seconds_mean: float
    simulation_seconds_min: float
    simulation_seconds_max: float
    total_seconds_mean: float
    dynamic_modules_instantiated: int
    input_modules: list[str] = field(default_factory=list)
    resolved_bindings_limited: int = 0
    global_input_bindings_limited: int = 0
    peak_memory_mb_after_run: float | None = None


@dataclass
class PipelineBenchmarkReport:
    cif_path: str
    generated_dir: str
    hours: int
    limits: list[int]
    repetitions: int
    phases: list[PhaseTiming]
    simulations: list[SimulationBenchmark]
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _peak_memory_mb() -> float | None:
    try:
        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    except Exception:
        return None

    # Linux reports KB, macOS reports bytes. This environment is Linux.
    if value > 10_000_000:
        return value / (1024 * 1024)
    return value / 1024


def _time_phase(name: str, func):
    gc.collect()
    start = time.perf_counter()
    result = func()
    seconds = time.perf_counter() - start
    return result, PhaseTiming(name=name, seconds=seconds, peak_memory_mb=_peak_memory_mb())


def _mean_min_max(values: list[float]) -> tuple[float, float, float]:
    return statistics.mean(values), min(values), max(values)


def _load_existing_manifest(generated_dir: Path) -> dict[str, Any]:
    report_dir = default_reports_dir(generated_dir=generated_dir, project_root=ROOT_DIR)
    manifest_path = report_dir / "translation_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            "translation_manifest.json not found. "
            "Generate the package once with scripts/cif_to_python.py before running benchmarks."
        )
    return json.loads(manifest_path.read_text())


def _load_generation_timings(generated_dir: Path) -> list[PhaseTiming]:
    report_dir = default_reports_dir(generated_dir=generated_dir, project_root=ROOT_DIR)
    timing_path = report_dir / "pipeline_generation_timing.json"
    if not timing_path.exists():
        return [
            PhaseTiming(
                name="code_generation",
                seconds=0.0,
                peak_memory_mb=_peak_memory_mb(),
            )
        ]

    data = json.loads(timing_path.read_text())
    phases = []
    for item in data.get("phases", []):
        phases.append(
            PhaseTiming(
                name=f"recorded_{item.get('name', 'unknown')}",
                seconds=float(item.get("seconds", 0.0)),
                peak_memory_mb=_peak_memory_mb(),
            )
        )
    return phases


def run_pipeline_benchmark(
    cif_path: str | Path,
    generated_dir: str | Path,
    output_dir: str | Path,
    limits: list[int],
    hours: int = 24,
    repetitions: int = 1,
    save_every: int = 24,
    clean_generated: bool = True,
) -> PipelineBenchmarkReport:
    cif_path = Path(cif_path)
    generated_dir = Path(generated_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if clean_generated:
        # Kept for CLI compatibility only. The benchmark does not delete or regenerate
        # modules anymore: generation must happen once through scripts/cif_to_python.py.
        pass

    generated_dir = require_generated_package(generated_dir, cif_path)

    phases: list[PhaseTiming] = []

    _, phase = _time_phase("parse", lambda: parse_file(cif_path))
    phases.append(phase)

    _, phase = _time_phase("feature_analysis", lambda: analyze_file(cif_path))
    phases.append(phase)

    phases.extend(_load_generation_timings(generated_dir))

    manifest = _load_existing_manifest(generated_dir)

    simulations: list[SimulationBenchmark] = []

    for limit in limits:
        build_times: list[float] = []
        simulation_times: list[float] = []
        last_build = None

        for _ in range(repetitions):
            gc.collect()

            build_start = time.perf_counter()
            build = build_engine_from_generated_package(
                generated_dir,
                cif_path=cif_path,
                limit=limit,
                hours=hours,
            )
            build_seconds = time.perf_counter() - build_start

            sim_start = time.perf_counter()
            run_engine_if_possible(build, save_every=save_every)
            simulation_seconds = time.perf_counter() - sim_start

            build_times.append(build_seconds)
            simulation_times.append(simulation_seconds)
            last_build = build

        build_mean, build_min, build_max = _mean_min_max(build_times)
        sim_mean, sim_min, sim_max = _mean_min_max(simulation_times)

        assert last_build is not None
        simulations.append(
            SimulationBenchmark(
                limit=limit,
                hours=hours,
                repetitions=repetitions,
                build_seconds_mean=build_mean,
                build_seconds_min=build_min,
                build_seconds_max=build_max,
                simulation_seconds_mean=sim_mean,
                simulation_seconds_min=sim_min,
                simulation_seconds_max=sim_max,
                total_seconds_mean=build_mean + sim_mean,
                dynamic_modules_instantiated=len(last_build.dynamic_modules),
                input_modules=last_build.input_modules,
                resolved_bindings_limited=len(getattr(last_build.engine, "ir_bindings", [])),
                global_input_bindings_limited=len(getattr(last_build.engine, "global_input_bindings", [])),
                peak_memory_mb_after_run=_peak_memory_mb(),
            )
        )

    notes = [
        "Peak memory is measured through resource.getrusage(RUSAGE_SELF).ru_maxrss; it is a process-level estimate.",
        "Generation is measured once because it is independent from the simulation limit.",
        "Simulation limit indicates how many instances per dynamic template are instantiated.",
        f"Full manifest bindings: {manifest.get('resolved_bindings_count', 0)}",
    ]

    report = PipelineBenchmarkReport(
        cif_path=str(cif_path),
        generated_dir=str(generated_dir),
        hours=hours,
        limits=limits,
        repetitions=repetitions,
        phases=phases,
        simulations=simulations,
        notes=notes,
    )

    _write_reports(report, output_dir)
    return report


def _write_reports(report: PipelineBenchmarkReport, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "pipeline_benchmark.json"
    csv_path = output_dir / "pipeline_benchmark.csv"
    md_path = output_dir / "pipeline_benchmark.md"

    json_path.write_text(json.dumps(report.as_dict(), indent=2))

    with csv_path.open("w", newline="") as handle:
        fieldnames = [
            "limit",
            "hours",
            "repetitions",
            "dynamic_modules_instantiated",
            "build_seconds_mean",
            "simulation_seconds_mean",
            "total_seconds_mean",
            "resolved_bindings_limited",
            "global_input_bindings_limited",
            "peak_memory_mb_after_run",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in report.simulations:
            writer.writerow(
                {
                    "limit": item.limit,
                    "hours": item.hours,
                    "repetitions": item.repetitions,
                    "dynamic_modules_instantiated": item.dynamic_modules_instantiated,
                    "build_seconds_mean": item.build_seconds_mean,
                    "simulation_seconds_mean": item.simulation_seconds_mean,
                    "total_seconds_mean": item.total_seconds_mean,
                    "resolved_bindings_limited": item.resolved_bindings_limited,
                    "global_input_bindings_limited": item.global_input_bindings_limited,
                    "peak_memory_mb_after_run": item.peak_memory_mb_after_run,
                }
            )

    lines = [
        "# Pipeline benchmark",
        "",
        f"- CIF: `{report.cif_path}`",
        f"- Generated directory: `{report.generated_dir}`",
        f"- Hours per simulation: `{report.hours}`",
        f"- Limits: `{report.limits}`",
        f"- Repetitions: `{report.repetitions}`",
        "",
        "## Pipeline phases",
        "",
        "| Phase | Seconds | Peak memory MB |",
        "|---|---:|---:|",
    ]

    for phase in report.phases:
        memory = "" if phase.peak_memory_mb is None else f"{phase.peak_memory_mb:.2f}"
        lines.append(f"| {phase.name} | {phase.seconds:.6f} | {memory} |")

    lines.extend(
        [
            "",
            "## Simulation scaling",
            "",
            "| Limit | Dynamic modules | Build s | Simulation s | Total s | Limited bindings | Input bindings | Peak memory MB |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )

    for item in report.simulations:
        memory = "" if item.peak_memory_mb_after_run is None else f"{item.peak_memory_mb_after_run:.2f}"
        lines.append(
            f"| {item.limit} | "
            f"{item.dynamic_modules_instantiated} | "
            f"{item.build_seconds_mean:.6f} | "
            f"{item.simulation_seconds_mean:.6f} | "
            f"{item.total_seconds_mean:.6f} | "
            f"{item.resolved_bindings_limited} | "
            f"{item.global_input_bindings_limited} | "
            f"{memory} |"
        )

    lines.extend(["", "## Notes", ""])
    lines.extend([f"- {note}" for note in report.notes])

    lines.extend(
        [
            "",
            "## Interpretation for the thesis",
            "",
            "The parsing and generation phases are mostly independent from the number of simulated plants.",
            "The build and simulation phases scale with the number of instantiated modules and bindings.",
            "This provides the quantitative basis for discussing future parallelization or GPU-oriented execution.",
        ]
    )

    md_path.write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cif", default=str(ROOT_DIR / "examples" / "Grid.cif"))
    parser.add_argument("--generated-dir", default=None, help="Generated package directory (default: out/generated/<CIF stem>)")
    parser.add_argument('--output-dir', default=None)
    parser.add_argument("--limits", nargs="+", type=int, default=[1, 10, 100, 1600])
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--save-every", type=int, default=24)
    parser.add_argument("--keep-generated", action="store_true")
    args = parser.parse_args()

    resolved_generated_dir = require_generated_package(resolve_generated_dir(args.generated_dir, args.cif, ROOT_DIR), args.cif)
    model_name = resolved_generated_dir.name
    report = run_pipeline_benchmark(
        args.cif,
        str(resolved_generated_dir),
        str(Path(args.output_dir) if args.output_dir else (default_benchmarks_dir(project_root=ROOT_DIR, model_name=model_name) / 'pipeline')),
        limits=args.limits,
        hours=args.hours,
        repetitions=args.repetitions,
        save_every=args.save_every,
        clean_generated=not args.keep_generated,
    )

    resolved_output_dir = Path(args.output_dir) if args.output_dir else (default_benchmarks_dir(project_root=ROOT_DIR, model_name=model_name) / 'pipeline')
    print(f"Benchmark report: {resolved_output_dir / 'pipeline_benchmark.md'}")
    for item in report.simulations:
        print(
            f"limit={item.limit} modules={item.dynamic_modules_instantiated} "
            f"build={item.build_seconds_mean:.4f}s sim={item.simulation_seconds_mean:.4f}s"
        )


if __name__ == "__main__":
    main()
