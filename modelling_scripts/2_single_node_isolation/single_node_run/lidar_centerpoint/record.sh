#!/bin/bash
# Recording script for: lidar_centerpoint
# Package: lidar_centerpoint
# Executable: lidar_centerpoint_node
# Namespace: /autoware
# Latency: 45.2 ms

set -e

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$(dirname "${SCRIPT_DIR}")")"

# Source environments
source /opt/ros/humble/setup.bash
source ${HOME}/autoware/install/setup.bash

# Set remapping file path (empty for now - can be customized)
REMAP_FILE=""

echo "Recording node: lidar_centerpoint"
echo "Package: lidar_centerpoint"
echo "Executable: lidar_centerpoint_node"
echo "Namespace: /autoware"

# Navigate to replayer directory
cd "/home/tristan-toye/ros2_single_node_replayer"

# Start recording
# Format: python3 recorder.py <package> <executable> <namespace> <node_name> <remap_file>
python3 recorder.py "lidar_centerpoint" "lidar_centerpoint_node" "/autoware" "lidar_centerpoint" "${REMAP_FILE}"

echo ""
echo "Recording complete for lidar_centerpoint"
echo "Output saved to: /home/tristan-toye/ros2_single_node_replayer/output/"
