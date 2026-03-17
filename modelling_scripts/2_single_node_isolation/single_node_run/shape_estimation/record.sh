#!/bin/bash
# Recording script for: shape_estimation
# Package: shape_estimation
# Executable: shape_estimation_node
# Namespace: /autoware
# Latency: 14.2 ms

set -e

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$(dirname "${SCRIPT_DIR}")")"

# Source environments
source /opt/ros/humble/setup.bash
source ${HOME}/autoware/install/setup.bash

# Set remapping file path (empty for now - can be customized)
REMAP_FILE=""

echo "Recording node: shape_estimation"
echo "Package: shape_estimation"
echo "Executable: shape_estimation_node"
echo "Namespace: /autoware"

# Navigate to replayer directory
cd "/home/tristan-toye/ros2_single_node_replayer"

# Start recording
# Format: python3 recorder.py <package> <executable> <namespace> <node_name> <remap_file>
python3 recorder.py "shape_estimation" "shape_estimation_node" "/autoware" "shape_estimation" "${REMAP_FILE}"

echo ""
echo "Recording complete for shape_estimation"
echo "Output saved to: /home/tristan-toye/ros2_single_node_replayer/output/"
