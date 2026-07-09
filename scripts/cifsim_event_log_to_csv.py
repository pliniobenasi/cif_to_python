#!/usr/bin/env python3
from __future__ import annotations

"""Convert a cifsim event-trace console log to an observable CSV.

This helper is scoped to event-trace validation cases. It executes no model
logic by itself: the scenario is executed by ESCET/cifsim, and this script only
extracts observable values from the textual cifsim log.

Supported observables:
- generated location history variables such as ``CoffeeMachine_0_location``;
- generated discrete/state variables such as ``ShipCounter_0_count``.

The parser supports several common textual forms used by cifsim/debug logs, for
example:

    CoffeeMachine: WaitingOrder
    CoffeeMachine.location = WaitingOrder
    TrafficLight_0_location = Red
    ShipCounter.count = 3
    ShipCounter_0_count = 3
    count = 3

If the local ESCET version prints a different log format, keep the raw log and
adapt this converter rather than replacing the ESCET reference with a manual
CSV.
"""

import argparse
import csv
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AutomatonLocations:
    name: str
    locations: list[str] = field(default_factory=list)
    initial: str | None = None


@dataclass
class AutomatonVariables:
    name: str
    variables: dict[str, str] = field(default_factory=dict)


def _strip_comments(text: str) -> str:
    text = re.sub(r"//.*?$", "", text, flags=re.MULTILINE)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return text


def _extract_balanced_automata(text: str) -> list[tuple[str, str]]:
    """Return (automaton_name, body) pairs for lightweight CIF automata."""

    result: list[tuple[str, str]] = []
    pattern = re.compile(r"\bautomaton\s+(?:def\s+)?([A-Za-z_]\w*)\b[^:]*:", re.MULTILINE)
    for match in pattern.finditer(text):
        name = match.group(1)
        body_start = match.end()
        end_match = re.search(r"^\s*end\b", text[body_start:], flags=re.MULTILINE)
        if not end_match:
            continue
        body_end = body_start + end_match.start()
        result.append((name, text[body_start:body_end]))
    return result


def read_cif_automaton_locations(cif_path: str | Path) -> dict[str, AutomatonLocations]:
    text = _strip_comments(Path(cif_path).read_text())
    automata: dict[str, AutomatonLocations] = {}

    for name, body in _extract_balanced_automata(text):
        item = AutomatonLocations(name=name)
        location_pattern = re.compile(
            r"\blocation\s+([A-Za-z_]\w*)\s*:(.*?)(?=\n\s*location\s+[A-Za-z_]\w*\s*:|\Z)",
            flags=re.DOTALL,
        )
        for loc_match in location_pattern.finditer(body):
            location_name = loc_match.group(1)
            location_body = loc_match.group(2)
            item.locations.append(location_name)
            if re.search(r"\binitial\b", location_body):
                item.initial = location_name
        if item.locations:
            if item.initial is None:
                item.initial = item.locations[0]
            automata[name] = item

    return automata


def read_cif_automaton_variables(cif_path: str | Path) -> dict[str, AutomatonVariables]:
    text = _strip_comments(Path(cif_path).read_text())
    automata: dict[str, AutomatonVariables] = {}
    variable_pattern = re.compile(
        r"\b(?:disc|alg|cont)\s+(?:[A-Za-z_]\w*(?:\s*\[[^\]]+\])?\s+)?([A-Za-z_]\w*)\s*(?:=\s*([^;]+))?;",
        flags=re.MULTILINE,
    )

    for name, body in _extract_balanced_automata(text):
        item = AutomatonVariables(name=name)
        for match in variable_pattern.finditer(body):
            var_name = match.group(1)
            initial = (match.group(2) or "").strip()
            if initial:
                item.variables[var_name] = initial
        automata[name] = item
    return automata


def _infer_automaton_from_history_var(history_var: str) -> str | None:
    match = re.match(r"(.+?)_\d+_([A-Za-z_]\w*)$", history_var)
    if match:
        return match.group(1)
    match = re.match(r"(.+?)_([A-Za-z_]\w*)$", history_var)
    if match:
        return match.group(1)
    return None


