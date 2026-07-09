#!/usr/bin/env bash
set -euo pipefail

# Convenience wrapper for the ShipCounter event-trace comparison.
# It delegates the actual workflow to run_event_trace_behavior_comparison.sh.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export CIF_PATH="${CIF_PATH:-examples/ship-counter-optimized.cif}"
export EVENTS_CSV="${EVENTS_CSV:-examples/ship-counter-optimized_events.csv}"
export HISTORY_VAR="${HISTORY_VAR:-ShipCounter_0_count}"
export DEFAULT_TARGET="${DEFAULT_TARGET:-ShipCounter}"

exec "$SCRIPT_DIR/run_event_trace_behavior_comparison.sh" "$@"
