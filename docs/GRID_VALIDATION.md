# Grid.cif behavioral validation

## Goal

Generation alone is not enough.

For `Grid.cif`, the validation checks that the generated modular simulator behaves coherently.

The expected dependency chain is:

```text
Greenhouse -> Nodes -> LAI -> Biomass
```

## Main script

```bash
python3 validation/run_grid_validation.py \
  --cif examples/Grid.cif \
  --limit 5 \
  --hours 48
```

With handwritten PyCrop TOMGRO reference modules:

```bash
python3 validation/run_grid_validation.py \
  --cif examples/Grid.cif \
  --limit 5 \
  --hours 48 \
  --reference-root ._pycrop/PyCrop_restrict
```

## Generated outputs

```text
out/outputs/Grid/validation/grid_validation/
  grid_validation_summary.md
  grid_validation_summary.json
  behavior/
    grid_behavior_validation.md
    grid_behavior_validation.json
    grid_behavior_summary.csv
  reference_similarity/
    code_bleu_similarity.md
    code_bleu_similarity.json
    code_bleu_similarity.csv
```

## Behavioral checks

| Check | Meaning |
|---|---|
| `manifest_valid` | the translation manifest is valid |
| `grid_instance_counts` | the expected Grid/TOMGRO instance counts are present |
| `dependency_order_nodes_lai_biomass` | execution order follows the dependency chain |
| `greenhouse_input_propagation_to_biomass` | Greenhouse values reach Biomass modules |
| `nodes_non_decreasing` | node count does not decrease |
| `lai_non_decreasing` | LAI does not decrease |
| `biomass_non_negative` | biomass remains non-negative |

## Interpretation

This validation is not a full biological proof of TOMGRO.

It validates the translation:

```text
CIF -> modular Python package -> modular Python simulator
```

and verifies that the generated structure produces coherent TOMGRO-style trends.
