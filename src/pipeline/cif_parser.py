from __future__ import annotations

"""
Experimental CIF Intermediate Representation parser.

Goal:
    Build a common IR that can describe both small event-driven CIF models
    and larger template-based CIF structures.

This parser is intentionally conservative. It is not a full CIF compiler.
It extracts the structural information needed by the current modular Python backend:

- inputs
- constants
- events
- automata and template automata
- parameters
- variables
- algebraic lists
- locations
- edges
- template instances
- dependency candidates between instances
"""

from dataclasses import asdict, dataclass, field
import json
import re
from pathlib import Path
from typing import Any


@dataclass
class CifDeclaration:
    kind: str
    name: str
    type_name: str | None = None
    value: str | None = None
    raw: str | None = None


@dataclass
class CifParameter:
    raw: str
    name: str
    type_name: str | None = None
    kind: str | None = None


@dataclass
class CifVariable:
    kind: str
    name: str
    type_name: str | None = None
    value: str | None = None
    raw: str | None = None


@dataclass
class CifAlgList:
    name: str
    type_name: str
    size: int
    values: list[str]
    raw: str | None = None


@dataclass
class CifEdge:
    event: str | None
    source_location: str | None
    guard: str | None = None
    updates: list[str] = field(default_factory=list)
    target_location: str | None = None
    raw: str | None = None


@dataclass
class CifLocation:
    name: str
    initial: bool = False
    marked: bool = False
    equations: list[str] = field(default_factory=list)
    invariants: list[str] = field(default_factory=list)
    edges: list[CifEdge] = field(default_factory=list)
    raw_header: str | None = None


@dataclass
class CifAutomaton:
    name: str
    is_template: bool = False
    parameters: list[CifParameter] = field(default_factory=list)
    events: list[CifDeclaration] = field(default_factory=list)
    variables: list[CifVariable] = field(default_factory=list)
    alg_lists: list[CifAlgList] = field(default_factory=list)
    locations: list[CifLocation] = field(default_factory=list)
    edges: list[CifEdge] = field(default_factory=list)
    raw_header: str | None = None
    raw_body: str | None = None


@dataclass
class CifInstance:
    name: str
    template_name: str
    args: list[str] = field(default_factory=list)
    line: int | None = None
    raw: str | None = None
    dependency_candidates: list[str] = field(default_factory=list)


