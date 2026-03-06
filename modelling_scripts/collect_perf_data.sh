#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PERF_OUTPUT="${SCRIPT_DIR}/3_perf_profiling/perf_data"
MAP_PATH="${HOME}/autoware_map/sample-map-rosbag"
ROSBAG_PATH="${HOME}/autoware_map/sample-rosbag"
AW_LOG="/tmp/autoware_launch.log"

source /opt/ros/humble/setup.bash
source "${HOME}/autoware/install/setup.bash"

declare -A SHORT_TO_LAUNCH_NAME
SHORT_TO_LAUNCH_NAME[lidar_centerpoint]="component_container_mt-1"
SHORT_TO_LAUNCH_NAME[ndt_scan_matcher]="autoware_ndt_scan_matcher_node"
SHORT_TO_LAUNCH_NAME[occupancy_grid_map_node]="component_container_mt-1"
SHORT_TO_LAUNCH_NAME[euclidean_cluster]="component_container_mt-1"
SHORT_TO_LAUNCH_NAME[multi_object_tracker]="multi_object_tracker_node"
SHORT_TO_LAUNCH_NAME[pointcloud_concatenate_data]="component_container_mt-1"
SHORT_TO_LAUNCH_NAME[behavior_path_planner]="component_container_mt-61"
SHORT_TO_LAUNCH_NAME[map_based_prediction]="map_based_prediction_node"
SHORT_TO_LAUNCH_NAME[motion_velocity_planner]="component_container_mt-62"
SHORT_TO_LAUNCH_NAME[ekf_localizer]="autoware_ekf_localizer_node"
SHORT_TO_LAUNCH_NAME[shape_estimation]="shape_estimation_node"
SHORT_TO_LAUNCH_NAME[autonomous_emergency_braking]="component_container_mt-69"
SHORT_TO_LAUNCH_NAME[trajectory_follower_controller]="component_container_mt-69"
SHORT_TO_LAUNCH_NAME[mission_planner]="component_container_mt-55"
SHORT_TO_LAUNCH_NAME[velocity_smoother]="component_container-59"

ORDERED_NODES=(
    lidar_centerpoint ndt_scan_matcher occupancy_grid_map_node euclidean_cluster
    multi_object_tracker pointcloud_concatenate_data behavior_path_planner
    map_based_prediction motion_velocity_planner ekf_localizer shape_estimation
    autonomous_emergency_braking trajectory_follower_controller mission_planner
    velocity_smoother
)

PERF_CLUSTERS=(
    "core_execution|instructions,cpu-cycles,branches,branch-misses,task-clock,cpu-clock,context-switches,cpu-migrations"
    "cache_l1_data|L1-dcache-loads,L1-dcache-load-misses,cache-references,cache-misses,instructions"
    "cache_l1_instruction|L1-icache-loads,L1-icache-load-misses,instructions"
    "memory_tlb|dTLB-loads,dTLB-load-misses,iTLB-loads,iTLB-load-misses,page-faults,major-faults,minor-faults"
)

cleanup() {
    echo "Cleaning up..."
    if [ -n "${AW_PID}" ]; then
        kill ${AW_PID} 2>/dev/null || true
        sleep 2
        kill -9 ${AW_PID} 2>/dev/null || true
    fi
}

echo "=============================================="
echo "Perf Data Collection"
echo "=============================================="

mkdir -p "${PERF_OUTPUT}/raw"

echo "Launching Autoware (headless)..."
ros2 launch autoware_launch logging_simulator.launch.xml \
    map_path:="${MAP_PATH}" \
    vehicle_model:=sample_vehicle \
    sensor_model:=sample_sensor_kit \
    rviz:=false > "${AW_LOG}" 2>&1 &
AW_PID=$!
trap cleanup EXIT

echo "Autoware PID: ${AW_PID}"
echo "Waiting 120s for all nodes to fully initialize..."
sleep 120

if ! kill -0 ${AW_PID} 2>/dev/null; then
    echo "ERROR: Autoware died during startup"
    tail -50 "${AW_LOG}"
    exit 1
fi

echo ""
echo "Autoware running. Node count:"
ros2 node list 2>/dev/null | wc -l
echo ""

echo "Building PID map from launch output..."
echo ""
declare -A NODE_PID_MAP
declare -A PID_NODES

