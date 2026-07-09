#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path
from typing import Any

from pipeline.cif_parser import CifModel, CifAutomaton, CifEdge, CifInstance, parse_file


RUNTIME_CODE = Path(__file__).with_name("optimized_runtime_template.py").read_text()


def _snake_case(name: str) -> str:
    first = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    snake = re.sub("([a-z0-9])([A-Z])", r"\1_\2", first).lower()
    return re.sub(r"[^a-z0-9_]+", "_", snake).strip("_")


def _class_name(name: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_]+", "_", name)
    parts = [part for part in clean.split("_") if part]
    return "".join(part[:1].upper() + part[1:] for part in parts) + "Module"


def _numeric_suffix(name: str) -> int:
    match = re.search(r"_(\d+)$", name)
    return int(match.group(1)) if match else 0


def _constant_map(model: CifModel) -> dict[str, str]:
    return {
        declaration.name: declaration.value
        for declaration in model.constants
        if declaration.value is not None
    }


def _global_input_names(model: CifModel) -> list[str]:
    return [declaration.name for declaration in model.inputs]


def _instances(model: CifModel, template_name: str) -> list[CifInstance]:
    instances = [
        instance
        for instance in model.instances
        if instance.template_name == template_name
    ]
    instances.sort(key=lambda instance: _numeric_suffix(instance.name))
    return instances


def _edge_to_dict(edge: CifEdge) -> dict[str, Any]:
    return {
        "event": edge.event,
        "source_location": edge.source_location,
        "guard": edge.guard,
        "updates": edge.updates,
        "target_location": edge.target_location,
        "raw": edge.raw,
    }


def _variable_to_dict(variable) -> dict[str, Any]:
    return {
        "kind": variable.kind,
        "name": variable.name,
        "type_name": variable.type_name,
        "value": variable.value,
        "raw": variable.raw,
    }


def _parameter_to_dict(parameter) -> dict[str, Any]:
    return {
        "raw": parameter.raw,
        "name": parameter.name,
        "kind": parameter.kind,
        "type_name": parameter.type_name,
    }


def _initial_location(template: CifAutomaton) -> str:
    for location in template.locations:
        if location.initial:
            return location.name
    if template.locations:
        return template.locations[0].name
    return "UNKNOWN"


def _derivatives(template: CifAutomaton) -> dict[str, str]:
    derivatives: dict[str, str] = {}
    for location in template.locations:
        for equation in location.equations:
            match = re.search(r"equation\s+([A-Za-z_]\w*)'\s*=\s*(.+)$", equation)
            if match:
                derivatives[match.group(1)] = match.group(2).strip().rstrip(";")
    return derivatives


def _template_text(template: CifAutomaton) -> str:
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


def _qualified_ref_map(template: CifAutomaton) -> dict[str, str]:
    mapping: dict[str, str] = {}
    raw_text = _template_text(template)
    for parameter in template.parameters:
        if parameter.kind is not None:
            continue
        prefix = parameter.name + "."
        for match in re.finditer(rf"\b{re.escape(parameter.name)}\.([A-Za-z_]\w*)\b", raw_text):
            attr = match.group(1)
            mapping[prefix + attr] = attr
    return mapping


def _required_input_names(template: CifAutomaton, model: CifModel) -> list[str]:
    names: list[str] = []
    text = _template_text(template)
    for parameter in template.parameters:
        if parameter.kind is not None:
            if parameter.name not in names:
                names.append(parameter.name)
            continue
        refs: list[str] = []
        for match in re.finditer(rf"\b{re.escape(parameter.name)}\.([A-Za-z_]\w*)\b", text):
            attr = match.group(1)
            if attr not in refs:
                refs.append(attr)
        for attr in refs:
            if attr not in names:
                names.append(attr)
    for global_input in _global_input_names(model):
        if re.search(rf"\b{re.escape(global_input)}\b", text) and global_input not in names:
            names.append(global_input)
    return names



_AUTOMATIC_TEMPORAL_EVENT_NAMES = {
    "tick",
    "time_step",
    "advance_time",
    "clock_tick",
    "hour",
    "day",
    "daily_update",
}


def _event_trigger(kind: str, name: str) -> str:
    if kind == "uncontrollable":
        return "automatic"
    if name in _AUTOMATIC_TEMPORAL_EVENT_NAMES:
        return "automatic_temporal"
    return "external"


def _event_metadata(template: CifAutomaton, model: CifModel) -> dict[str, dict[str, Any]]:
    metadata: dict[str, dict[str, Any]] = {}

    def register(name: str, kind: str, scope: str, raw: str | None = None) -> None:
        clean_name = str(name).strip()
        if not clean_name:
            return

        # Automaton-local declarations override global generic declarations.
        existing = metadata.get(clean_name)
        if existing is not None and existing.get("scope") == "automaton" and scope == "global":
            return

        metadata[clean_name] = {
            "name": clean_name,
            "kind": kind,
            "trigger": _event_trigger(kind, clean_name),
            "scope": scope,
            "raw": raw,
        }

    for declaration in model.events:
        register(declaration.name, declaration.kind, "global", declaration.raw)

    for declaration in template.events:
        register(declaration.name, declaration.kind, "automaton", declaration.raw)

    for edge in template.edges:
        if edge.event is not None and edge.event not in metadata:
            register(edge.event, "event", "implicit", edge.raw)

    return metadata


