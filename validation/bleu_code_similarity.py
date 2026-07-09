from __future__ import annotations

"""
BLEU-style source-code similarity for generated modules vs reference modules.

BLEU was designed for natural-language machine translation, not for code
correctness. Here it is used only as a rough textual/lexical similarity index.
Behavioral validation remains the primary evidence.

The script compares generated Python modules with handwritten reference modules.
For generated CIF modules, the runtime contains most of the common behavior, so
the script reports two scores:

- module_only_bleu: generated module source only;
- module_plus_runtime_bleu: generated module source concatenated with runtime.py.
"""

from dataclasses import asdict, dataclass
import argparse
import csv
import io
import json
import keyword
import math
from pathlib import Path
import re
import shutil
import sys
import tokenize
import zipfile
from typing import Iterable


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pipeline.path_defaults import resolve_generated_dir, require_generated_package, default_validation_dir


@dataclass
class SimilarityResult:
    module_name: str
    generated_path: str
    reference_path: str
    module_only_bleu: float
    module_plus_runtime_bleu: float
    generated_tokens: int
    reference_tokens: int

    def as_dict(self):
        return asdict(self)


def tokenize_python_source(text: str) -> list[str]:
    tokens: list[str] = []
    stream = io.StringIO(text)

    try:
        generated = tokenize.generate_tokens(stream.readline)
        for token in generated:
            token_type = token.type
            token_string = token.string

            if token_type in {
                tokenize.COMMENT,
                tokenize.NL,
                tokenize.NEWLINE,
                tokenize.INDENT,
                tokenize.DEDENT,
                tokenize.ENCODING,
                tokenize.ENDMARKER,
            }:
                continue

            if token_type == tokenize.STRING:
                tokens.append("<STRING>")
            elif token_type == tokenize.NUMBER:
                tokens.append("<NUMBER>")
            elif token_string in keyword.kwlist:
                tokens.append(token_string)
            elif re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", token_string):
                tokens.append("<ID>")
            else:
                tokens.append(token_string)
    except tokenize.TokenError:
        # Fallback for incomplete snippets.
        tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?|\S", text)

    return tokens


def _ngrams(tokens: list[str], n: int) -> dict[tuple[str, ...], int]:
    counts: dict[tuple[str, ...], int] = {}
    if len(tokens) < n:
        return counts

    for index in range(len(tokens) - n + 1):
        gram = tuple(tokens[index:index + n])
        counts[gram] = counts.get(gram, 0) + 1

    return counts


def sentence_bleu(candidate: list[str], reference: list[str], max_n: int = 4, smooth: float = 1.0) -> float:
    """
    Small self-contained BLEU implementation with add-k smoothing.

    Candidate = generated module.
    Reference = handwritten module.
    """

    if not candidate or not reference:
        return 0.0

    log_precisions: list[float] = []
    for n in range(1, max_n + 1):
        cand_counts = _ngrams(candidate, n)
        ref_counts = _ngrams(reference, n)

        if not cand_counts:
            precision = smooth / smooth
        else:
            clipped = 0
            total = 0
            for gram, count in cand_counts.items():
                clipped += min(count, ref_counts.get(gram, 0))
                total += count
            precision = (clipped + smooth) / (total + smooth)

        log_precisions.append(math.log(precision))

    geo_mean = math.exp(sum(log_precisions) / max_n)

    cand_len = len(candidate)
    ref_len = len(reference)
    if cand_len > ref_len:
        brevity_penalty = 1.0
    else:
        brevity_penalty = math.exp(1.0 - ref_len / max(cand_len, 1))

    return brevity_penalty * geo_mean


def _extract_reference_zip(reference_zip: Path, target_dir: Path) -> Path:
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True)

    with zipfile.ZipFile(reference_zip) as zf:
        zf.extractall(target_dir)

    children = [path for path in target_dir.iterdir() if path.is_dir()]
    return children[0] if len(children) == 1 else target_dir


def _find_reference_file(reference_root: Path, patterns: Iterable[str]) -> Path | None:
    for pattern in patterns:
        matches = sorted(reference_root.rglob(pattern))
        if matches:
            return matches[0]
    return None


def _module_pairs(generated_dir: Path, reference_root: Path) -> list[tuple[str, Path, Path]]:
    specs = [
        ("Nodes", generated_dir / "nodes.py", ["TOMGRONodesModule.py", "*Nodes*.py"]),
        ("LAI", generated_dir / "lai.py", ["TOMGROLaiModule.py", "*Lai*.py", "*LAI*.py"]),
        ("Biomass", generated_dir / "biomass.py", ["TOMGROBiomassModule.py", "*Biomass*.py"]),
    ]

    pairs: list[tuple[str, Path, Path]] = []
    for module_name, generated_path, patterns in specs:
        if not generated_path.exists():
            continue

        reference_path = _find_reference_file(reference_root, patterns)
        if reference_path is None:
            continue

        pairs.append((module_name, generated_path, reference_path))

    return pairs


