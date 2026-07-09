# Event-trace behavior comparison summary

- model name: `coffee_machine`
- CIF: `examples/coffee_machine.cif`
- generated package: `out/generated/coffee_machine`
- events CSV: `examples/coffee_machine_events.csv`
- event column: `event`
- target column: `target`
- default target: `CoffeeMachine`
- event resolution: `auto`
- history variable: `CoffeeMachine_0_location`
- ESCET trace file generated for cifsim: `out/outputs/coffee_machine/validation/event_trace_behavior_comparison/coffee_machine.trace`
- cifsim log: `out/outputs/coffee_machine/validation/event_trace_behavior_comparison/cifsim_trace_mode.log`
- ESCET observable reference CSV generated from cifsim: `out/outputs/coffee_machine/validation/event_trace_behavior_comparison/escet_reference.csv`
- generated trace produced during comparison: `out/outputs/coffee_machine/validation/event_trace_behavior_comparison/escet_comparison/generated_trace.csv`
- ESCET comparison report: `out/outputs/coffee_machine/validation/event_trace_behavior_comparison/escet_comparison/escet_vs_generated_behavior.md`
- PyCrop comparison status: `skipped`
- PyCrop comparison report: `out/outputs/coffee_machine/validation/event_trace_behavior_comparison/pycrop_comparison/generated_vs_pycrop_behavior.md`

This workflow targets CIF models whose simulation scenario can be represented as an ordered event trace.
It is a validation/comparison workflow only: it does not translate or regenerate the Python package.
Run `scripts/run_pipeline.sh` first when the generated package is missing or outdated.
