# Arithmetic Intensity per Node — `ai_per_node.png`

## Description

Horizontal bar chart showing the aggregate arithmetic intensity (AI = FLOPs / Byte) for each of the 14 successfully compiled Autoware nodes, sorted from highest to lowest.

## What It Shows

- Each bar represents a node's aggregate AI across all compiled source files.
- Bars are annotated with the exact AI value and the raw FLOPs/bytes count.
- Red dashed line: FP32 scalar ridge point (0.52 FLOPs/byte).
- Blue dashed line: FP64 ridge point (0.26 FLOPs/byte).

## Key Observations

- `occupancy_grid_map_node` has the highest AI (0.139) — its tight grid computation has a relatively high FP-to-memory ratio, but still falls below both ridge points.
- `multi_object_tracker` (AI=0.027) and `map_based_prediction` (AI=0.016) are the next highest, driven by Eigen matrix operations and geometric computations.
- Most nodes have AI < 0.01, indicating they are overwhelmingly memory-bound on this platform.
