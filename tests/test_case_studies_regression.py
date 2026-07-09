from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.auto_builder import build_engine_from_generated_package, run_engine_if_possible
from pipeline.python_generator_general import generate_general_from_cif
from pipeline.generated_artifacts import write_generated_artifacts
from pipeline.scenario_inputs import read_event_trace_csv, read_input_series_csv

ROOT = Path(__file__).resolve().parents[1]


def _locations_from_event_run(result: dict) -> list[str]:
    return [item["variables"]["location"] for item in result["events"]]


def test_coffee_machine_stop_and_reset_path(tmp_path):
    """CoffeeMachine must follow the explicit emergency path in the CIF."""

    cif = ROOT / "examples" / "coffee_machine.cif"
    out = tmp_path / "generated_coffee_emergency"
    generate_general_from_cif(cif, out)

    build = build_engine_from_generated_package(out, cif)
    result = run_engine_if_possible(
        build,
        events=["input_coffee", "heat_water", "stop", "reset"],
    )

    assert result["mode"] == "event-driven"
    assert _locations_from_event_run(result) == [
        "WaitingOrder",
        "GrindingCoffee",
        "HeatingWater",
        "EmergencyMode",
        "WaitingOrder",
    ]


def test_traffic_light_tick_trace_cycles_locations(tmp_path):
    """TrafficLight is an intermediate event-trace case, not a CoffeeMachine-specific workflow."""

    cif = ROOT / "examples" / "traffic_light_temporal.cif"
    out = tmp_path / "generated_traffic_light"
    generate_general_from_cif(cif, out)

    build = build_engine_from_generated_package(out, cif)
    trace = read_event_trace_csv(ROOT / "examples" / "traffic_light_temporal_events.csv")
    result = run_engine_if_possible(build, event_trace=trace)

    assert result["mode"] == "event-trace"
    assert build.engine.get_results()["TrafficLight_0_location"] == [
        "Red",
        "Green",
        "Yellow",
        "Red",
        "Green",
        "Yellow",
        "Red",
    ]


def test_ship_counter_valid_trace_updates_discrete_count(tmp_path):
    """ShipCounter covers guarded discrete-variable updates."""

    cif = ROOT / "examples" / "ship-counter-optimized.cif"
    out = tmp_path / "generated_ship_counter"
    generate_general_from_cif(cif, out)

    build = build_engine_from_generated_package(out, cif)
    trace = read_event_trace_csv(ROOT / "examples" / "ship-counter-optimized_events.csv")
    result = run_engine_if_possible(build, event_trace=trace)

    assert result["mode"] == "event-trace"
    assert build.engine.get_results()["ShipCounter_0_count"] == [
        0,
        1,
        2,
        3,
        4,
        5,
        4,
        3,
        2,
        1,
        0,
    ]
    assert build.engine.get_results()["ShipCounter_0_location"] == ["Counter"] * 11


def test_ship_counter_invalid_guard_event_is_not_a_silent_noop(tmp_path):
    """Regression for strict event-trace semantics discovered with ShipCounter.

    A trace item whose guard is false must be rejected, matching ESCET trace-input
    semantics. It must not be recorded as a no-op sample in the history.
    """

    cif = ROOT / "examples" / "ship-counter-optimized.cif"
    out = tmp_path / "generated_ship_counter_invalid"
    generate_general_from_cif(cif, out)

    build = build_engine_from_generated_package(out, cif)
    invalid_trace = read_event_trace_csv(ROOT / "examples" / "ship-counter-optimized_invalid_guard_events.csv")

    with pytest.raises(RuntimeError, match="not enabled"):
        run_engine_if_possible(build, event_trace=invalid_trace)

    # The runtime may have saved the initial state and valid prefix, but it must
    # not save a fake sample for the disabled event at count=5.
    assert build.engine.get_results()["ShipCounter_0_count"] == [0, 1, 2, 3, 4, 5]


def test_grid_semplified_rejects_hours_beyond_input_csv_length():
    """The data-driven Grid case must fail clearly when the requested horizon exceeds the CSV."""

    input_values, row_count = read_input_series_csv(ROOT / "examples" / "grid_weather_input.csv")
    assert row_count == 24

    with pytest.raises(ValueError, match="at least 'hours' values"):
        build_engine_from_generated_package(
            ROOT / "out" / "generated" / "Grid_semplified",
            cif_path=ROOT / "examples" / "Grid_semplified.cif",
            limit=1,
            hours=row_count + 1,
            input_values=input_values,
        )


def test_generated_ship_counter_runner_fails_on_invalid_guard_event_csv(tmp_path):
    """The standalone generated runner must also use strict event-trace semantics."""

    import subprocess
    import sys

    cif = ROOT / "examples" / "ship-counter-optimized.cif"
    out = tmp_path / "generated_ship_counter_runner_invalid"
    generate_general_from_cif(cif, out)
    write_generated_artifacts(cif, out, pipeline_root=ROOT / "src")

    proc = subprocess.run(
        [
            sys.executable,
            str(out / "run_generated_model.py"),
            "--events-csv",
            str(ROOT / "examples" / "ship-counter-optimized_invalid_guard_events.csv"),
            "--history-vars",
            "ShipCounter_0_count",
            "ShipCounter_0_location",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=60,
    )

    assert proc.returncode != 0
    assert "not enabled" in proc.stdout
    assert "disabled events are invalid" in proc.stdout.lower()