def _infer_variable_from_history_var(history_var: str) -> str | None:
    match = re.match(r".+?_\d+_([A-Za-z_]\w*)$", history_var)
    if match:
        return match.group(1)
    match = re.match(r".+?_([A-Za-z_]\w*)$", history_var)
    if match:
        return match.group(1)
    return None


def _compile_location_patterns(automaton: str, history_var: str, locations: list[str]) -> list[re.Pattern[str]]:
    loc_alt = "|".join(re.escape(loc) for loc in sorted(locations, key=len, reverse=True))
    aut = re.escape(automaton)
    hist = re.escape(history_var)

    return [
        re.compile(rf"\b{hist}\b\s*[:=]\s*\b({loc_alt})\b"),
        re.compile(rf"\b{aut}(?:_0)?_location\b\s*[:=]\s*\b({loc_alt})\b"),
        re.compile(rf"\b{aut}\s*\.\s*location\b\s*[:=]\s*\b({loc_alt})\b"),
        re.compile(rf"\blocation\s+(?:of\s+)?\b{aut}\b\s*[:=]\s*\b({loc_alt})\b", re.IGNORECASE),
        re.compile(rf"\b{aut}\b\s*[:=]\s*\b({loc_alt})\b"),
        re.compile(rf"\b{aut}\b.*?\blocation\b.*?\b({loc_alt})\b", re.IGNORECASE),
        re.compile(rf"\blocation\b.*?\b{aut}\b.*?\b({loc_alt})\b", re.IGNORECASE),
    ]


def extract_location_history(
    log_text: str,
    automaton: str,
    history_var: str,
    locations: list[str],
    initial: str | None,
) -> list[str]:
    patterns = _compile_location_patterns(automaton, history_var, locations)
    seen: list[str] = []

    for raw_line in log_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        for pattern in patterns:
            match = pattern.search(line)
            if match:
                seen.append(match.group(1))
                break

    compressed: list[str] = []
    for location in seen:
        if not compressed or compressed[-1] != location:
            compressed.append(location)

    if compressed:
        return compressed

    loc_alt = "|".join(re.escape(loc) for loc in sorted(locations, key=len, reverse=True))
    generic_patterns = [
        re.compile(rf"\b(?:state|location)\b\s*[:=]\s*\b({loc_alt})\b", re.IGNORECASE),
    ]
    for raw_line in log_text.splitlines():
        line = raw_line.strip()
        for pattern in generic_patterns:
            match = pattern.search(line)
            if match:
                loc = match.group(1)
                if not compressed or compressed[-1] != loc:
                    compressed.append(loc)
                break

    return compressed


def _compile_variable_patterns(automaton: str, variable: str, history_var: str) -> list[re.Pattern[str]]:
    aut = re.escape(automaton)
    var = re.escape(variable)
    hist = re.escape(history_var)
    value = r"([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?|true|false|[A-Za-z_]\w*)"
    return [
        re.compile(rf"\b{hist}\b\s*[:=]\s*{value}"),
        re.compile(rf"\b{aut}(?:_0)?_{var}\b\s*[:=]\s*{value}"),
        re.compile(rf"\b{aut}\s*\.\s*{var}\b\s*[:=]\s*{value}"),
        re.compile(rf"\b{aut}\b.*?\b{var}\b\s*[:=]\s*{value}"),
        re.compile(rf"\b{var}\b\s*[:=]\s*{value}"),
    ]


def extract_variable_history(
    log_text: str,
    automaton: str,
    variable: str,
    history_var: str,
) -> list[str]:
    patterns = _compile_variable_patterns(automaton, variable, history_var)
    values: list[str] = []
    for raw_line in log_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        for pattern in patterns:
            match = pattern.search(line)
            if match:
                values.append(match.group(1))
                break
    return values


def _normalize_samples(values: list[str], expected_samples: int | None, initial_value: str | None, allow_short: bool) -> list[str]:
    normalized = list(values)
    if expected_samples is not None and initial_value is not None:
        if len(normalized) == expected_samples - 1:
            normalized.insert(0, initial_value)
        elif normalized and normalized[0] != initial_value and len(normalized) < expected_samples:
            normalized.insert(0, initial_value)

    if expected_samples is not None:
        if len(normalized) < expected_samples and not allow_short:
            raise SystemExit(
                f"Extracted only {len(normalized)} samples, expected {expected_samples}. "
                "The cifsim log may not contain the full observable history."
            )
        if len(normalized) > expected_samples:
            normalized = normalized[:expected_samples]
    return normalized


