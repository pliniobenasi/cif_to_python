from __future__ import annotations

from typing import Callable, Iterable

try:
    from PyCrop.Abstract.Core.AbstractCropModule import AbstractCropModule
except ImportError:
    class AbstractCropModule:
        def __init__(self, name='AbstractCropModule', granularity=3600, params=None):
            self.name=name
            self.granularity=granularity
            self.params=params or {}
            self.state_variables={}
        def get_name(self):
            return self.name


class GeneratedModulePyCropAdapter(AbstractCropModule):
    def __init__(self, generated_module, mode: str = 'data', event_input_name: str = 'events', event_target: str | None = None, event_filter: Callable[[dict], bool] | None = None, allow_automatic_step: bool = True) -> None:
        self.generated_module = generated_module
        self.mode = mode
        self.event_input_name = event_input_name
        self.event_target = event_target
        self.event_filter = event_filter
        self.allow_automatic_step = allow_automatic_step
        super().__init__(name=getattr(generated_module, 'name', generated_module.__class__.__name__), granularity=getattr(generated_module, 'granularity', 3600), params=getattr(generated_module, 'params', {}))
        self.accepted_event_targets = self._build_target_aliases()
        self.state_variables = self.generated_module.get_variables()

    def get_name(self):
        return self.name

    def change_params(self, params: dict) -> None:
        if hasattr(self.generated_module, 'params'):
            self.generated_module.params.update(params)
        self.params.update(params)

    def show_required_inputs(self) -> list[str]:
        if self.mode == 'event':
            return [self.event_input_name]
        return list(self.generated_module.show_required_inputs())

    def get_variables(self) -> dict:
        self.state_variables = self.generated_module.get_variables()
        return self.state_variables

    def get_variable_names(self) -> list[str]:
        return list(self.get_variables().keys())

    def reset(self) -> None:
        self.generated_module.reset()
        self.state_variables = self.generated_module.get_variables()

    def _build_target_aliases(self) -> set[str]:
        aliases: set[str] = set()
        raw_candidates = [
            self.event_target,
            self.name,
            getattr(self.generated_module, 'name', None),
            getattr(self.generated_module.__class__, 'CIF_TEMPLATE_NAME', None),
            getattr(self.generated_module, 'CIF_TEMPLATE_NAME', None),
            getattr(getattr(self.generated_module, 'spec', {}), 'get', lambda *_: None)('template_name'),
        ]
        for candidate in raw_candidates:
            if not candidate:
                continue
            value = str(candidate)
            aliases.add(value)
            if '_' in value:
                base, suffix = value.rsplit('_', 1)
                if suffix.isdigit():
                    aliases.add(base)
        return aliases

    def _extract_events(self, payload) -> list[str]:
        if payload is None:
            return []
        if isinstance(payload, str):
            return [payload]
        if not isinstance(payload, Iterable):
            return []
        events=[]
        for item in payload:
            if isinstance(item, str):
                events.append(item)
                continue
            if not isinstance(item, dict):
                continue
            target = item.get('target')
            if self.accepted_event_targets and target and str(target) not in self.accepted_event_targets:
                continue
            if self.event_filter and not self.event_filter(item):
                continue
            event_name=item.get('event')
            if event_name:
                events.append(str(event_name))
        return events

    def step(self, input_data: list) -> None:
        if self.mode == 'event':
            payload = input_data[0] if input_data else []
            for event in self._extract_events(payload):
                fired = self.generated_module.fire(event)
                if not fired:
                    variables = (
                        self.generated_module.get_variables()
                        if hasattr(self.generated_module, 'get_variables')
                        else {}
                    )
                    raise RuntimeError(
                        "Event trace requested an event that is not enabled in the current CIF state: "
                        f"module={self.get_name()!r}, event={event!r}, variables={variables!r}. "
                        "This matches ESCET trace-input semantics: disabled events are invalid trace items, "
                        "not silent no-ops."
                    )
            if self.allow_automatic_step:
                self.generated_module.step([])
        else:
            self.generated_module.step(input_data)
        self.state_variables = self.generated_module.get_variables()
