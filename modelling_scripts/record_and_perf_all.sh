#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SINGLE_NODE_DIR="${SCRIPT_DIR}/2_single_node_isolation/single_node_run"
REPLAYER_PATH="${HOME}/ros2_single_node_replayer"
PERF_OUTPUT="${SCRIPT_DIR}/3_perf_profiling/perf_data"
MAP_PATH="${HOME}/autoware_map/sample-map-rosbag"
ROSBAG_PATH="${HOME}/autoware_map/sample-rosbag"
ROSBAG_RATE="0.2"

source /opt/ros/humble/setup.bash
source "${HOME}/autoware/install/setup.bash"

declare -A NODE_MAP
NODE_MAP[lidar_centerpoint]="/perception/object_recognition/detection/centerpoint|lidar_centerpoint|lidar_centerpoint|lidar_centerpoint_node"
NODE_MAP[ndt_scan_matcher]="/localization/pose_estimator|ndt_scan_matcher|ndt_scan_matcher|ndt_scan_matcher_node"
NODE_MAP[occupancy_grid_map_node]="/perception/occupancy_grid_map|occupancy_grid_map_node|probabilistic_occupancy_grid_map|occupancy_grid_map_node"
NODE_MAP[euclidean_cluster]="/perception/object_recognition/detection/clustering|euclidean_cluster|euclidean_cluster|euclidean_cluster_node"
NODE_MAP[multi_object_tracker]="/perception/object_recognition/tracking|multi_object_tracker|multi_object_tracker|multi_object_tracker_node"
NODE_MAP[pointcloud_concatenate_data]="/sensing/lidar|concatenate_data|pointcloud_preprocessor|pointcloud_concatenate_data_synchronizer_node"
NODE_MAP[behavior_path_planner]="/planning/scenario_planning/lane_driving/behavior_planning|behavior_path_planner|behavior_path_planner|behavior_path_planner_node"
NODE_MAP[map_based_prediction]="/perception/object_recognition/prediction|map_based_prediction|map_based_prediction|map_based_prediction_node"
NODE_MAP[motion_velocity_planner]="/planning/scenario_planning/lane_driving/motion_planning|motion_velocity_planner|motion_velocity_planner|motion_velocity_planner_node"
NODE_MAP[ekf_localizer]="/localization/pose_twist_fusion_filter|ekf_localizer|ekf_localizer|ekf_localizer_node"
NODE_MAP[shape_estimation]="/perception/object_recognition/detection/clustering|shape_estimation|shape_estimation|shape_estimation_node"
NODE_MAP[autonomous_emergency_braking]="/control|autonomous_emergency_braking|autonomous_emergency_braking|autonomous_emergency_braking_node"
NODE_MAP[trajectory_follower_controller]="/control/trajectory_follower|controller_node_exe|trajectory_follower_nodes|controller_node"
NODE_MAP[mission_planner]="/planning/mission_planning|mission_planner|mission_planner|mission_planner_node"
NODE_MAP[velocity_smoother]="/planning/scenario_planning|velocity_smoother|velocity_smoother|velocity_smoother_node"

ORDERED_NODES=(
    lidar_centerpoint ndt_scan_matcher occupancy_grid_map_node euclidean_cluster
    multi_object_tracker pointcloud_concatenate_data behavior_path_planner
    map_based_prediction motion_velocity_planner ekf_localizer shape_estimation
    autonomous_emergency_braking trajectory_follower_controller mission_planner
    velocity_smoother
)

cleanup_autoware() {
    echo "Stopping Autoware..."
    kill ${AW_PID} 2>/dev/null || true
    sleep 3
    kill -9 ${AW_PID} 2>/dev/null || true
    wait ${AW_PID} 2>/dev/null || true
}

echo "=============================================="
echo "PHASE 1: Record All Nodes"
echo "=============================================="

echo "Launching Autoware (headless)..."
ros2 launch autoware_launch logging_simulator.launch.xml \
    map_path:="${MAP_PATH}" \
    vehicle_model:=sample_vehicle \
    sensor_model:=sample_sensor_kit \
    rviz:=false &
AW_PID=$!
trap cleanup_autoware EXIT

echo "Autoware PID: ${AW_PID}"
echo "Waiting 60s for all nodes to start..."
sleep 60

echo "Verifying nodes are running..."
ros2 node list 2>/dev/null | wc -l
echo ""

