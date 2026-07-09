from __future__ import annotations

try:
    from PyCrop.Abstract.Core.AbstractInputModule import AbstractInputModule, STEP_GRANULARITY
except ImportError:
    class AbstractInputModule:
        def __init__(self, name='AbstractInputModule', granularity=3600):
            self.name=name
            self.granularity=granularity
            self.current_timestep=0
            self.data_size=-1
        def get_name(self):
            return self.name
    STEP_GRANULARITY = {"HOURLY": 3600}


class GeneratedInputModulePyCropAdapter(AbstractInputModule):
    """Wrap a generated input-like module so it can be hosted by PyCrop."""

    def __init__(self, wrapped, granularity: int = STEP_GRANULARITY["HOURLY"]):
        super().__init__(name=getattr(wrapped, "name", wrapped.__class__.__name__), granularity=granularity)
        self.wrapped = wrapped
        self.current_timestep = getattr(wrapped, "current_timestep", 0)
        self.data_size = getattr(wrapped, "data_size", -1)

    def get_name(self):
        return self.name

    def read_input(self, input=None, *args) -> None:
        reader = getattr(self.wrapped, "read_input", None)
        if callable(reader):
            reader(input, *args)
            self.current_timestep = getattr(self.wrapped, "current_timestep", self.current_timestep)
            self.data_size = getattr(self.wrapped, "data_size", self.data_size)

    def get_variables(self):
        return self.wrapped.get_variables()

    def get_variable_names(self):
        getter = getattr(self.wrapped, "get_variable_names", None)
        if callable(getter):
            return list(getter())
        vars_now = self.get_variables() or {}
        return list(vars_now.keys())

    def step(self) -> int:
        value = int(self.wrapped.step())
        self.current_timestep = value
        return value

    def closeFile(self) -> None:
        closer = getattr(self.wrapped, "closeFile", None)
        if callable(closer):
            closer()

    def assignHeader(self, header) -> None:
        setter = getattr(self.wrapped, "assignHeader", None)
        if callable(setter):
            setter(header)

    def reset(self) -> None:
        resetter = getattr(self.wrapped, "reset", None)
        if callable(resetter):
            resetter()
        self.current_timestep = getattr(self.wrapped, "current_timestep", 0)
