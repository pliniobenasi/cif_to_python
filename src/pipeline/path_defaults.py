from __future__ import annotations

from pathlib import Path


def _normalize_model_key(name: str) -> str:
    return ''.join(ch.lower() for ch in name if ch.isalnum())


def default_generated_root(project_root: str | Path | None = None) -> Path:
    base = Path(project_root) if project_root is not None else Path.cwd()
    return base / "out" / "generated"


def default_generated_dir(cif_path: str | Path, project_root: str | Path | None = None) -> Path:
    cif = Path(cif_path)
    return default_generated_root(project_root) / cif.stem


def infer_model_name(
    cif_path: str | Path | None = None,
    generated_dir: str | Path | None = None,
    source_model_path: str | Path | None = None,
    fallback: str = "ad_hoc",
) -> str:
    if generated_dir:
        return Path(generated_dir).name
    if cif_path:
        return Path(cif_path).stem
    if source_model_path:
        return Path(source_model_path).stem
    return fallback


def _find_existing_model_dir(root: Path, model_name: str) -> Path | None:
    exact = root / model_name
    if exact.exists():
        return exact

    target_key = _normalize_model_key(model_name)
    for child in root.iterdir() if root.exists() else []:
        if not child.is_dir():
            continue
        if _normalize_model_key(child.name) == target_key:
            return child
        source_model = child / 'source_model.cif'
        if source_model.exists() and _normalize_model_key(source_model.stem) == target_key:
            return child
    return None


def default_reports_root(project_root: str | Path | None = None) -> Path:
    base = Path(project_root) if project_root is not None else Path.cwd()
    return base / "out" / "reports"


def default_reports_dir(
    cif_path: str | Path | None = None,
    generated_dir: str | Path | None = None,
    project_root: str | Path | None = None,
    model_name: str | None = None,
) -> Path:
    name = model_name or infer_model_name(cif_path=cif_path, generated_dir=generated_dir)
    return default_reports_root(project_root) / name


def default_outputs_root(project_root: str | Path | None = None) -> Path:
    base = Path(project_root) if project_root is not None else Path.cwd()
    return base / "out" / "outputs"


def default_model_output_dir(
    cif_path: str | Path | None = None,
    generated_dir: str | Path | None = None,
    project_root: str | Path | None = None,
    model_name: str | None = None,
) -> Path:
    name = model_name or infer_model_name(cif_path=cif_path, generated_dir=generated_dir)
    return default_outputs_root(project_root) / name


def default_results_dir(
    cif_path: str | Path | None = None,
    generated_dir: str | Path | None = None,
    project_root: str | Path | None = None,
    model_name: str | None = None,
) -> Path:
    return default_model_output_dir(cif_path, generated_dir, project_root, model_name) / "results"


def default_validation_dir(
    cif_path: str | Path | None = None,
    generated_dir: str | Path | None = None,
    project_root: str | Path | None = None,
    model_name: str | None = None,
) -> Path:
    return default_model_output_dir(cif_path, generated_dir, project_root, model_name) / "validation"


def default_benchmarks_dir(
    cif_path: str | Path | None = None,
    generated_dir: str | Path | None = None,
    project_root: str | Path | None = None,
    model_name: str | None = None,
) -> Path:
    return default_model_output_dir(cif_path, generated_dir, project_root, model_name) / "benchmarks"


def default_pycrop_dir(
    cif_path: str | Path | None = None,
    generated_dir: str | Path | None = None,
    project_root: str | Path | None = None,
    model_name: str | None = None,
) -> Path:
    return default_model_output_dir(cif_path, generated_dir, project_root, model_name) / "pycrop"


def resolve_generated_dir(
    generated_dir: str | Path | None,
    cif_path: str | Path | None = None,
    project_root: str | Path | None = None,
) -> Path:
    """Resolve the generated package directory.

    Low-level Python CLIs may still accept an explicit ``generated_dir`` for
    testing or advanced use. When it is omitted, the project-wide deterministic
    convention is used:

        out/generated/<MODEL_NAME>

    This function only resolves the path. Use ``require_generated_package`` when
    a validation or benchmark script needs to enforce that the package already
    exists.
    """
    if generated_dir:
        return Path(generated_dir)
    if cif_path:
        default_path = default_generated_dir(cif_path, project_root)
        if default_path.exists():
            return default_path
        resolved = _find_existing_model_dir(default_generated_root(project_root), Path(cif_path).stem)
        if resolved is not None:
            return resolved
        return default_path
    raise ValueError(
        "Generated package directory could not be inferred. "
        "Provide --cif so the default out/generated/<MODEL_NAME> path can be used, "
        "or pass --generated-dir in low-level Python CLIs only."
    )


def require_generated_package(
    generated_dir: str | Path,
    cif_path: str | Path | None = None,
    require_runner: bool = True,
) -> Path:
    """Return a generated package path or raise a clear validation error.

    Validation and benchmark workflows are intentionally separated from the
    translation pipeline. They must consume a package that was already produced
    by ``scripts/run_pipeline.sh``.
    """
    path = Path(generated_dir)
    if not path.exists() or not path.is_dir():
        message = [
            f"Generated Python package not found: {path}",
            "Validation and benchmark workflows do not translate the CIF model.",
        ]
        if cif_path is not None:
            message.extend(
                [
                    "Generate it first with:",
                    f"  ./scripts/run_pipeline.sh {cif_path}",
                ]
            )
        else:
            message.extend(
                [
                    "Generate it first with scripts/run_pipeline.sh, or pass --cif",
                    "so the default out/generated/<MODEL_NAME> path can be inferred.",
                ]
            )
        raise FileNotFoundError("\n".join(message))

    if require_runner and not (path / "run_generated_model.py").exists():
        message = [
            f"Generated runner not found: {path / 'run_generated_model.py'}",
            "The selected directory does not look like a complete generated package.",
        ]
        if cif_path is not None:
            message.extend(
                [
                    "Regenerate it with:",
                    f"  ./scripts/run_pipeline.sh {cif_path}",
                ]
            )
        raise FileNotFoundError("\n".join(message))

    return path
