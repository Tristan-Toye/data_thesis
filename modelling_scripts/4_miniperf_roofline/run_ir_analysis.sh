#!/bin/bash
# =============================================================================
# Experiment 5: LLVM IR Roofline Analysis using miniperf Clang Plugin
# =============================================================================
# Compiles each top-15 Autoware node's C++ to LLVM IR using clang-19 with the
# miniperf Clang plugin. Then a Python script parses the IR to extract per-loop
# operation counts (FLOPs, memory bytes) and compute arithmetic intensity.
# =============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLANG="$HOME/llvm-19/bin/clang++"
PLUGIN="$HOME/miniperf/target/clang_plugin/lib/miniperf_plugin.so"
AUTOWARE_ROOT="$HOME/autoware"
OUTPUT_DIR="${SCRIPT_DIR}/../experiments/5_miniperf_roofline"
IR_DIR="${OUTPUT_DIR}/ir_output"

mkdir -p "${IR_DIR}"

declare -A NODE_PACKAGE=(
    [lidar_centerpoint]="autoware_lidar_centerpoint"
    [ndt_scan_matcher]="autoware_ndt_scan_matcher"
    [occupancy_grid_map_node]="autoware_probabilistic_occupancy_grid_map"
    [euclidean_cluster]="autoware_euclidean_cluster"
    [multi_object_tracker]="autoware_multi_object_tracker"
    [pointcloud_concatenate_data]="autoware_pointcloud_preprocessor"
    [behavior_path_planner]="autoware_behavior_path_planner"
    [map_based_prediction]="autoware_map_based_prediction"
    [motion_velocity_planner]="autoware_motion_velocity_planner_node"
    [ekf_localizer]="autoware_ekf_localizer"
    [shape_estimation]="autoware_shape_estimation"
    [autonomous_emergency_braking]="autoware_autonomous_emergency_braking"
    [trajectory_follower_controller]="autoware_trajectory_follower_node"
    [mission_planner]="autoware_mission_planner_universe"
    [velocity_smoother]="autoware_velocity_smoother"
)

echo "============================================================"
echo "  Experiment 5: LLVM IR Roofline Analysis"
echo "============================================================"

extract_flags() {
    local pkg="$1"
    local build_dir="${AUTOWARE_ROOT}/build/${pkg}"

    if [ ! -d "${build_dir}" ]; then
        echo ""
        return
    fi

    local flags_file
    flags_file=$(find "${build_dir}/CMakeFiles" -name "flags.make" \
        -not -path "*/test*" -not -path "*_tests*" 2>/dev/null | head -1)

    if [ -z "${flags_file}" ] || [ ! -f "${flags_file}" ]; then
        echo ""
        return
    fi

    local includes defines cxxflags
    includes=$(grep "^CXX_INCLUDES" "${flags_file}" | sed 's/^CXX_INCLUDES = //')
    defines=$(grep "^CXX_DEFINES" "${flags_file}" | sed 's/^CXX_DEFINES = //')
    cxxflags=$(grep "^CXX_FLAGS" "${flags_file}" | sed 's/^CXX_FLAGS = //' | sed 's/-Werror//g')

    echo "${defines} ${includes} ${cxxflags}"
}

find_sources() {
    local pkg="$1"
    find "${AUTOWARE_ROOT}/src" -maxdepth 10 \
        -path "*/${pkg}/*" -name "*.cpp" \
        -not -path "*/test/*" -not -name "test_*" \
        -not -path "*/benchmark*" \
        2>/dev/null
}

SUCCESS=0
FAILED=0
LOG="${IR_DIR}/compilation_results.csv"
echo "node,source_file,status,ir_file,loop_messages" > "${LOG}"

for node in "${!NODE_PACKAGE[@]}"; do
    pkg="${NODE_PACKAGE[$node]}"
    echo ""
    echo "===== ${node} (package: ${pkg}) ====="

    FLAGS=$(extract_flags "${pkg}")
    if [ -z "${FLAGS}" ]; then
        echo "  WARNING: No build flags found for ${pkg}, skipping"
        echo "${node},,no_flags,," >> "${LOG}"
        FAILED=$((FAILED + 1))
        continue
    fi

    SOURCES=$(find_sources "${pkg}")
    if [ -z "${SOURCES}" ]; then
        echo "  WARNING: No source files found for ${pkg}"
        echo "${node},,no_sources,," >> "${LOG}"
        FAILED=$((FAILED + 1))
        continue
    fi

    NODE_IR_DIR="${IR_DIR}/${node}"
    mkdir -p "${NODE_IR_DIR}"

    while IFS= read -r src; do
        base=$(basename "${src}" .cpp)
        ir_file="${NODE_IR_DIR}/${base}.ll"
        log_file="${NODE_IR_DIR}/${base}.log"

        echo -n "  $(basename ${src}) ... "

        ${CLANG} -S -emit-llvm -O3 -g -std=c++17 \
            --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/11 \
            -Xclang -fpass-plugin="${PLUGIN}" \
            ${FLAGS} \
            -Wno-everything \
            -o "${ir_file}" \
            "${src}" 2>"${log_file}"

        if [ $? -eq 0 ]; then
            loop_count=$(grep -c "Found a loop\|extractCodeRegion\|Failed to outline" "${log_file}" 2>/dev/null || echo 0)
            echo "OK (${loop_count} loop messages)"
            echo "${node},${base},ok,${ir_file},${loop_count}" >> "${LOG}"
            SUCCESS=$((SUCCESS + 1))
        else
            echo "FAILED"
            echo "${node},${base},failed,${ir_file},0" >> "${LOG}"
            FAILED=$((FAILED + 1))
        fi
    done <<< "${SOURCES}"
done

echo ""
echo "============================================================"
echo "  Compilation Summary"
echo "  Succeeded : ${SUCCESS}"
echo "  Failed    : ${FAILED}"
echo "  IR output : ${IR_DIR}/"
echo "  Log       : ${LOG}"
echo "============================================================"
