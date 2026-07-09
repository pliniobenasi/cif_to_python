# Scenario inputs

## Goal

The CIF model describes the system.

A scenario input describes one concrete simulation run.

The pipeline supports two external scenario types:

```text
event trace CSV
data trace CSV
```

This avoids reintroducing manual module-to-module bindings for external inputs.

## Event trace CSV

Event trace CSV files are used for event-driven models such as CoffeeMachine.

Example:

```csv
step,event,target
0,input_coffee,CoffeeMachine
1,heat_water,CoffeeMachine
2,add_water,CoffeeMachine
3,deliver_cup,CoffeeMachine
```

Run:

```bash
python3 out/generated/CoffeeMachine/run_generated_model.py \
  --events-csv examples/coffee_machine_events.csv
```


A guarded-counter event trace can use the same format:

```csv
step,event,target
0,ship_enters,ShipCounter
1,ship_enters,ShipCounter
2,ship_leaves,ShipCounter
```

For ESCET trace generation, `events_csv_to_escet_trace.py` inspects the CIF when available. If events are declared inside an automaton, as in `ship-counter-optimized.cif`, the generated ESCET trace uses qualified event names such as `ShipCounter.ship_enters`. If events are declared globally, as in `coffee_machine.cif` and `traffic_light_temporal.cif`, they are emitted without an automaton prefix.

If the generated package contains only one dynamic module, the `target` column can be omitted.

Minimal example:

```csv
step,event
0,input_coffee
1,heat_water
2,add_water
3,deliver_cup
```

## Data trace CSV

Data trace CSV files are used for step-driven models with generated input modules, such as Grid/TOMGRO.

Example:

```csv
step,T_in,Rad,T_mean,T_daytime_mean
0,20.0,300.0,21.0,22.0
1,20.5,310.0,21.3,22.4
```

Run:

```bash
python3 out/generated/Grid/run_generated_model.py \
  --input-csv examples/grid_weather_input.csv \
  --limit 100
```

The `step` column is optional and ignored by the data reader. All other columns are treated as numeric input series.

## Override policy

Default behavior:

```text
no CSV provided
->
use the package default input values
```

With data CSV:

```text
--input-csv provided
->
override generated input-module series using the CSV columns
```

With event CSV:

```text
--events-csv provided
->
drive external events from the CSV trace through fire(event)
```

## Model/scenario separation

The intended separation is:

```text
CIF model
  describes the system structure and behavior

generated Python package
  contains modules, runtime, factory, and manifest

scenario input
  describes one concrete simulation run
```

This makes the pipeline cleaner than manual binding-based external input injection.


## Related history export

Scenario runs can export simulation history with:

```bash
--history-csv
--history-json
--history-vars
```

See:

```text
docs/HISTORY_EXPORT.md
```


### ShipCounter event trace note

`examples/ship-counter-optimized_events.csv` intentionally contains only events that are enabled in ESCET trace mode: five `ship_enters` events followed by five `ship_leaves` events. This validates discrete variable updates and guards along an executable trace. A separate negative scenario, `examples/ship-counter-optimized_invalid_guard_events.csv`, requests one extra `ship_enters` event after `count` has reached 5; ESCET and the generated runtime both reject it because event-trace inputs are strict and disabled events are not silent no-ops.
