from __future__ import annotations

"""
End-to-end validation workflow for Grid.cif.

It combines:
1. generated Grid behavioral validation;
2. optional BLEU-style source-code comparison with handwritten PyCrop TOMGRO modules.
"""

import argparse
import json
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pipeline.path_defaults import resolve_generated_dir, require_generated_package, default_validation_dir

from validation.validate_grid_behavior import validate_grid_behavior
from validation.bleu_code_similarity import compare_generated_to_reference


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cif", default=str(ROOT_DIR / "examples" / "Grid.cif"))
    parser.add_argument("--generated-dir", default=None, help="Generated package directory (default: out/generated/<CIF stem>)")
    parser.add_argument('--output-dir', default=None)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--hours", type=int, default=72)
    parser.add_argument("--save-every", type=int, default=1)
    parser.add_argument("--reference-root", default=None)
    parser.add_argument("--reference-zip", default=None)
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else (default_validation_dir(cif_path=args.cif, project_root=ROOT_DIR) / 'grid_validation')
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_dir = str(require_generated_package(resolve_generated_dir(args.generated_dir, args.cif, ROOT_DIR), args.cif))

    behavior = validate_grid_behavior(
        args.cif,
        generated_dir,
        output_dir / "behavior",
        limit=args.limit,
        hours=args.hours,
        save_every=args.save_every,
    )

    similarity_results = []
    if args.reference_root or args.reference_zip:
        similarity_results = compare_generated_to_reference(
            generated_dir,
            output_dir / "reference_similarity",
            reference_root=args.reference_root,
            reference_zip=args.reference_zip,
        )

    summary = {
        "behavior_validation_passed": behavior.passed,
        "behavior_report": str(output_dir / "behavior" / "grid_behavior_validation.md"),
        "behavior_csv": str(output_dir / "behavior" / "grid_behavior_summary.csv"),
        "reference_similarity_enabled": bool(args.reference_root or args.reference_zip),
        "reference_similarity_report": str(output_dir / "reference_similarity" / "code_bleu_similarity.md") if similarity_results else None,
        "reference_similarity_pairs": len(similarity_results),
    }

    (output_dir / "grid_validation_summary.json").write_text(json.dumps(summary, indent=2))

    lines = [
        "# Grid.cif validation summary",
        "",
        f"Behavior validation: **{'PASS' if behavior.passed else 'FAIL'}**",
        "",
        f"- Behavior report: `{summary['behavior_report']}`",
        f"- Behavior CSV: `{summary['behavior_csv']}`",
    ]

    if similarity_results:
        lines.extend(
            [
                "",
                "Reference source-code similarity: **enabled**",
                f"- BLEU-style report: `{summary['reference_similarity_report']}`",
                f"- Compared pairs: `{len(similarity_results)}`",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "Reference source-code similarity: **not enabled**",
                "",
                "Pass `--reference-root` or `--reference-zip` to compare generated code with handwritten modules.",
            ]
        )

    (output_dir / "grid_validation_summary.md").write_text("\n".join(lines))

    print(f"Grid validation summary: {output_dir / 'grid_validation_summary.md'}")
    if not behavior.passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
