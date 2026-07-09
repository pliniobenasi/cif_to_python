# Reference comparison and BLEU-style similarity

## Why BLEU

Papineni et al. (2002), *BLEU: a Method for Automatic Evaluation of Machine Translation*, introduced BLEU as an automatic metric for comparing a candidate translation with one or more references using modified n-gram precision and a brevity penalty.

In this project, BLEU is used only as a supplementary lexical similarity indicator between:

```text
automatically generated Python code
handwritten PyCrop/TOMGRO reference modules
```

## Important limitation

BLEU is not a semantic correctness metric for code.

Two code fragments can have low BLEU and equivalent behavior, or high BLEU and different behavior.

Therefore, BLEU is secondary.

The primary validation evidence is:

```text
behavioral validation
translation manifest
reconstructed bindings
main-variable trends
```

## Script

```bash
python3 validation/bleu_code_similarity.py \
  --cif examples/Grid.cif \
  --reference-root ._pycrop/PyCrop_restrict
```

By default the script looks for the generated package in:

```text
out/generated/Grid/
```

and writes the report under:

```text
out/outputs/Grid/validation/reference_similarity/
```

`--generated-dir` is still available only as a low-level override, but the selected package must already exist.

## Outputs

```text
code_bleu_similarity.md
code_bleu_similarity.json
code_bleu_similarity.csv
```

## Interpreting results

The report includes:

```text
module_only_bleu
module_plus_runtime_bleu
```

`module_only_bleu` compares only the generated module source.

`module_plus_runtime_bleu` compares the generated module together with `runtime.py`, because most common execution logic is centralized there.
