# CIF support matrix

This matrix summarizes the current implementation status.

| CIF feature | Status | Runtime mapping |
|---|---|---|
| `automaton` | supported | generated Python module |
| `automaton def` | supported | generated Python template/factory entry |
| template instantiation | supported | generated instance counts |
| `location` | supported | module `location` variable |
| `initial` | supported | initial module state |
| `edge` | supported | transition evaluated by `fire(...)` or `step(...)` |
| `when` | supported subset | Python guard expression |
| `do` | supported subset | Python state update |
| `goto` | supported | location assignment |
| discrete variables | supported | module state variables |
| algebraic variables | supported subset | generated algebraic/input modules |
| list algebraic variables | supported subset | generated per-instance input series |
| controllable events | partial | external event policy |
| uncontrollable events | partial | automatic candidate during `step(...)` |
| temporal event names | partial | automatic temporal trigger policy |
| `marked` predicates | partial | accepted for simulation; not used as runtime acceptance conditions |
| derivative syntax | partial | restricted step-based approximation |
| `sync` | not supported | diagnostics reject explicit synchronization |
| urgent semantics | not supported | future work |
| invariants | not supported | future work |
| channels | not supported | future work |
| priorities | not supported | future work |
| general ODEs | not supported | future work |

## Grid.cif coverage

`Grid.cif` is compatible with the currently supported subset.

The current translation manifest reports:

```text
Greenhouse_template: 1
Nodes: 1600
LAI: 1600
Biomass: 1600
resolved bindings: 14400
```
