#!/bin/bash
# Recording script for: motion_velocity_planner
# Package: motion_velocity_planner
# Executable: motion_velocity_planner_node
# Namespace: /autoware
# Latency: 18.5 ms

set -e

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$(dirname "${SCRIPT_DIR}")")"

# Source environments
source /opt/ros/humble/setup.bash
source ${HOME}/autoware/install/setup.bash

# Set remapping file path (empty for now - can be customized)
REMAP_FILE=""

echo "Recording node: motion_velocity_planner"
echo "Package: motion_velocity_planner"
echo "Executable: motion_velocity_planner_node"
echo "Namespace: /autoware"

# Navigate to replayer directory
cd "/home/tristan-toye/ros2_single_node_replayer"

# Start recording
# Format: python3 recorder.py <package> <executable> <namespace> <node_name> <remap_file>
python3 recorder.py "motion_velocity_planner" "motion_velocity_planner_node" "/autoware" "motion_velocity_planner" "${REMAP_FILE}"

echo ""
echo "Recording complete for motion_velocity_planner"
echo "Output saved to: /home/tristan-toye/ros2_single_node_replayer/output/"
