#!/bin/bash
# Recording script for: autonomous_emergency_braking
# Package: autonomous_emergency_braking
# Executable: autonomous_emergency_braking_node
# Namespace: /autoware
# Latency: 12.7 ms

set -e

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$(dirname "${SCRIPT_DIR}")")"

# Source environments
source /opt/ros/humble/setup.bash
source ${HOME}/autoware/install/setup.bash

# Set remapping file path (empty for now - can be customized)
REMAP_FILE=""

echo "Recording node: autonomous_emergency_braking"
echo "Package: autonomous_emergency_braking"
echo "Executable: autonomous_emergency_braking_node"
echo "Namespace: /autoware"

# Navigate to replayer directory
cd "/home/tristan-toye/ros2_single_node_replayer"

# Start recording
# Format: python3 recorder.py <package> <executable> <namespace> <node_name> <remap_file>
python3 recorder.py "autonomous_emergency_braking" "autonomous_emergency_braking_node" "/autoware" "autonomous_emergency_braking" "${REMAP_FILE}"

echo ""
echo "Recording complete for autonomous_emergency_braking"
echo "Output saved to: /home/tristan-toye/ros2_single_node_replayer/output/"
