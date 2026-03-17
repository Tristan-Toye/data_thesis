# Experiment 5: Cross-Methodology Comparison -- Overview

This experiment synthesises results from three complementary performance analysis methods applied to 15 Autoware ROS 2 nodes.

## Key Findings

1. **Top-priority targets** (high CARET latency + memory-bound in both perf and miniperf):
   - `lidar_centerpoint` (rank 1, AI = 0.99 FLOPs/byte)
   - `ndt_scan_matcher` (rank 2, AI = 1.44 FLOPs/byte)
   - `occupancy_grid_map_node` (rank 3, AI = 0.84 FLOPs/byte)
   - `pointcloud_concatenate_data` (rank 6, AI = 1.72 FLOPs/byte)

2. **Method agreement**: perf and miniperf agree on bottleneck classification for 8/15 nodes (53.3%). The divergence is expected given their fundamentally different measurement approaches (PMU counters vs LLVM IR instrumentation).

3. **CARET top-10 coverage**: 70% of CARET's highest-latency nodes are confirmed as memory/cache-bound by perf; 40% by miniperf. The difference reflects miniperf's finer per-loop granularity, which can classify a node as compute-bound if its hot loops are compute-intensive even when the overall process is memory-bound.

## Artifacts

- `tables/comparison_table.csv` -- per-node side-by-side metrics
- `tables/bottleneck_agreement.csv` -- method pairwise agreement rates
- `tables/methodology_summary.md` -- auto-generated markdown summary
- `graphs/01_latency_rank_vs_ai.png` through `05_combined_dashboard.png` -- comparison plots
