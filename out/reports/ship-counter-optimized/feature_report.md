# Feature compatibility report

```text
CIF feature analysis
source: examples/ship-counter-optimized.cif
supported by current pipeline: True

Dynamic automata/templates:
- ShipCounter

Algebraic/input automata/templates:
- none

Plain automata:
- ShipCounter

Template automata:
- none

Instance counts:
- none

Supported features detected:
- automata/templates with locations and edges
- plain non-template automata
- events and event-driven fire(event)
- guards on edges
- discrete updates on edges
- discrete variables

Warnings:
- marked predicates beyond simple marked locations are accepted for simulation but are not used as runtime acceptance conditions [MARKED_EXPRESSION]

Unsupported features detected:
- none

Detailed raw diagnostics are available in feature_report.json.
```
