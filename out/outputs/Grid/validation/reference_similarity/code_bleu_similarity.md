# BLEU-style generated/reference code similarity

BLEU is used here only as a rough lexical similarity index.
It is not a semantic equivalence proof for code.

| Module | Module-only BLEU | Module + runtime BLEU | Generated tokens | Reference tokens |
|---|---:|---:|---:|---:|
| Nodes | 0.0061 | 0.0173 | 29355 | 787 |
| LAI | 0.0048 | 0.0121 | 29230 | 581 |
| Biomass | 0.0067 | 0.0225 | 42754 | 1992 |

## Interpretation

Low module-only BLEU is expected because the generated modules are data/specification-driven,
while most execution logic is centralized in `runtime.py`.
Therefore, behavior validation and manifest checks remain more important than BLEU.