def compare_generated_to_reference(
    generated_dir: str | Path,
    output_dir: str | Path,
    reference_root: str | Path | None = None,
    reference_zip: str | Path | None = None,
) -> list[SimilarityResult]:
    generated_dir = Path(generated_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if reference_root is None and reference_zip is None:
        raise ValueError("Provide either reference_root or reference_zip")

    if reference_zip is not None:
        reference_root_path = _extract_reference_zip(Path(reference_zip), output_dir / "_reference_extracted")
    else:
        reference_root_path = Path(reference_root)  # type: ignore[arg-type]

    runtime_path = generated_dir / "runtime.py"
    runtime_text = runtime_path.read_text() if runtime_path.exists() else ""

    results: list[SimilarityResult] = []

    for module_name, generated_path, reference_path in _module_pairs(generated_dir, reference_root_path):
        generated_text = generated_path.read_text()
        reference_text = reference_path.read_text()

        gen_tokens = tokenize_python_source(generated_text)
        gen_runtime_tokens = tokenize_python_source(generated_text + "\n" + runtime_text)
        ref_tokens = tokenize_python_source(reference_text)

        results.append(
            SimilarityResult(
                module_name=module_name,
                generated_path=str(generated_path),
                reference_path=str(reference_path),
                module_only_bleu=sentence_bleu(gen_tokens, ref_tokens),
                module_plus_runtime_bleu=sentence_bleu(gen_runtime_tokens, ref_tokens),
                generated_tokens=len(gen_tokens),
                reference_tokens=len(ref_tokens),
            )
        )

    json_path = output_dir / "code_bleu_similarity.json"
    csv_path = output_dir / "code_bleu_similarity.csv"
    md_path = output_dir / "code_bleu_similarity.md"

    json_path.write_text(json.dumps([result.as_dict() for result in results], indent=2))

    with csv_path.open("w", newline="") as handle:
        fieldnames = [
            "module_name",
            "generated_path",
            "reference_path",
            "module_only_bleu",
            "module_plus_runtime_bleu",
            "generated_tokens",
            "reference_tokens",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result.as_dict())

    lines = [
        "# BLEU-style generated/reference code similarity",
        "",
        "BLEU is used here only as a rough lexical similarity index.",
        "It is not a semantic equivalence proof for code.",
        "",
        "| Module | Module-only BLEU | Module + runtime BLEU | Generated tokens | Reference tokens |",
        "|---|---:|---:|---:|---:|",
    ]

    for result in results:
        lines.append(
            f"| {result.module_name} | "
            f"{result.module_only_bleu:.4f} | "
            f"{result.module_plus_runtime_bleu:.4f} | "
            f"{result.generated_tokens} | "
            f"{result.reference_tokens} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Low module-only BLEU is expected because the generated modules are data/specification-driven,",
            "while most execution logic is centralized in `runtime.py`.",
            "Therefore, behavior validation and manifest checks remain more important than BLEU.",
        ]
    )

    md_path.write_text("\n".join(lines))
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cif", default=None, help="Optional CIF path used to infer out/generated/<MODEL_NAME> when --generated-dir is omitted")
    parser.add_argument("--generated-dir", default=None, help="Generated package directory (default: out/generated/<CIF stem>)")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: out/outputs/<MODEL_NAME>/validation/reference_similarity)")
    parser.add_argument("--reference-root", default=None)
    parser.add_argument("--reference-zip", default=None)
    args = parser.parse_args()

    if not args.generated_dir and not args.cif:
        raise ValueError("Provide --cif so out/generated/<MODEL_NAME> can be used, or pass --generated-dir in low-level mode.")

    generated_dir = require_generated_package(
        resolve_generated_dir(args.generated_dir, args.cif, ROOT_DIR),
        args.cif,
        require_runner=False,
    )
    output_dir = Path(args.output_dir) if args.output_dir else (
        default_validation_dir(project_root=ROOT_DIR, model_name=generated_dir.name) / "reference_similarity"
    )

    results = compare_generated_to_reference(
        generated_dir,
        output_dir,
        reference_root=args.reference_root,
        reference_zip=args.reference_zip,
    )

    print(f"Compared {len(results)} generated/reference module pairs.")
    print(f"Report: {Path(output_dir) / 'code_bleu_similarity.md'}")


if __name__ == "__main__":
    main()
