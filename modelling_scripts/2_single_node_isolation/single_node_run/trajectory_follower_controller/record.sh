#!/bin/bash
# Recording script for: trajectory_follower_controller
# Package: trajectory_follower_nodes
# Executable: controller_node
# Namespace: /autoware
# Latency: 10.5 ms

set -e

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$(dirname "${SCRIPT_DIR}")")"

# Source environments
source /opt/ros/humble/setup.bash
source ${HOME}/autoware/install/setup.bash

# Set remapping file path (empty for now - can be customized)
REMAP_FILE=""

echo "Recording node: trajectory_follower_controller"
echo "Package: trajectory_follower_nodes"
echo "Executable: controller_node"
echo "Namespace: /autoware"

# Navigate to replayer directory
cd "/home/tristan-toye/ros2_single_node_replayer"

# Start recording
# Format: python3 recorder.py <package> <executable> <namespace> <node_name> <remap_file>
python3 recorder.py "trajectory_follower_nodes" "controller_node" "/autoware" "trajectory_follower_controller" "${REMAP_FILE}"

echo ""
echo "Recording complete for trajectory_follower_controller"
echo "Output saved to: /home/tristan-toye/ros2_single_node_replayer/output/"
