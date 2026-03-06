#!/bin/bash
# =============================================================================
# Master Script to Record All Top Nodes
# =============================================================================
# This script records each node one at a time.
# Run while Autoware is NOT running - each node recording will start Autoware.
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Recording all top nodes..."
echo ""

echo '[1/15] Recording: lidar_centerpoint'
# Uncomment below to auto-run:
# "${SCRIPT_DIR}/lidar_centerpoint/record.sh"

echo '[2/15] Recording: ndt_scan_matcher'
# Uncomment below to auto-run:
# "${SCRIPT_DIR}/ndt_scan_matcher/record.sh"

echo '[3/15] Recording: occupancy_grid_map_node'
# Uncomment below to auto-run:
# "${SCRIPT_DIR}/occupancy_grid_map_node/record.sh"

echo '[4/15] Recording: euclidean_cluster'
# Uncomment below to auto-run:
# "${SCRIPT_DIR}/euclidean_cluster/record.sh"

echo '[5/15] Recording: multi_object_tracker'
# Uncomment below to auto-run:
# "${SCRIPT_DIR}/multi_object_tracker/record.sh"

echo '[6/15] Recording: pointcloud_concatenate_data'
# Uncomment below to auto-run:
# "${SCRIPT_DIR}/pointcloud_concatenate_data/record.sh"

echo '[7/15] Recording: behavior_path_planner'
# Uncomment below to auto-run:
# "${SCRIPT_DIR}/behavior_path_planner/record.sh"

echo '[8/15] Recording: map_based_prediction'
# Uncomment below to auto-run:
# "${SCRIPT_DIR}/map_based_prediction/record.sh"

echo '[9/15] Recording: motion_velocity_planner'
# Uncomment below to auto-run:
# "${SCRIPT_DIR}/motion_velocity_planner/record.sh"

echo '[10/15] Recording: ekf_localizer'
# Uncomment below to auto-run:
# "${SCRIPT_DIR}/ekf_localizer/record.sh"

echo '[11/15] Recording: shape_estimation'
# Uncomment below to auto-run:
# "${SCRIPT_DIR}/shape_estimation/record.sh"

echo '[12/15] Recording: autonomous_emergency_braking'
# Uncomment below to auto-run:
# "${SCRIPT_DIR}/autonomous_emergency_braking/record.sh"

echo '[13/15] Recording: trajectory_follower_controller'
# Uncomment below to auto-run:
# "${SCRIPT_DIR}/trajectory_follower_controller/record.sh"

echo '[14/15] Recording: mission_planner'
# Uncomment below to auto-run:
# "${SCRIPT_DIR}/mission_planner/record.sh"

echo '[15/15] Recording: velocity_smoother'
# Uncomment below to auto-run:
# "${SCRIPT_DIR}/velocity_smoother/record.sh"

