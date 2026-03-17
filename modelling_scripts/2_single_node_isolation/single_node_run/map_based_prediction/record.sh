#!/bin/bash
# Recording script for: map_based_prediction
# Package: map_based_prediction
# Executable: map_based_prediction_node
# Namespace: /autoware
# Latency: 20.9 ms

set -e

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$(dirname "${SCRIPT_DIR}")")"

# Source environments
source /opt/ros/humble/setup.bash
source ${HOME}/autoware/install/setup.bash

# Set remapping file path (empty for now - can be customized)
REMAP_FILE=""

echo "Recording node: map_based_prediction"
echo "Package: map_based_prediction"
echo "Executable: map_based_prediction_node"
echo "Namespace: /autoware"

# Navigate to replayer directory
cd "/home/tristan-toye/ros2_single_node_replayer"

# Start recording
# Format: python3 recorder.py <package> <executable> <namespace> <node_name> <remap_file>
python3 recorder.py "map_based_prediction" "map_based_prediction_node" "/autoware" "map_based_prediction" "${REMAP_FILE}"

echo ""
echo "Recording complete for map_based_prediction"
echo "Output saved to: /home/tristan-toye/ros2_single_node_replayer/output/"
