# Grid.cif behavioral validation report

Overall result: **PASS**

- CIF: `examples/Grid.cif`
- Generated package: `./out/generated/Grid`
- Simulated instances per template: `5`
- Simulated steps/hours: `72`

## Checks

| Check | Result | Details |
|---|---:|---|
| `manifest_valid` | PASS | dynamic_templates=Biomass,LAI,Nodes, input_templates=Greenhouse_template, resolved_bindings=14400 |
| `grid_instance_counts` | PASS | Nodes=1600, LAI=1600, Biomass=1600, Greenhouse_template=1 |
| `dependency_order_nodes_lai_biomass` | PASS | execution_order_sample=['Nodes_0', 'Nodes_1', 'Nodes_2', 'Nodes_3', 'Nodes_4', 'LAI_0', 'LAI_1', 'LAI_2', 'LAI_3', 'LAI_4', 'Biomass_0', 'Biomass_1', 'Biomass_2', 'Biomass_3', 'Biomass_4'] |
| `greenhouse_input_propagation_to_biomass` | PASS | plant_0_T_mean_final=21.0, plant_0_Rad_final=300.0, plant_1_T_mean_final=20.998765432098764, plant_1_Rad_final=299.6296296296296, plant_2_T_mean_final=20.997530864197532, plant_2_Rad_final=299.2592592592593, plant_3_T_mean_final=20.996296296296297, plant_3_Rad_final=298.8888888888889, plant_4_T_mean_final=20.99506172839506, plant_4_Rad_final=298.51851851851853 |
| `nodes_non_decreasing` | PASS | plant_0_nodes_delta=1.5344999999999995, plant_0_lai_delta=0.0033910721587199696, plant_0_biomass_final=1.3280967275351576, plant_1_nodes_delta=1.5344214285714282, plant_1_lai_delta=0.00339081967668484, plant_1_biomass_final=1.3272480678844554, plant_2_nodes_delta=1.5343428571428568, plant_2_lai_delta=0.0033905672039387484, plant_2_biomass_final=1.3263983993915454, plant_3_nodes_delta=1.5342642857142854, plant_3_lai_delta=0.0033903147404815044, plant_3_biomass_final=1.3255477202419086, plant_4_nodes_delta=1.534185714285714, plant_4_lai_delta=0.0033900622863129136, plant_4_biomass_final=1.3246960286167122 |
| `lai_non_decreasing` | PASS | plant_0_nodes_delta=1.5344999999999995, plant_0_lai_delta=0.0033910721587199696, plant_0_biomass_final=1.3280967275351576, plant_1_nodes_delta=1.5344214285714282, plant_1_lai_delta=0.00339081967668484, plant_1_biomass_final=1.3272480678844554, plant_2_nodes_delta=1.5343428571428568, plant_2_lai_delta=0.0033905672039387484, plant_2_biomass_final=1.3263983993915454, plant_3_nodes_delta=1.5342642857142854, plant_3_lai_delta=0.0033903147404815044, plant_3_biomass_final=1.3255477202419086, plant_4_nodes_delta=1.534185714285714, plant_4_lai_delta=0.0033900622863129136, plant_4_biomass_final=1.3246960286167122 |
| `biomass_non_negative` | PASS | plant_0_nodes_delta=1.5344999999999995, plant_0_lai_delta=0.0033910721587199696, plant_0_biomass_final=1.3280967275351576, plant_1_nodes_delta=1.5344214285714282, plant_1_lai_delta=0.00339081967668484, plant_1_biomass_final=1.3272480678844554, plant_2_nodes_delta=1.5343428571428568, plant_2_lai_delta=0.0033905672039387484, plant_2_biomass_final=1.3263983993915454, plant_3_nodes_delta=1.5342642857142854, plant_3_lai_delta=0.0033903147404815044, plant_3_biomass_final=1.3255477202419086, plant_4_nodes_delta=1.534185714285714, plant_4_lai_delta=0.0033900622863129136, plant_4_biomass_final=1.3246960286167122 |

## Key metrics

```json
{
  "run_mode": "step-driven",
  "steps": 72,
  "input_modules": [
    "Greenhouse"
  ],
  "dynamic_templates": [
    "Biomass",
    "LAI",
    "Nodes"
  ],
  "dynamic_modules_instantiated": 15,
  "resolved_bindings_for_limited_run": 45,
  "global_input_bindings_for_limited_run": 5,
  "manifest_resolved_bindings_full_model": 14400
}
```

## Interpretation

This validation is behavioral, not a proof of full biological correctness.
It checks that the generated modular Python simulator preserves the expected dependency flow
and produces coherent TOMGRO-style trends for a limited Grid.cif execution.
