# Miniperf Roofline (Per-Node Aggregate)

**File:** `miniperf_roofline_agg.csv`

One row per node with aggregated roofline metrics.

## Key columns

| Column | Description |
|---|---|
| `weighted_ai` | Weighted arithmetic intensity across hotspots |
| `max_performance_gflops` | Peak observed performance |
| `dominant_bound` | Primary bottleneck: `Memory` or `Compute` |
| `n_hotspots` | Number of hotspots detected |

## How to read it

- Nodes with `dominant_bound = Memory` and low `weighted_ai` (< 2 FLOPs/byte) are memory-bandwidth-limited.
- 4 nodes (lidar_centerpoint, ndt_scan_matcher, occupancy_grid_map_node, pointcloud_concatenate_data) are memory-bound; the rest are compute-bound.
