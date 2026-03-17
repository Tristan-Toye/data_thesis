#!/bin/bash
# =============================================================================
# Record All 15 Isolated Nodes for Parameter Sweep
# =============================================================================
# Launches Autoware, discovers each target node's real namespace, then uses
# ros2_single_node_replayer/recorder.py to capture a rosbag of each node's
# input topics plus a parameter dump.
#
# Prerequisites:
#   - Autoware installed at ~/autoware
#   - ros2_single_node_replayer at ~/ros2_single_node_replayer
#   - Sample rosbag at ~/autoware_map/sample-rosbag
#   - Sample map at ~/autoware_map/sample-map-rosbag
#
# Usage: ./record_all_isolated.sh [--skip-recorded]
# =============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPLAYER_DIR="${HOME}/ros2_single_node_replayer"
OUTPUT_DIR="${REPLAYER_DIR}/output"
MAP_PATH="${HOME}/autoware_map/sample-map-rosbag"
ROSBAG_PATH="${HOME}/autoware_map/sample-rosbag"
ROSBAG_RATE=0.2
AUTOWARE_INIT_WAIT=120
ROSBAG_SETTLE_WAIT=10

NODES=(
    "lidar_centerpoint:lidar_centerpoint:lidar_centerpoint_node"
    "ndt_scan_matcher:ndt_scan_matcher:ndt_scan_matcher_node"
    "occupancy_grid_map_node:probabilistic_occupancy_grid_map:occupancy_grid_map_node"
    "euclidean_cluster:euclidean_cluster:euclidean_cluster_node"
    "multi_object_tracker:multi_object_tracker:multi_object_tracker_node"
    "pointcloud_concatenate_data:pointcloud_preprocessor:pointcloud_concatenate_data_synchronizer_node"
    "behavior_path_planner:behavior_path_planner:behavior_path_planner_node"
    "map_based_prediction:map_based_prediction:map_based_prediction_node"
    "motion_velocity_planner:motion_velocity_planner:motion_velocity_planner_node"
    "ekf_localizer:ekf_localizer:ekf_localizer_node"
    "shape_estimation:shape_estimation:shape_estimation_node"
    "autonomous_emergency_braking:autonomous_emergency_braking:autonomous_emergency_braking_node"
    "trajectory_follower_controller:trajectory_follower_nodes:controller_node"
    "mission_planner:mission_planner:mission_planner_node"
    "velocity_smoother:velocity_smoother:velocity_smoother_node"
)

source /opt/ros/humble/setup.bash
source "${HOME}/autoware/install/setup.bash"

