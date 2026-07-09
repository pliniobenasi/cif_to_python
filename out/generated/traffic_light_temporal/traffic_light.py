from __future__ import annotations

from .runtime import CifTemplateModule, STEP_GRANULARITY


TEMPLATE_NAME = 'TrafficLight'
TEMPLATE_SPEC = {'template_name': 'TrafficLight', 'parameters': [], 'variables': [{'kind': 'disc', 'name': 'granularity', 'type_name': 'int', 'value': '3600', 'raw': 'disc int granularity = 3600;'}], 'edges': [{'event': 'tick', 'source_location': 'Red', 'guard': None, 'updates': [], 'target_location': 'Green', 'raw': 'edge tick goto Green;'}, {'event': 'tick', 'source_location': 'Green', 'guard': None, 'updates': [], 'target_location': 'Yellow', 'raw': 'edge tick goto Yellow;'}, {'event': 'tick', 'source_location': 'Yellow', 'guard': None, 'updates': [], 'target_location': 'Red', 'raw': 'edge tick goto Red;'}], 'events': {'tick': {'name': 'tick', 'kind': 'event', 'trigger': 'automatic_temporal', 'scope': 'global', 'raw': 'event tick;'}}, 'event_metadata': {'tick': {'name': 'tick', 'kind': 'event', 'trigger': 'automatic_temporal', 'scope': 'global', 'raw': 'event tick;'}}, 'derivatives': {}, 'initial_location': 'Red', 'required_inputs': []}
QUALIFIED_REF_MAP = {}
INSTANCE_SPECS = {'TrafficLight_0': {'template': 'TrafficLight', 'args': [], 'instance_index': 0}}
INSTANCE_COUNT = 1


class TrafficLightModule(CifTemplateModule):
    CIF_TEMPLATE_NAME = TEMPLATE_NAME
    CIF_TEMPLATE_SPEC = TEMPLATE_SPEC
    CIF_QUALIFIED_REF_MAP = QUALIFIED_REF_MAP

    def __init__(self, name: str | None = None, instance_index: int | None = None, granularity=STEP_GRANULARITY["HOURLY"], params=None):
        self.instance_index = instance_index
        super().__init__(name or TEMPLATE_NAME, granularity, params)


def get_instance_spec(index: int) -> dict:
    instance_name = f"{TEMPLATE_NAME}_{index}"
    if instance_name not in INSTANCE_SPECS:
        raise IndexError(f"{TEMPLATE_NAME} instance index out of range: {index}")
    spec = dict(INSTANCE_SPECS[instance_name])
    spec["name"] = instance_name
    return spec


def create_module(index: int, granularity=STEP_GRANULARITY["HOURLY"]) -> TrafficLightModule:
    spec = get_instance_spec(index)
    return TrafficLightModule(name=spec["name"], instance_index=spec["instance_index"], granularity=granularity)
