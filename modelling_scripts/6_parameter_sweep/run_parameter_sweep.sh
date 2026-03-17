#!/bin/bash
# =============================================================================
# Parameter Sweep Orchestrator
# =============================================================================
# For each (node, parameter, value) combination:
#   1. Copy baseline .param.yaml
#   2. Modify the target parameter
#   3. Launch isolated node with CARET LD_PRELOAD
#   4. Attach perf stat to the node process
#   5. Start LTTng tracing
#   6. Play recorded rosbag
#   7. Stop tracing, kill node, parse results
#   8. Append row to raw_results.csv
#
# Usage: ./run_parameter_sweep.sh [--dry-run] [--node NODE_NAME]
# =============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/param_sweep_config.yaml"
REPLAYER_OUTPUT="${HOME}/ros2_single_node_replayer/output"
OUTPUT_BASE="${HOME}/scripts/experiments/6_parameter_sweep"
TRACE_DIR="${OUTPUT_BASE}/sweep_traces"
PERF_DIR="${OUTPUT_BASE}/perf_data"
RAW_CSV="${OUTPUT_BASE}/tables/raw_results.csv"
LOCK_FILE="${OUTPUT_BASE}/.sweep.lock"
PROGRESS_LOG="${OUTPUT_BASE}/sweep_progress.log"

MODIFY_SCRIPT="${SCRIPT_DIR}/modify_param.py"
LATENCY_SCRIPT="${SCRIPT_DIR}/extract_callback_latency.py"
INITIAL_POSE_SCRIPT="${SCRIPT_DIR}/publish_initial_pose.py"

RUN_TIMEOUT=120
NODE_STARTUP_WAIT=5
POST_ROSBAG_WAIT=3
DRY_RUN=false
FILTER_NODE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN=true; shift ;;
        --node) FILTER_NODE="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

source /opt/ros/humble/setup.bash
source "${HOME}/autoware/install/setup.bash"
if [ -f "${HOME}/ros2_caret_ws/install/local_setup.bash" ]; then
    source "${HOME}/ros2_caret_ws/install/local_setup.bash"
fi

CARET_LIB=$(find "${HOME}/ros2_caret_ws" -name "libcaret.so" -path "*/install/*" 2>/dev/null | head -1)
if [ -z "$CARET_LIB" ]; then
    CARET_LIB=$(find "${HOME}/ros2_caret_ws" -name "libcaret.so" 2>/dev/null | head -1)
fi
if [ -z "$CARET_LIB" ]; then
    echo "WARNING: libcaret.so not found. CARET tracing will be disabled."
fi

PERF_AVAILABLE=false
if command -v perf &>/dev/null; then
    PARANOID=$(cat /proc/sys/kernel/perf_event_paranoid 2>/dev/null || echo "4")
    if [ "$PARANOID" -le 1 ]; then
        PERF_AVAILABLE=true
        echo "perf stat: ENABLED (paranoid=$PARANOID)"
    else
        echo "perf stat: DISABLED (paranoid=$PARANOID, need <= 1)"
        echo "  Run: sudo sysctl kernel.perf_event_paranoid=-1"
    fi
fi

mkdir -p "${TRACE_DIR}" "${PERF_DIR}" "$(dirname "${RAW_CSV}")"

# Run sudo; use SUDO_PASSWORD (e.g. from restart_sweep.sh) when running in background so sysctl works
run_sudo() {
    if [ -n "${SUDO_PASSWORD:-}" ]; then
        echo "$SUDO_PASSWORD" | sudo -S "$@" 2>/dev/null
    else
        sudo "$@"
    fi
}

# Prevent concurrent runs: only one sweep process may write to RAW_CSV at a time.
if [ -f "${LOCK_FILE}" ]; then
    LOCK_PID=$(cat "${LOCK_FILE}" 2>/dev/null)
    if [ -n "$LOCK_PID" ] && kill -0 "$LOCK_PID" 2>/dev/null; then
        echo "ERROR: Another parameter sweep is already running (PID $LOCK_PID). Exiting."
        echo "  If that process is dead, remove: ${LOCK_FILE}"
        exit 1
    fi
    rm -f "${LOCK_FILE}"
