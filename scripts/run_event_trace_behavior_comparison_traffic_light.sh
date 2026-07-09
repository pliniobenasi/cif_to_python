#!/usr/bin/env bash
set -euo pipefail

# Behavior-validation wrapper for CIF models whose simulation scenario can be
# represented as an ordered trace of external events.
#
# This script does not translate the CIF model. It expects an already generated
# Python package, typically produced beforehand with scripts/run_pipeline.sh.
#
# The workflow compares:
#   1. an ESCET observable reference produced from a cifsim trace-mode run;
#   2. the generated Python runtime history;
#   3. an optional PyCrop-hosted history through the adapter.
#
# The ESCET .trace file is generated from an events CSV, then cifsim executes
# that trace and its console log is converted to an observable CSV.
# CoffeeMachine is only the default example shipped with the repository; other
# compatible event-trace CIF models can be used by overriding the environment
# variables below.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

CIF_PATH="${CIF_PATH:-examples/traffic_light_temporal.cif}"
MODEL_NAME="$(basename "$CIF_PATH" .cif)"
GENERATED_DIR="out/generated/$MODEL_NAME"
EVENTS_CSV="${EVENTS_CSV:-examples/traffic_light_temporal_events.csv}"
ESCET_REFERENCE_CSV_FALLBACK="${ESCET_REFERENCE_CSV_FALLBACK:-}"
OBSERVED_AUTOMATON="${OBSERVED_AUTOMATON:-}"
PYCROP_ROOT="${PYCROP_ROOT:-._pycrop/PyCrop_restrict}"
OUTPUT_DIR="${OUTPUT_DIR:-out/outputs/$MODEL_NAME/validation/event_trace_behavior_comparison}"
HISTORY_VAR="${HISTORY_VAR:-TrafficLight_0_location}"
DEFAULT_TARGET="${DEFAULT_TARGET:-TrafficLight}"
EVENT_COLUMN="${EVENT_COLUMN:-event}"
TARGET_COLUMN="${TARGET_COLUMN:-target}"
EVENT_RESOLUTION="${EVENT_RESOLUTION:-auto}"
TOLERANCE="${TOLERANCE:-1e-9}"
RUN_PYCROP="${RUN_PYCROP:-auto}"
RUN_CIFSIM="${RUN_CIFSIM:-auto}"

