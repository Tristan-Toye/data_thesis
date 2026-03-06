#!/bin/bash
# Recording script for: occupancy_grid_map_node
# Package: probabilistic_occupancy_grid_map
# Executable: occupancy_grid_map_node
# Namespace: /autoware
# Latency: 35.1 ms

set -e

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$(dirname "${SCRIPT_DIR}")")"

# Source environments
source /opt/ros/humble/setup.bash
source ${HOME}/autoware/install/setup.bash

# Set remapping file path (empty for now - can be customized)
REMAP_FILE=""

echo "Recording node: occupancy_grid_map_node"
echo "Package: probabilistic_occupancy_grid_map"
echo "Executable: occupancy_grid_map_node"
echo "Namespace: /autoware"

# Navigate to replayer directory
cd "/home/tristan-toye/ros2_single_node_replayer"

# Start recording
# Format: python3 recorder.py <package> <executable> <namespace> <node_name> <remap_file>
python3 recorder.py "probabilistic_occupancy_grid_map" "occupancy_grid_map_node" "/autoware" "occupancy_grid_map_node" "${REMAP_FILE}"

echo ""
echo "Recording complete for occupancy_grid_map_node"
echo "Output saved to: /home/tristan-toye/ros2_single_node_replayer/output/"
