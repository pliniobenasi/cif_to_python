# Supported CIF subset

The pipeline is not a complete CIF/ESCET compiler.

Its goal is to accept a CIF model, analyze its constructs automatically, and translate it when it belongs to the implemented subset.

## Fully supported or supported in the current prototype

| Construct | Status | Notes |
|---|---|---|
| plain `automaton` | supported | Used for simple event-driven models such as CoffeeMachine. |
| `automaton def` | supported | Used for instantiable templates such as `Nodes`, `LAI`, and `Biomass`. |
| template instances | supported | Instances are reconstructed by the parser and used by the generated factory. |
| `location` | supported | Translated to a `location` state variable. |
| `initial` | supported | Used to initialize the current location. |
| `edge` | supported | Translated to runtime transitions. |
| `when` guards | supported subset | Guards are translated when they belong to the supported expression subset. |
| `do` updates | supported subset | Assignments to discrete/continuous state variables are supported in the restricted expression subset. |
| `goto` | supported | Updates the generated `location`. |
| discrete variables | supported | Stored as generated state variables. |
| algebraic variables | supported subset | Used for generated input/algebraic modules such as `Greenhouse`. |
| list algebraic inputs | supported subset | Used to represent per-plant greenhouse values in `Grid.cif`. |
| automatic factory generation | supported | Produces registries and instance counts. |
| translation manifest | supported | Records what was generated and validated. |

## Partially supported

| Construct | Status | Notes |
|---|---|---|
| `controllable` / `uncontrollable` | partial | Mapped to the current runtime event-trigger policy, not to full supervisory-control semantics. |
| `marked` predicates | partial | Accepted for simulation and reported as a warning when used as predicates, but not used as runtime acceptance conditions. |
| continuous derivative syntax | partial | Handled as a restricted step-based approximation, not as a general ODE solver. |
| temporal events | policy-based | Conventional temporal events may be triggered automatically during `step(...)`. |
| event-driven execution | supported subset | Explicit external events can be executed through `fire(event)`. |
| step-driven execution | supported subset | Used for TOMGRO/Grid-style simulation. |

## Not supported

| Construct | Status | Notes |
|---|---|---|
| complete CIF synchronization | not supported | Explicit `sync` is rejected by diagnostics. |
| channels | not supported | No send/receive channel semantics. |
| priorities | not supported | No priority-based event resolution. |
| urgent locations/events | not supported | No urgent-time semantics. |
| complete invariants | not supported | No full invariant enforcement. |
| general ODEs | not supported | Only restricted step-based derivative handling. |
| global simultaneous-transition semantics | not supported | The runtime executes module-level transitions according to the generated modular policy. |

## Practical statement

The pipeline currently translates CIF models that can be represented as modular Python components with explicit state, guards, updates, generated bindings, and either step-driven or event-driven execution.


## Grid.cif reference coverage

`Grid.cif` is compatible with the currently supported subset.

Current reference manifest values:

```text
Greenhouse_template: 1
Nodes: 1600
LAI: 1600
Biomass: 1600
resolved bindings: 14400
```
