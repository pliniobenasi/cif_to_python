from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pipeline.binding_resolver import resolve_bindings_from_file


@dataclass(frozen=True)
class AppliedBinding:
    source_module: str
    source_variable: str | list[str]
    target_module: str
    target_variable: str | list[str]


def apply_cif_bindings(
    engine,
    cif_path: str | Path,
    template_filter: Iterable[str] | None = None,
    limit_per_template: int | None = None,
) -> list[AppliedBinding]:
    """
    Apply bindings extracted from CIF to an engine.

    The function is generic. A case study may pass a template_filter,
    but this function does not hardcode any template name.
    """

    bindings = resolve_bindings_from_file(
        cif_path,
        template_filter=list(template_filter) if template_filter is not None else None,
        limit_per_template=limit_per_template,
    )

    applied: list[AppliedBinding] = []

    for binding in bindings:
        if not engine.has_module(binding.source_module):
            continue
        if not engine.has_module(binding.target_module):
            continue

        engine.bind_variables(
            binding.source_module,
            binding.source_variable,
            binding.target_module,
            binding.target_variable,
        )

        applied.append(
            AppliedBinding(
                source_module=binding.source_module,
                source_variable=binding.source_variable,
                target_module=binding.target_module,
                target_variable=binding.target_variable,
            )
        )

    engine.ir_bindings = applied
    return applied


def apply_input_bindings(engine, input_module_name: str) -> list[tuple[str, str, str, str]]:
    """
    Bind input-module variables to all dynamic modules requiring variables
    with the same name.
    """

    input_module = engine.input_modules[input_module_name]
    available_input_names = set(input_module.get_variable_names())
    applied: list[tuple[str, str, str, str]] = []

    for module_name, module in engine.modules.items():
        for required_input in module.show_required_inputs():
            if required_input in engine.input_bindings.get(module_name, {}):
                continue
            if required_input in available_input_names:
                engine.bind_variables(input_module_name, required_input, module_name, required_input)
                applied.append((input_module_name, required_input, module_name, required_input))

    engine.global_input_bindings = applied
    return applied
