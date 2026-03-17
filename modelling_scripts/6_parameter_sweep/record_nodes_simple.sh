#!/bin/bash
# =============================================================================
# Simple Node Recorder - Works with already-running Autoware
# =============================================================================
# For each target node: get subscriptions, dump params, record input topics.
# Assumes Autoware is already running. Does NOT launch/stop Autoware.
# =============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_BASE="${HOME}/ros2_single_node_replayer/output"
ROSBAG_PATH="${HOME}/autoware_map/sample-rosbag"
ROSBAG_RATE=0.2

source /opt/ros/humble/setup.bash
source "${HOME}/autoware/install/setup.bash"

declare -A NODE_NAMES=(
    ["lidar_centerpoint"]="lidar_centerpoint"
    ["ndt_scan_matcher"]="ndt_scan_matcher"
    ["occupancy_grid_map_node"]="occupancy_grid_map_node"
    ["euclidean_cluster"]="euclidean_cluster"
    ["multi_object_tracker"]="multi_object_tracker"
    ["pointcloud_concatenate_data"]="concatenate_data"
    ["behavior_path_planner"]="behavior_path_planner"
    ["map_based_prediction"]="map_based_prediction"
    ["motion_velocity_planner"]="motion_velocity_planner"
    ["ekf_localizer"]="ekf_localizer"
    ["shape_estimation"]="shape_estimation"
    ["autonomous_emergency_braking"]="autonomous_emergency_braking"
    ["trajectory_follower_controller"]="controller_node_exe"
    ["mission_planner"]="mission_planner"
    ["velocity_smoother"]="velocity_smoother"
)

declare -A NODE_PACKAGES=(
    ["lidar_centerpoint"]="lidar_centerpoint:lidar_centerpoint_node"
    ["ndt_scan_matcher"]="ndt_scan_matcher:ndt_scan_matcher_node"
    ["occupancy_grid_map_node"]="probabilistic_occupancy_grid_map:occupancy_grid_map_node"
    ["euclidean_cluster"]="euclidean_cluster:euclidean_cluster_node"
    ["multi_object_tracker"]="multi_object_tracker:multi_object_tracker_node"
    ["pointcloud_concatenate_data"]="pointcloud_preprocessor:pointcloud_concatenate_data_synchronizer_node"
    ["behavior_path_planner"]="behavior_path_planner:behavior_path_planner_node"
    ["map_based_prediction"]="map_based_prediction:map_based_prediction_node"
    ["motion_velocity_planner"]="motion_velocity_planner:motion_velocity_planner_node"
    ["ekf_localizer"]="ekf_localizer:ekf_localizer_node"
    ["shape_estimation"]="shape_estimation:shape_estimation_node"
    ["autonomous_emergency_braking"]="autonomous_emergency_braking:autonomous_emergency_braking_node"
    ["trajectory_follower_controller"]="trajectory_follower_nodes:controller_node"
    ["mission_planner"]="mission_planner:mission_planner_node"
    ["velocity_smoother"]="velocity_smoother:velocity_smoother_node"
)

NODES_TO_RECORD=(
    "lidar_centerpoint"
    "euclidean_cluster"
    "multi_object_tracker"
    "pointcloud_concatenate_data"
    "behavior_path_planner"
    "map_based_prediction"
    "motion_velocity_planner"
    "ekf_localizer"
    "shape_estimation"
    "autonomous_emergency_braking"
    "trajectory_follower_controller"
    "mission_planner"
    "velocity_smoother"
)

find_node_full_path() {
    local ros_name="$1"
    ros2 node list 2>/dev/null | grep "/${ros_name}$" | head -1
}

echo "=============================================="
echo "  Simple Node Recorder"
echo "=============================================="
echo "  Checking for already-recorded nodes..."
echo ""

