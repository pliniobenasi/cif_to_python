#!/usr/bin/env bash
set -u

# Interactive wrapper for the CIF -> modular Python simulator pipeline.
#
# This script orchestrates:
# 1. optional official ESCET command-line validation;
# 2. internal feature/compatibility analysis;
# 3. automatic Python module generation;
# 4. optional verification simulation using the current GenericSimulationEngine.
#
# Output directory policy:
# the generated package path is always derived from the CIF filename:
#   out/generated/<MODEL_NAME>
# where <MODEL_NAME> is the CIF basename without the .cif extension.
# The user cannot override this destination from this wrapper, because the
# repository validation scripts use the same deterministic convention.
#
# Verification simulation history is also fixed by convention:
#   out/outputs/<MODEL_NAME>/results/history.csv
# The wrapper always exports this file whenever the optional verification
# simulation is executed.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

print_usage() {
  cat <<'USAGE'
Usage:
  ./scripts/run_pipeline.sh MODEL.cif

Examples:
  ./scripts/run_pipeline.sh examples/Grid.cif
  ./scripts/run_pipeline.sh examples/Grid_semplified.cif
  ./scripts/run_pipeline.sh examples/coffee_machine.cif
  ./scripts/run_pipeline.sh examples/traffic_light_temporal.cif

Generated package destination:
  out/generated/<MODEL_NAME>/

Verification simulation history destination:
  out/outputs/<MODEL_NAME>/results/history.csv

Optional environment variables:
  ESCET_CIF_CHECK_CMD   Command template for ESCET validation.
                        Placeholders: {cif}, {cif_abs}
                        Example:
                        export ESCET_CIF_CHECK_CMD='cif2cif {cif_abs} /tmp/validated.cif'

  ESCET_TIMEOUT         Timeout in seconds for ESCET validation.
                        Default: 300
USAGE
}

ask_yes_no() {
  local prompt="$1"
  local default="${2:-n}"
  local answer

  if [[ "$default" == "y" || "$default" == "Y" ]]; then
    read -r -p "$prompt [Y/n]: " answer
    answer="${answer:-y}"
  else
    read -r -p "$prompt [y/N]: " answer
    answer="${answer:-n}"
  fi

  case "${answer,,}" in
    y|yes) return 0 ;;
    *) return 1 ;;
  esac
}

ask_value() {
  local prompt="$1"
  local default="$2"
  local answer

  read -r -p "$prompt [$default]: " answer
  echo "${answer:-$default}"
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -lt 1 ]]; then
  print_usage
  exit 0
fi

