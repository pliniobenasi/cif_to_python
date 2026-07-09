#!/usr/bin/env python3
from __future__ import annotations

"""
Generic CIF -> modular Python package generator.

This module contains the main backend entry point used to translate a supported
CIF model into a split Python package. It builds the generated modules, the
shared runtime, the factory and the translation artifacts required to execute
and inspect the result.

Supported by this generator:
- plain automata with locations and edges;
- template automata with instances;
- algebraic/input templates based on CIF algebraic lists;
- optimized shared runtime generation;
- generated factory with dynamic module and input registries.
"""

import argparse
import re
import shutil
from pathlib import Path
from typing import Any

import pipeline.module_codegen_backend as base_generator
from pipeline.cif_parser import CifAutomaton, CifInstance, CifModel, parse_file
from pipeline.feature_analyzer import analyze_model


def _snake_case(name: str) -> str:
    name = re.sub(r"_template$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    name = re.sub(r"[^A-Za-z0-9]+", "_", name)
    return name.strip("_").lower()


def _pascal_case(name: str) -> str:
    return "".join(part.capitalize() for part in _snake_case(name).split("_") if part)


def _base_module_name(template_name: str) -> str:
    return re.sub(r"_template$", "", template_name, flags=re.IGNORECASE)


def _instances_general(model: CifModel, automaton_name: str) -> list[CifInstance]:
    real_instances = [
        instance
        for instance in model.instances
        if instance.template_name == automaton_name
    ]

    if real_instances:
        real_instances.sort(key=lambda instance: base_generator._numeric_suffix(instance.name))
        return real_instances

    automaton = model.automaton_by_name(automaton_name)
    if automaton is not None and not automaton.is_template:
        return [
            CifInstance(
                name=f"{automaton.name}_0",
                template_name=automaton.name,
                args=[],
                line=None,
                raw=f"generated single instance for plain automaton {automaton.name}",
                dependency_candidates=[],
            )
        ]

    return []


def _selected_dynamic_automata(model: CifModel) -> list[CifAutomaton]:
    selected: list[CifAutomaton] = []

    for automaton in model.automata:
        if not automaton.edges:
            continue

        if automaton.is_template and not _instances_general(model, automaton.name):
            continue

        selected.append(automaton)

    selected.sort(key=lambda automaton: automaton.name)
    return selected


def _algebraic_input_automata(model: CifModel) -> list[CifAutomaton]:
    result = [
        automaton
        for automaton in model.automata
        if automaton.alg_lists and not automaton.edges
    ]
    result.sort(key=lambda automaton: automaton.name)
    return result


def _input_instance_name(model: CifModel, template_name: str) -> str:
    for instance in model.instances:
        if instance.template_name == template_name:
            return instance.name
    return _base_module_name(template_name)


def _input_names(model: CifModel) -> list[str]:
    return [decl.name for decl in model.inputs]


def _default_input_value_expr() -> str:
    return '''def _default_input_value(name: str) -> float:
    lower = name.lower()
    if lower in {"rad", "radiation", "solar_radiation", "ppfd"} or "rad" in lower:
        return 300.0
    if lower.startswith("t_") or "temp" in lower or lower in {"t", "tin", "t_in", "tmean", "t_mean"}:
        return 20.0
    return 0.0
'''


def _algebraic_input_module_code(automaton: CifAutomaton, model: CifModel) -> str:
    template_name = automaton.name
    module_name = _input_instance_name(model, template_name)
    class_name = f"{_pascal_case(module_name)}InputModule"
    input_names = _input_names(model)
    specs = {alg.name: alg.values for alg in automaton.alg_lists}

    return f'''from __future__ import annotations

# Generated algebraic input module from CIF automaton/template: {template_name}

import math
import re
from typing import Iterable, Any


TEMPLATE_NAME = {template_name!r}
MODULE_NAME = {module_name!r}
INPUT_NAMES = {input_names!r}
ALGEBRAIC_LIST_SPECS = {specs!r}
LIST_NAMES = sorted(ALGEBRAIC_LIST_SPECS.keys())
LIST_SIZE = min(len(values) for values in ALGEBRAIC_LIST_SPECS.values()) if ALGEBRAIC_LIST_SPECS else 0

_NORMALIZED_CACHE: dict[str, str] = {{}}
_COMPILED_CACHE: dict[str, object] = {{}}


{_default_input_value_expr()}


def _normalize_expr(expr: str) -> str:
    cached = _NORMALIZED_CACHE.get(expr)
    if cached is not None:
        return cached

    normalized = str(expr).strip()
    normalized = re.sub(r"\\btrue\\b", "True", normalized)
    normalized = re.sub(r"\\bfalse\\b", "False", normalized)
    normalized = normalized.replace("^", "**")
    _NORMALIZED_CACHE[expr] = normalized
    return normalized



def _safe_eval(expr: str, env: dict[str, Any]) -> float:
    code = _COMPILED_CACHE.get(expr)
    if code is None:
        code = compile(_normalize_expr(expr), "<algebraic-input-expr>", "eval")
        _COMPILED_CACHE[expr] = code

    safe_globals = {{
        "__builtins__": {{}},
        "math": math,
        "pow": pow,
        "max": max,
        "min": min,
        "abs": abs,
        "exp": math.exp,
        "log": math.log,
        "ln": math.log,
    }}
    return float(eval(code, safe_globals, env))


class {class_name}:
    def __init__(
        self,
        name: str = MODULE_NAME,
        limit: int | None = None,
        hours: int = 48,
        **input_series,
    ) -> None:
        if hours <= 0:
            raise ValueError("hours must be greater than zero")
        if LIST_SIZE <= 0:
            raise ValueError(f"No algebraic lists were generated for {{TEMPLATE_NAME}}")

        self.name = name
        self.limit = LIST_SIZE if limit is None else min(int(limit), LIST_SIZE)
        if self.limit <= 0:
            raise ValueError("limit must be greater than zero")

        self.hours = int(hours)
        self.current_timestep = 0
        self.data_size = self.hours
        self.input_series = {{
            input_name: self._normalize_series(
                input_series.get(input_name, _default_input_value(input_name)),
                self.hours,
            )
            for input_name in INPUT_NAMES
        }}

    @staticmethod
    def _normalize_series(value: float | Iterable[float], hours: int) -> list[float]:
        if isinstance(value, (int, float)):
            return [float(value) for _ in range(hours)]

        values = [float(item) for item in value]
        if len(values) < hours:
            raise ValueError("Input time series must contain at least 'hours' values")
        return values[:hours]

    def get_variable_names(self):
        names = list(INPUT_NAMES)
        for index in range(self.limit):
            for list_name in LIST_NAMES:
                names.append(f"{{list_name}}_{{index}}")
        return names

    def _env_for_step(self, step: int) -> dict[str, float]:
        return {{
            input_name: values[step]
            for input_name, values in self.input_series.items()
        }}

    def get_variables(self):
        if self.current_timestep >= self.data_size:
            return None

        step = self.current_timestep
        env = self._env_for_step(step)
        values = dict(env)

        for index in range(self.limit):
            for list_name in LIST_NAMES:
                expr = ALGEBRAIC_LIST_SPECS[list_name][index]
                values[f"{{list_name}}_{{index}}"] = _safe_eval(expr, env)

        return values

    def step(self):
        self.current_timestep += 1
        return self.current_timestep

    def reset(self):
        self.current_timestep = 0

    def read_input(self, input=None, *args):
        return None

    def closeFile(self):
        return None

    def assignHeader(self, header):
        return None


def create_input_module(name: str = MODULE_NAME, limit: int | None = None, hours: int = 48, **input_series) -> {class_name}:
    return {class_name}(name=name, limit=limit, hours=hours, **input_series)
'''


def _patch_factory_for_inputs(output_dir: Path, model: CifModel, algebraic_inputs: list[CifAutomaton]) -> None:
    if not algebraic_inputs:
        return

    factory_path = output_dir / "factory.py"
    original = factory_path.read_text()

    imports: list[str] = []
    registry_items: list[str] = []
    instance_items: list[str] = []

    for automaton in algebraic_inputs:
        module_file = _snake_case(automaton.name)
        module_name = _input_instance_name(model, automaton.name)
        imports.append(f"from . import {module_file} as input_{module_file}")
        registry_items.append(f"    {automaton.name!r}: input_{module_file},")
        instance_items.append(f"    {automaton.name!r}: {module_name!r},")

    patch_lines = ["", "# Algebraic/input modules generated from CIF."]
    patch_lines.extend(imports)
    patch_lines.extend([
        "",
        "INPUT_REGISTRY = {",
        *registry_items,
        "}",
        "",
        "INPUT_INSTANCE_NAMES = {",
        *instance_items,
        "}",
        "",
        "def create_input_module(template_name: str, name: str | None = None, limit: int | None = None, hours: int = 48, **input_series):",
        "    module = INPUT_REGISTRY[template_name]",
        "    return module.create_input_module(",
        "        name=name or INPUT_INSTANCE_NAMES[template_name],",
        "        limit=limit,",
        "        hours=hours,",
        "        **input_series,",
        "    )",
        "",
        "def create_input_modules(limit: int | None = None, hours: int = 48, **input_series):",
        "    modules = {}",
        "    for template_name in INPUT_REGISTRY:",
        "        module = create_input_module(template_name, limit=limit, hours=hours, **input_series)",
        "        modules[module.name] = module",
        "    return modules",
        "",
    ])

    patch = "\n".join(patch_lines)
    if "INPUT_REGISTRY" not in original:
        factory_path.write_text(original + patch)



def generate_general_from_cif(cif_path: str | Path, output_dir: str | Path, force: bool = True):
    cif_path = Path(cif_path)
    output_dir = Path(output_dir)
    model = parse_file(cif_path)
    report = analyze_model(model)

    if not report.supported:
        raise ValueError("CIF model contains unsupported features:\n" + "\n".join(report.unsupported_features))

    original_runtime = base_generator.RUNTIME_CODE
    original_instances = base_generator._instances
    original_selected = base_generator._selected_templates

    try:
        base_generator.RUNTIME_CODE = Path(__file__).with_name("optimized_runtime_template.py").read_text()
        base_generator._instances = _instances_general
        base_generator._selected_templates = _selected_dynamic_automata
        base_generator.generate_split_from_cif(cif_path, output_dir)
    finally:
        base_generator.RUNTIME_CODE = original_runtime
        base_generator._instances = original_instances
        base_generator._selected_templates = original_selected

    algebraic_inputs = _algebraic_input_automata(model)
    for automaton in algebraic_inputs:
        module_file = _snake_case(automaton.name)
        (output_dir / f"{module_file}.py").write_text(_algebraic_input_module_code(automaton, model))

    _patch_factory_for_inputs(output_dir, model, algebraic_inputs)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cif")
    parser.add_argument("--output-dir", "-o", default="out/generated/modules")
    args = parser.parse_args()

    report = generate_general_from_cif(args.cif, args.output_dir)
    print(f"Generated modules in: {args.output_dir}")
    if report.warnings:
        print("\nWarnings:")
        for warning in report.warnings:
            print(f"- {warning}")


if __name__ == "__main__":
    main()
