#!/bin/bash
# Simple perf collection: profile Autoware process tree during rosbag replay

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PERF_RAW="${SCRIPT_DIR}/3_perf_profiling/perf_data/raw"
MAP="${HOME}/autoware_map/sample-map-rosbag"
BAG="${HOME}/autoware_map/sample-rosbag"

source /opt/ros/humble/setup.bash
source "${HOME}/autoware/install/setup.bash"

rm -rf "${PERF_RAW}"
mkdir -p "${PERF_RAW}"

cleanup() { echo "Cleanup..."; kill $AW 2>/dev/null; sleep 2; kill -9 $AW 2>/dev/null; }
trap cleanup EXIT

echo "=== 1. Launch Autoware ==="
ros2 launch autoware_launch logging_simulator.launch.xml \
    map_path:="${MAP}" vehicle_model:=sample_vehicle \
    sensor_model:=sample_sensor_kit rviz:=false >/dev/null 2>&1 &
AW=$!
echo "Autoware PID=$AW, waiting 120s..."
sleep 120
kill -0 $AW 2>/dev/null || { echo "Autoware died"; exit 1; }
echo "Autoware running"

echo ""
echo "=== 2. Collect child PIDs ==="
CHILD_PIDS=""
for p in $(pgrep -P $AW 2>/dev/null); do
    if kill -0 $p 2>/dev/null; then
        CHILD_PIDS="${CHILD_PIDS:+${CHILD_PIDS},}$p"
    fi
done
echo "Found $(echo $CHILD_PIDS | tr ',' '\n' | wc -l) child processes"

CLUSTERS=(
    "core_execution|instructions,cpu-cycles,branches,branch-misses,task-clock,cpu-clock,context-switches,cpu-migrations"
    "cache_l1_data|L1-dcache-loads,L1-dcache-load-misses,cache-references,cache-misses,instructions"
    "cache_l1_instruction|L1-icache-loads,L1-icache-load-misses,instructions"
    "memory_tlb|dTLB-loads,dTLB-load-misses,iTLB-loads,iTLB-load-misses,page-faults,major-faults,minor-faults"
)

# Identify specific node PIDs for per-node profiling
echo ""
echo "=== 3. Map node PIDs ==="
declare -A NP
for pid in $(echo $CHILD_PIDS | tr ',' ' '); do
    cmd=$(cat /proc/$pid/cmdline 2>/dev/null | tr '\0' ' ')
    case "$cmd" in
        *ndt_scan_matcher*)     NP[ndt_scan_matcher]=$pid ;;
        *ekf_localizer*)        NP[ekf_localizer]=$pid ;;
        *shape_estimation*)     NP[shape_estimation]=$pid ;;
        *multi_object_tracker*) NP[multi_object_tracker]=$pid ;;
        *map_based_prediction*) NP[map_based_prediction]=$pid ;;
        *pointcloud_container*) NP[pointcloud_container]=$pid ;;
        *behavior_planning_container*) NP[behavior_path_planner]=$pid ;;
        *motion_planning_container*)   NP[motion_velocity_planner]=$pid ;;
        *mission_planner_container*)   NP[mission_planner]=$pid ;;
        *velocity_smoother_container*) NP[velocity_smoother]=$pid ;;
    esac
done

# Also try the full tree (grandchildren)
for pid in $(echo $CHILD_PIDS | tr ',' ' '); do
    for gp in $(pgrep -P $pid 2>/dev/null); do
        cmd=$(cat /proc/$gp/cmdline 2>/dev/null | tr '\0' ' ')
        case "$cmd" in
            *ndt_scan_matcher*)     [ -z "${NP[ndt_scan_matcher]}" ] && NP[ndt_scan_matcher]=$gp ;;
            *ekf_localizer*)        [ -z "${NP[ekf_localizer]}" ] && NP[ekf_localizer]=$gp ;;
            *shape_estimation*)     [ -z "${NP[shape_estimation]}" ] && NP[shape_estimation]=$gp ;;
            *multi_object_tracker*) [ -z "${NP[multi_object_tracker]}" ] && NP[multi_object_tracker]=$gp ;;
            *map_based_prediction*) [ -z "${NP[map_based_prediction]}" ] && NP[map_based_prediction]=$gp ;;
            *pointcloud_container*) [ -z "${NP[pointcloud_container]}" ] && NP[pointcloud_container]=$gp ;;
            *behavior_planning_container*) [ -z "${NP[behavior_path_planner]}" ] && NP[behavior_path_planner]=$gp ;;
            *motion_planning_container*)   [ -z "${NP[motion_velocity_planner]}" ] && NP[motion_velocity_planner]=$gp ;;
            *mission_planner_container*)   [ -z "${NP[mission_planner]}" ] && NP[mission_planner]=$gp ;;
            *velocity_smoother_container*) [ -z "${NP[velocity_smoother]}" ] && NP[velocity_smoother]=$gp ;;
            *trajectory_follower*controller*) [ -z "${NP[trajectory_follower_controller]}" ] && NP[trajectory_follower_controller]=$gp ;;
            *autonomous_emergency*) [ -z "${NP[autonomous_emergency_braking]}" ] && NP[autonomous_emergency_braking]=$gp ;;
        esac
    done
done

# Copy container mappings for composable nodes
[ -n "${NP[pointcloud_container]}" ] && {
    NP[lidar_centerpoint]=${NP[pointcloud_container]}
    NP[occupancy_grid_map_node]=${NP[pointcloud_container]}
    NP[euclidean_cluster]=${NP[pointcloud_container]}
    NP[pointcloud_concatenate_data]=${NP[pointcloud_container]}
}

for n in "${!NP[@]}"; do echo "  $n -> PID ${NP[$n]}"; done
echo "Total mapped: ${#NP[@]}"

echo ""
echo "=== 4. Run perf clusters ==="

for ce in "${CLUSTERS[@]}"; do
    IFS='|' read -r cname events <<< "$ce"
    echo ""
    echo "--- $cname ---"

    PPIDS=()
    for node in "${!NP[@]}"; do
        pid=${NP[$node]}
        mkdir -p "${PERF_RAW}/${node}"
        outf="${PERF_RAW}/${node}/${cname}.txt"
        perf stat -e "$events" -p "$pid" -o "$outf" -- sleep 999 2>/dev/null &
        PPIDS+=($!)
    done
    sleep 1

    echo "  Playing rosbag (timeout 60s)..."
    timeout 60 ros2 bag play "${BAG}" -r 1.0 -s sqlite3 --disable-keyboard-controls </dev/null 2>/dev/null
    RET=$?
    [ $RET -eq 124 ] && echo "  (rosbag timed out)" || echo "  (rosbag finished, exit=$RET)"
    sleep 2

    for pp in "${PPIDS[@]}"; do kill -INT $pp 2>/dev/null; done
    sleep 2
    for pp in "${PPIDS[@]}"; do kill -9 $pp 2>/dev/null; wait $pp 2>/dev/null; done

    OK=0; FAIL=0
    for node in "${!NP[@]}"; do
        f="${PERF_RAW}/${node}/${cname}.txt"
        if [ -s "$f" ]; then OK=$((OK+1)); else FAIL=$((FAIL+1)); fi
    done
    echo "  Results: $OK ok, $FAIL empty"
done

echo ""
echo "=== Done ==="
echo "Perf raw data:"
find "${PERF_RAW}" -name "*.txt" -exec echo "  {}" \;
echo ""
echo "Next: cd 3_perf_profiling && python3 clean_perf_data.py"
