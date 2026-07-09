from __future__ import annotations

import math
import re

from .constants import CIF_CONSTANTS

DEFAULT_STEP_GRANULARITY = {"SECONDLY": 1, "HOURLY": 3600}
STEP_GRANULARITY = DEFAULT_STEP_GRANULARITY


class GeneratedModuleBase:
    """Minimal base class for generated runtime modules."""

    def __init__(self, name, granularity=DEFAULT_STEP_GRANULARITY["HOURLY"], params=None):
        self.name = name
        self.granularity = granularity
        self.params = params or {}
        self.state_variables = {}


_NORMALIZED_EXPR_CACHE: dict[tuple[str, tuple[tuple[str, str], ...]], str] = {}
_COMPILED_EXPR_CACHE: dict[tuple[str, tuple[tuple[str, str], ...]], object] = {}
_CONSTANT_VALUES: dict[str, float] | None = None

# Default automatic temporal event names.
# The event metadata generated from CIF declarations takes precedence.
AUTOMATIC_TEMPORAL_EVENT_NAMES = {
    "tick",
    "time_step",
    "advance_time",
    "clock_tick",
    "hour",
    "day",
    "daily_update",
}



def _qmap_key(qualified_ref_map: dict[str, str]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted(qualified_ref_map.items()))


def _normalize_expr(expr: str, qualified_ref_map: dict[str, str]) -> str:
    key = (str(expr), _qmap_key(qualified_ref_map))
    cached = _NORMALIZED_EXPR_CACHE.get(key)
    if cached is not None:
        return cached

    normalized = str(expr).strip()

    for src, dst in sorted(qualified_ref_map.items(), key=lambda item: len(item[0]), reverse=True):
        normalized = re.sub(rf"\b{re.escape(src)}\b", dst, normalized)

    normalized = re.sub(r"\btrue\b", "True", normalized)
    normalized = re.sub(r"\bfalse\b", "False", normalized)
    normalized = normalized.replace("^", "**")
    normalized = re.sub(r"(?<![<>=!:])=(?!=)", "==", normalized)

    _NORMALIZED_EXPR_CACHE[key] = normalized
    return normalized


def _safe_eval(expr: str, env: dict, qualified_ref_map: dict[str, str]):
    key = (str(expr), _qmap_key(qualified_ref_map))
    code = _COMPILED_EXPR_CACHE.get(key)

    if code is None:
        normalized = _normalize_expr(expr, qualified_ref_map)
        code = compile(normalized, "<cif-expr>", "eval")
        _COMPILED_EXPR_CACHE[key] = code

    safe_globals = {
        "__builtins__": {},
        "math": math,
        "pow": pow,
        "max": max,
        "min": min,
        "abs": abs,
        "exp": math.exp,
        "log": math.log,
        "ln": math.log,
    }
    return eval(code, safe_globals, env)


def _eval_piecewise(expr: str, env: dict, qualified_ref_map: dict[str, str]):
    raw_lines = [line.strip() for line in expr.strip().splitlines() if line.strip()]
    if raw_lines and raw_lines[-1] == "end":
        raw_lines = raw_lines[:-1]

    for line in raw_lines:
        if line.startswith("if "):
            condition, value = line[3:].split(":", 1)
            if _safe_eval(condition, env, qualified_ref_map):
                return _safe_eval(value, env, qualified_ref_map)

        elif line.startswith("elif "):
            condition, value = line[5:].split(":", 1)
            if _safe_eval(condition, env, qualified_ref_map):
                return _safe_eval(value, env, qualified_ref_map)

        elif line.startswith("else"):
            value = line.split(":", 1)[1] if ":" in line else line[4:]
            return _safe_eval(value, env, qualified_ref_map)

    return None


def _eval_cif_expr(expr: str | None, env: dict, qualified_ref_map: dict[str, str]):
    if expr is None or str(expr).strip() == "":
        return 0.0

    expr = str(expr).strip()
    if expr.startswith("if "):
        return _eval_piecewise(expr, env, qualified_ref_map)

    return _safe_eval(expr, env, qualified_ref_map)


