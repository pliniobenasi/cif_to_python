from __future__ import annotations

from . import traffic_light

REGISTRY = {
    'TrafficLight': traffic_light,
}

INSTANCE_COUNTS = {name: module.INSTANCE_COUNT for name, module in REGISTRY.items()}

def create_module(template_name: str, index: int, granularity=None):
    module = REGISTRY[template_name]
    if granularity is None:
        return module.create_module(index)
    return module.create_module(index, granularity=granularity)


def create_modules(limit_per_template: int | None = None, granularity=None):
    modules = {}
    for template_name, module in REGISTRY.items():
        count = module.INSTANCE_COUNT
        if limit_per_template is not None:
            count = min(count, limit_per_template)
        modules[template_name] = {}
        for index in range(count):
            instance = create_module(template_name, index, granularity=granularity)
            modules[template_name][instance.name] = instance
    return modules