def write_reference_csv(values: list[str], output_csv: str | Path, history_var: str) -> Path:
    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sample", history_var])
        writer.writeheader()
        for index, value in enumerate(values):
            writer.writerow({"sample": index, history_var: value})
    return output_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a cifsim event-trace log to an observable CSV reference.")
    parser.add_argument("--cif", required=True, help="Source CIF model used to discover automata, locations and variables.")
    parser.add_argument("--log", required=True, help="cifsim stdout/stderr log produced in trace mode.")
    parser.add_argument("--output-csv", required=True, help="Output observable ESCET reference CSV.")
    parser.add_argument("--history-var", required=True, help="Generated history variable to compare, e.g. CoffeeMachine_0_location or ShipCounter_0_count.")
    parser.add_argument("--automaton", default=None, help="Observable automaton name. Defaults to the prefix of --history-var.")
    parser.add_argument("--variable", default=None, help="Observable CIF variable name for non-location histories. Defaults to the suffix of --history-var.")
    parser.add_argument("--expected-samples", type=int, default=None, help="Expected number of samples, usually number of events + 1.")
    parser.add_argument("--allow-short", action="store_true", help="Allow fewer samples than --expected-samples.")
    args = parser.parse_args()

    automata_locations = read_cif_automaton_locations(args.cif)
    automata_variables = read_cif_automaton_variables(args.cif)
    automaton = args.automaton or _infer_automaton_from_history_var(args.history_var)
    if not automaton:
        raise SystemExit(
            "Cannot infer observable automaton from --history-var. "
            "Pass --automaton explicitly."
        )

    log_text = Path(args.log).read_text(errors="replace")

    if args.history_var.endswith("_location"):
        if automaton not in automata_locations:
            available = ", ".join(sorted(automata_locations)) or "none"
            raise SystemExit(f"Automaton {automaton!r} not found in {args.cif}. Available: {available}")
        meta = automata_locations[automaton]
        values = extract_location_history(
            log_text=log_text,
            automaton=automaton,
            history_var=args.history_var,
            locations=meta.locations,
            initial=meta.initial,
        )
        initial_value = meta.initial
    else:
        variable = args.variable or _infer_variable_from_history_var(args.history_var)
        if not variable:
            raise SystemExit(
                "Cannot infer observable variable from --history-var. "
                "Pass --variable explicitly."
            )
        if automaton not in automata_variables:
            available = ", ".join(sorted(automata_variables)) or "none"
            raise SystemExit(f"Automaton {automaton!r} not found in {args.cif}. Available: {available}")
        values = extract_variable_history(
            log_text=log_text,
            automaton=automaton,
            variable=variable,
            history_var=args.history_var,
        )
        initial_value = automata_variables[automaton].variables.get(variable)

    if not values:
        raise SystemExit(
            "Could not extract an observable history from the cifsim log. "
            "Keep the log file and adapt scripts/cifsim_event_log_to_csv.py for this ESCET output format."
        )

    if (
        args.expected_samples is not None
        and len(values) < args.expected_samples
        and "Simulation resulted in deadlock" in log_text
    ):
        raise SystemExit(
            f"Extracted only {len(values)} samples, expected {args.expected_samples}, "
            "and the cifsim log reports a deadlock. This usually means that the "
            "event trace requested an event that was not enabled by the current CIF state. "
            "For behavior comparison, use an executable event trace; keep boundary/disabled-event "
            "checks as separate negative tests."
        )

    values = _normalize_samples(values, args.expected_samples, initial_value, args.allow_short)
    path = write_reference_csv(values, args.output_csv, args.history_var)
    print(f"ESCET observable reference CSV: {path}")
    print(f"samples: {len(values)}")
    print(f"history variable: {args.history_var}")


if __name__ == "__main__":
    main()