def _compute_constant_values() -> dict[str, float]:
    env: dict[str, float] = {}
    pending = dict(CIF_CONSTANTS)

    for _ in range(max(1, len(pending))):
        if not pending:
            break

        changed = False

        for name, expr in list(pending.items()):
            try:
                env[name] = _eval_cif_expr(expr, env, {})
            except NameError:
                continue

            del pending[name]
            changed = True

        if not changed:
            for name in pending:
                env.setdefault(name, 0.0)
            break

    return env


def _get_constant_values() -> dict[str, float]:
    global _CONSTANT_VALUES
    if _CONSTANT_VALUES is None:
        _CONSTANT_VALUES = _compute_constant_values()
    return _CONSTANT_VALUES


def _parse_update(update: str):
    match = re.match(r"^\s*([A-Za-z_]\w*)\s*:=\s*(.+?)\s*$", update)
    if not match:
        return None
    return match.group(1), match.group(2)


class CifTemplateModule(GeneratedModuleBase):
    CIF_TEMPLATE_NAME = None
    CIF_TEMPLATE_SPEC = None
    CIF_QUALIFIED_REF_MAP = None

    def __init__(self, name: str, granularity=STEP_GRANULARITY["HOURLY"], params=None):
        super().__init__(name, granularity, params or {})
        if not hasattr(self, "state_variables"):
            self.state_variables = {}
        self.reset()

    @property
    def spec(self):
        return self.CIF_TEMPLATE_SPEC

    @property
    def qualified_ref_map(self):
        return self.CIF_QUALIFIED_REF_MAP

    def _env(self, snapshot: dict | None = None) -> dict:
        env = dict(_get_constant_values())
        env.update(self.state_variables)
        if snapshot is not None:
            env.update(snapshot)
        return env

    def reset(self):
        self.state_variables.clear()
        self.state_variables["location"] = self.spec["initial_location"]

        for input_name in self.show_required_inputs():
            self.state_variables[input_name] = 0.0

        for variable in self.spec["variables"]:
            if variable["kind"] == "alg":
                continue
            self.state_variables[variable["name"]] = _eval_cif_expr(
                variable["value"], self._env(), self.qualified_ref_map
            )

        self._compute_algebraic()

    def show_required_inputs(self):
        return list(self.spec["required_inputs"])

    def get_variable_names(self):
        return list(self.state_variables.keys())

    def get_variables(self):
        return self.state_variables

    def _compute_algebraic(self):
        alg_variables = [
            variable for variable in self.spec["variables"] if variable["kind"] == "alg"
        ]

        pending = list(alg_variables)
        env = self._env()

        for _ in range(max(1, len(alg_variables))):
            if not pending:
                break

            next_pending = []
            changed = False

            for variable in pending:
                try:
                    value = _eval_cif_expr(variable["value"], env, self.qualified_ref_map)
                except NameError:
                    next_pending.append(variable)
                    continue

                self.state_variables[variable["name"]] = value
                env[variable["name"]] = value
                changed = True

            if not changed:
                for variable in next_pending:
                    self.state_variables.setdefault(variable["name"], 0.0)
                    env.setdefault(variable["name"], 0.0)
                break

            pending = next_pending

    def _advance_derivatives(self):
        env = self._env()
        for variable_name, expr in self.spec["derivatives"].items():
            self.state_variables[variable_name] = self.state_variables.get(variable_name, 0.0) + _eval_cif_expr(
                expr, env, self.qualified_ref_map
            )

    def _edge_enabled(self, edge: dict, snapshot: dict) -> bool:
        if edge["source_location"] is not None and snapshot.get("location") != edge["source_location"]:
            return False
        guard = edge["guard"]
        if guard is None or guard.strip() == "":
            return True
        return bool(_eval_cif_expr(guard, self._env(snapshot), self.qualified_ref_map))

    def _apply_edge(self, edge: dict, snapshot: dict) -> bool:
        new_values = {}
        env = self._env(snapshot)

        for update in edge["updates"]:
            parsed = _parse_update(update)
            if parsed is None:
                continue
            variable_name, expr = parsed
            new_values[variable_name] = _eval_cif_expr(expr, env, self.qualified_ref_map)

        self.state_variables.update(new_values)

        if edge["target_location"] is not None:
            self.state_variables["location"] = edge["target_location"]

        self._compute_algebraic()
        return True

    def event_metadata(self) -> dict:
        return dict(self.spec.get("event_metadata", {}))

    def event_info(self, event: str | None) -> dict:
        if event is None:
            return {
                "name": None,
                "kind": "tau",
                "trigger": "automatic_internal",
                "scope": "implicit",
            }

        metadata = self.spec.get("event_metadata", {})
        return metadata.get(
            event,
            {
                "name": event,
                "kind": "event",
                "trigger": (
                    "automatic_temporal"
                    if event in AUTOMATIC_TEMPORAL_EVENT_NAMES
                    else "external"
                ),
                "scope": "implicit",
            },
        )

    def is_automatic_event(self, event: str | None) -> bool:
        trigger = self.event_info(event).get("trigger")
        return trigger in {
            "automatic",
            "automatic_temporal",
            "automatic_internal",
        }

    def automatic_events(self) -> list[str]:
        names = []
        for edge in self.spec["edges"]:
            event = edge["event"]
            if event is not None and self.is_automatic_event(event) and event not in names:
                names.append(event)
        return names

    def external_events(self) -> list[str]:
        names = []
        for edge in self.spec["edges"]:
            event = edge["event"]
            if event is not None and not self.is_automatic_event(event) and event not in names:
                names.append(event)
        return names

    def fire(self, event: str) -> bool:
        """
        Fire an explicit external event.

        The method remains permissive and can fire any named event if requested
        by a runner/test. Automatic events are normally handled by step().
        """

        self._compute_algebraic()
        old = dict(self.state_variables)
        for edge in self.spec["edges"]:
            if edge["event"] != event:
                continue
            if not self._edge_enabled(edge, old):
                continue
            return self._apply_edge(edge, old)
        return False

    def _fire_automatic_until_quiescent(self, max_transitions: int = 1000) -> bool:
        """
        Fire automatic/internal edges until no more are enabled.

        This is closer to ESCET simulator behavior than firing at most one
        automatic edge per logical step. It is especially important for chains
        such as Biomass.day followed almost immediately by Biomass.hour when the
        day edge does not reset the local continuous clock.
        """
        fired_any = False
        transitions = 0

        while transitions < max_transitions:
            self._compute_algebraic()
            old = dict(self.state_variables)
            fired = False

            for edge in self.spec["edges"]:
                event = edge["event"]
                if not self.is_automatic_event(event):
                    continue
                if not self._edge_enabled(edge, old):
                    continue
                self._apply_edge(edge, old)
                fired_any = True
                fired = True
                transitions += 1
                if self.state_variables == old:
                    return fired_any
                break

            if not fired:
                return fired_any

        raise RuntimeError(f"Automatic transition fixpoint did not converge for {self.name}")

    def step(self, input_data):
        """
        Advance one simulation step.

        Policy:
        - external/controllable/plain events are not fired automatically;
        - uncontrollable or temporal events are considered automatic candidates;
        - eventless edges are considered internal automatic edges;
        - automatic transitions are drained repeatedly in deterministic CIF
          edge order until local quiescence is reached.

        This intentionally does not claim full CIF simultaneous-transition
        semantics. It is the runtime policy of the current modular Python
        simulator target.
        """

        for index, input_name in enumerate(self.show_required_inputs()):
            if index < len(input_data):
                self.state_variables[input_name] = float(input_data[index])

        self._advance_derivatives()
        self._compute_algebraic()
        return self._fire_automatic_until_quiescent()
