#!/bin/bash
# Recording script for: euclidean_cluster
# Package: euclidean_cluster
# Executable: euclidean_cluster_node
# Namespace: /autoware
# Latency: 32.4 ms

set -e

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$(dirname "${SCRIPT_DIR}")")"

# Source environments
source /opt/ros/humble/setup.bash
source ${HOME}/autoware/install/setup.bash

# Set remapping file path (empty for now - can be customized)
REMAP_FILE=""

echo "Recording node: euclidean_cluster"
echo "Package: euclidean_cluster"
echo "Executable: euclidean_cluster_node"
echo "Namespace: /autoware"

# Navigate to replayer directory
cd "/home/tristan-toye/ros2_single_node_replayer"

# Start recording
# Format: python3 recorder.py <package> <executable> <namespace> <node_name> <remap_file>
python3 recorder.py "euclidean_cluster" "euclidean_cluster_node" "/autoware" "euclidean_cluster" "${REMAP_FILE}"

echo ""
echo "Recording complete for euclidean_cluster"
echo "Output saved to: /home/tristan-toye/ros2_single_node_replayer/output/"
