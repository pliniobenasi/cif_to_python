from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .binding_applier import apply_cif_bindings, apply_input_bindings
from .generic_engine import GenericSimulationEngine
from .module_loader import load_generated_factory


@dataclass
class InputModuleConfig:
    factory_function: str
    name: str = "Input"
    kwargs: dict[str, Any] = field(default_factory=dict)


@dataclass
class DynamicModuleGroupConfig:
    template_name: str
    limit: int | None = None


@dataclass
class BuilderConfig:
    generated_package_dir: Path
    cif_path: Path
    input_modules: list[InputModuleConfig]
    dynamic_groups: list[DynamicModuleGroupConfig]
    binding_template_filter: list[str] | None = None
    limit_per_template: int | None = None
    engine_name: str = "GeneratedCifPythonEngine"


class GenericEngineBuilder:
    """
    Generic engine builder driven by configuration.

    It does not hardcode model-specific names. A caller/configuration provides:
    - generated package directory
    - CIF file path
    - input modules to create
    - dynamic template groups to instantiate
    - optional binding filter
    """

    def __init__(self, config: BuilderConfig):
        self.config = config

    def build(self) -> GenericSimulationEngine:
        factory = load_generated_factory(self.config.generated_package_dir)
        engine = GenericSimulationEngine(self.config.engine_name)

        for input_config in self.config.input_modules:
            creator = getattr(factory, input_config.factory_function)
            module = creator(**input_config.kwargs)
            if module.name != input_config.name:
                module.name = input_config.name
            engine.add_input_module(module)

        for group in self.config.dynamic_groups:
            count = factory.INSTANCE_COUNTS[group.template_name]
            if group.limit is not None:
                count = min(count, group.limit)

            for index in range(count):
                module = factory.create_module(group.template_name, index)
                engine.add_module(module)

        apply_cif_bindings(
            engine,
            cif_path=self.config.cif_path,
            template_filter=self.config.binding_template_filter,
            limit_per_template=self.config.limit_per_template,
        )

        for input_config in self.config.input_modules:
            apply_input_bindings(engine, input_config.name)

        return engine
