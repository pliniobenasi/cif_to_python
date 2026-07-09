from __future__ import annotations

"""
Feature analyzer for the experimental CIF -> Python pipeline.

The goal is not to claim full ESCET/CIF coverage. The analyzer classifies the
input CIF model and returns an explicit support report before generation.
"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from pipeline.cif_parser import CifModel, parse_file
from pipeline.diagnostics import scan_cif_file


@dataclass
class FeatureReport:
    source_path: str | None
    supported: bool
    dynamic_automata: list[str] = field(default_factory=list)
    algebraic_input_automata: list[str] = field(default_factory=list)
    plain_automata: list[str] = field(default_factory=list)
    template_automata: list[str] = field(default_factory=list)
    instance_counts: dict[str, int] = field(default_factory=dict)
    supported_features: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unsupported_features: list[str] = field(default_factory=list)
    diagnostics: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_text(self) -> str:
        lines = [
            "CIF feature analysis",
            f"source: {self.source_path}",
            f"supported by current pipeline: {self.supported}",
            "",
            "Dynamic automata/templates:",
        ]
        lines.extend([f"- {name}" for name in self.dynamic_automata] or ["- none"])
        lines.append("")
        lines.append("Algebraic/input automata/templates:")
        lines.extend([f"- {name}" for name in self.algebraic_input_automata] or ["- none"])
        lines.append("")
        lines.append("Plain automata:")
        lines.extend([f"- {name}" for name in self.plain_automata] or ["- none"])
        lines.append("")
        lines.append("Template automata:")
        lines.extend([f"- {name}" for name in self.template_automata] or ["- none"])
        lines.append("")
        lines.append("Instance counts:")
        lines.extend([f"- {name}: {count}" for name, count in sorted(self.instance_counts.items())] or ["- none"])
        lines.append("")
        lines.append("Supported features detected:")
        lines.extend([f"- {item}" for item in self.supported_features] or ["- none"])
        lines.append("")
        lines.append("Warnings:")
        lines.extend([f"- {item}" for item in self.warnings] or ["- none"])
        lines.append("")
        lines.append("Unsupported features detected:")
        lines.extend([f"- {item}" for item in self.unsupported_features] or ["- none"])
        lines.append("")
        lines.append(
            "Detailed raw diagnostics are available in feature_report.json."
        )
        return "\n".join(lines)


def _has_guards(model: CifModel) -> bool:
    return any(edge.guard for automaton in model.automata for edge in automaton.edges)


def _has_updates(model: CifModel) -> bool:
    return any(edge.updates for automaton in model.automata for edge in automaton.edges)


def _has_events(model: CifModel) -> bool:
    return bool(model.events) or any(edge.event for automaton in model.automata for edge in automaton.edges)


def _has_algebraic_variables(model: CifModel) -> bool:
    return any(variable.kind == "alg" for automaton in model.automata for variable in automaton.variables)


def _has_discrete_variables(model: CifModel) -> bool:
    return any(variable.kind == "disc" for automaton in model.automata for variable in automaton.variables)


def analyze_model(model: CifModel) -> FeatureReport:
    diagnostic_report = scan_cif_file(model.source_path) if model.source_path else None

    dynamic = [automaton.name for automaton in model.automata if automaton.edges]
    algebraic_inputs = [
        automaton.name
        for automaton in model.automata
        if automaton.alg_lists and not automaton.edges
    ]
    plain = [automaton.name for automaton in model.plain_automata()]
    templates = [automaton.name for automaton in model.template_automata()]

    supported_features: list[str] = []
    warnings: list[str] = []
    unsupported_features: list[str] = []

    if dynamic:
        supported_features.append("automata/templates with locations and edges")
    if plain:
        supported_features.append("plain non-template automata")
    if templates:
        supported_features.append("template automata with instances")
    if model.instances:
        supported_features.append("template instances")
    if model.inputs:
        supported_features.append("global input declarations")
    if model.constants:
        supported_features.append("global constants")
    if _has_events(model):
        supported_features.append("events and event-driven fire(event)")
    if _has_guards(model):
        supported_features.append("guards on edges")
    if _has_updates(model):
        supported_features.append("discrete updates on edges")
    if _has_discrete_variables(model):
        supported_features.append("discrete variables")
    if _has_algebraic_variables(model):
        supported_features.append("algebraic variables")
    if algebraic_inputs:
        supported_features.append("algebraic list input modules")

    # The parser counts these constructs syntactically. Some are handled in a
    # restricted way by the current runtime; therefore they are warnings unless
    # they are known to be outside the implemented subset.
    unsupported_counts = model.unsupported_constructs

    if unsupported_counts.get("continuous_derivative_der", 0) > 0:
        warnings.append("der(...) continuous derivative syntax detected; translated by current runtime only in a restricted step-based way")
    if unsupported_counts.get("continuous_derivative_apostrophe", 0) > 0:
        warnings.append("apostrophe derivative syntax detected; translated by current runtime only in a restricted step-based way")
    if unsupported_counts.get("piecewise_if", 0) > 0:
        supported_features.append("piecewise if/elif/else expressions in supported expression subset")
    if unsupported_counts.get("math_functions", 0) > 0:
        supported_features.append("common math functions in supported expression subset")
    if unsupported_counts.get("qualified_references", 0) > 0:
        supported_features.append("qualified references for binding reconstruction")

    # Text-level diagnostics complement the parser and make unsupported
    # constructs explicit before generation.
    diagnostic_items: list[dict[str, Any]] = []
    if diagnostic_report is not None:
        diagnostic_items = [diagnostic.as_dict() for diagnostic in diagnostic_report.diagnostics]

        for diagnostic in diagnostic_report.warnings:
            message = f"{diagnostic.message} [{diagnostic.code}]"
            if message not in warnings:
                warnings.append(message)

        for diagnostic in diagnostic_report.unsupported:
            message = f"{diagnostic.message} [{diagnostic.code}]"
            if message not in unsupported_features:
                unsupported_features.append(message)

    raw_text = "\n".join(automaton.raw_body or "" for automaton in model.automata)
    if "invariant" in raw_text or any(loc.invariants for aut in model.automata for loc in aut.locations):
        message = "invariants detected; current support is partial and expression-level only"
        if message not in warnings:
            warnings.append(message)

    if not dynamic and not algebraic_inputs:
        unsupported_features.append("no translatable dynamic or algebraic component detected")

    supported = not unsupported_features

    return FeatureReport(
        source_path=model.source_path,
        supported=supported,
        dynamic_automata=dynamic,
        algebraic_input_automata=algebraic_inputs,
        plain_automata=plain,
        template_automata=templates,
        instance_counts=model.instance_counts_by_template(),
        supported_features=supported_features,
        warnings=warnings,
        unsupported_features=unsupported_features,
        diagnostics=diagnostic_items,
    )


def analyze_file(cif_path: str | Path) -> FeatureReport:
    return analyze_model(parse_file(cif_path))


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("cif")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = analyze_file(args.cif)
    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(report.to_text())
