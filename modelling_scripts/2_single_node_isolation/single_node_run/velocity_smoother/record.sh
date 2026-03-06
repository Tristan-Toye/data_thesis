#!/bin/bash
# Recording script for: velocity_smoother
# Package: velocity_smoother
# Executable: velocity_smoother_node
# Namespace: /autoware
# Latency: 6.3 ms

set -e

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$(dirname "${SCRIPT_DIR}")")"

# Source environments
source /opt/ros/humble/setup.bash
source ${HOME}/autoware/install/setup.bash

# Set remapping file path (empty for now - can be customized)
REMAP_FILE=""

echo "Recording node: velocity_smoother"
echo "Package: velocity_smoother"
echo "Executable: velocity_smoother_node"
echo "Namespace: /autoware"

# Navigate to replayer directory
cd "/home/tristan-toye/ros2_single_node_replayer"

# Start recording
# Format: python3 recorder.py <package> <executable> <namespace> <node_name> <remap_file>
python3 recorder.py "velocity_smoother" "velocity_smoother_node" "/autoware" "velocity_smoother" "${REMAP_FILE}"

echo ""
echo "Recording complete for velocity_smoother"
echo "Output saved to: /home/tristan-toye/ros2_single_node_replayer/output/"
