from __future__ import annotations

"""
Translation manifest for the generic CIF -> Python pipeline.

The manifest is generated after code generation and records what was actually
translated, which modules were produced, how many instances are expected and
which bindings were reconstructed from the CIF model.

It is intentionally model-independent: every supported CIF input is treated through the same manifest structure.
"""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any

from pipeline.binding_resolver import resolve_bindings_from_file
from pipeline.cif_parser import parse_file
from pipeline.core.module_loader import load_generated_factory
from pipeline.feature_analyzer import FeatureReport, analyze_file


@dataclass
class GeneratedPackageManifest:
    source_path: str
    generated_package_dir: str
    generated_files: list[str] = field(default_factory=list)

    supported: bool = True
    warnings: list[str] = field(default_factory=list)
    unsupported_features: list[str] = field(default_factory=list)

    dynamic_templates: list[str] = field(default_factory=list)
    algebraic_input_templates: list[str] = field(default_factory=list)
    plain_automata: list[str] = field(default_factory=list)

    expected_instance_counts: dict[str, int] = field(default_factory=dict)
    generated_instance_counts: dict[str, int] = field(default_factory=dict)

    input_instance_names: dict[str, str] = field(default_factory=dict)

    resolved_bindings_count: int = 0
    resolved_bindings_sample: list[dict[str, Any]] = field(default_factory=list)

    validation_errors: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return self.supported and not self.validation_errors

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["valid"] = self.valid
        return data

    def to_text(self) -> str:
        lines = [
            "CIF -> Python translation manifest",
            f"source: {self.source_path}",
            f"generated package: {self.generated_package_dir}",
            f"valid: {self.valid}",
            "",
            "Dynamic templates/automata:",
        ]

        lines.extend([f"- {name}" for name in self.dynamic_templates] or ["- none"])
        lines.append("")
        lines.append("Algebraic/input templates:")
        lines.extend([f"- {name}" for name in self.algebraic_input_templates] or ["- none"])
        lines.append("")
        lines.append("Plain automata:")
        lines.extend([f"- {name}" for name in self.plain_automata] or ["- none"])
        lines.append("")
        lines.append("Expected instance counts:")
        lines.extend([f"- {name}: {count}" for name, count in sorted(self.expected_instance_counts.items())] or ["- none"])
        lines.append("")
        lines.append("Generated instance counts:")
        lines.extend([f"- {name}: {count}" for name, count in sorted(self.generated_instance_counts.items())] or ["- none"])
        lines.append("")
        lines.append("Input instance names:")
        lines.extend([f"- {template}: {name}" for template, name in sorted(self.input_instance_names.items())] or ["- none"])
        lines.append("")
        lines.append(f"Resolved bindings: {self.resolved_bindings_count}")
        if self.resolved_bindings_sample:
            lines.append("Resolved bindings sample:")
            for item in self.resolved_bindings_sample:
                lines.append(
                    f"- {item['source_module']}.{item['source_variable']} -> "
                    f"{item['target_module']}.{item['target_variable']}"
                )
        lines.append("")
        lines.append("Generated files:")
        lines.extend([f"- {name}" for name in self.generated_files] or ["- none"])
        lines.append("")
        lines.append("Warnings:")
        lines.extend([f"- {item}" for item in self.warnings] or ["- none"])
        lines.append("")
        lines.append("Unsupported features:")
        lines.extend([f"- {item}" for item in self.unsupported_features] or ["- none"])
        lines.append("")
        lines.append("Validation errors:")
        lines.extend([f"- {item}" for item in self.validation_errors] or ["- none"])
        return "\n".join(lines)


def _binding_to_dict(binding) -> dict[str, Any]:
    return {
        "source_module": binding.source_module,
        "source_variable": binding.source_variable,
        "target_module": binding.target_module,
        "target_variable": binding.target_variable,
    }


def _generated_files(generated_package_dir: Path) -> list[str]:
    return sorted(
        str(path.relative_to(generated_package_dir))
        for path in generated_package_dir.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    )


def _expected_counts_from_model(cif_path: str | Path, report: FeatureReport) -> dict[str, int]:
    model = parse_file(cif_path)
    counts = dict(model.instance_counts_by_template())

    for plain_name in report.plain_automata:
        counts.setdefault(plain_name, 1)

    return counts


def build_manifest(
    cif_path: str | Path,
    generated_package_dir: str | Path,
    report: FeatureReport | None = None,
    binding_sample_size: int = 20,
) -> GeneratedPackageManifest:
    cif_path = Path(cif_path)
    generated_package_dir = Path(generated_package_dir)

    report = report or analyze_file(cif_path)
    factory = load_generated_factory(generated_package_dir)

    generated_instance_counts = dict(getattr(factory, "INSTANCE_COUNTS", {}))
    input_instance_names = dict(getattr(factory, "INPUT_INSTANCE_NAMES", {}))
    dynamic_templates = list(getattr(factory, "REGISTRY", {}).keys())
    input_templates = list(getattr(factory, "INPUT_REGISTRY", {}).keys())

    expected_counts = _expected_counts_from_model(cif_path, report)
    validation_errors: list[str] = []

    for name in report.dynamic_automata:
        if name not in generated_instance_counts:
            validation_errors.append(f"dynamic automaton/template not generated: {name}")

    for name in report.algebraic_input_automata:
        if name not in input_templates:
            validation_errors.append(f"algebraic/input automaton not generated: {name}")

    for name, expected in expected_counts.items():
        if name in generated_instance_counts:
            generated = generated_instance_counts[name]
            if generated != expected:
                validation_errors.append(
                    f"instance count mismatch for {name}: expected {expected}, generated {generated}"
                )

    bindings = []
    if dynamic_templates:
        bindings = resolve_bindings_from_file(
            cif_path,
            template_filter=dynamic_templates,
            limit_per_template=None,
        )

    return GeneratedPackageManifest(
        source_path=str(cif_path),
        generated_package_dir=str(generated_package_dir),
        generated_files=_generated_files(generated_package_dir),
        supported=report.supported,
        warnings=list(report.warnings),
        unsupported_features=list(report.unsupported_features),
        dynamic_templates=dynamic_templates,
        algebraic_input_templates=input_templates,
        plain_automata=list(report.plain_automata),
        expected_instance_counts=expected_counts,
        generated_instance_counts=generated_instance_counts,
        input_instance_names=input_instance_names,
        resolved_bindings_count=len(bindings),
        resolved_bindings_sample=[_binding_to_dict(binding) for binding in bindings[:binding_sample_size]],
        validation_errors=validation_errors,
    )


def write_manifest(
    cif_path: str | Path,
    generated_package_dir: str | Path,
    report: FeatureReport | None = None,
    report_dir: str | Path | None = None,
) -> GeneratedPackageManifest:
    generated_package_dir = Path(generated_package_dir)
    manifest = build_manifest(cif_path, generated_package_dir, report=report)
    target_dir = Path(report_dir) if report_dir is not None else generated_package_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    (target_dir / "translation_manifest.json").write_text(
        json.dumps(manifest.as_dict(), indent=2)
    )
    (target_dir / "translation_manifest.md").write_text(
        "# Translation manifest\n\n"
        "```text\n"
        f"{manifest.to_text()}\n"
        "```\n"
    )

    return manifest


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("cif")
    parser.add_argument("generated_package_dir")
    args = parser.parse_args()

    manifest = write_manifest(args.cif, args.generated_package_dir)
    print(manifest.to_text())
