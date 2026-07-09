#!/usr/bin/env python3
from __future__ import annotations

"""Convert an event CSV scenario to an ESCET/cifsim trace file.

This helper targets CIF simulations whose scenario is an ordered sequence of
external events. It is generic at the event-trace level: the CSV provides event
names and, when useful, a target automaton column/default target.

Expected CSV columns by default:
  step,event,target

Event resolution policy:
- if the CSV event already contains a dot, it is treated as an absolute CIF
  event name and is emitted unchanged;
- with --event-resolution=global, relative event names are emitted as global
  events;
- with --event-resolution=targeted, relative event names are prefixed with the
  row target or --default-target;
- with --event-resolution=auto, the converter inspects --cif when provided:
  top-level CIF events are emitted globally, while automaton-local events are
  prefixed only when needed. If --cif is not provided, auto falls back to the
  targeted behavior for backward compatibility.

CoffeeMachine is the default example in the repository, but its events are
actually declared at CIF top level. Therefore, with --cif and auto resolution,
rows such as `input_coffee,CoffeeMachine` correctly become `event input_coffee`,
not `event CoffeeMachine.input_coffee`.
"""

import argparse
import csv
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CifEventScope:
    """Minimal event declaration map used by this converter.

    This is intentionally lightweight and independent from the main CIF parser:
    it only needs to know whether an event was declared at CIF top level or
    inside an automaton/template block.
    """

    global_events: set[str] = field(default_factory=set)
    automaton_events: dict[str, set[str]] = field(default_factory=dict)

    def automata_declaring(self, event_name: str) -> list[str]:
        return [
            automaton
            for automaton, events in self.automaton_events.items()
            if event_name in events
        ]


def _strip_line_comment(line: str) -> str:
    return line.split("//", 1)[0]


def _parse_event_names(raw: str) -> list[str]:
    names: list[str] = []
    for part in raw.split(","):
        token = part.strip()
        if not token:
            continue
        # Drop optional type annotations or initialization-like fragments if a
        # future model contains more decorated declarations. For the supported
        # event-trace use case, plain identifiers are expected.
        token = token.split(":", 1)[0].strip()
        token = token.split("=", 1)[0].strip()
        if token:
            names.append(token)
    return names


def read_cif_event_scope(cif_path: str | Path | None) -> CifEventScope:
    if cif_path is None:
        return CifEventScope()

    path = Path(cif_path)
    if not path.exists():
        raise FileNotFoundError(f"CIF file not found: {path}")

    scope = CifEventScope()
    current_automaton: str | None = None
    pending_event_decl: list[str] | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = _strip_line_comment(raw_line).strip()
        if not line:
            continue

        automaton_match = re.match(r"automaton(?:\s+def)?\s+([A-Za-z_][A-Za-z0-9_]*)\b", line)
        if automaton_match:
            current_automaton = automaton_match.group(1)
            scope.automaton_events.setdefault(current_automaton, set())
            # Continue parsing the line below as well, in case an unusual one-line
            # declaration also contains an event statement.

        if re.fullmatch(r"end\s*", line):
            current_automaton = None
            pending_event_decl = None
            continue

        if pending_event_decl is not None:
            pending_event_decl.append(line)
            if ";" not in line:
                continue
            statement = " ".join(pending_event_decl)
            pending_event_decl = None
        elif re.match(r"event\b", line):
            statement = line
            if ";" not in line:
                pending_event_decl = [line]
                continue
        else:
            continue

        match = re.match(r"event\s+(.+?);", statement)
        if not match:
            continue

        names = _parse_event_names(match.group(1))
        if current_automaton is None:
            scope.global_events.update(names)
        else:
            scope.automaton_events.setdefault(current_automaton, set()).update(names)

    return scope


def _targeted_event(event_name: str, target: str | None) -> str:
    if not target:
        raise ValueError(
            f"Event {event_name!r} is not absolute and no target/default target was provided."
        )
    return f"{target}.{event_name}"


