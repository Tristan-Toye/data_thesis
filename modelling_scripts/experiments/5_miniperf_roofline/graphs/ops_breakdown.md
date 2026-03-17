# Operation & Memory Breakdown — `ops_breakdown.png`

## Description

Dual bar chart showing the static operation mix (left) and memory access pattern (right) for each node.

## Left Panel: FP vs Integer Operations

- Red bars: Floating-point operations (fadd, fmul, fdiv, fma, fcmp, etc.)
- Blue bars: Integer operations (add, sub, mul, shifts, bitwise ops)
- Most nodes are heavily integer-dominated, reflecting the control-flow-heavy nature of ROS 2 autonomous driving nodes.
- `multi_object_tracker` stands out with the highest FP count due to Kalman filter and association computations.

## Right Panel: Load vs Store Bytes

- Green bars: Load bytes (memory reads)
- Orange bars: Store bytes (memory writes)
- Load/store ratio is approximately 2:1 across all nodes, typical for computation that reads inputs, processes, and writes smaller outputs.
- `behavior_path_planner` has the highest total memory traffic, reflecting its complex data structure traversals.