RECORDED=0
FAILED=0
TOTAL=${#NODES_TO_RECORD[@]}

for SHORT_NAME in "${NODES_TO_RECORD[@]}"; do
    ROS_NAME="${NODE_NAMES[$SHORT_NAME]}"
    PKG_EXE="${NODE_PACKAGES[$SHORT_NAME]}"
    IFS=':' read -r PACKAGE EXECUTABLE <<< "$PKG_EXE"

    existing=$(ls -d "${OUTPUT_BASE}"/*"${SHORT_NAME}"* 2>/dev/null | head -1 || true)
    if [ -n "$existing" ] && ls "$existing"/rosbag2_* &>/dev/null 2>&1; then
        echo "SKIP: ${SHORT_NAME} already recorded at ${existing}"
        RECORDED=$((RECORDED + 1))
        continue
    fi

    echo ""
    echo "--- Recording: ${SHORT_NAME} ---"

    FULL_PATH=$(find_node_full_path "$ROS_NAME")
    if [ -z "$FULL_PATH" ]; then
        echo "  NOT FOUND in ROS graph (ROS name: $ROS_NAME)"
        FAILED=$((FAILED + 1))
        continue
    fi
    echo "  Found at: ${FULL_PATH}"

    NAMESPACE="${FULL_PATH%/$ROS_NAME}"
    [ -z "$NAMESPACE" ] && NAMESPACE="/"
    echo "  Namespace: ${NAMESPACE}"

    NS_FLAT=$(echo "$NAMESPACE" | sed 's|^/||; s|/|__|g')
    DIR_NAME="$(date +%Y-%m-%d-%H-%M-%S)_${NS_FLAT}__${ROS_NAME}"
    REC_DIR="${OUTPUT_BASE}/${DIR_NAME}"
    mkdir -p "${REC_DIR}"

    PARAM_FILE="${REC_DIR}/${NS_FLAT}__${ROS_NAME}.yaml"
    echo "  Dumping params to ${PARAM_FILE}..."
    ros2 param dump "${FULL_PATH}" > "${PARAM_FILE}" 2>/dev/null || echo "  WARNING: param dump failed"

    RUN_CMD="ros2 run ${PACKAGE} ${EXECUTABLE} --ros-args --params-file ${NS_FLAT}__${ROS_NAME}.yaml -r __ns:=${NAMESPACE} -r __node:=${ROS_NAME}"
    echo "$RUN_CMD" > "${REC_DIR}/ros2_run_${PACKAGE}_${EXECUTABLE}"

    TOPICS=$(ros2 node info "${FULL_PATH}" 2>/dev/null | grep "Subscribers:" -A 100 | grep "Publishers:" -B 100 | grep -E "^\s+/" | awk '{print $1}' | sed 's|:$||')

    if [ -z "$TOPICS" ]; then
        echo "  WARNING: No subscriber topics found"
        FAILED=$((FAILED + 1))
        continue
    fi

    TOPIC_LIST="/tf /tf_static"
    while IFS= read -r topic; do
        [ -n "$topic" ] && TOPIC_LIST="$TOPIC_LIST $topic"
    done <<< "$TOPICS"
    echo "  Recording topics: $(echo $TOPIC_LIST | wc -w) topics"

    cd "${REC_DIR}"
    ros2 bag record $TOPIC_LIST &
    BAG_PID=$!

    sleep 3

    echo "  Playing rosbag at rate ${ROSBAG_RATE}..."
    ros2 bag play "${ROSBAG_PATH}" -r "${ROSBAG_RATE}" --disable-keyboard-controls </dev/null 2>/dev/null || true

    sleep 5

    echo "  Stopping recording..."
    kill -INT "$BAG_PID" 2>/dev/null || true
    sleep 2
    kill -9 "$BAG_PID" 2>/dev/null || true
    wait "$BAG_PID" 2>/dev/null || true

    if ls "${REC_DIR}"/rosbag2_* &>/dev/null 2>&1; then
        echo "  SUCCESS: Recorded to ${REC_DIR}"
        RECORDED=$((RECORDED + 1))
    else
        echo "  FAILED: No rosbag created"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "=============================================="
echo "  Recording Summary"
echo "=============================================="
echo "  Recorded: ${RECORDED}"
echo "  Failed:   ${FAILED}"
echo "  Total:    ${TOTAL}"
echo "=============================================="
