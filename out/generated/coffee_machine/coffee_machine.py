from __future__ import annotations

from .runtime import CifTemplateModule, STEP_GRANULARITY


TEMPLATE_NAME = 'CoffeeMachine'
TEMPLATE_SPEC = {'template_name': 'CoffeeMachine', 'parameters': [], 'variables': [], 'edges': [{'event': 'input_coffee', 'source_location': 'WaitingOrder', 'guard': None, 'updates': [], 'target_location': 'GrindingCoffee', 'raw': 'edge input_coffee goto GrindingCoffee;'}, {'event': 'heat_water', 'source_location': 'GrindingCoffee', 'guard': None, 'updates': [], 'target_location': 'HeatingWater', 'raw': 'edge heat_water goto HeatingWater;'}, {'event': 'stop', 'source_location': 'GrindingCoffee', 'guard': None, 'updates': [], 'target_location': 'EmergencyMode', 'raw': 'edge stop goto EmergencyMode;'}, {'event': 'add_water', 'source_location': 'HeatingWater', 'guard': None, 'updates': [], 'target_location': 'ExtractingCoffee', 'raw': 'edge add_water goto ExtractingCoffee;'}, {'event': 'stop', 'source_location': 'HeatingWater', 'guard': None, 'updates': [], 'target_location': 'EmergencyMode', 'raw': 'edge stop goto EmergencyMode;'}, {'event': 'deliver_cup', 'source_location': 'ExtractingCoffee', 'guard': None, 'updates': [], 'target_location': 'WaitingOrder', 'raw': 'edge deliver_cup goto WaitingOrder;'}, {'event': 'stop', 'source_location': 'ExtractingCoffee', 'guard': None, 'updates': [], 'target_location': 'EmergencyMode', 'raw': 'edge stop goto EmergencyMode;'}, {'event': 'reset', 'source_location': 'EmergencyMode', 'guard': None, 'updates': [], 'target_location': 'WaitingOrder', 'raw': 'edge reset goto WaitingOrder;'}], 'events': {'input_coffee': {'name': 'input_coffee', 'kind': 'event', 'trigger': 'external', 'scope': 'global', 'raw': 'event input_coffee, heat_water, add_water, deliver_cup, stop, reset;'}, 'heat_water': {'name': 'heat_water', 'kind': 'event', 'trigger': 'external', 'scope': 'global', 'raw': 'event input_coffee, heat_water, add_water, deliver_cup, stop, reset;'}, 'add_water': {'name': 'add_water', 'kind': 'event', 'trigger': 'external', 'scope': 'global', 'raw': 'event input_coffee, heat_water, add_water, deliver_cup, stop, reset;'}, 'deliver_cup': {'name': 'deliver_cup', 'kind': 'event', 'trigger': 'external', 'scope': 'global', 'raw': 'event input_coffee, heat_water, add_water, deliver_cup, stop, reset;'}, 'stop': {'name': 'stop', 'kind': 'event', 'trigger': 'external', 'scope': 'global', 'raw': 'event input_coffee, heat_water, add_water, deliver_cup, stop, reset;'}, 'reset': {'name': 'reset', 'kind': 'event', 'trigger': 'external', 'scope': 'global', 'raw': 'event input_coffee, heat_water, add_water, deliver_cup, stop, reset;'}}, 'event_metadata': {'input_coffee': {'name': 'input_coffee', 'kind': 'event', 'trigger': 'external', 'scope': 'global', 'raw': 'event input_coffee, heat_water, add_water, deliver_cup, stop, reset;'}, 'heat_water': {'name': 'heat_water', 'kind': 'event', 'trigger': 'external', 'scope': 'global', 'raw': 'event input_coffee, heat_water, add_water, deliver_cup, stop, reset;'}, 'add_water': {'name': 'add_water', 'kind': 'event', 'trigger': 'external', 'scope': 'global', 'raw': 'event input_coffee, heat_water, add_water, deliver_cup, stop, reset;'}, 'deliver_cup': {'name': 'deliver_cup', 'kind': 'event', 'trigger': 'external', 'scope': 'global', 'raw': 'event input_coffee, heat_water, add_water, deliver_cup, stop, reset;'}, 'stop': {'name': 'stop', 'kind': 'event', 'trigger': 'external', 'scope': 'global', 'raw': 'event input_coffee, heat_water, add_water, deliver_cup, stop, reset;'}, 'reset': {'name': 'reset', 'kind': 'event', 'trigger': 'external', 'scope': 'global', 'raw': 'event input_coffee, heat_water, add_water, deliver_cup, stop, reset;'}}, 'derivatives': {}, 'initial_location': 'WaitingOrder', 'required_inputs': []}
QUALIFIED_REF_MAP = {}
INSTANCE_SPECS = {'CoffeeMachine_0': {'template': 'CoffeeMachine', 'args': [], 'instance_index': 0}}
INSTANCE_COUNT = 1


class CoffeeMachineModule(CifTemplateModule):
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


def create_module(index: int, granularity=STEP_GRANULARITY["HOURLY"]) -> CoffeeMachineModule:
    spec = get_instance_spec(index)
    return CoffeeMachineModule(name=spec["name"], instance_index=spec["instance_index"], granularity=granularity)
