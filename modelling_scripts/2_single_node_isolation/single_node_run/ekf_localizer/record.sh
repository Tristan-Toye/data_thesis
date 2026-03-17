#!/bin/bash
# Recording script for: ekf_localizer
# Package: ekf_localizer
# Executable: ekf_localizer_node
# Namespace: /autoware
# Latency: 15.3 ms

set -e

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$(dirname "${SCRIPT_DIR}")")"

# Source environments
source /opt/ros/humble/setup.bash
source ${HOME}/autoware/install/setup.bash

# Set remapping file path (empty for now - can be customized)
REMAP_FILE=""

echo "Recording node: ekf_localizer"
echo "Package: ekf_localizer"
echo "Executable: ekf_localizer_node"
echo "Namespace: /autoware"

# Navigate to replayer directory
cd "/home/tristan-toye/ros2_single_node_replayer"

# Start recording
# Format: python3 recorder.py <package> <executable> <namespace> <node_name> <remap_file>
python3 recorder.py "ekf_localizer" "ekf_localizer_node" "/autoware" "ekf_localizer" "${REMAP_FILE}"

echo ""
echo "Recording complete for ekf_localizer"
echo "Output saved to: /home/tristan-toye/ros2_single_node_replayer/output/"
