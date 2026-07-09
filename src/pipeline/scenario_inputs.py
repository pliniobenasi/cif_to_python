from __future__ import annotations

"""
Scenario input readers.

The CIF model describes the system. Scenario files describe one concrete
simulation run.

Supported scenario types:

- event trace CSV: drives external events through fire(event)
- data trace CSV: overrides generated input-module numeric series
"""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STEP_COLUMNS = {"step", "timestep", "time", "hour"}
EVENT_COLUMNS = {"event", "event_name"}
TARGET_COLUMNS = {"target", "module", "module_name"}


@dataclass(frozen=True)
class EventTraceItem:
    step: int
    event: str
    target: str | None = None


def _normalize_header(name: str) -> str:
    return name.strip()


def _find_column(fieldnames: list[str], candidates: set[str]) -> str | None:
    by_lower = {name.lower(): name for name in fieldnames}
    for candidate in candidates:
        if candidate in by_lower:
            return by_lower[candidate]
    return None


def read_event_trace_csv(path: str | Path) -> list[EventTraceItem]:
    """
    Read an event trace CSV.

    Supported formats:

    step,event,target
    0,input_coffee,CoffeeMachine

    step,event
    0,input_coffee

    event
    input_coffee

    If the step column is omitted, events are assigned consecutive steps.
    If the target column is omitted, the runner uses the only generated module
    when the model is single-module.
    """

    path = Path(path)
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"Event trace CSV has no header: {path}")

        fieldnames = [_normalize_header(name) for name in reader.fieldnames]
        reader.fieldnames = fieldnames

        event_column = _find_column(fieldnames, EVENT_COLUMNS)
        if event_column is None:
            raise ValueError(
                "Event trace CSV must contain an 'event' column. "
                f"Available columns: {fieldnames}"
            )

        step_column = _find_column(fieldnames, STEP_COLUMNS)
        target_column = _find_column(fieldnames, TARGET_COLUMNS)

        trace: list[EventTraceItem] = []
        for row_index, row in enumerate(reader):
            raw_event = (row.get(event_column) or "").strip()
            if not raw_event:
                continue

            if step_column is None or not (row.get(step_column) or "").strip():
                step = row_index
            else:
                step = int(float((row.get(step_column) or "").strip()))

            target = None
            if target_column is not None:
                raw_target = (row.get(target_column) or "").strip()
                target = raw_target or None

            trace.append(EventTraceItem(step=step, event=raw_event, target=target))

    trace.sort(key=lambda item: item.step)
    return trace


def read_input_series_csv(path: str | Path) -> tuple[dict[str, list[float]], int]:
    """
    Read a numeric data trace CSV.

    Time columns such as step/time/hour are ignored.
    Every other column becomes an input series.

    Example:

    step,T_in,Rad,T_mean,T_daytime_mean
    0,20,300,21,22
    1,20.5,310,21.3,22.4
    """

    path = Path(path)
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"Input CSV has no header: {path}")

        fieldnames = [_normalize_header(name) for name in reader.fieldnames]
        reader.fieldnames = fieldnames

        data_columns = [
            name
            for name in fieldnames
            if name.lower() not in STEP_COLUMNS
        ]

        if not data_columns:
            raise ValueError(
                "Input CSV must contain at least one numeric data column "
                "besides optional step/time columns."
            )

        series: dict[str, list[float]] = {name: [] for name in data_columns}
        row_count = 0

        for row_index, row in enumerate(reader):
            row_count += 1
            for column in data_columns:
                raw = (row.get(column) or "").strip()
                if raw == "":
                    raise ValueError(
                        f"Missing numeric value in column '{column}' at CSV row {row_index + 2}"
                    )
                try:
                    series[column].append(float(raw))
                except ValueError as exc:
                    raise ValueError(
                        f"Invalid numeric value in column '{column}' at CSV row {row_index + 2}: {raw!r}"
                    ) from exc

    return series, row_count


def event_trace_to_dicts(trace: list[EventTraceItem]) -> list[dict[str, Any]]:
    return [
        {
            "step": item.step,
            "event": item.event,
            "target": item.target,
        }
        for item in trace
    ]
