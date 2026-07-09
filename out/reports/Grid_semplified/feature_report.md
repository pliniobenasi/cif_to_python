# Feature compatibility report

```text
CIF feature analysis
source: examples/Grid_semplified.cif
supported by current pipeline: True

Dynamic automata/templates:
- Nodes
- LAI
- Biomass

Algebraic/input automata/templates:
- Greenhouse_template

Plain automata:
- none

Template automata:
- Greenhouse_template
- Nodes
- LAI
- Biomass

Instance counts:
- Biomass: 100
- Greenhouse_template: 1
- LAI: 100
- Nodes: 100

Supported features detected:
- automata/templates with locations and edges
- template automata with instances
- template instances
- global input declarations
- global constants
- events and event-driven fire(event)
- guards on edges
- discrete updates on edges
- discrete variables
- algebraic variables
- algebraic list input modules
- piecewise if/elif/else expressions in supported expression subset
- common math functions in supported expression subset
- qualified references for binding reconstruction

Warnings:
- der(...) continuous derivative syntax detected; translated by current runtime only in a restricted step-based way
- apostrophe derivative syntax detected; translated by current runtime only in a restricted step-based way
- controllable/uncontrollable event kind is mapped to the current runtime event-trigger policy, not full CIF supervisory-control semantics [CONTROLLABLE_UNCONTROLLABLE]
- continuous derivative syntax is handled only in a restricted step-based approximation [CONTINUOUS_DERIVATIVE]

Unsupported features detected:
- none

Detailed raw diagnostics are available in feature_report.json.
```
