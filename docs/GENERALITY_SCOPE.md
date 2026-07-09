# Actual generality of the pipeline

## Correct statement

The pipeline should not be described as a complete CIF compiler.

The correct statement is:

```text
The pipeline accepts a CIF model as input, analyzes its constructs automatically,
and translates into Python modules the models that fall within the currently
supported CIF subset.
```

Therefore:

```text
any CIF input
->
optional ESCET validation
->
feature analysis / internal diagnostics
->
if compatible: automatic translation
->
if not compatible: unsupported-construct diagnostics
```

## Meaning of "any CIF input"

"Any CIF input" means that the pipeline can receive an arbitrary CIF file and produce a structured answer.

The answer can be:

```text
1. translatable model
2. partially supported model with warnings
3. non-translatable model with explicit diagnostics
```

It does not mean that every CIF/ESCET construct is already implemented.

## Meaning of "automatic translation"

Translation is automatic when the model belongs to the implemented subset.

In that case the pipeline produces:

```text
generated modular Python package
shared runtime
generic factory
feature report
translation manifest
optional runner
```

## Meaning of "modular Python simulators"

The target is not generic Python code, but a modular Python simulator.

In this project this means:

```text
generated Python modules
->
bindings reconstructed from CIF
->
modular Python engine
->
step-driven/event-driven simulation
```

The `GenericSimulationEngine` is part of the experimental target.

PyCrop remains an important architectural reference because it inspired:

```text
modules
input modules
bindings
SimulationEngine
system_variables_history
```

but the thesis should not be framed as simply generating code for the original PyCrop engine.

## Wording to keep in the thesis

Avoid:

```text
The system translates any CIF model.
```

Use:

```text
The system accepts any CIF file as input, performs automatic diagnostics,
and translates models compatible with the supported subset.
```

A more precise formulation is:

```text
The contribution is an automatic CIF-to-modular-Python-simulator translation
pipeline based on an explicit subset of CIF constructs, with diagnostics for
currently unsupported constructs.
```

## Role of Grid.cif

`Grid.cif` is the main realistic reference model, not a hardcoded case.

It is important because it exercises several supported constructs:

```text
template automata
multiple instances
algebraic/input module
reconstructed bindings
Nodes -> LAI -> Biomass dependency chain
spatial simulation
```

## Declared limitation

The pipeline does not implement the full CIF semantics yet.

Constructs such as:

```text
complete sync semantics
urgent locations/events
complete invariants
channels
priorities
general ODEs
global simultaneous-transition semantics
```

remain outside the fully implemented subset, or are handled only partially.

This does not weaken the work if stated clearly, because the thesis is about a prototypical translation pipeline validated on an explicit subset.