fi
echo $$ > "${LOCK_FILE}"
# Restore NMI watchdog on exit if we disabled it for perf (avoids "<not counted>" events)
trap 'rm -f "${LOCK_FILE}"; [ -n "${NMI_WATCHDOG_DISABLED:-}" ] && run_sudo sysctl -w kernel.nmi_watchdog=1 >/dev/null 2>&1 || true' EXIT

# Disable NMI watchdog once for entire sweep so perf stat can count events (otherwise "<not counted>")
if $PERF_AVAILABLE; then
    if run_sudo sysctl -w kernel.nmi_watchdog=0 >/dev/null 2>&1; then
        NMI_WATCHDOG_DISABLED=1
        echo "NMI watchdog disabled for perf counting (will restore on exit)"
    fi
fi

: > "${PROGRESS_LOG}"

if [ ! -f "${RAW_CSV}" ]; then
    echo "node,parameter,value,run_id,callback_count,latency_mean_us,latency_min_us,latency_max_us,latency_std_us,latency_p50_us,latency_p95_us,latency_p99_us,instructions,cycles,ipc,l1_dcache_load_misses,l1_dcache_loads,l1_miss_rate,llc_load_misses,llc_loads,llc_miss_rate,cache_references,cache_misses,cache_miss_rate,bus_cycles" > "${RAW_CSV}"
fi

parse_config_nodes() {
    python3 -c "
import yaml, sys
with open('${CONFIG_FILE}') as f:
    cfg = yaml.safe_load(f)
for name in cfg.get('nodes', {}):
    print(name)
"
}

get_node_field() {
    local node_name="$1"
    local field="$2"
    python3 -c "
import yaml
with open('${CONFIG_FILE}') as f:
    cfg = yaml.safe_load(f)
node = cfg['nodes']['${node_name}']
print(node.get('${field}', ''))
"
}

get_node_params() {
    local node_name="$1"
    python3 -c "
import yaml
with open('${CONFIG_FILE}') as f:
    cfg = yaml.safe_load(f)
params = cfg['nodes']['${node_name}'].get('parameters', {})
for pname, pdata in params.items():
    yaml_path = pdata['yaml_path']
    values = ','.join(str(v) for v in pdata['values'])
    default = pdata['default']
    print(f'{pname}|{yaml_path}|{values}|{default}')
"
}

