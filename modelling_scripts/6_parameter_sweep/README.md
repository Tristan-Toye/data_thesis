# Experiment 6: Parameter Sensitivity Sweep

## Overview

This experiment systematically varies performance-relevant parameters for each of the top 15 Autoware nodes (by callback latency) and measures the impact on callback latency and hardware performance counters (PMU). The goal is to understand which parameters have the greatest influence on node execution time.

## Methodology

### Phase 1: Record Isolated Nodes

Each of the 15 target nodes is recorded in isolation using `ros2_single_node_replayer`:

1. Launch full Autoware stack
2. Discover the target node's actual namespace via `ros2 node list`
3. Use `recorder.py` to capture all input topics into a rosbag and dump current parameters
4. Play the sample rosbag to generate realistic input data
5. Stop recording and move to the next node

**Script**: `record_all_isolated.sh`

### Phase 2: Parameter Sweep

For each node, each performance-relevant parameter is swept through 3 values (low, default, high) while keeping all other parameters at their defaults. For each combination:

1. Modify the parameter YAML file using `modify_param.py`
2. Start an LTTng/CARET tracing session to capture callback events
3. Launch the isolated node with `LD_PRELOAD=libcaret.so`
4. Attach `perf stat` to the node's PID (if `perf_event_paranoid <= 1`)
5. Play the recorded rosbag through the node
6. Extract callback latencies from the LTTng trace using `extract_callback_latency.py`
7. Parse `perf stat` output for PMU counters
8. Append results to `raw_results.csv`

**Script**: `run_parameter_sweep.sh`

**Concurrent runs**: Only one sweep process should run at a time (both append to `raw_results.csv` and use LTTng). The script uses a lock file `experiments/6_parameter_sweep/.sweep.lock` and exits with an error if another instance is already running. If you see more CSV rows than "Done" logs, a second process was likely writing to the same CSV; deduplicate with one row per `(node,parameter,value,run_id)` (keep last).

**Resume / skip existing**: Before each run the script checks if `(node, parameter, value, run_id)` already exists in `raw_results.csv`. If so, that combination is skipped and the summary reports "Skipped (in CSV)". You can safely re-run the script to finish only missing combinations.

**TF_OLD_DATA / “initial position” in logs**: The script uses **simulation time** (`use_sim_time:=true` on the node and `ros2 bag play --clock`) so the node's clock matches the bag, which avoids this warning. If you still see it, it is only a TF2 warning and does not stop the sweep.

**"Node is not activated, provide initial pose"**: The **ekf_localizer** and **ndt_scan_matcher** nodes wait for an initial pose before processing. When run in isolation, the script publishes one `geometry_msgs/msg/PoseWithCovarianceStamped` after the node starts (ekf: `/localization/pose_twist_fusion_filter/initialpose`, ndt: `/localization/pose_estimator/ekf_pose_with_covariance`). Payload is in `initial_pose_ekf.yaml`.

### Phase 3: Analysis & Visualization

Process the raw CSV data to generate summary statistics and visualizations.

**Script**: `analyze_sweep.py`

## Configuration

All sweep parameters are defined in `param_sweep_config.yaml`. Each node lists:
- Package name, executable, and namespace
- Path to the parameter YAML file in the Autoware source
- Parameters to sweep with their YAML path, 3 values, and default

**Adaptability**: Change `repetitions: 1` to `repetitions: N` for multiple runs per parameter set.

## Files

| File | Description |
|------|-------------|
| `param_sweep_config.yaml` | Sweep configuration (nodes, params, values) |
| `record_all_isolated.sh` | Phase 1: record all nodes |
| `run_parameter_sweep.sh` | Phase 2: sweep orchestrator |
| `modify_param.py` | Helper: modify YAML parameter values |
| `extract_callback_latency.py` | Extract latency from LTTng/CARET trace |
| `analyze_sweep.py` | Phase 3: analysis and visualization |

## Outputs

All outputs are in `experiments/6_parameter_sweep/`:

### Tables
- `raw_results.csv` — One row per (node, parameter, value, repetition) with latency stats and PMU counters
- `parameter_sensitivity.csv` — Per-node summary (mean, min, max, std, range, CV across all parameter sets)

### Graphs
- `violin_all_nodes.png` — Violin plot showing latency distribution for all 15 nodes
- `boxplot_all_nodes.png` — Box plot companion with quartiles and outliers
- `sensitivity_ranking.png` — Horizontal bar chart ranking most sensitive (node, parameter) pairs
- `normalized_sensitivity.png` — Percentage change from default for top 20 parameters
- `heatmap_<node>.png` — Per-node heatmap (parameters x values, colored by latency)
- `tornado_<node>.png` — Per-node tornado chart (deviation from default)
- `latency_vs_param_<node>.png` — Per-node line plot (value vs latency per parameter)
- `pmu_correlation.png` — Scatter plots: latency vs PMU metrics (if PMU data available)

## Latency Measurement

Callback latency is measured using CARET (Callback Architecture for ROS 2 Execution Tracing):
- LTTng userspace tracepoints capture `callback_start` and `callback_end` timestamps
- `libcaret.so` is preloaded to instrument the node without source code modification
- Microsecond-resolution timing without modifying node source code

## PMU Counters

When `perf_event_paranoid <= 1`, the following hardware counters are collected:
- **instructions** — Retired instructions
- **cycles** — CPU cycles
- **L1-dcache-load-misses / loads** — L1 data cache miss rate
- **LLC-load-misses / loads** — Last-level cache (L3) miss rate
- **cache-references / misses** — Overall cache miss rate
- **bus-cycles** — Memory bus cycles (proxy for RAM traffic)

The script disables the NMI watchdog once at startup when perf is enabled (`sudo sysctl -w kernel.nmi_watchdog=0`) so PMU events are counted instead of `<not counted>`, and restores it on exit. You need `sudo` for that; ensure passwordless `sudo sysctl` or run the sweep under sudo if prompted.

## Target Nodes

The 15 nodes are the same top-latency nodes from Experiment 1 (CARET tracing):

| Rank | Node | Latency (ms) |
|------|------|-------------|
| 1 | lidar_centerpoint | 45.2 |
| 2 | ndt_scan_matcher | 38.7 |
| 3 | occupancy_grid_map_node | 35.1 |
| 4 | euclidean_cluster | 32.4 |
| 5 | multi_object_tracker | 28.6 |
| 6 | pointcloud_concatenate_data | 25.8 |
| 7 | behavior_path_planner | 22.1 |
| 8 | map_based_prediction | 20.9 |
| 9 | motion_velocity_planner | 18.5 |
| 10 | ekf_localizer | 15.3 |
| 11 | shape_estimation | 14.2 |
| 12 | autonomous_emergency_braking | 12.7 |
| 13 | trajectory_follower_controller | 10.5 |
| 14 | mission_planner | 8.4 |
| 15 | velocity_smoother | 6.3 |
