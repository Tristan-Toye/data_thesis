#!/bin/bash

# Restart Experiment 8 backfill/analysis for start-to-publish latency.
# - Kills any existing backfill process
# - Starts a fresh backfill with logging you can tail
#
# Usage:
#   ./restart_analysis.sh
#
# Logs:
#   ~/exp8_backfill.log

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.."

echo "[restart_analysis] Killing any existing Experiment 8 backfill processes..."
pkill -f "modelling_scripts/8_start_to_publish/backfill_publish_latency.py" 2>/dev/null || true

echo "[restart_analysis] Starting fresh backfill with logging..."
python3 modelling_scripts/8_start_to_publish/backfill_publish_latency.py 