find_recording_dir() {
    local short_name="$1"
    local alt_names=""
    case "$short_name" in
        pointcloud_concatenate_data) alt_names="concatenate_data" ;;
        trajectory_follower_controller) alt_names="controller_node_exe" ;;
    esac
    for search_name in "$short_name" $alt_names; do
        for dir in "${REPLAYER_OUTPUT}"/*/; do
            [ -d "$dir" ] || continue
            local dirname
            dirname=$(basename "$dir")
            if echo "$dirname" | grep -q "${search_name}$"; then
                if ls "$dir"/rosbag2_* &>/dev/null; then
                    echo "$dir"
                    return 0
                fi
            fi
        done
    done
    return 1
}

find_param_file_in_recording() {
    local rec_dir="$1"
    ls "${rec_dir}"/*.yaml 2>/dev/null | head -1
}

find_rosbag_in_recording() {
    local rec_dir="$1"
    ls -d "${rec_dir}"/rosbag2_* 2>/dev/null | head -1
}

find_run_command() {
    local rec_dir="$1"
    ls "${rec_dir}"/ros2_run_* 2>/dev/null | head -1
}

# Check if (node, parameter, value, run_id) already has a row in raw_results.csv
csv_has_run() {
    local n="$1" p="$2" v="$3" r="$4"
    [ ! -f "${RAW_CSV}" ] && return 1
    awk -F',' -v n="$n" -v p="$p" -v v="$v" -v r="$r" \
        'NR>1 && $1==n && $2==p && $3==v && $4==r { found=1; exit } END { exit !found }' \
        "${RAW_CSV}" 2>/dev/null
}

parse_perf_stat() {
    local perf_file="$1"
    python3 -c "
import re, sys

metrics = {
    'instructions': '0', 'cycles': '0', 'L1-dcache-load-misses': '0',
    'L1-dcache-loads': '0', 'LLC-load-misses': '0', 'LLC-loads': '0',
    'cache-references': '0', 'cache-misses': '0', 'bus-cycles': '0',
}

def norm(s):
    return s.replace(',', '').replace('.', '')

try:
    with open('${perf_file}') as f:
        for line in f:
            line = line.strip()
            for metric in metrics:
                if metric in line:
                    if '<not counted>' in line:
                        break
                    # Match numeric value: locale may use comma or dot as thousands sep (e.g. 6.889.766.091)
                    m = re.match(r'^\s*([\d,.]+)\s+' + re.escape(metric), line)
                    if m:
                        metrics[metric] = norm(m.group(1))
                        break
except FileNotFoundError:
    pass

instr = int(metrics['instructions']) if metrics['instructions'] else 0
cyc = int(metrics['cycles']) if metrics['cycles'] else 0
ipc = f'{instr/cyc:.3f}' if cyc > 0 else '0'

l1_misses = int(metrics['L1-dcache-load-misses']) if metrics['L1-dcache-load-misses'] else 0
l1_loads = int(metrics['L1-dcache-loads']) if metrics['L1-dcache-loads'] else 0
l1_rate = f'{l1_misses/l1_loads:.6f}' if l1_loads > 0 else '0'

llc_misses = int(metrics['LLC-load-misses']) if metrics['LLC-load-misses'] else 0
llc_loads = int(metrics['LLC-loads']) if metrics['LLC-loads'] else 0
llc_rate = f'{llc_misses/llc_loads:.6f}' if llc_loads > 0 else '0'

c_refs = int(metrics['cache-references']) if metrics['cache-references'] else 0
c_misses = int(metrics['cache-misses']) if metrics['cache-misses'] else 0
c_rate = f'{c_misses/c_refs:.6f}' if c_refs > 0 else '0'

bus = metrics['bus-cycles']

print(f'{instr},{cyc},{ipc},{l1_misses},{l1_loads},{l1_rate},{llc_misses},{llc_loads},{llc_rate},{c_refs},{c_misses},{c_rate},{bus}')
"
}

run_single_sweep() {
    local node_name="$1"
    local package="$2"
    local executable="$3"
    local param_name="$4"
    local yaml_path="$5"
    local value="$6"
    local run_id="$7"
    local base_param_file="$8"
    local rosbag_dir="$9"
    local run_command_file="${10}"
    local warmup="${11:-0}"

    local sweep_id="${node_name}_${param_name}_${value}_r${run_id}"
    if [ "$warmup" = "1" ]; then
        echo "    Warmup: ${sweep_id}"
        echo "    Warmup: ${sweep_id}" >> "${PROGRESS_LOG}"
    else
        echo "    Running: ${sweep_id}"
        echo "    Running: ${sweep_id}" >> "${PROGRESS_LOG}"
    fi

    local modified_yaml="/tmp/sweep_${sweep_id}.yaml"
    python3 "${MODIFY_SCRIPT}" "${base_param_file}" "${modified_yaml}" "${yaml_path}" "${value}"
    if [ $? -ne 0 ]; then
        echo "    ERROR: Failed to modify parameter"
        return 1
    fi

    local trace_session="sweep_${sweep_id}"
    local trace_output="${TRACE_DIR}/${sweep_id}"
    mkdir -p "${trace_output}"

    if [ -n "$CARET_LIB" ]; then
        lttng create "${trace_session}" --output="${trace_output}/lttng" 2>/dev/null || true
        lttng enable-event -u 'ros2:*' -s "${trace_session}" 2>/dev/null || true
        lttng enable-event -u 'ros2_caret:*' -s "${trace_session}" 2>/dev/null || true
        lttng start "${trace_session}" 2>/dev/null || true
    fi

    local node_env=""
    if [ -n "$CARET_LIB" ]; then
        node_env="LD_PRELOAD=${CARET_LIB}"
    fi

    local run_cmd
    if [ -f "$run_command_file" ]; then
        run_cmd=$(cat "$run_command_file")
        run_cmd=$(echo "$run_cmd" | sed "s|--params-file [^ ]*|--params-file ${modified_yaml}|")
    else
        run_cmd="ros2 run ${package} ${executable} --ros-args --params-file ${modified_yaml}"
    fi
    # mission_planner crashes with UninitializedStaticallyTypedParameterException for
    # 'arrival_check_distance' if it is not explicitly set. The recorded params do
    # not include it, so we pass a reasonable default here.
    if [ "${node_name}" = "mission_planner" ]; then
        run_cmd="${run_cmd} -p arrival_check_distance:=5.0"
    fi
    # motion_velocity_planner crashes with UninitializedStaticallyTypedParameterException for
    # several statically-typed vehicle parameters when launched with the isolated params;
    # set them explicitly from the vehicle config used elsewhere in Autoware.
    if [ "${node_name}" = "motion_velocity_planner" ]; then
        run_cmd="${run_cmd} -p wheel_radius:=0.383 -p wheel_width:=0.235 -p wheel_base:=2.79 -p wheel_tread:=1.64"
    fi
    # Use sim time so TF from the bag is not "in the past" (avoids TF_OLD_DATA warnings)
    run_cmd="${run_cmd} --ros-args -p use_sim_time:=true"

    # Start bag first so /clock is published before the node starts
    ros2 bag play "${rosbag_dir}" --clock --disable-keyboard-controls </dev/null 2>/dev/null &
    local BAG_PID=$!

    local POSE_PID=""
    if [ -f "${INITIAL_POSE_SCRIPT}" ]; then
        sleep 8
        python3 "${INITIAL_POSE_SCRIPT}" --use-sim-time 25 &
        POSE_PID=$!
        sleep 5
        echo "    Published initial pose (sim time, repeating in background)"
    fi

    local perf_file="${PERF_DIR}/${sweep_id}.txt"
    # Run node under perf (not perf -p PID) so PMU events are counted; use process group for clean kill
    local RUN_PID=""
    local USE_PGID=""
    if $PERF_AVAILABLE; then
        set -m
        if [ -n "$node_env" ]; then
            env $node_env perf stat -e instructions,cycles,L1-dcache-load-misses,L1-dcache-loads,LLC-load-misses,LLC-loads,cache-references,cache-misses,bus-cycles \
                -o "${perf_file}" -- bash -c "${run_cmd}" &
        else
            perf stat -e instructions,cycles,L1-dcache-load-misses,L1-dcache-loads,LLC-load-misses,LLC-loads,cache-references,cache-misses,bus-cycles \
                -o "${perf_file}" -- bash -c "${run_cmd}" &
        fi
        RUN_PID=$!
        USE_PGID=1
        set +m
    else
        if [ -n "$node_env" ]; then
            env $node_env bash -c "${run_cmd}" &
        else
            bash -c "${run_cmd}" &
        fi
        RUN_PID=$!
    fi

    sleep "${NODE_STARTUP_WAIT}"

    if ! kill -0 "$RUN_PID" 2>/dev/null; then
        echo "    ERROR: Node failed to start"
        lttng stop "${trace_session}" 2>/dev/null || true
        lttng destroy "${trace_session}" 2>/dev/null || true
        wait "$BAG_PID" 2>/dev/null || true
        [ -n "${POSE_PID:-}" ] && kill "$POSE_PID" 2>/dev/null || true
        return 1
    fi

    wait "$BAG_PID" 2>/dev/null || true
    sleep "${POST_ROSBAG_WAIT}"

    # Stop node (and perf if running). With perf we used set -m so RUN_PID is process group leader.
    if [ -n "${USE_PGID:-}" ]; then
        kill -INT "-${RUN_PID}" 2>/dev/null || true
        sleep 2
        kill -9 "-${RUN_PID}" 2>/dev/null || true
    else
        kill -INT "$RUN_PID" 2>/dev/null || true
        sleep 2
        pkill -9 -P "$RUN_PID" 2>/dev/null || true
        kill -9 "$RUN_PID" 2>/dev/null || true
    fi
    wait "$RUN_PID" 2>/dev/null || true
    [ -n "${POSE_PID:-}" ] && kill "$POSE_PID" 2>/dev/null || true
    wait "${POSE_PID:-}" 2>/dev/null || true

    if [ -n "$CARET_LIB" ]; then
        lttng stop "${trace_session}" 2>/dev/null || true
        lttng destroy "${trace_session}" 2>/dev/null || true
    fi

    local latency_json="/tmp/latency_${sweep_id}.json"
    local latency_csv_row="0,0,0,0,0,0,0,0"

    if [ -d "${trace_output}/lttng" ]; then
        python3 "${LATENCY_SCRIPT}" "${trace_output}/lttng" \
            --node-name "${node_name}" \
            --output "${latency_json}" 2>/dev/null || true

        if [ -f "${latency_json}" ]; then
            latency_csv_row=$(python3 -c "
import json
with open('${latency_json}') as f:
    data = json.load(f)
if data:
    stats = list(data.values())[0]
    print(f\"{stats['count']},{stats['mean_us']:.2f},{stats['min_us']:.2f},{stats['max_us']:.2f},{stats['std_us']:.2f},{stats['p50_us']:.2f},{stats['p95_us']:.2f},{stats['p99_us']:.2f}\")
else:
    print('0,0,0,0,0,0,0,0')
" 2>/dev/null || echo "0,0,0,0,0,0,0,0")
        fi
    fi

    local perf_csv_row="0,0,0,0,0,0,0,0,0,0,0,0,0"
    if $PERF_AVAILABLE && [ -f "${perf_file}" ]; then
        perf_csv_row=$(parse_perf_stat "${perf_file}" 2>/dev/null || echo "0,0,0,0,0,0,0,0,0,0,0,0,0")
    fi

    if [ "$warmup" != "1" ]; then
        echo "${node_name},${param_name},${value},${run_id},${latency_csv_row},${perf_csv_row}" >> "${RAW_CSV}"
    fi

    rm -f "${modified_yaml}" "${latency_json}"

    if [ "$warmup" = "1" ]; then
        echo "    Warmup done: ${sweep_id}"
        echo "    Warmup done: ${sweep_id}" >> "${PROGRESS_LOG}"
    else
        echo "    Done: ${sweep_id}"
        echo "    Done: ${sweep_id}" >> "${PROGRESS_LOG}"
    fi
}

echo "=============================================="
echo "  Parameter Sweep"
echo "=============================================="
echo "  Config:  ${CONFIG_FILE}"
echo "  Output:  ${OUTPUT_BASE}"
echo "  Dry run: ${DRY_RUN}"
echo "  perf:    ${PERF_AVAILABLE}"
echo "  CARET:   ${CARET_LIB:-DISABLED}"
echo "=============================================="
echo ""

REPETITIONS=$(python3 -c "
import yaml
with open('${CONFIG_FILE}') as f:
    cfg = yaml.safe_load(f)
print(cfg.get('repetitions', 1))
")

TOTAL_RUNS=0
COMPLETED_RUNS=0
FAILED_RUNS=0
SKIPPED_RUNS=0

ALL_NODES=$(parse_config_nodes)
for NODE in $ALL_NODES; do
    if [ -n "$FILTER_NODE" ] && [ "$NODE" != "$FILTER_NODE" ]; then
        continue
    fi

    PACKAGE=$(get_node_field "$NODE" "package")
    EXECUTABLE=$(get_node_field "$NODE" "executable")

    echo ""
    echo "=== Node: ${NODE} (${PACKAGE}/${EXECUTABLE}) ==="

    REC_DIR=$(find_recording_dir "$NODE" || echo "")
    if [ -z "$REC_DIR" ]; then
        echo "  SKIP: No recording found for ${NODE}"
        continue
    fi
    echo "  Recording: ${REC_DIR}"

    PARAM_FILE=$(find_param_file_in_recording "$REC_DIR")
    ROSBAG=$(find_rosbag_in_recording "$REC_DIR")
    RUN_CMD_FILE=$(find_run_command "$REC_DIR")

    if [ -z "$PARAM_FILE" ]; then
        echo "  SKIP: No parameter file found"
        continue
    fi
    if [ -z "$ROSBAG" ]; then
        echo "  SKIP: No rosbag found"
        continue
    fi

    echo "  Params:  ${PARAM_FILE}"
    echo "  Rosbag:  ${ROSBAG}"
    echo "  Run cmd: ${RUN_CMD_FILE:-none}"

    PARAMS=$(get_node_params "$NODE")
    FIRST_RUN_FOR_NODE=1
    while IFS='|' read -r PNAME YPATH VALUES DEFAULT; do
        [ -z "$PNAME" ] && continue

        echo ""
        echo "  Parameter: ${PNAME} (default=${DEFAULT})"
        echo "    Values: ${VALUES}"

        IFS=',' read -ra VALUE_ARR <<< "$VALUES"
        for VAL in "${VALUE_ARR[@]}"; do
            VAL=$(echo "$VAL" | xargs)

            for REP in $(seq 1 "$REPETITIONS"); do
                TOTAL_RUNS=$((TOTAL_RUNS + 1))

                if $DRY_RUN; then
                    echo "    [DRY RUN] ${NODE}/${PNAME}=${VAL} rep=${REP}"
                    continue
                fi

                if csv_has_run "$NODE" "$PNAME" "$VAL" "$REP"; then
                    echo "    SKIP: already in CSV (${NODE}/${PNAME}=${VAL} rep=${REP})"
                    SKIPPED_RUNS=$((SKIPPED_RUNS + 1))
                    continue
                fi

                if [ "$FIRST_RUN_FOR_NODE" = "1" ]; then
                    run_single_sweep "$NODE" "$PACKAGE" "$EXECUTABLE" \
                        "$PNAME" "$YPATH" "$VAL" "$REP" \
                        "$PARAM_FILE" "$ROSBAG" "${RUN_CMD_FILE:-/dev/null}" "1" || true
                    run_single_sweep "$NODE" "$PACKAGE" "$EXECUTABLE" \
                        "$PNAME" "$YPATH" "$VAL" "$REP" \
                        "$PARAM_FILE" "$ROSBAG" "${RUN_CMD_FILE:-/dev/null}" "0"
                    if [ $? -eq 0 ]; then COMPLETED_RUNS=$((COMPLETED_RUNS + 1)); else FAILED_RUNS=$((FAILED_RUNS + 1)); fi
                    FIRST_RUN_FOR_NODE=0
                else
                    if run_single_sweep "$NODE" "$PACKAGE" "$EXECUTABLE" \
                        "$PNAME" "$YPATH" "$VAL" "$REP" \
                        "$PARAM_FILE" "$ROSBAG" "${RUN_CMD_FILE:-/dev/null}"; then
                        COMPLETED_RUNS=$((COMPLETED_RUNS + 1))
                    else
                        FAILED_RUNS=$((FAILED_RUNS + 1))
                    fi
                fi
            done
        done
    done <<< "$PARAMS"
done

echo ""
echo "=============================================="
echo "  Sweep Summary"
echo "=============================================="
echo "  Total planned:  ${TOTAL_RUNS}"
echo "  Skipped (in CSV): ${SKIPPED_RUNS}"
echo "  Completed:      ${COMPLETED_RUNS}"
echo "  Failed:         ${FAILED_RUNS}"
echo "  Results:        ${RAW_CSV}"
echo "=============================================="
