# Translation manifest

```text
CIF -> Python translation manifest
source: /home/bena/GitHub_PB/cif_to_python/examples/Grid.cif
generated package: /tmp/pytest-of-bena/pytest-1/test_generated_runner_can_expo0/generated_grid_history_export
valid: True

Dynamic templates/automata:
- Biomass
- LAI
- Nodes

Algebraic/input templates:
- Greenhouse_template

Plain automata:
- none

Expected instance counts:
- Biomass: 1600
- Greenhouse_template: 1
- LAI: 1600
- Nodes: 1600

Generated instance counts:
- Biomass: 1600
- LAI: 1600
- Nodes: 1600

Input instance names:
- Greenhouse_template: Greenhouse

Resolved bindings: 14400
Resolved bindings sample:
- Nodes_0.N -> Biomass_0.N
- Nodes_0.Nd -> Biomass_0.Nd
- Greenhouse.Rad_input_0 -> Biomass_0.Rad
- Greenhouse.T_sparse_daytime_0 -> Biomass_0.T_d_mean
- Greenhouse.T_sparse_mean_0 -> Biomass_0.T_mean
- LAI_0.lai -> Biomass_0.lai
- Nodes_1.N -> Biomass_1.N
- Nodes_1.Nd -> Biomass_1.Nd
- Greenhouse.Rad_input_1 -> Biomass_1.Rad
- Greenhouse.T_sparse_daytime_1 -> Biomass_1.T_d_mean
- Greenhouse.T_sparse_mean_1 -> Biomass_1.T_mean
- LAI_1.lai -> Biomass_1.lai
- Nodes_10.N -> Biomass_10.N
- Nodes_10.Nd -> Biomass_10.Nd
- Greenhouse.Rad_input_10 -> Biomass_10.Rad
- Greenhouse.T_sparse_daytime_10 -> Biomass_10.T_d_mean
- Greenhouse.T_sparse_mean_10 -> Biomass_10.T_mean
- LAI_10.lai -> Biomass_10.lai
- Nodes_100.N -> Biomass_100.N
- Nodes_100.Nd -> Biomass_100.Nd

Generated files:
- __init__.py
- biomass.py
- constants.py
- factory.py
- greenhouse.py
- lai.py
- nodes.py
- runtime.py

Warnings:
- der(...) continuous derivative syntax detected; translated by current runtime only in a restricted step-based way
- apostrophe derivative syntax detected; translated by current runtime only in a restricted step-based way
- controllable/uncontrollable event kind is mapped to the current runtime event-trigger policy, not full CIF supervisory-control semantics [CONTROLLABLE_UNCONTROLLABLE]
- continuous derivative syntax is handled only in a restricted step-based approximation [CONTINUOUS_DERIVATIVE]

Unsupported features:
- none

Validation errors:
- none
```
