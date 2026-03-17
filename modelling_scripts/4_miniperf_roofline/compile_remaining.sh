#!/bin/bash
# Quick targeted recompilation of failed nodes using all available flags.make files
set -uo pipefail

CLANG="$HOME/llvm-19/bin/clang++"
PLUGIN="$HOME/miniperf/target/clang_plugin/lib/miniperf_plugin.so"
AUTOWARE="$HOME/autoware"
IR_DIR="$(dirname "$0")/../experiments/5_miniperf_roofline/ir_output"
LOG="${IR_DIR}/compilation_results.csv"

compile_file() {
    local src="$1" pkg="$2" node="$3"
    local base=$(basename "$src" .cpp)
    local out_dir="${IR_DIR}/${node}"
    local ir_file="${out_dir}/${base}.ll"
    local log_file="${out_dir}/${base}.log"

    [ -s "${ir_file}" ] && return 0  # already compiled

    mkdir -p "${out_dir}"

    # Try each flags.make for this package
    for flags_file in $(find "${AUTOWARE}/build/${pkg}/CMakeFiles" -name "flags.make" -not -path "*/test*" 2>/dev/null); do
        local includes=$(grep "^CXX_INCLUDES" "${flags_file}" | sed 's/^CXX_INCLUDES = //')
        local defines=$(grep "^CXX_DEFINES" "${flags_file}" | sed 's/^CXX_DEFINES = //')

        ${CLANG} -S -emit-llvm -O3 -g -std=c++17 \
            --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/11 \
            -Xclang -fpass-plugin="${PLUGIN}" \
            ${defines} ${includes} \
            -Wno-everything \
            -o "${ir_file}" "${src}" 2>"${log_file}" && {
            echo "  OK: ${node}/${base}.cpp (via $(basename $(dirname $(dirname ${flags_file}))))"
            echo "${node},${base},ok,${ir_file},0" >> "${LOG}"
            return 0
        }
    done

    echo "  STILL FAILED: ${node}/${base}.cpp"
    return 1
}

echo "Recompiling failed nodes..."
SUCCESS=0
FAILED=0

# ekf_localizer
for src in $(find ${AUTOWARE}/src -path "*/autoware_ekf_localizer/src/*.cpp" -not -path "*/test/*" 2>/dev/null); do
    compile_file "$src" "autoware_ekf_localizer" "ekf_localizer" && SUCCESS=$((SUCCESS+1)) || FAILED=$((FAILED+1))
done

# ndt_scan_matcher
for src in $(find ${AUTOWARE}/src -path "*/autoware_ndt_scan_matcher/src/*.cpp" -not -path "*/test/*" 2>/dev/null); do
    compile_file "$src" "autoware_ndt_scan_matcher" "ndt_scan_matcher" && SUCCESS=$((SUCCESS+1)) || FAILED=$((FAILED+1))
done

# map_based_prediction
for src in $(find ${AUTOWARE}/src -path "*/autoware_map_based_prediction/src/*.cpp" -not -path "*/test/*" 2>/dev/null); do
    compile_file "$src" "autoware_map_based_prediction" "map_based_prediction" && SUCCESS=$((SUCCESS+1)) || FAILED=$((FAILED+1))
done

# multi_object_tracker
for src in $(find ${AUTOWARE}/src -path "*/autoware_multi_object_tracker/*.cpp" -not -path "*/test/*" 2>/dev/null); do
    compile_file "$src" "autoware_multi_object_tracker" "multi_object_tracker" && SUCCESS=$((SUCCESS+1)) || FAILED=$((FAILED+1))
done

# autonomous_emergency_braking
for src in $(find ${AUTOWARE}/src -path "*/autoware_autonomous_emergency_braking/src/*.cpp" -not -path "*/test/*" 2>/dev/null); do
    compile_file "$src" "autoware_autonomous_emergency_braking" "autonomous_emergency_braking" && SUCCESS=$((SUCCESS+1)) || FAILED=$((FAILED+1))
done

# velocity_smoother
for src in $(find ${AUTOWARE}/src -path "*/autoware_velocity_smoother/src/*.cpp" -not -path "*/test/*" 2>/dev/null); do
    compile_file "$src" "autoware_velocity_smoother" "velocity_smoother" && SUCCESS=$((SUCCESS+1)) || FAILED=$((FAILED+1))
done

# behavior_path_planner (the core node, not modules)
for src in $(find ${AUTOWARE}/src -path "*/autoware_behavior_path_planner/src/*.cpp" -not -path "*/test/*" 2>/dev/null); do
    compile_file "$src" "autoware_behavior_path_planner" "behavior_path_planner" && SUCCESS=$((SUCCESS+1)) || FAILED=$((FAILED+1))
done

echo ""
echo "Recompilation: ${SUCCESS} succeeded, ${FAILED} still failed"
