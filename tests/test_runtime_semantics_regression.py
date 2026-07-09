from pathlib import Path

from pipeline.auto_builder import build_engine_from_generated_package
from pipeline.scenario_inputs import read_input_series_csv

ROOT = Path(__file__).resolve().parents[1]


def _build_grid_engine(limit: int = 1, hours: int = 48):
    input_values, _ = read_input_series_csv(ROOT / "examples" / "grid_weather_input_48h_repeat.csv")
    return build_engine_from_generated_package(
        ROOT / "out/generated/Grid_semplified",
        cif_path=ROOT / "examples" / "Grid_semplified.cif",
        limit=limit,
        hours=hours,
        input_values=input_values,
    ).engine


def test_biomass_day_is_followed_by_hour_within_same_logical_step():
    engine = _build_grid_engine(limit=1, hours=25)
    engine.run_till_timestep(25, save_every=1)
    results = engine.get_results()

    # After the first full day, the corrected runtime drains automatic edges
    # until quiescence. Therefore step 25 ends with Biomass.hour already fired
    # again, leaving cd=1 and c=0.
    assert results["Biomass_0_cd"][25] == 1
    assert results["Biomass_0_c"][25] == 0
    assert results["Nodes_0_c"][25] == 1


def test_second_nodes_day_occurs_at_logical_step_48():
    engine = _build_grid_engine(limit=1, hours=48)
    engine.run_till_timestep(48, save_every=1)
    results = engine.get_results()

    assert results["Nodes_0_c"][48] == 0
    assert results["Nodes_0_N"][48] > results["Nodes_0_N"][24]

import pytest

from pipeline.auto_builder import run_engine_if_possible
from pipeline.scenario_inputs import read_event_trace_csv


def _build_ship_counter_engine():
    return build_engine_from_generated_package(
        ROOT / "out/generated/ship-counter-optimized",
        cif_path=ROOT / "examples" / "ship-counter-optimized.cif",
        limit=None,
        hours=1,
        input_values={},
    )


def test_event_trace_rejects_disabled_guarded_event():
    build_result = _build_ship_counter_engine()
    invalid_trace = read_event_trace_csv(ROOT / "examples" / "ship-counter-optimized_invalid_guard_events.csv")

    with pytest.raises(RuntimeError, match="not enabled"):
        run_engine_if_possible(build_result, event_trace=invalid_trace)


def test_valid_ship_counter_event_trace_updates_count():
    build_result = _build_ship_counter_engine()
    trace = read_event_trace_csv(ROOT / "examples" / "ship-counter-optimized_events.csv")

    run_engine_if_possible(build_result, event_trace=trace)
    results = build_result.engine.get_results()

    assert results["ShipCounter_0_count"] == [0, 1, 2, 3, 4, 5, 4, 3, 2, 1, 0]
