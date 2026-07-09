from __future__ import annotations

from .runtime import CifTemplateModule, STEP_GRANULARITY


TEMPLATE_NAME = 'ShipCounter'
TEMPLATE_SPEC = {'template_name': 'ShipCounter', 'parameters': [], 'variables': [{'kind': 'disc', 'name': 'count', 'type_name': 'int', 'value': '0', 'raw': 'disc int count = 0;'}], 'edges': [{'event': 'ship_enters', 'source_location': 'Counter', 'guard': 'count < 5', 'updates': ['count := count+1'], 'target_location': 'Counter', 'raw': 'edge ship_enters when count < 5 do count := count+1 goto Counter;'}, {'event': 'ship_leaves', 'source_location': 'Counter', 'guard': 'count > 0', 'updates': ['count := count-1'], 'target_location': 'Counter', 'raw': 'edge ship_leaves when count > 0 do count := count-1 goto Counter;'}], 'events': {'ship_enters': {'name': 'ship_enters', 'kind': 'event', 'trigger': 'external', 'scope': 'automaton', 'raw': 'event ship_enters, ship_leaves;'}, 'ship_leaves': {'name': 'ship_leaves', 'kind': 'event', 'trigger': 'external', 'scope': 'automaton', 'raw': 'event ship_enters, ship_leaves;'}}, 'event_metadata': {'ship_enters': {'name': 'ship_enters', 'kind': 'event', 'trigger': 'external', 'scope': 'automaton', 'raw': 'event ship_enters, ship_leaves;'}, 'ship_leaves': {'name': 'ship_leaves', 'kind': 'event', 'trigger': 'external', 'scope': 'automaton', 'raw': 'event ship_enters, ship_leaves;'}}, 'derivatives': {}, 'initial_location': 'Counter', 'required_inputs': []}
QUALIFIED_REF_MAP = {}
INSTANCE_SPECS = {'ShipCounter_0': {'template': 'ShipCounter', 'args': [], 'instance_index': 0}}
INSTANCE_COUNT = 1


class ShipCounterModule(CifTemplateModule):
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


def create_module(index: int, granularity=STEP_GRANULARITY["HOURLY"]) -> ShipCounterModule:
    spec = get_instance_spec(index)
    return ShipCounterModule(name=spec["name"], instance_index=spec["instance_index"], granularity=granularity)
