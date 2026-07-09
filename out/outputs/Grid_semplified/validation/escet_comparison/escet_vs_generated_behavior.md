# ESCET vs generated behavior comparison

- status: **PASS**
- generated trace: `./out/outputs/Grid_semplified/validation/escet_comparison/generated_trace.csv`
- ESCET trace: `./out/outputs/Grid_semplified/validation/escet_comparison/escet_trace.csv`
- compared variables: `Greenhouse_Rad, Nodes_0_N, LAI_0_lai, Biomass_0_w`
- compared cells: `195`
- matched cells: `195`
- mismatched cells: `0`
- max absolute error: `0.0`

## Notes

- Compared 49 aligned samples.
- Comparison is behavioral trace comparison, not source-code comparison.
- Generated trace shifts applied: Greenhouse_Rad=1
- Skipped 1 shifted cells outside the available sample range.
