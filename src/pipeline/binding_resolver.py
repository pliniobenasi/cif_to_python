"""Binding resolver for generated CIF module instances.

The resolver analyzes template instances and qualified references to derive
source -> target variable bindings without relying on case-study names.

Example pattern:

    SourceInstance.variable[index] -> TargetInstance.required_input

The output is consumed by the generic builder to connect generated modules.
"""

from dataclasses import dataclass
import re
from pathlib import Path
from typing import Iterable

from pipeline.cif_parser import CifAutomaton, CifInstance, CifModel, parse_file


@dataclass(frozen=True)
class IRBinding:
    source_module: str
    source_variable: str
    target_module: str
    target_variable: str
    reason: str
    source_expression: str | None = None
    target_parameter: str | None = None

    def as_tuple(self) -> tuple[str, str, str, str]:
        return (
            self.source_module,
            self.source_variable,
            self.target_module,
            self.target_variable,
        )

    def as_dict(self) -> dict[str, str | None]:
        return {
            "source_module": self.source_module,
            "source_variable": self.source_variable,
            "target_module": self.target_module,
            "target_variable": self.target_variable,
            "reason": self.reason,
            "source_expression": self.source_expression,
            "target_parameter": self.target_parameter,
        }


def _instance_numeric_suffix(name: str) -> int:
    match = re.search(r"_(\d+)$", name)
    return int(match.group(1)) if match else -1


def _template_by_name(model: CifModel, name: str) -> CifAutomaton:
    template = model.automaton_by_name(name)
    if template is None:
        raise ValueError(f"Template {name!r} not found in IR")
    return template


def _instances(model: CifModel, template_filter: Iterable[str] | None = None) -> list[CifInstance]:
    allowed = set(template_filter) if template_filter is not None else None
    result = [
        instance
        for instance in model.instances
        if allowed is None or instance.template_name in allowed
    ]
    result.sort(key=lambda instance: (instance.template_name, _instance_numeric_suffix(instance.name), instance.name))
    return result


def _source_expr_to_module_variable(expr: str) -> tuple[str, str] | None:
    expr = expr.strip()

    match = re.match(r"^([A-Za-z_]\w*)\.([A-Za-z_]\w*)\[(\d+)\]$", expr)
    if match:
        return match.group(1), f"{match.group(2)}_{match.group(3)}"

    match = re.match(r"^([A-Za-z_]\w*)\.([A-Za-z_]\w*)$", expr)
    if match:
        return match.group(1), match.group(2)

    return None


def _collect_template_text(template: CifAutomaton) -> str:
    parts: list[str] = []

    for variable in template.variables:
        if variable.value:
            parts.append(variable.value)

    for location in template.locations:
        parts.extend(location.equations)
        parts.extend(location.invariants)

    for edge in template.edges:
        if edge.guard:
            parts.append(edge.guard)
        parts.extend(edge.updates)

    return "\n".join(parts)


def _qualified_references_for_parameter(template: CifAutomaton, parameter_name: str) -> list[str]:
    text = _collect_template_text(template)
    refs: list[str] = []

    for match in re.finditer(rf"\b{re.escape(parameter_name)}\.([A-Za-z_]\w*)\b", text):
        attr = match.group(1)
        if attr not in refs:
            refs.append(attr)

    return refs


def resolve_bindings(
    model: CifModel,
    template_filter: Iterable[str] | None = None,
    limit_per_template: int | None = None,
) -> list[IRBinding]:
    bindings: list[IRBinding] = []
    per_template_count: dict[str, int] = {}

    for instance in _instances(model, template_filter):
        seen_for_template = per_template_count.get(instance.template_name, 0)
        if limit_per_template is not None and seen_for_template >= limit_per_template:
            continue
        per_template_count[instance.template_name] = seen_for_template + 1

        template = _template_by_name(model, instance.template_name)

        for index, parameter in enumerate(template.parameters):
            if index >= len(instance.args):
                continue

            arg = instance.args[index].strip()

            # Direct/input-like parameter, e.g. alg real T_mean.
            if parameter.kind is not None:
                source = _source_expr_to_module_variable(arg)
                if source is None:
                    continue

                source_module, source_variable = source
                bindings.append(
                    IRBinding(
                        source_module=source_module,
                        source_variable=source_variable,
                        target_module=instance.name,
                        target_variable=parameter.name,
                        reason="direct_template_parameter",
                        source_expression=arg,
                        target_parameter=parameter.name,
                    )
                )
                continue

            # Object-like parameter, e.g. Nodes nodes, LAI lai.
            refs = _qualified_references_for_parameter(template, parameter.name)

            for attr in refs:
                bindings.append(
                    IRBinding(
                        source_module=arg,
                        source_variable=attr,
                        target_module=instance.name,
                        target_variable=attr,
                        reason="object_parameter_qualified_reference",
                        source_expression=arg,
                        target_parameter=parameter.name,
                    )
                )

    bindings.sort(key=lambda b: (b.target_module, b.target_variable, b.source_module, b.source_variable))
    return bindings


def resolve_bindings_from_file(
    cif_path: str | Path,
    template_filter: Iterable[str] | None = None,
    limit_per_template: int | None = None,
) -> list[IRBinding]:
    model = parse_file(cif_path)
    return resolve_bindings(
        model,
        template_filter=template_filter,
        limit_per_template=limit_per_template,
    )


def bindings_as_dicts(bindings: Iterable[IRBinding]) -> list[dict[str, str | None]]:
    return [binding.as_dict() for binding in bindings]


def main() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("cif", help="Path to CIF file")
    parser.add_argument("--templates", nargs="*", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    bindings = resolve_bindings_from_file(
        args.cif,
        template_filter=args.templates,
        limit_per_template=args.limit,
    )

    if args.json:
        print(json.dumps(bindings_as_dicts(bindings), indent=2))
        return

    for binding in bindings:
        print(
            f"{binding.source_module}.{binding.source_variable} -> "
            f"{binding.target_module}.{binding.target_variable} "
            f"({binding.reason})"
        )

    print(f"\nTotal bindings: {len(bindings)}")


if __name__ == "__main__":
    main()