for node in "${ORDERED_NODES[@]}"; do
    LAUNCH_NAME="${SHORT_TO_LAUNCH_NAME[${node}]}"
    if [ -z "${LAUNCH_NAME}" ]; then
        echo "  ${node}: no launch name mapping"
        continue
    fi

    PID=$(grep "${LAUNCH_NAME}" "${AW_LOG}" | grep "process started with pid" | head -1 | grep -oP '\[\K[0-9]+(?=\])' | tail -1)

    if [ -z "${PID}" ]; then
        PID=$(pgrep -f "${LAUNCH_NAME}" --newest 2>/dev/null || true)
    fi

    if [ -n "${PID}" ] && kill -0 "${PID}" 2>/dev/null; then
        NODE_PID_MAP["${node}"]="${PID}"
        PID_NODES["${PID}"]="${PID_NODES[${PID}]:+${PID_NODES[${PID}]},}${node}"
        echo "  ${node} -> PID ${PID} (via ${LAUNCH_NAME})"
    else
        echo "  WARNING: ${node} PID not found (${LAUNCH_NAME})"
    fi
done

echo ""
echo "Unique PIDs:"
UNIQUE_PIDS=($(printf '%s\n' "${!PID_NODES[@]}" | sort -un))
for pid in "${UNIQUE_PIDS[@]}"; do
    echo "  PID ${pid}: ${PID_NODES[${pid}]}"
done
echo "Total: ${#UNIQUE_PIDS[@]}"
echo ""

if [ ${#UNIQUE_PIDS[@]} -eq 0 ]; then
    echo "ERROR: No PIDs found. Dumping launch log tail..."
    tail -100 "${AW_LOG}"
    exit 1
fi

echo "=============================================="
echo "Running Perf Clusters"
echo "=============================================="

CLUSTER_NUM=0
TOTAL_CLUSTERS=${#PERF_CLUSTERS[@]}

for cluster_entry in "${PERF_CLUSTERS[@]}"; do
    IFS='|' read -r cluster_name events <<< "${cluster_entry}"
    CLUSTER_NUM=$((CLUSTER_NUM + 1))

    echo ""
    echo "--- Cluster ${CLUSTER_NUM}/${TOTAL_CLUSTERS}: ${cluster_name} ---"
    echo ""

    PERF_PIDS=()
    for pid in "${UNIQUE_PIDS[@]}"; do
        FIRST_NODE=$(echo "${PID_NODES[${pid}]}" | cut -d',' -f1)
        NODE_DIR="${PERF_OUTPUT}/raw/${FIRST_NODE}"
        mkdir -p "${NODE_DIR}"
        OUTPUT_FILE="${NODE_DIR}/${cluster_name}.txt"

        perf stat -e "${events}" -p "${pid}" -o "${OUTPUT_FILE}" &
        PERF_PIDS+=($!)
    done

    sleep 2
    echo "  Playing rosbag..."
    ros2 bag play "${ROSBAG_PATH}" -r 1.0 -s sqlite3 2>/dev/null || true

    echo "  Rosbag done. Stopping perf collectors..."
    sleep 3

    for ppid in "${PERF_PIDS[@]}"; do
        kill -SIGINT ${ppid} 2>/dev/null || true
    done
    sleep 2
    for ppid in "${PERF_PIDS[@]}"; do
        kill -9 ${ppid} 2>/dev/null || true
        wait ${ppid} 2>/dev/null || true
    done

    for pid in "${UNIQUE_PIDS[@]}"; do
        FIRST_NODE=$(echo "${PID_NODES[${pid}]}" | cut -d',' -f1)
        FILE="${PERF_OUTPUT}/raw/${FIRST_NODE}/${cluster_name}.txt"
        if [ -f "${FILE}" ] && [ -s "${FILE}" ]; then
            SIZE=$(stat -c%s "${FILE}" 2>/dev/null || echo "?")
            echo "  PID ${pid} (${PID_NODES[${pid}]}): ${SIZE} bytes"
        else
            echo "  PID ${pid} (${PID_NODES[${pid}]}): NO DATA"
        fi
    done
done

echo ""
echo "=============================================="
echo "Copying data for shared-container nodes..."
echo "=============================================="

for node in "${ORDERED_NODES[@]}"; do
    PID="${NODE_PID_MAP[${node}]}"
    if [ -z "${PID}" ]; then continue; fi

    FIRST_NODE=$(echo "${PID_NODES[${PID}]}" | cut -d',' -f1)

    if [ "${node}" != "${FIRST_NODE}" ]; then
        SRC="${PERF_OUTPUT}/raw/${FIRST_NODE}"
        DST="${PERF_OUTPUT}/raw/${node}"
        if [ -d "${SRC}" ]; then
            mkdir -p "${DST}"
            cp "${SRC}"/*.txt "${DST}/" 2>/dev/null || true
            echo "  ${node} -> copied from ${FIRST_NODE} (shared PID ${PID})"
        fi
    fi
done

echo ""
echo "=============================================="
echo "Perf data collection complete!"
echo "=============================================="
echo "Raw data:"
ls "${PERF_OUTPUT}/raw/" 2>/dev/null
echo ""
echo "Next: cd 3_perf_profiling && python3 clean_perf_data.py"