RECORD_COUNT=0
RECORD_TOTAL=${#ORDERED_NODES[@]}

for short_name in "${ORDERED_NODES[@]}"; do
    RECORD_COUNT=$((RECORD_COUNT + 1))
    IFS='|' read -r ns node_name pkg exec_name <<< "${NODE_MAP[$short_name]}"

    echo ""
    echo "[$RECORD_COUNT/$RECORD_TOTAL] Recording: $short_name (${ns}/${node_name})"

    NODE_DIR="${SINGLE_NODE_DIR}/${short_name}"
    mkdir -p "${NODE_DIR}"

    cd "${REPLAYER_PATH}"
    python3 recorder.py "${pkg}" "${exec_name}" "${ns}" "${node_name}" "empty_remapping.yaml" &
    REC_PID=$!

    sleep 8

    if ! kill -0 ${REC_PID} 2>/dev/null; then
        echo "  WARNING: Recorder exited early for ${short_name}"
        wait ${REC_PID} 2>/dev/null || true
        continue
    fi

    echo "  Playing rosbag..."
    ros2 bag play "${ROSBAG_PATH}" -r "${ROSBAG_RATE}" -s sqlite3 2>&1 | tail -1 || true

    sleep 2
    kill -SIGINT -${REC_PID} 2>/dev/null || kill -SIGINT ${REC_PID} 2>/dev/null || true
    WAIT_N=0
    while kill -0 ${REC_PID} 2>/dev/null && [ ${WAIT_N} -lt 15 ]; do
        sleep 1
        WAIT_N=$((WAIT_N + 1))
    done
    kill -9 ${REC_PID} 2>/dev/null || true

    RECORDING_DIR=$(ls -dt "${REPLAYER_PATH}/output"/* 2>/dev/null | head -1)
    if [ -n "${RECORDING_DIR}" ] && [ -d "${RECORDING_DIR}" ]; then
        cp -r "${RECORDING_DIR}"/* "${NODE_DIR}/" 2>/dev/null || true
        rm -rf "${RECORDING_DIR}"
        echo "  Saved to: ${NODE_DIR}"
        ls "${NODE_DIR}/" 2>/dev/null | head -5
    else
        echo "  WARNING: No recording found for ${short_name}"
    fi
done

echo ""
echo "Stopping Autoware for perf phase..."
cleanup_autoware
trap - EXIT
sleep 5

echo ""
echo "=============================================="
echo "PHASE 2: Run Perf on Recorded Nodes"
echo "=============================================="

PERF_CLUSTERS=(
    "core_execution|instructions,cpu-cycles,branches,branch-misses,task-clock,cpu-clock,context-switches,cpu-migrations"
    "cache_l1_data|L1-dcache-loads,L1-dcache-load-misses,cache-references,cache-misses,instructions"
    "cache_l1_instruction|L1-icache-loads,L1-icache-load-misses,instructions"
    "memory_tlb|dTLB-loads,dTLB-load-misses,iTLB-loads,iTLB-load-misses,page-faults,major-faults,minor-faults"
)

mkdir -p "${PERF_OUTPUT}/raw"

PERF_COUNT=0
for short_name in "${ORDERED_NODES[@]}"; do
    PERF_COUNT=$((PERF_COUNT + 1))
    NODE_DIR="${SINGLE_NODE_DIR}/${short_name}"

    RUN_SCRIPT=$(find "${NODE_DIR}" -name "ros2_run_*" -type f 2>/dev/null | head -1)
    ROSBAG_DIR=$(find "${NODE_DIR}" -name "rosbag2_*" -type d 2>/dev/null | head -1)

    if [ -z "${RUN_SCRIPT}" ] || [ -z "${ROSBAG_DIR}" ]; then
        echo "[$PERF_COUNT/$RECORD_TOTAL] SKIP ${short_name}: missing run script or rosbag"
        continue
    fi

    echo ""
    echo "[$PERF_COUNT/$RECORD_TOTAL] Perf profiling: ${short_name}"

    NODE_PERF_DIR="${PERF_OUTPUT}/raw/${short_name}"
    mkdir -p "${NODE_PERF_DIR}"

    for cluster_entry in "${PERF_CLUSTERS[@]}"; do
        IFS='|' read -r cluster_name events <<< "${cluster_entry}"
        echo "  Cluster: ${cluster_name}"

        TMPSCRIPT=$(mktemp)
        cat > "${TMPSCRIPT}" << INNEREOF
#!/bin/bash
source /opt/ros/humble/setup.bash
source \${HOME}/autoware/install/setup.bash
cd "${NODE_DIR}"
bash "$(basename "${RUN_SCRIPT}")" &
NODE_PID=\$!
sleep 3
ros2 bag play "${ROSBAG_DIR}" -s sqlite3
sleep 1
kill \$NODE_PID 2>/dev/null || true
wait \$NODE_PID 2>/dev/null || true
INNEREOF
        chmod +x "${TMPSCRIPT}"

        perf stat -e "${events}" -o "${NODE_PERF_DIR}/${cluster_name}.txt" \
            bash "${TMPSCRIPT}" 2>/dev/null || echo "    WARNING: perf error"

        rm -f "${TMPSCRIPT}"
    done
done

echo ""
echo "=============================================="
echo "All Done!"
echo "=============================================="
echo "Recordings: ${SINGLE_NODE_DIR}"
echo "Perf data:  ${PERF_OUTPUT}/raw/"
