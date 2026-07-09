from __future__ import annotations

"""
Text-level diagnostics for the experimental CIF -> Python pipeline.

The parser builds the IR used by the generator. This module complements it with
explicit diagnostics for CIF constructs that may be recognized syntactically but
are not yet fully implemented by the current runtime.

The goal is transparency: every input CIF can be analyzed, and unsupported or
partially supported constructs are reported before generation.
"""

from dataclasses import asdict, dataclass, field
from pathlib import Path
import re
from typing import Any


@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: str  # "supported", "warning", "unsupported"
    message: str
    occurrences: int = 1

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DiagnosticReport:
    diagnostics: list[Diagnostic] = field(default_factory=list)

    def by_severity(self, severity: str) -> list[Diagnostic]:
        return [diagnostic for diagnostic in self.diagnostics if diagnostic.severity == severity]

    @property
    def unsupported(self) -> list[Diagnostic]:
        return self.by_severity("unsupported")

    @property
    def warnings(self) -> list[Diagnostic]:
        return self.by_severity("warning")

    @property
    def supported(self) -> list[Diagnostic]:
        return self.by_severity("supported")

    def as_dict(self) -> dict[str, Any]:
        return {"diagnostics": [diagnostic.as_dict() for diagnostic in self.diagnostics]}

    def to_text(self) -> str:
        lines = ["CIF diagnostics"]
        if not self.diagnostics:
            lines.append("- none")
            return "\n".join(lines)

        for diagnostic in self.diagnostics:
            lines.append(
                f"- [{diagnostic.severity}] {diagnostic.code}: "
                f"{diagnostic.message} ({diagnostic.occurrences})"
            )

        return "\n".join(lines)


def _strip_comments(text: str) -> str:
    text = re.sub(r"//.*?$", "", text, flags=re.MULTILINE)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return text


def _count(pattern: str, text: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE | re.MULTILINE))


def scan_cif_text(text: str) -> DiagnosticReport:
    """
    Scan raw CIF text for explicitly supported/restricted/unsupported constructs.

    This is not a replacement for parsing. It is a transparent diagnostic layer
    used by feature_analyzer.py before generation.
    """

    clean = _strip_comments(text)
    diagnostics: list[Diagnostic] = []

    supported_patterns = [
        (
            "AUTOMATON",
            r"\bautomaton\b",
            "automata are parsed into generated Python modules",
        ),
        (
            "TEMPLATE_AUTOMATON",
            r"\bautomaton\s+def\b",
            "template automata are supported when instantiated",
        ),
        (
            "LOCATION",
            r"\blocation\b",
            "locations are translated to location state variables",
        ),
        (
            "EDGE",
            r"\bedge\b",
            "edges are translated to fire(event) transitions",
        ),
        (
            "GUARD",
            r"\bwhen\b",
            "guards are translated in the supported expression subset",
        ),
        (
            "UPDATE",
            r"\bdo\b",
            "discrete updates are translated in the supported assignment subset",
        ),
        (
            "ALGEBRAIC",
            r"\balg\b",
            "algebraic variables/lists are translated in the supported expression subset",
        ),
    ]

    warning_patterns = [
        (
            "CONTROLLABLE_UNCONTROLLABLE",
            r"\b(controllable|uncontrollable)\b",
            "controllable/uncontrollable event kind is mapped to the current runtime event-trigger policy, not full CIF supervisory-control semantics",
        ),
        (
            "INVARIANT",
            r"\binvariant\b",
            "invariants are detected but current support is partial and not equivalent to full ESCET semantics",
        ),
        (
            "CONTINUOUS_DERIVATIVE",
            r"\bder\s*\(|[A-Za-z_][A-Za-z0-9_]*\s*'",
            "continuous derivative syntax is handled only in a restricted step-based approximation",
        ),
        (
            "URGENT",
            r"\burgent\b",
            "urgent semantics is detected; current runtime does not implement urgency",
        ),
        (
            "MARKED_EXPRESSION",
            r"\bmarked\s+[^;]+;",
            "marked predicates beyond simple marked locations are accepted for simulation but are not used as runtime acceptance conditions",
        ),
    ]

    unsupported_patterns = [
        (
            "SYNC",
            r"\bsync\b",
            "explicit CIF synchronization declarations are not implemented by the current runtime",
        ),
        (
            "CHANNEL",
            r"\bchannel\b",
            "CIF channels are not implemented by the current runtime",
        ),
        (
            "TAU_PRIORITY",
            r"\bpriority\b",
            "priority semantics is not implemented by the current runtime",
        ),
        (
            "SVG_IO",
            r"\b(svgfile|svgout|svgin|printfile)\b",
            "CIF SVG/print I/O declarations are outside the translation target",
        ),
    ]

    for code, pattern, message in supported_patterns:
        occurrences = _count(pattern, clean)
        if occurrences:
            diagnostics.append(Diagnostic(code, "supported", message, occurrences))

    for code, pattern, message in warning_patterns:
        occurrences = _count(pattern, clean)
        if occurrences:
            diagnostics.append(Diagnostic(code, "warning", message, occurrences))

    for code, pattern, message in unsupported_patterns:
        occurrences = _count(pattern, clean)
        if occurrences:
            diagnostics.append(Diagnostic(code, "unsupported", message, occurrences))

    return DiagnosticReport(diagnostics=diagnostics)


def scan_cif_file(cif_path: str | Path) -> DiagnosticReport:
    return scan_cif_text(Path(cif_path).read_text())


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("cif")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = scan_cif_file(args.cif)
    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(report.to_text())
