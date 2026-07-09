from __future__ import annotations

"""
Simulation-result export helpers.

The engine keeps simulation history in memory through system_variables_history.
These helpers export that history only when explicitly requested by the user.
"""

import csv
import json
from pathlib import Path
from typing import Any


def _selected_history(history: dict[str, list[Any]], variables: list[str] | None = None) -> dict[str, list[Any]]:
    if not variables:
        return dict(history)

    selected: dict[str, list[Any]] = {}
    for variable in variables:
        if variable in history:
            selected[variable] = history[variable]
            continue

        matches = {
            name: values
            for name, values in history.items()
            if name.endswith(f"_{variable}") or variable in name
        }
        selected.update(matches)

    return selected


def export_history_csv(
    history: dict[str, list[Any]],
    output_path: str | Path,
    variables: list[str] | None = None,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    selected = _selected_history(history, variables)
    keys = sorted(selected)
    row_count = max((len(values) for values in selected.values()), default=0)

    with output_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["sample", *keys])

        for sample_index in range(row_count):
            row: list[Any] = [sample_index]
            for key in keys:
                values = selected[key]
                row.append(values[sample_index] if sample_index < len(values) else "")
            writer.writerow(row)

    return output_path


def export_history_json(
    history: dict[str, list[Any]],
    output_path: str | Path,
    variables: list[str] | None = None,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    selected = _selected_history(history, variables)
    output_path.write_text(json.dumps(selected, indent=2, default=str))
    return output_path


def parse_history_variables(raw: list[str] | None) -> list[str] | None:
    if not raw:
        return None

    variables: list[str] = []
    for item in raw:
        for part in item.split(","):
            name = part.strip()
            if name:
                variables.append(name)

    return variables or None
