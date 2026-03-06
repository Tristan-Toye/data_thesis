#!/bin/bash
# Recording script for: multi_object_tracker
# Package: multi_object_tracker
# Executable: multi_object_tracker_node
# Namespace: /autoware
# Latency: 28.6 ms

set -e

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$(dirname "${SCRIPT_DIR}")")"

# Source environments
source /opt/ros/humble/setup.bash
source ${HOME}/autoware/install/setup.bash

# Set remapping file path (empty for now - can be customized)
REMAP_FILE=""

echo "Recording node: multi_object_tracker"
echo "Package: multi_object_tracker"
echo "Executable: multi_object_tracker_node"
echo "Namespace: /autoware"

# Navigate to replayer directory
cd "/home/tristan-toye/ros2_single_node_replayer"

# Start recording
# Format: python3 recorder.py <package> <executable> <namespace> <node_name> <remap_file>
python3 recorder.py "multi_object_tracker" "multi_object_tracker_node" "/autoware" "multi_object_tracker" "${REMAP_FILE}"

echo ""
echo "Recording complete for multi_object_tracker"
echo "Output saved to: /home/tristan-toye/ros2_single_node_replayer/output/"
