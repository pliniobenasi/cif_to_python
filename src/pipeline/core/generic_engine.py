from __future__ import annotations

from collections import defaultdict
from typing import Any


class GenericSimulationEngine:
    """
    Minimal modular Python simulation engine.

    It is independent from model-specific names and only knows:
    - input modules
    - dynamic modules
    - bindings between source variables and target required inputs
    """

    def __init__(self, name: str = "GenericSimulationEngine") -> None:
        self.name = name
        self.input_modules: dict[str, Any] = {}
        self.modules: dict[str, Any] = {}
        self.input_bindings: dict[str, dict[str, str]] = defaultdict(dict)
        self.system_variables: dict[str, Any] = {}
        self.system_variables_history: dict[str, list[Any]] = defaultdict(list)
        self.current_timestep = 0

    def _prefix_variables(self, module_name: str, variables: dict[str, Any]) -> dict[str, Any]:
        return {
            f"{module_name}_{variable_name}": value
            for variable_name, value in variables.items()
        }

    def _refresh_module_variables(self, module_name: str, module: Any) -> None:
        self.system_variables.update(
            self._prefix_variables(module_name, module.get_variables())
        )

    def add_input_module(self, input_module: Any) -> None:
        self.input_modules[input_module.name] = input_module
        variables = input_module.get_variables()
        if variables is not None:
            self.system_variables.update(
                self._prefix_variables(input_module.name, variables)
            )

    def add_module(self, module: Any) -> None:
        self.modules[module.name] = module
        self._refresh_module_variables(module.name, module)

    def has_module(self, module_name: str) -> bool:
        return module_name in self.modules or module_name in self.input_modules

    def bind_variables(self, source_module: str, source_variable, target_module: str, target_variable) -> None:
        if isinstance(source_variable, list):
            if not isinstance(target_variable, list):
                raise ValueError("target_variable must be a list when source_variable is a list")
            if len(source_variable) != len(target_variable):
                raise ValueError("source_variable and target_variable must have the same length")
            for src, dst in zip(source_variable, target_variable):
                self.bind_variables(source_module, src, target_module, dst)
            return

        self.input_bindings[target_module][target_variable] = f"{source_module}_{source_variable}"

    # Alias compatibile con PyCrop.
    def bindVariables(self, source_module: str, source_variable, target_module: str, target_variable) -> None:
        self.bind_variables(source_module, source_variable, target_module, target_variable)

    def _input_data_for_module(self, module_name: str, module: Any) -> list[Any]:
        values = []
        bindings = self.input_bindings.get(module_name, {})

        for required_input in module.show_required_inputs():
            source_key = bindings.get(required_input)
            if source_key is None:
                values.append(self.system_variables.get(required_input, 0.0))
            else:
                values.append(self.system_variables[source_key])

        return values

    def _save_results(self) -> None:
        for key, value in self.system_variables.items():
            self.system_variables_history[key].append(value)

    def run_till_timestep(self, timestep: int = -1, save_every: int = 1):
        if save_every <= 0:
            raise ValueError("save_every must be greater than zero")

        if timestep == -1:
            max_steps = min(module.data_size for module in self.input_modules.values()) if self.input_modules else 1
        else:
            max_steps = int(timestep)

        self._save_results()

        for step_index in range(max_steps):
            for input_module in self.input_modules.values():
                variables = input_module.get_variables()
                if variables is not None:
                    self.system_variables.update(
                        self._prefix_variables(input_module.name, variables)
                    )
                input_module.step()

            for module_name, module in self.modules.items():
                input_data = self._input_data_for_module(module_name, module)
                module.step(input_data)
                self._refresh_module_variables(module_name, module)

            self.current_timestep += 1

            if (step_index + 1) % save_every == 0:
                self._save_results()

        return self

    def get_results(self):
        return dict(self.system_variables_history)