def _resolve_event(
    event_name: str,
    target: str | None,
    event_scope: CifEventScope | None,
    event_resolution: str,
) -> str:
    event_name = event_name.strip()
    if not event_name:
        raise ValueError("Empty event name in CSV scenario.")
    if "." in event_name:
        return event_name

    if event_resolution == "global":
        return event_name
    if event_resolution == "targeted":
        return _targeted_event(event_name, target)

    # auto mode
    scope = event_scope or CifEventScope()

    # CIF top-level events are global in cifsim trace input. They must not be
    # prefixed with the automaton name, even if the CSV has a target column.
    if event_name in scope.global_events:
        return event_name

    if target and event_name in scope.automaton_events.get(target, set()):
        return f"{target}.{event_name}"

    declaring_automata = scope.automata_declaring(event_name)
    if not target and len(declaring_automata) == 1:
        return f"{declaring_automata[0]}.{event_name}"

    # If no CIF scope was provided, keep the previous targeted behavior.
    if not scope.global_events and not scope.automaton_events:
        return _targeted_event(event_name, target)

    if target:
        # Conservative fallback for compatible models where the declaration was
        # not picked up by the lightweight scanner, but the user supplied a
        # target explicitly.
        return f"{target}.{event_name}"

    raise ValueError(
        f"Cannot resolve relative event {event_name!r}. Provide a target/default target, "
        "use an absolute event name, or declare the event in the CIF model."
    )


def convert_events_csv_to_escet_trace(
    events_csv: str | Path,
    output_trace: str | Path,
    event_column: str = "event",
    target_column: str = "target",
    default_target: str | None = None,
    strict_mode: str = "off",
    time_mode: str = "implicit",
    cif_path: str | Path | None = None,
    event_resolution: str = "auto",
) -> Path:
    events_csv = Path(events_csv)
    output_trace = Path(output_trace)
    output_trace.parent.mkdir(parents=True, exist_ok=True)
    event_scope = read_cif_event_scope(cif_path) if cif_path else CifEventScope()

    lines: list[str] = [
        f"option strict {strict_mode}",
        f"option time {time_mode}",
        "",
    ]

    with events_csv.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {events_csv}")
        if event_column not in reader.fieldnames:
            raise ValueError(
                f"CSV column {event_column!r} not found in {events_csv}. "
                f"Available columns: {reader.fieldnames}"
            )

        for row_index, row in enumerate(reader, start=2):
            event_name = (row.get(event_column) or "").strip()
            target = (row.get(target_column) or default_target or "").strip() or None
            try:
                resolved = _resolve_event(event_name, target, event_scope, event_resolution)
            except ValueError as exc:
                raise ValueError(f"Invalid event scenario at CSV line {row_index}: {exc}") from exc
            lines.append(f"event {resolved}")

    output_trace.write_text("\n".join(lines) + "\n")
    return output_trace


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert an event CSV scenario to an ESCET/cifsim .trace file.")
    parser.add_argument("--events-csv", required=True, help="Input event CSV scenario.")
    parser.add_argument("--output-trace", required=True, help="Output ESCET .trace path.")
    parser.add_argument("--cif", default=None, help="Optional CIF model used to resolve global vs automaton-local events.")
    parser.add_argument("--event-column", default="event", help="Column containing event names. Default: event")
    parser.add_argument("--target-column", default="target", help="Column containing automaton targets. Default: target")
    parser.add_argument("--default-target", default=None, help="Target automaton used when the CSV has no target column/value and the event is not global.")
    parser.add_argument("--event-resolution", default="auto", choices=["auto", "global", "targeted"], help="How to resolve relative event names. Default: auto")
    parser.add_argument("--strict-mode", default="off", choices=["on", "off"], help="ESCET trace strict mode. Default: off")
    parser.add_argument("--time-mode", default="implicit", choices=["implicit", "explicit"], help="ESCET trace time mode. Default: implicit")
    args = parser.parse_args()

    output = convert_events_csv_to_escet_trace(
        events_csv=args.events_csv,
        output_trace=args.output_trace,
        event_column=args.event_column,
        target_column=args.target_column,
        default_target=args.default_target,
        strict_mode=args.strict_mode,
        time_mode=args.time_mode,
        cif_path=args.cif,
        event_resolution=args.event_resolution,
    )
    print(f"ESCET trace written to: {output}")


if __name__ == "__main__":
    main()
