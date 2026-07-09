# Event-trace behavior comparison summary

- model name: `ship-counter-optimized`
- CIF: `examples/ship-counter-optimized.cif`
- generated package: `out/generated/ship-counter-optimized`
- events CSV: `examples/ship-counter-optimized_events.csv`
- event column: `event`
- target column: `target`
- default target: `ShipCounter`
- event resolution: `auto`
- history variable: `ShipCounter_0_count`
- ESCET trace file generated for cifsim: `out/outputs/ship-counter-optimized/validation/event_trace_behavior_comparison/ship-counter-optimized.trace`
- cifsim log: `out/outputs/ship-counter-optimized/validation/event_trace_behavior_comparison/cifsim_trace_mode.log`
- ESCET observable reference CSV generated from cifsim: `out/outputs/ship-counter-optimized/validation/event_trace_behavior_comparison/escet_reference.csv`
- generated trace produced during comparison: `out/outputs/ship-counter-optimized/validation/event_trace_behavior_comparison/escet_comparison/generated_trace.csv`
- ESCET comparison report: `out/outputs/ship-counter-optimized/validation/event_trace_behavior_comparison/escet_comparison/escet_vs_generated_behavior.md`
- PyCrop comparison status: `completed`
- PyCrop comparison report: `out/outputs/ship-counter-optimized/validation/event_trace_behavior_comparison/pycrop_comparison/generated_vs_pycrop_behavior.md`

This workflow targets CIF models whose simulation scenario can be represented as an ordered event trace.
It is a validation/comparison workflow only: it does not translate or regenerate the Python package.
Run `scripts/run_pipeline.sh` first when the generated package is missing or outdated.
