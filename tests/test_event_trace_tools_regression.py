from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_events_csv_to_escet_trace_keeps_top_level_coffee_events_global(tmp_path):
    output_trace = tmp_path / "coffee.trace"

    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "events_csv_to_escet_trace.py"),
            "--events-csv",
            str(ROOT / "examples" / "coffee_machine_events.csv"),
            "--output-trace",
            str(output_trace),
            "--cif",
            str(ROOT / "examples" / "coffee_machine.cif"),
            "--default-target",
            "CoffeeMachine",
            "--event-resolution",
            "auto",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=60,
    )

    assert proc.returncode == 0, proc.stdout
    text = output_trace.read_text()
    assert "event input_coffee" in text
    assert "event CoffeeMachine.input_coffee" not in text


def test_events_csv_to_escet_trace_prefixes_automaton_local_ship_events(tmp_path):
    output_trace = tmp_path / "ship.trace"

    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "events_csv_to_escet_trace.py"),
            "--events-csv",
            str(ROOT / "examples" / "ship-counter-optimized_events.csv"),
            "--output-trace",
            str(output_trace),
            "--cif",
            str(ROOT / "examples" / "ship-counter-optimized.cif"),
            "--default-target",
            "ShipCounter",
            "--event-resolution",
            "auto",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=60,
    )

    assert proc.returncode == 0, proc.stdout
    text = output_trace.read_text()
    assert "event ShipCounter.ship_enters" in text
    assert "event ship_enters" not in text


def test_cifsim_event_log_to_csv_extracts_ship_counter_values(tmp_path):
    log = tmp_path / "cifsim_ship.log"
    output_csv = tmp_path / "escet_reference.csv"
    log.write_text(
        """
Initial state: time=0.0, ShipCounter=Counter, ShipCounter.count=0

Transition: event ShipCounter.ship_enters
State: time=0.0, ShipCounter=Counter, ShipCounter.count=1

Transition: event ShipCounter.ship_enters
State: time=0.0, ShipCounter=Counter, ShipCounter.count=2

Transition: event ShipCounter.ship_leaves
State: time=0.0, ShipCounter=Counter, ShipCounter.count=1
        """.strip()
    )

    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "cifsim_event_log_to_csv.py"),
            "--cif",
            str(ROOT / "examples" / "ship-counter-optimized.cif"),
            "--log",
            str(log),
            "--output-csv",
            str(output_csv),
            "--history-var",
            "ShipCounter_0_count",
            "--expected-samples",
            "4",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=60,
    )

    assert proc.returncode == 0, proc.stdout
    rows = list(csv.DictReader(output_csv.open()))
    assert [row["ShipCounter_0_count"] for row in rows] == ["0", "1", "2", "1"]


def test_cifsim_event_log_to_csv_reports_deadlock_for_invalid_trace(tmp_path):
    log = tmp_path / "cifsim_deadlock.log"
    output_csv = tmp_path / "escet_reference.csv"
    log.write_text(
        """
Initial state: time=0.0, ShipCounter=Counter, ShipCounter.count=0

Transition: event ShipCounter.ship_enters
State: time=0.0, ShipCounter=Counter, ShipCounter.count=1

WARNING: No transition found for event "ShipCounter.ship_enters" from the trace input.
Simulation resulted in deadlock.
        """.strip()
    )

    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "cifsim_event_log_to_csv.py"),
            "--cif",
            str(ROOT / "examples" / "ship-counter-optimized.cif"),
            "--log",
            str(log),
            "--output-csv",
            str(output_csv),
            "--history-var",
            "ShipCounter_0_count",
            "--expected-samples",
            "3",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=60,
    )

    assert proc.returncode != 0
    assert "deadlock" in proc.stdout
    assert "event trace requested" in proc.stdout


def test_cifsim_event_log_to_csv_extracts_coffee_machine_locations(tmp_path):
    log = tmp_path / "cifsim_coffee.log"
    output_csv = tmp_path / "coffee_reference.csv"
    log.write_text(
        """
Initial state: time=0.0, CoffeeMachine=WaitingOrder

Transition: event input_coffee
State: time=0.0, CoffeeMachine=GrindingCoffee

Transition: event heat_water
State: time=0.0, CoffeeMachine=HeatingWater

Transition: event add_water
State: time=0.0, CoffeeMachine=ExtractingCoffee

Transition: event deliver_cup
State: time=0.0, CoffeeMachine=WaitingOrder
        """.strip()
    )

    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "cifsim_event_log_to_csv.py"),
            "--cif",
            str(ROOT / "examples" / "coffee_machine.cif"),
            "--log",
            str(log),
            "--output-csv",
            str(output_csv),
            "--history-var",
            "CoffeeMachine_0_location",
            "--expected-samples",
            "5",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=60,
    )

    assert proc.returncode == 0, proc.stdout
    rows = list(csv.DictReader(output_csv.open()))
    assert [row["CoffeeMachine_0_location"] for row in rows] == [
        "WaitingOrder",
        "GrindingCoffee",
        "HeatingWater",
        "ExtractingCoffee",
        "WaitingOrder",
    ]
