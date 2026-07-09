from __future__ import annotations

from . import biomass
from . import lai
from . import nodes

REGISTRY = {
    'Biomass': biomass,
    'LAI': lai,
    'Nodes': nodes,
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

# Algebraic/input modules generated from CIF.
from . import greenhouse as input_greenhouse

INPUT_REGISTRY = {
    'Greenhouse_template': input_greenhouse,
}

INPUT_INSTANCE_NAMES = {
    'Greenhouse_template': 'Greenhouse',
}

def create_input_module(template_name: str, name: str | None = None, limit: int | None = None, hours: int = 48, **input_series):
    module = INPUT_REGISTRY[template_name]
    return module.create_input_module(
        name=name or INPUT_INSTANCE_NAMES[template_name],
        limit=limit,
        hours=hours,
        **input_series,
    )

def create_input_modules(limit: int | None = None, hours: int = 48, **input_series):
    modules = {}
    for template_name in INPUT_REGISTRY:
        module = create_input_module(template_name, limit=limit, hours=hours, **input_series)
        modules[module.name] = module
    return modules