if [[ $# -gt 1 ]]; then
  echo "Error: run_pipeline.sh no longer accepts a custom generated package output directory." >&2
  echo >&2
  echo "The output path is fixed by convention:" >&2
  echo "  out/generated/<MODEL_NAME>/" >&2
  echo >&2
  echo "Use:" >&2
  echo "  ./scripts/run_pipeline.sh MODEL.cif" >&2
  exit 1
fi

CIF_PATH="$1"

if [[ ! -f "$CIF_PATH" ]]; then
  echo "Error: CIF file not found: $CIF_PATH"
  exit 1
fi

base_name="$(basename "$CIF_PATH")"
MODEL_NAME="${base_name%.*}"
OUTPUT_DIR="out/generated/${MODEL_NAME}"
HISTORY_CSV="out/outputs/${MODEL_NAME}/results/history.csv"


echo
echo "============================================================"
echo "Automatic translation of CIF models to modular Python simulators"
echo "============================================================"
echo "CIF input:      $CIF_PATH"
echo "Model name:     $MODEL_NAME"
echo "Output package: $OUTPUT_DIR"
echo "Default history: $HISTORY_CSV"
echo

ESCET_ARGS=()
if ask_yes_no "Validate the CIF with ESCET before translation?" "n"; then
  ESCET_TIMEOUT_DEFAULT="${ESCET_TIMEOUT:-300}"
  ESCET_TIMEOUT_VALUE="$(ask_value "ESCET timeout in seconds" "$ESCET_TIMEOUT_DEFAULT")"

  if [[ -n "${ESCET_CIF_CHECK_CMD:-}" ]]; then
    echo "Using configured ESCET_CIF_CHECK_CMD:"
    echo "  $ESCET_CIF_CHECK_CMD"
    ESCET_ARGS+=(--escet-check --require-escet --escet-timeout "$ESCET_TIMEOUT_VALUE")
  else
    echo
    echo "ESCET_CIF_CHECK_CMD is not configured."
    echo "Enter an ESCET command containing the {cif_abs} placeholder, or leave empty to abort."
    echo "Example: cif2cif {cif_abs} --output-mode=error"
    read -r -p "ESCET command: " ESCET_CMD

    if [[ -z "$ESCET_CMD" ]]; then
      echo "ESCET validation was requested, but no command was provided. Aborting."
      exit 1
    fi

    ESCET_ARGS+=(--escet-cmd "$ESCET_CMD" --require-escet --escet-timeout "$ESCET_TIMEOUT_VALUE")
  fi
else
  echo "ESCET validation skipped by user request."
fi

echo
echo "Step 1/3 - Internal compatibility analysis and Python module generation"
echo "------------------------------------------------------------"

set +e
python3 scripts/cif_to_python.py "$CIF_PATH" --output "$OUTPUT_DIR" "${ESCET_ARGS[@]}"
GEN_STATUS=$?
set -e

if [[ $GEN_STATUS -ne 0 ]]; then
  echo
  echo "Pipeline stopped: ESCET validation, internal compatibility analysis, or module generation failed."
  exit "$GEN_STATUS"
fi

echo
echo "Generation completed."
echo "Output written to: $OUTPUT_DIR"
echo

REPORT_DIR="out/reports/${MODEL_NAME}"
if [[ -f "$REPORT_DIR/feature_report.md" ]]; then
  echo "Compatibility report:"
  echo "  $REPORT_DIR/feature_report.md"
fi

if [[ -f "$REPORT_DIR/translation_manifest.md" ]]; then
  echo "Translation manifest:"
  echo "  $REPORT_DIR/translation_manifest.md"
fi

echo
if ! ask_yes_no "Run a verification simulation for the generated package?" "n"; then
  echo "Simulation skipped. Pipeline completed after translation."
  exit 0
fi

echo
echo "Step 2/3 - Verification simulation setup"
echo "------------------------------------------------------------"
echo "The verification simulation currently runs on the project GenericSimulationEngine."
echo

SIM_MODE="$(ask_value "Simulation type: step or event" "step")"

if [[ "${SIM_MODE,,}" == "event" || "${SIM_MODE,,}" == "event-driven" ]]; then
  echo
  echo "You can provide either an event CSV trace or a manual event sequence."
  echo "Event CSV examples:
  examples/coffee_machine_events.csv
  examples/traffic_light_temporal_events.csv
  examples/ship-counter-optimized_events.csv"
  read -r -p "Event CSV path (leave empty for manual events): " EVENTS_CSV

  if [[ -n "$EVENTS_CSV" ]]; then
    echo "History CSV output: $HISTORY_CSV"
    RUN_ARGS=(--events-csv "$EVENTS_CSV" --history-csv "$HISTORY_CSV")

    echo
    echo "Step 3/3 - Event-trace simulation"
    echo "------------------------------------------------------------"
    python3 "$OUTPUT_DIR/run_generated_model.py" "${RUN_ARGS[@]}"
  else
    echo
    echo "Enter the event sequence separated by spaces."
    echo "Example: input_coffee heat_water add_water deliver_cup"
    read -r -p "Events: " EVENTS_LINE

    if [[ -z "$EVENTS_LINE" ]]; then
      echo "No events were provided. Aborting simulation."
      exit 1
    fi

    # shellcheck disable=SC2206
    EVENTS_ARRAY=($EVENTS_LINE)

    echo "History CSV output: $HISTORY_CSV"
    RUN_ARGS=(--events "${EVENTS_ARRAY[@]}" --history-csv "$HISTORY_CSV")

    echo
    echo "Step 3/3 - Event-driven simulation"
    echo "------------------------------------------------------------"
    python3 "$OUTPUT_DIR/run_generated_model.py" "${RUN_ARGS[@]}"
  fi
else
  LIMIT="$(ask_value "Maximum number of instances per template to simulate" "3")"
  HOURS="$(ask_value "Number of steps/hours to simulate. Leave empty to infer it from --input-csv when provided" "48")"
  SAVE_EVERY="$(ask_value "History sampling frequency save_every" "1")"
  echo "Data CSV example: examples/grid_weather_input.csv"
  read -r -p "Data input CSV path (leave empty to use package default inputs): " INPUT_CSV
  echo "History CSV output: $HISTORY_CSV"
  read -r -p "History variable filters, comma-separated or space-separated (leave empty for all): " HISTORY_VARS

  RUN_ARGS=(--limit "$LIMIT" --save-every "$SAVE_EVERY" --history-csv "$HISTORY_CSV")
  if [[ -n "$HOURS" ]]; then
    RUN_ARGS+=(--hours "$HOURS")
  fi
  if [[ -n "$INPUT_CSV" ]]; then
    RUN_ARGS+=(--input-csv "$INPUT_CSV")
  fi
  if [[ -n "$HISTORY_VARS" ]]; then
    # shellcheck disable=SC2206
    HISTORY_VAR_ARRAY=(${HISTORY_VARS//,/ })
    RUN_ARGS+=(--history-vars "${HISTORY_VAR_ARRAY[@]}")
  fi

  echo
  echo "Step 3/3 - Step-driven simulation"
  echo "------------------------------------------------------------"
  python3 "$OUTPUT_DIR/run_generated_model.py" "${RUN_ARGS[@]}"
fi

echo
echo "Pipeline completed."