def _template_spec(template: CifAutomaton, model: CifModel) -> dict[str, Any]:
    return {
        "template_name": template.name,
        "parameters": [_parameter_to_dict(parameter) for parameter in template.parameters],
        "variables": [_variable_to_dict(variable) for variable in template.variables],
        "edges": [_edge_to_dict(edge) for edge in template.edges],
        "events": _event_metadata(template, model),
        "event_metadata": _event_metadata(template, model),
        "derivatives": _derivatives(template),
        "initial_location": _initial_location(template),
        "required_inputs": _required_input_names(template, model),
    }


def _instance_source_specs(instances: list[CifInstance]) -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}
    for instance in instances:
        specs[instance.name] = {
            "template": instance.template_name,
            "args": list(instance.args),
            "instance_index": _numeric_suffix(instance.name),
        }
    return specs


def _selected_templates(model: CifModel) -> list[CifAutomaton]:
    templates: list[CifAutomaton] = []
    for automaton in model.automata:
        if not automaton.is_template:
            continue
        if not _instances(model, automaton.name):
            continue
        if not automaton.edges:
            continue
        templates.append(automaton)
    templates.sort(key=lambda template: template.name)
    return templates


def _module_code(template: CifAutomaton, model: CifModel) -> str:
    spec = _template_spec(template, model)
    qualified_ref_map = _qualified_ref_map(template)
    instances = _instances(model, template.name)
    cls = _class_name(template.name)

    lines = [
        "from __future__ import annotations",
        "",
        "from .runtime import CifTemplateModule, STEP_GRANULARITY",
        "",
        "",
        f"TEMPLATE_NAME = {template.name!r}",
        f"TEMPLATE_SPEC = {spec!r}",
        f"QUALIFIED_REF_MAP = {qualified_ref_map!r}",
        f"INSTANCE_SPECS = {_instance_source_specs(instances)!r}",
        f"INSTANCE_COUNT = {len(instances)}",
        "",
        "",
        f"class {cls}(CifTemplateModule):",
        "    CIF_TEMPLATE_NAME = TEMPLATE_NAME",
        "    CIF_TEMPLATE_SPEC = TEMPLATE_SPEC",
        "    CIF_QUALIFIED_REF_MAP = QUALIFIED_REF_MAP",
        "",
        "    def __init__(self, name: str | None = None, instance_index: int | None = None, granularity=STEP_GRANULARITY[\"HOURLY\"], params=None):",
        "        self.instance_index = instance_index",
        "        super().__init__(name or TEMPLATE_NAME, granularity, params)",
        "",
        "",
        "def get_instance_spec(index: int) -> dict:",
        "    instance_name = f\"{TEMPLATE_NAME}_{index}\"",
        "    if instance_name not in INSTANCE_SPECS:",
        "        raise IndexError(f\"{TEMPLATE_NAME} instance index out of range: {index}\")",
        "    spec = dict(INSTANCE_SPECS[instance_name])",
        "    spec[\"name\"] = instance_name",
        "    return spec",
        "",
        "",
        f"def create_module(index: int, granularity=STEP_GRANULARITY[\"HOURLY\"]) -> {cls}:",
        "    spec = get_instance_spec(index)",
        f"    return {cls}(name=spec[\"name\"], instance_index=spec[\"instance_index\"], granularity=granularity)",
        "",
    ]
    return "\n".join(lines)


def _factory_code(templates: list[CifAutomaton]) -> str:
    imports = []
    registry_items = []
    for template in templates:
        module_name = _snake_case(template.name)
        imports.append(f"from . import {module_name}")
        registry_items.append(f"    {template.name!r}: {module_name},")
    template_names = {template.name for template in templates}

    lines = ["from __future__ import annotations", ""]
    lines.extend(imports)
    lines.extend(["", "REGISTRY = {"])
    lines.extend(registry_items)
    lines.extend(["}", "", "INSTANCE_COUNTS = {name: module.INSTANCE_COUNT for name, module in REGISTRY.items()}", ""])
    lines.extend([
        "def create_module(template_name: str, index: int, granularity=None):",
        "    module = REGISTRY[template_name]",
        "    if granularity is None:",
        "        return module.create_module(index)",
        "    return module.create_module(index, granularity=granularity)",
        "",
        "",
        "def create_modules(limit_per_template: int | None = None, granularity=None):",
        "    modules = {}",
        "    for template_name, module in REGISTRY.items():",
        "        count = module.INSTANCE_COUNT",
        "        if limit_per_template is not None:",
        "            count = min(count, limit_per_template)",
        "        modules[template_name] = {}",
        "        for index in range(count):",
        "            instance = create_module(template_name, index, granularity=granularity)",
        "            modules[template_name][instance.name] = instance",
        "    return modules",
        "",
    ])

    return "\n".join(lines)


def generate_split_from_cif(cif_path: str | Path, output_dir: str | Path) -> None:
    model = parse_file(cif_path)
    output_dir = Path(output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    templates = _selected_templates(model)
    (output_dir / "__init__.py").write_text("# Generated split modular Python modules.\n")
    (output_dir / "constants.py").write_text(f"CIF_CONSTANTS = {_constant_map(model)!r}\n")
    (output_dir / "runtime.py").write_text(RUNTIME_CODE)
    for template in templates:
        (output_dir / f"{_snake_case(template.name)}.py").write_text(_module_code(template, model))
    (output_dir / "factory.py").write_text(_factory_code(templates))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cif", help="Path to a supported CIF file")
    parser.add_argument("--output-dir", "-o", default="out/generated/modules")
    args = parser.parse_args()
    generate_split_from_cif(args.cif, args.output_dir)
    print(f"Generated split modules in: {args.output_dir}")


if __name__ == "__main__":
    main()