print_usage() {
  cat <<'USAGE'
Usage:
  ./scripts/run_event_trace_behavior_comparison.sh

This workflow targets CIF models whose simulation scenario can be represented
as an ordered event trace. CoffeeMachine is the default example.

Important:
  This script is a validation/comparison workflow only. It does not generate
  or refresh the Python package. Run scripts/run_pipeline.sh first.

Optional environment variables:
  CIF_PATH          Default: examples/coffee_machine.cif
  EVENTS_CSV        Default: examples/coffee_machine_events.csv
  ESCET_REFERENCE_CSV_FALLBACK  Optional fallback CSV used only when cifsim is skipped/unavailable.
  OBSERVED_AUTOMATON Optional observable automaton name. Usually inferred from HISTORY_VAR.
  PYCROP_ROOT       Default: ._pycrop/PyCrop_restrict
  OUTPUT_DIR        Default: out/outputs/$MODEL_NAME/validation/event_trace_behavior_comparison
  HISTORY_VAR       Default: CoffeeMachine_0_location
  DEFAULT_TARGET    Default: CoffeeMachine. Used for automaton-local events when needed.
  EVENT_COLUMN      Default: event
  TARGET_COLUMN     Default: target
  EVENT_RESOLUTION  auto|global|targeted. Default: auto
  RUN_CIFSIM        auto|yes|no. Default: auto
  RUN_PYCROP        auto|yes|no. Default: auto
  TOLERANCE         Default: 1e-9

Example for another compatible event-trace model:
  CIF_PATH=examples/my_model.cif \
  EVENTS_CSV=examples/my_model_events.csv \
  HISTORY_VAR=MyAutomaton_0_location \
  DEFAULT_TARGET=MyAutomaton \
  ./scripts/run_event_trace_behavior_comparison.sh
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  print_usage
  exit 0
fi

if [[ ! -f "$CIF_PATH" ]]; then
  echo "Error: CIF file not found: $CIF_PATH" >&2
  exit 1
fi
if [[ ! -f "$EVENTS_CSV" ]]; then
  echo "Error: events CSV not found: $EVENTS_CSV" >&2
  exit 1
fi
if [[ ! -d "$GENERATED_DIR" ]]; then
  echo "Error: generated Python package not found:" >&2
  echo "  $GENERATED_DIR" >&2
  echo >&2
  echo "This script only performs event-trace behavior comparison." >&2
  echo "Generate the Python package first, for example:" >&2
  echo "  ./scripts/run_pipeline.sh $CIF_PATH" >&2
  exit 1
fi
if [[ ! -f "$GENERATED_DIR/run_generated_model.py" ]]; then
  echo "Error: generated runner not found:" >&2
  echo "  $GENERATED_DIR/run_generated_model.py" >&2
  echo >&2
  echo "Run scripts/run_pipeline.sh first for the selected CIF model." >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

ESCET_TRACE_FILE="$OUTPUT_DIR/${MODEL_NAME}.trace"
CIFSIM_LOG="$OUTPUT_DIR/cifsim_trace_mode.log"
ESCET_REFERENCE_CSV="$OUTPUT_DIR/escet_reference.csv"
ESCET_COMPARISON_DIR="$OUTPUT_DIR/escet_comparison"
PYCROP_COMPARISON_DIR="$OUTPUT_DIR/pycrop_comparison"
EVENT_COUNT="$(( $(wc -l < "$EVENTS_CSV") - 1 ))"
PYCROP_SECONDS="$EVENT_COUNT"
if [[ "$PYCROP_SECONDS" -lt 1 ]]; then
  PYCROP_SECONDS=1
fi

echo
echo "============================================================"
echo "Event-trace behavior comparison"
echo "============================================================"
echo "Model name:          $MODEL_NAME"
echo "CIF:                 $CIF_PATH"
echo "Generated package:   $GENERATED_DIR"
echo "Events CSV:          $EVENTS_CSV"
echo "Event column:        $EVENT_COLUMN"
echo "Target column:       $TARGET_COLUMN"
echo "Default target:      $DEFAULT_TARGET"
echo "Event resolution:   $EVENT_RESOLUTION"
echo "ESCET reference CSV: $ESCET_REFERENCE_CSV"
echo "History variable:    $HISTORY_VAR"
echo "Output directory:    $OUTPUT_DIR"
echo

echo "Step 1/4 - Convert events CSV to ESCET .trace"
python3 scripts/events_csv_to_escet_trace.py \
  --events-csv "$EVENTS_CSV" \
  --output-trace "$ESCET_TRACE_FILE" \
  --cif "$CIF_PATH" \
  --event-column "$EVENT_COLUMN" \
  --target-column "$TARGET_COLUMN" \
  --default-target "$DEFAULT_TARGET" \
  --event-resolution "$EVENT_RESOLUTION"

echo
echo "Step 2/4 - Run cifsim and build ESCET observable reference CSV"
rm -f "$CIFSIM_LOG" "$ESCET_REFERENCE_CSV"
if command -v cifsim >/dev/null 2>&1 && [[ "$RUN_CIFSIM" != "no" ]]; then
  set +e
  cifsim "$CIF_PATH" \
    -i trace \
    --trace-input-file="$ESCET_TRACE_FILE" \
    --output-mode=debug \
    --gui=off \
    --ask-terminate=off \
    >"$CIFSIM_LOG" 2>&1
  CIFSIM_STATUS=$?
  set -e
  if [[ $CIFSIM_STATUS -ne 0 ]]; then
    echo "cifsim returned a non-zero status. See: $CIFSIM_LOG" >&2
    if [[ "$RUN_CIFSIM" == "yes" ]]; then
      exit $CIFSIM_STATUS
    fi
  else
    echo "cifsim trace-mode run completed. Log: $CIFSIM_LOG"
  fi

  OBSERVED_ARGS=()
  if [[ -n "$OBSERVED_AUTOMATON" ]]; then
    OBSERVED_ARGS=(--automaton "$OBSERVED_AUTOMATON")
  fi

  python3 scripts/cifsim_event_log_to_csv.py \
    --cif "$CIF_PATH" \
    --log "$CIFSIM_LOG" \
    --output-csv "$ESCET_REFERENCE_CSV" \
    --history-var "$HISTORY_VAR" \
    --expected-samples "$((EVENT_COUNT + 1))" \
    "${OBSERVED_ARGS[@]}"
elif [[ -n "$ESCET_REFERENCE_CSV_FALLBACK" ]]; then
  if [[ ! -f "$ESCET_REFERENCE_CSV_FALLBACK" ]]; then
    echo "Error: fallback ESCET reference CSV not found: $ESCET_REFERENCE_CSV_FALLBACK" >&2
    exit 1
  fi
  cp "$ESCET_REFERENCE_CSV_FALLBACK" "$ESCET_REFERENCE_CSV"
  echo "cifsim was skipped or unavailable. Copied explicit fallback reference: $ESCET_REFERENCE_CSV_FALLBACK"
elif [[ "$RUN_CIFSIM" == "yes" ]]; then
  echo "Error: cifsim not found in PATH, but RUN_CIFSIM=yes was requested." >&2
  exit 1
else
  echo "Error: cifsim not found in PATH or RUN_CIFSIM=no, and no ESCET_REFERENCE_CSV_FALLBACK was provided." >&2
  echo "This workflow normally generates the ESCET reference CSV by running cifsim and parsing its log." >&2
  echo "Install/configure cifsim, or provide an explicit fallback only for offline smoke tests:" >&2
  echo "  ESCET_REFERENCE_CSV_FALLBACK=examples/<model>_escet_trace_sample.csv ./scripts/run_event_trace_behavior_comparison.sh" >&2
  exit 1
fi

echo
echo "Step 3/4 - Compare ESCET reference vs generated runtime"
python3 validation/compare_with_escet_behavior.py \
  --cif "$CIF_PATH" \
  --generated-dir "$GENERATED_DIR" \
  --events-csv "$EVENTS_CSV" \
  --history-vars "$HISTORY_VAR" \
  --escet-trace "$ESCET_REFERENCE_CSV" \
  --var-map "$HISTORY_VAR=$HISTORY_VAR" \
  --tolerance "$TOLERANCE" \
  --output-dir "$ESCET_COMPARISON_DIR"

echo
echo "Step 4/4 - Optional generated runtime vs PyCrop-hosted comparison"
PYCROP_STATUS="skipped"
if [[ "$RUN_PYCROP" != "no" && -d "$PYCROP_ROOT" ]]; then
  python3 validation/compare_with_pycrop_behavior.py \
    --cif "$CIF_PATH" \
    --generated-dir "$GENERATED_DIR" \
    --pycrop-root "$PYCROP_ROOT" \
    --events-csv "$EVENTS_CSV" \
    --seconds "$PYCROP_SECONDS" \
    --history-vars "$HISTORY_VAR" \
    --var-map "$HISTORY_VAR=$HISTORY_VAR" \
    --tolerance "$TOLERANCE" \
    --output-dir "$PYCROP_COMPARISON_DIR"
  PYCROP_STATUS="completed"
elif [[ "$RUN_PYCROP" == "yes" ]]; then
  echo "PyCrop comparison requested, but PYCROP_ROOT does not exist: $PYCROP_ROOT" >&2
  exit 1
else
  echo "PyCrop comparison skipped. PYCROP_ROOT not found or RUN_PYCROP=no."
fi

GENERATED_TRACE="$ESCET_COMPARISON_DIR/generated_trace.csv"
SUMMARY_MD="$OUTPUT_DIR/${MODEL_NAME}_event_trace_behavior_comparison_summary.md"
cat > "$SUMMARY_MD" <<EOF_SUMMARY
# Event-trace behavior comparison summary

- model name: \`$MODEL_NAME\`
- CIF: \`$CIF_PATH\`
- generated package: \`$GENERATED_DIR\`
- events CSV: \`$EVENTS_CSV\`
- event column: \`$EVENT_COLUMN\`
- target column: \`$TARGET_COLUMN\`
- default target: \`$DEFAULT_TARGET\`
- event resolution: \`$EVENT_RESOLUTION\`
- history variable: \`$HISTORY_VAR\`
- ESCET trace file generated for cifsim: \`$ESCET_TRACE_FILE\`
- cifsim log: \`$CIFSIM_LOG\`
- ESCET observable reference CSV generated from cifsim: \`$ESCET_REFERENCE_CSV\`
- generated trace produced during comparison: \`$GENERATED_TRACE\`
- ESCET comparison report: \`$ESCET_COMPARISON_DIR/escet_vs_generated_behavior.md\`
- PyCrop comparison status: \`$PYCROP_STATUS\`
- PyCrop comparison report: \`$PYCROP_COMPARISON_DIR/generated_vs_pycrop_behavior.md\`

This workflow targets CIF models whose simulation scenario can be represented as an ordered event trace.
It is a validation/comparison workflow only: it does not translate or regenerate the Python package.
Run \`scripts/run_pipeline.sh\` first when the generated package is missing or outdated.
EOF_SUMMARY

echo
echo "Done. Summary: $SUMMARY_MD"
echo "ESCET comparison report: $ESCET_COMPARISON_DIR/escet_vs_generated_behavior.md"
if [[ "$PYCROP_STATUS" == "completed" ]]; then
  echo "PyCrop comparison report: $PYCROP_COMPARISON_DIR/generated_vs_pycrop_behavior.md"
fi