is_already_recorded() {
    local short_name="$1"
    for dir in "${OUTPUT_DIR}"/*/; do
        [ -d "$dir" ] || continue
        local dirname
        dirname=$(basename "$dir")
        if echo "$dirname" | grep -q "${short_name}\$"; then
            if [ -d "$dir"/rosbag2_* ] 2>/dev/null; then
                echo "$dir"
                return 0
            fi
        fi
    done
    return 1
}

discover_namespace() {
    local short_name="$1"
    local full_path
    full_path=$(ros2 node list 2>/dev/null | grep "/${short_name}\$" | head -1)
    if [ -n "$full_path" ]; then
        local ns="${full_path%/$short_name}"
        [ -z "$ns" ] && ns="/"
        echo "$ns"
        return 0
    fi
    return 1
}

cleanup_autoware() {
    echo "  Stopping Autoware..."
    if [ -n "${AUTOWARE_PID:-}" ] && kill -0 "$AUTOWARE_PID" 2>/dev/null; then
        kill -INT "$AUTOWARE_PID" 2>/dev/null || true
        sleep 3
        kill -9 "$AUTOWARE_PID" 2>/dev/null || true
        wait "$AUTOWARE_PID" 2>/dev/null || true
    fi
    pkill -f "ros2 launch" 2>/dev/null || true
    pkill -f "component_container" 2>/dev/null || true
    sleep 5
}

trap cleanup_autoware EXIT

SKIP_RECORDED=false
if [[ "${1:-}" == "--skip-recorded" ]]; then
    SKIP_RECORDED=true
fi

echo "=============================================="
echo "  Recording All 15 Isolated Nodes"
echo "=============================================="
echo "  Output: ${OUTPUT_DIR}"
echo "  Skip recorded: ${SKIP_RECORDED}"
echo ""

TOTAL=${#NODES[@]}
RECORDED=0
SKIPPED=0
FAILED=0

for i in "${!NODES[@]}"; do
    IFS=':' read -r SHORT_NAME PACKAGE EXECUTABLE <<< "${NODES[$i]}"
    IDX=$((i + 1))

    echo ""
    echo "[$IDX/$TOTAL] Node: ${SHORT_NAME} (${PACKAGE}/${EXECUTABLE})"
    echo "----------------------------------------------"

    if $SKIP_RECORDED; then
        existing=$(is_already_recorded "$SHORT_NAME" || echo "")
        if [ -n "$existing" ]; then
            echo "  SKIP: Already recorded at ${existing}"
            SKIPPED=$((SKIPPED + 1))
            continue
        fi
    fi

    if [ -z "${AUTOWARE_RUNNING:-}" ]; then
        echo "  Launching Autoware (full stack, no CARET)..."
        ros2 launch autoware_launch autoware.launch.xml \
            map_path:="${MAP_PATH}" \
            vehicle_model:=sample_vehicle \
            sensor_model:=sample_sensor_kit \
            rviz:=false &
        AUTOWARE_PID=$!
        AUTOWARE_RUNNING=1

        echo "  Waiting ${AUTOWARE_INIT_WAIT}s for Autoware initialization..."
        sleep "${AUTOWARE_INIT_WAIT}"

        if ! kill -0 "$AUTOWARE_PID" 2>/dev/null; then
            echo "  ERROR: Autoware failed to start"
            AUTOWARE_RUNNING=""
            FAILED=$((FAILED + 1))
            continue
        fi

        echo "  Available target nodes:"
        for check_entry in "${NODES[@]}"; do
            IFS=':' read -r cn _ _ <<< "$check_entry"
            ns_check=$(discover_namespace "$cn" || echo "NOT_FOUND")
            printf "    %-40s => %s\n" "$cn" "$ns_check"
        done
    fi

    NS=$(discover_namespace "$SHORT_NAME" || echo "")
    if [ -z "$NS" ]; then
        echo "  SKIP: Node not found in Autoware graph (composable/not loaded)"
        FAILED=$((FAILED + 1))
        continue
    fi
    echo "  Discovered namespace: ${NS}"

    echo "  Starting recorder..."
    cd "${REPLAYER_DIR}"
    python3 recorder.py "${PACKAGE}" "${EXECUTABLE}" "${NS}" "${SHORT_NAME}" "" &
    RECORDER_PID=$!

    sleep 8

    echo "  Playing rosbag at rate ${ROSBAG_RATE}..."
    ros2 bag play "${ROSBAG_PATH}" -r "${ROSBAG_RATE}" --disable-keyboard-controls </dev/null || true

    echo "  Rosbag complete. Waiting ${ROSBAG_SETTLE_WAIT}s to settle..."
    sleep "${ROSBAG_SETTLE_WAIT}"

    echo "  Stopping recorder..."
    kill -INT "$RECORDER_PID" 2>/dev/null || true
    sleep 3
    kill -9 "$RECORDER_PID" 2>/dev/null || true
    wait "$RECORDER_PID" 2>/dev/null || true

    LATEST_DIR=$(ls -td "${OUTPUT_DIR}"/*"${SHORT_NAME}"* 2>/dev/null | head -1)
    if [ -n "$LATEST_DIR" ] && [ -d "$LATEST_DIR" ]; then
        echo "  SUCCESS: Recorded to ${LATEST_DIR}"
        RECORDED=$((RECORDED + 1))
    else
        echo "  WARNING: Recording dir not found"
        FAILED=$((FAILED + 1))
    fi

    sleep 3
done

echo ""
echo "=============================================="
echo "  Recording Summary"
echo "=============================================="
echo "  Recorded: ${RECORDED}"
echo "  Skipped:  ${SKIPPED}"
echo "  Failed:   ${FAILED}"
echo "  Total:    ${TOTAL}"
echo "=============================================="
