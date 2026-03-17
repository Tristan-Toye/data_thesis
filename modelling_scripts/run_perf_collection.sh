#!/bin/bash
# Perf collection: start Autoware, discover PIDs, run perf during rosbag replay.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PERF_RAW="${SCRIPT_DIR}/3_perf_profiling/perf_data/raw"
MAP_PATH="${HOME}/autoware_map/sample-map-rosbag"
ROSBAG="${HOME}/autoware_map/sample-rosbag"
LOGFILE="/tmp/aw_launch_$$.log"

source /opt/ros/humble/setup.bash
source "${HOME}/autoware/install/setup.bash"

rm -rf "${PERF_RAW}"
mkdir -p "${PERF_RAW}"

cleanup() { echo "Stopping Autoware..."; kill $AW 2>/dev/null; sleep 2; kill -9 $AW 2>/dev/null; }
trap cleanup EXIT

echo "=== Launching Autoware ==="
ros2 launch autoware_launch logging_simulator.launch.xml \
    map_path:="${MAP_PATH}" vehicle_model:=sample_vehicle \
    sensor_model:=sample_sensor_kit rviz:=false >"${LOGFILE}" 2>&1 &
AW=$!
echo "PID $AW — waiting 120 s …"
sleep 120

kill -0 $AW 2>/dev/null || { echo "Autoware died"; tail -30 "${LOGFILE}"; exit 1; }

echo "=== Playing rosbag once to warm up ==="
ros2 bag play "${ROSBAG}" -r 1.0 -s sqlite3 --disable-keyboard-controls </dev/null 2>/dev/null || true
sleep 5

echo "=== Discovering PIDs ==="
declare -A NODE_PID

discover() {
    local label="$1" pattern="$2"
    local pid
    pid=$(pgrep -f "$pattern" | head -1)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        NODE_PID["$label"]=$pid
        echo "  $label -> $pid"
    else
        echo "  $label -> NOT FOUND ($pattern)"
    fi
}

discover ndt_scan_matcher          "autoware_ndt_scan_matcher_node"
discover ekf_localizer             "autoware_ekf_localizer_node"
discover shape_estimation          "shape_estimation_node"
discover multi_object_tracker      "multi_object_tracker_node"
discover map_based_prediction      "map_based_prediction"
discover pointcloud_container      "pointcloud_container"
discover behavior_planning_cont    "behavior_planning_container"
discover motion_planning_cont      "motion_planning_container"
discover control_cont              "__ns:=/control"
discover mission_planner_cont      "mission_planner_container"
discover velocity_smoother_cont    "velocity_smoother_container"

UNIQUE_PIDS=($(printf '%s\n' "${NODE_PID[@]}" | sort -un))
echo ""
echo "Unique PIDs: ${#UNIQUE_PIDS[@]}"
for p in "${UNIQUE_PIDS[@]}"; do echo "  $p"; done

if [ ${#UNIQUE_PIDS[@]} -eq 0 ]; then
    echo "ERROR: no PIDs found"
    exit 1
fi

CLUSTERS=(
    "core_execution|instructions,cpu-cycles,branches,branch-misses,task-clock,cpu-clock,context-switches,cpu-migrations"
    "cache_l1_data|L1-dcache-loads,L1-dcache-load-misses,cache-references,cache-misses,instructions"
    "cache_l1_instruction|L1-icache-loads,L1-icache-load-misses,instructions"
    "memory_tlb|dTLB-loads,dTLB-load-misses,iTLB-loads,iTLB-load-misses,page-faults,major-faults,minor-faults"
)

for ce in "${CLUSTERS[@]}"; do
    IFS='|' read -r cname events <<< "$ce"
    echo ""
    echo "=== Cluster: $cname ==="

    PPERF=()
    for label in "${!NODE_PID[@]}"; do
        pid=${NODE_PID[$label]}
        mkdir -p "${PERF_RAW}/${label}"
        perf stat -e "$events" -p "$pid" -o "${PERF_RAW}/${label}/${cname}.txt" &
        PPERF+=($!)
    done

    sleep 2
    echo "  rosbag playing…"
    ros2 bag play "${ROSBAG}" -r 1.0 -s sqlite3 --disable-keyboard-controls </dev/null 2>/dev/null || true
    sleep 3

    for pp in "${PPERF[@]}"; do kill -INT $pp 2>/dev/null; done
    sleep 2
    for pp in "${PPERF[@]}"; do kill -9 $pp 2>/dev/null; wait $pp 2>/dev/null; done

    for label in "${!NODE_PID[@]}"; do
        f="${PERF_RAW}/${label}/${cname}.txt"
        [ -s "$f" ] && echo "  $label: $(wc -c < "$f") bytes" || echo "  $label: EMPTY"
    done
done

echo ""
echo "=== Mapping shared containers to node names ==="
NODE_CONTAINER_MAP=(
    "lidar_centerpoint:pointcloud_container"
    "occupancy_grid_map_node:pointcloud_container"
    "euclidean_cluster:pointcloud_container"
    "pointcloud_concatenate_data:pointcloud_container"
    "behavior_path_planner:behavior_planning_cont"
    "motion_velocity_planner:motion_planning_cont"
    "autonomous_emergency_braking:control_cont"
    "trajectory_follower_controller:control_cont"
    "mission_planner:mission_planner_cont"
    "velocity_smoother:velocity_smoother_cont"
)

for mapping in "${NODE_CONTAINER_MAP[@]}"; do
    IFS=':' read -r node_short cont_label <<< "$mapping"
    src="${PERF_RAW}/${cont_label}"
    dst="${PERF_RAW}/${node_short}"
    if [ -d "$src" ] && [ "$src" != "$dst" ]; then
        mkdir -p "$dst"
        cp "$src"/*.txt "$dst/" 2>/dev/null && echo "  $node_short <- $cont_label" || true
    fi
done

echo ""
echo "=== Done ==="
echo "Perf data in: ${PERF_RAW}"
ls "${PERF_RAW}"
