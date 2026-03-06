#!/bin/bash
# Recording script for: ndt_scan_matcher
# Package: ndt_scan_matcher
# Executable: ndt_scan_matcher_node
# Namespace: /autoware
# Latency: 38.7 ms

set -e

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$(dirname "${SCRIPT_DIR}")")"

# Source environments
source /opt/ros/humble/setup.bash
source ${HOME}/autoware/install/setup.bash

# Set remapping file path (empty for now - can be customized)
REMAP_FILE=""

echo "Recording node: ndt_scan_matcher"
echo "Package: ndt_scan_matcher"
echo "Executable: ndt_scan_matcher_node"
echo "Namespace: /autoware"

# Navigate to replayer directory
cd "/home/tristan-toye/ros2_single_node_replayer"

# Start recording
# Format: python3 recorder.py <package> <executable> <namespace> <node_name> <remap_file>
python3 recorder.py "ndt_scan_matcher" "ndt_scan_matcher_node" "/autoware" "ndt_scan_matcher" "${REMAP_FILE}"

echo ""
echo "Recording complete for ndt_scan_matcher"
echo "Output saved to: /home/tristan-toye/ros2_single_node_replayer/output/"
