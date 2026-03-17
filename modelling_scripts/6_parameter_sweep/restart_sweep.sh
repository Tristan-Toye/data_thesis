#!/bin/bash
# =============================================================================
# Kill any running parameter sweep and start a new one.
# Logs go to ~/sweep_output.log (override with SWEEP_LOG=path ./restart_sweep.sh).
#
# If the sweep needs sudo for perf (NMI watchdog), set SUDO_PASSWORD so the
# background process can run sysctl. Example: SUDO_PASSWORD=yourpass ./restart_sweep.sh
# Or set it in this script (less secure): SUDO_PASSWORD="yourpass"
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SWEEP_LOG="${SWEEP_LOG:-$HOME/sweep_output.log}"
LOCK_FILE="${HOME}/scripts/experiments/6_parameter_sweep/.sweep.lock"

# Prompt for sudo password once if not set (so background sweep can run sudo sysctl)
if [ -z "${SUDO_PASSWORD:-}" ]; then
    echo "Sweep may need sudo for perf (NMI watchdog). Enter password (or leave empty to skip):"
    read -rs SUDO_PASSWORD
    echo
fi
export SUDO_PASSWORD

echo "Stopping any running parameter sweep..."
pkill -f "run_parameter_sweep.sh" 2>/dev/null || true
sleep 2
if pgrep -f "run_parameter_sweep.sh" >/dev/null 2>&1; then
    echo "Force killing..."
    pkill -9 -f "run_parameter_sweep.sh" 2>/dev/null || true
    sleep 1
fi

echo "Removing lock file (if any)..."
rm -f "${LOCK_FILE}"

echo "Starting parameter sweep (log: ${SWEEP_LOG})..."
source /opt/ros/humble/setup.bash
source "${HOME}/autoware/install/setup.bash"
[ -f "${HOME}/ros2_caret_ws/install/local_setup.bash" ] && source "${HOME}/ros2_caret_ws/install/local_setup.bash"

cd "${SCRIPT_DIR}"
# Line-buffer stdout so "Running:" / "Done:" appear in the log immediately (not when buffer fills)
nohup stdbuf -oL bash run_parameter_sweep.sh > "${SWEEP_LOG}" 2>&1 &
echo "Sweep PID: $!"
PROGRESS_LOG="${HOME}/scripts/experiments/6_parameter_sweep/sweep_progress.log"
echo "Done. Tail logs with: tail -f ${SWEEP_LOG}"
echo "Running/Done (historical + live): cat ${PROGRESS_LOG}; tail -n 0 -f ${PROGRESS_LOG}"