@dataclass
class CifModel:
    source_path: str | None = None
    inputs: list[CifDeclaration] = field(default_factory=list)
    constants: list[CifDeclaration] = field(default_factory=list)
    events: list[CifDeclaration] = field(default_factory=list)
    automata: list[CifAutomaton] = field(default_factory=list)
    instances: list[CifInstance] = field(default_factory=list)
    unsupported_constructs: dict[str, int] = field(default_factory=dict)

    def template_automata(self) -> list[CifAutomaton]:
        return [automaton for automaton in self.automata if automaton.is_template]

    def plain_automata(self) -> list[CifAutomaton]:
        return [automaton for automaton in self.automata if not automaton.is_template]

    def instance_counts_by_template(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for instance in self.instances:
            counts[instance.template_name] = counts.get(instance.template_name, 0) + 1
        return counts

    def automaton_by_name(self, name: str) -> CifAutomaton | None:
        for automaton in self.automata:
            if automaton.name == name:
                return automaton
        return None

    def summary(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "inputs": len(self.inputs),
            "constants": len(self.constants),
            "global_events": len(self.events),
            "automata": len(self.automata),
            "template_automata": len(self.template_automata()),
            "plain_automata": len(self.plain_automata()),
            "instances": len(self.instances),
            "instance_counts_by_template": self.instance_counts_by_template(),
            "unsupported_constructs": self.unsupported_constructs,
        }

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    lines = []
    for line in text.splitlines():
        lines.append(line.split("//", 1)[0])
    return "\n".join(lines)


def split_top_level_csv(raw: str) -> list[str]:
    result: list[str] = []
    current: list[str] = []
    depth_round = 0
    depth_square = 0

    for ch in raw:
        if ch == "(":
            depth_round += 1
        elif ch == ")":
            depth_round = max(0, depth_round - 1)
        elif ch == "[":
            depth_square += 1
        elif ch == "]":
            depth_square = max(0, depth_square - 1)

        if ch == "," and depth_round == 0 and depth_square == 0:
            item = "".join(current).strip()
            if item:
                result.append(item)
            current = []
        else:
            current.append(ch)

    item = "".join(current).strip()
    if item:
        result.append(item)

    return result


def split_statements(text: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    depth_round = 0
    depth_square = 0

    for ch in text:
        if ch == "(":
            depth_round += 1
        elif ch == ")":
            depth_round = max(0, depth_round - 1)
        elif ch == "[":
            depth_square += 1
        elif ch == "]":
            depth_square = max(0, depth_square - 1)

        if ch == ";" and depth_round == 0 and depth_square == 0:
            item = "".join(current).strip()
            if item:
                statements.append(item + ";")
            current = []
        else:
            current.append(ch)

    item = "".join(current).strip()
    if item:
        statements.append(item)

    return statements


def parse_parameter(raw: str) -> CifParameter:
    raw = raw.strip()
    parts = raw.split()
    if not parts:
        return CifParameter(raw=raw, name=raw)

    if len(parts) >= 3 and parts[0] in {"alg", "disc", "cont", "input"}:
        return CifParameter(
            raw=raw,
            name=parts[-1],
            kind=parts[0],
            type_name=" ".join(parts[1:-1]),
        )

    if len(parts) >= 2:
        return CifParameter(raw=raw, name=parts[-1], type_name=" ".join(parts[:-1]))

    return CifParameter(raw=raw, name=raw)


def parse_parameters(raw: str | None) -> list[CifParameter]:
    if raw is None or not raw.strip():
        return []

    return [parse_parameter(part) for part in split_top_level_csv(raw.replace(";", ","))]


def parse_declaration_statement(statement: str) -> CifDeclaration | None:
    stmt = statement.strip().rstrip(";").strip()

    input_match = re.match(r"^input\s+(.+?)\s+([A-Za-z_]\w*)$", stmt)
    if input_match:
        return CifDeclaration(
            kind="input",
            type_name=input_match.group(1).strip(),
            name=input_match.group(2),
            raw=statement,
        )

    const_match = re.match(r"^const\s+(.+?)\s+([A-Za-z_]\w*)\s*=\s*(.+)$", stmt)
    if const_match:
        return CifDeclaration(
            kind="const",
            type_name=const_match.group(1).strip(),
            name=const_match.group(2),
            value=const_match.group(3).strip(),
            raw=statement,
        )

    event_match = re.match(r"^event\s+(.+)$", stmt)
    if event_match:
        # CIF can declare multiple events in one statement.
        names = [name.strip() for name in event_match.group(1).split(",") if name.strip()]
        if len(names) == 1:
            return CifDeclaration(kind="event", name=names[0], raw=statement)

    return None


def parse_event_declarations(statement: str) -> list[CifDeclaration]:
    stmt = statement.strip().rstrip(";").strip()

    match = re.match(r"^(event|controllable|uncontrollable)\s+(.+)$", stmt)
    if not match:
        return []

    kind = match.group(1)
    names = [name.strip() for name in match.group(2).split(",") if name.strip()]

    return [
        CifDeclaration(kind=kind, name=name, raw=statement)
        for name in names
    ]


def parse_variable_statement(statement: str) -> CifVariable | None:
    stmt = statement.strip().rstrip(";").strip()

    typed_match = re.match(
        r"^(disc|alg)\s+(.+?)\s+([A-Za-z_]\w*)\s*(?:=|der\s+)?\s*(.*)$",
        stmt,
        flags=re.DOTALL,
    )
    if typed_match:
        value = typed_match.group(4).strip()
        return CifVariable(
            kind=typed_match.group(1),
            type_name=typed_match.group(2).strip(),
            name=typed_match.group(3),
            value=value if value else None,
            raw=statement,
        )

    cont_match = re.match(
        r"^cont\s+(?:(.+?)\s+)?([A-Za-z_]\w*)\s*(?:=|der\s+)?\s*(.*)$",
        stmt,
        flags=re.DOTALL,
    )
    if cont_match:
        value = cont_match.group(3).strip()
        return CifVariable(
            kind="cont",
            type_name=cont_match.group(1).strip() if cont_match.group(1) else None,
            name=cont_match.group(2),
            value=value if value else None,
            raw=statement,
        )

    return None


def parse_alg_lists(text: str) -> list[CifAlgList]:
    lists: list[CifAlgList] = []

    pattern = re.compile(
        r"alg\s+list\s*\[\s*(\d+)\s*\]\s+(.+?)\s+([A-Za-z_]\w*)\s*=\s*\[(.*?)\]\s*;",
        flags=re.DOTALL,
    )

    for match in pattern.finditer(text):
        size = int(match.group(1))
        type_name = match.group(2).strip()
        name = match.group(3)
        values = split_top_level_csv(match.group(4))
        lists.append(
            CifAlgList(
                name=name,
                type_name=type_name,
                size=size,
                values=values,
                raw=match.group(0),
            )
        )

    return lists


def parse_edge_statement(statement: str, source_location: str | None) -> CifEdge | None:
    stmt = statement.strip().rstrip(";").strip()
    if not stmt.startswith("edge "):
        return None

    raw = statement
    rest = stmt[len("edge "):].strip()

    event = None
    guard = None
    updates: list[str] = []
    target = None

    if not rest:
        return CifEdge(event=None, source_location=source_location, raw=raw)

    parts = rest.split(None, 1)
    event = parts[0]
    tail = parts[1] if len(parts) > 1 else ""

    guard_match = re.search(r"\bwhen\b\s+(.*?)(?=\bdo\b|\bgoto\b|$)", tail)
    if guard_match:
        guard = guard_match.group(1).strip()

    do_match = re.search(r"\bdo\b\s+(.*?)(?=\bgoto\b|$)", tail)
    if do_match:
        update_raw = do_match.group(1).strip()
        updates = [item.strip() for item in split_top_level_csv(update_raw) if item.strip()]

    goto_match = re.search(r"\bgoto\b\s+([A-Za-z_]\w*)", tail)
    if goto_match:
        target = goto_match.group(1)

    return CifEdge(
        event=event,
        source_location=source_location,
        guard=guard,
        updates=updates,
        target_location=target,
        raw=raw,
    )


def _location_flags(header_tail: str) -> tuple[bool, bool]:
    normalized = header_tail.replace(";", " ").replace(":", " ")
    words = set(normalized.split())
    return "initial" in words, "marked" in words


def parse_locations_and_edges(body: str) -> tuple[list[CifLocation], list[CifEdge]]:
    locations: list[CifLocation] = []
    automaton_level_edges: list[CifEdge] = []

    current: CifLocation | None = None

    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        loc_match = re.match(r"^location\s+([A-Za-z_]\w*)\s*:(.*)$", line)
        if loc_match:
            name = loc_match.group(1)
            header_tail = loc_match.group(2)
            initial, marked = _location_flags(header_tail)
            current = CifLocation(
                name=name,
                initial=initial,
                marked=marked,
                raw_header=line,
            )
            locations.append(current)
            continue

        if line.startswith("equation "):
            equation = line.rstrip(";")
            if current is not None:
                current.equations.append(equation)
            continue

        if line.startswith("invariant "):
            invariant = line.rstrip(";")
            if current is not None:
                current.invariants.append(invariant)
            continue

        if line.startswith("initial"):
            if current is not None:
                current.initial = True
            continue

        if line.startswith("marked"):
            if current is not None:
                current.marked = True
            continue

        if line.startswith("edge "):
            edge = parse_edge_statement(line, current.name if current else None)
            if edge is None:
                continue
            if current is not None:
                current.edges.append(edge)
            else:
                automaton_level_edges.append(edge)

    return locations, automaton_level_edges


def extract_automaton_blocks(text: str) -> tuple[list[tuple[str, str, int, int]], str]:
    lines = text.splitlines()
    blocks: list[tuple[str, str, int, int]] = []
    outside_lines: list[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"^\s*automaton\b", line):
            start = i
            block_lines = [line]
            i += 1

            while i < len(lines):
                block_lines.append(lines[i])

                # CIF expressions can contain an indented "end;" as part of
                # piecewise expressions. Automaton blocks in the analysed CIF
                # files end with a left-aligned "end".
                if re.match(r"^end\s*;?\s*$", lines[i]):
                    break

                i += 1

            end = i
            header = line.strip()
            body = "\n".join(block_lines[1:-1])
            blocks.append((header, body, start + 1, end + 1))
            i += 1
        else:
            outside_lines.append(line)
            i += 1

    return blocks, "\n".join(outside_lines)


def parse_automaton_block(header: str, body: str) -> CifAutomaton:
    header_clean = header.strip().rstrip(":").strip()

    match = re.match(
        r"^automaton\s+(def\s+)?([A-Za-z_]\w*)\s*(?:\((.*?)\))?\s*:?\s*$",
        header_clean,
    )
    if not match:
        raise ValueError(f"Unsupported automaton header: {header}")

    is_template = bool(match.group(1))
    name = match.group(2)
    params_raw = match.group(3)

    alg_lists = parse_alg_lists(body)

    body_without_lists = body
    for alg_list in alg_lists:
        if alg_list.raw:
            body_without_lists = body_without_lists.replace(alg_list.raw, "")

    events: list[CifDeclaration] = []
    variables: list[CifVariable] = []

    for statement in split_statements(body_without_lists):
        events.extend(parse_event_declarations(statement))

        variable = parse_variable_statement(statement)
        if variable is not None:
            variables.append(variable)

    locations, automaton_level_edges = parse_locations_and_edges(body_without_lists)

    all_edges = list(automaton_level_edges)
    for location in locations:
        all_edges.extend(location.edges)

    return CifAutomaton(
        name=name,
        is_template=is_template,
        parameters=parse_parameters(params_raw),
        events=events,
        variables=variables,
        alg_lists=alg_lists,
        locations=locations,
        edges=all_edges,
        raw_header=header,
        raw_body=body,
    )


def parse_top_level_declarations(outside_text: str) -> tuple[list[CifDeclaration], list[CifDeclaration], list[CifDeclaration]]:
    inputs: list[CifDeclaration] = []
    constants: list[CifDeclaration] = []
    events: list[CifDeclaration] = []

    for statement in split_statements(outside_text):
        declaration = parse_declaration_statement(statement)
        if declaration is not None:
            if declaration.kind == "input":
                inputs.append(declaration)
            elif declaration.kind == "const":
                constants.append(declaration)
            elif declaration.kind == "event":
                events.append(declaration)

        events.extend(parse_event_declarations(statement))

    return inputs, constants, events


def dependency_candidates_from_args(args: list[str]) -> list[str]:
    candidates: list[str] = []

    for arg in args:
        for name in re.findall(r"\b[A-Za-z_]\w*\b", arg):
            if name in {"if", "elif", "else", "end", "real", "alg", "disc", "cont"}:
                continue
            if name not in candidates:
                candidates.append(name)

    return candidates


def parse_instances(outside_text: str) -> list[CifInstance]:
    instances: list[CifInstance] = []

    for line_no, raw_line in enumerate(outside_text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue

        match = re.match(
            r"^([A-Za-z_]\w*)\s*:\s*([A-Za-z_]\w*)\s*\((.*?)\)\s*;\s*$",
            line,
        )
        if not match:
            continue

        name = match.group(1)
        template_name = match.group(2)
        args = split_top_level_csv(match.group(3))

        instances.append(
            CifInstance(
                name=name,
                template_name=template_name,
                args=args,
                line=line_no,
                raw=line,
                dependency_candidates=dependency_candidates_from_args(args),
            )
        )

    return instances


def detect_unsupported_constructs(text: str) -> dict[str, int]:
    patterns = {
        "automaton_def": r"\bautomaton\s+def\b",
        "continuous_derivative_apostrophe": r"[A-Za-z_]\w*'\s*=",
        "continuous_derivative_der": r"\bder\b",
        "algebraic_lists": r"\balg\s+list\s*\[",
        "piecewise_if": r"\bif\b.*:",
        "qualified_references": r"\b[A-Za-z_]\w*\.[A-Za-z_]\w*\b",
        "math_functions": r"\b(pow|exp|ln|max|min)\s*\(",
        "template_instances": r"^\s*[A-Za-z_]\w*\s*:\s*[A-Za-z_]\w*\s*\(",
    }

    result: dict[str, int] = {}
    for name, pattern in patterns.items():
        result[name] = len(re.findall(pattern, text, flags=re.MULTILINE | re.DOTALL))

    return result


class CifIRParser:
    def parse_text(self, text: str, source_path: str | None = None) -> CifModel:
        clean = strip_comments(text)
        blocks, outside_text = extract_automaton_blocks(clean)

        automata = [
            parse_automaton_block(header, body)
            for header, body, _start, _end in blocks
        ]

        inputs, constants, global_events = parse_top_level_declarations(outside_text)
        instances = parse_instances(outside_text)

        return CifModel(
            source_path=source_path,
            inputs=inputs,
            constants=constants,
            events=global_events,
            automata=automata,
            instances=instances,
            unsupported_constructs=detect_unsupported_constructs(clean),
        )

    def parse_file(self, path: str | Path) -> CifModel:
        path = Path(path)
        return self.parse_text(path.read_text(), source_path=str(path))


def parse_file(path: str | Path) -> CifModel:
    return CifIRParser().parse_file(path)


def parse_text(text: str, source_path: str | None = None) -> CifModel:
    return CifIRParser().parse_text(text, source_path=source_path)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("cif", help="Path to the CIF model")
    parser.add_argument("--json", help="Optional JSON output path")
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()

    model = parse_file(args.cif)
    print(json.dumps(model.summary(), indent=2))

    if args.json:
        output_path = Path(args.json)
        output_path.write_text(model.to_json(indent=2))
        print(f"Written IR JSON: {output_path}")

    if not args.summary_only:
        print("\nAutomata:")
        for automaton in model.automata:
            kind = "template" if automaton.is_template else "automaton"
            print(
                f"- {automaton.name} ({kind}): "
                f"{len(automaton.locations)} locations, "
                f"{len(automaton.edges)} edges, "
                f"{len(automaton.variables)} variables, "
                f"{len(automaton.alg_lists)} alg lists"
            )

        if model.instances:
            print("\nInstance counts:")
            for template_name, count in model.instance_counts_by_template().items():
                print(f"- {template_name}: {count}")


if __name__ == "__main__":
    main()
