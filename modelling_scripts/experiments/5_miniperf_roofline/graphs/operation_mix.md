# Aggregate Operation Mix — `operation_mix.png`

## Description

Two pie charts showing the aggregate operation and memory access characteristics across all 14 compiled nodes.

## Left: FP vs Integer Operations

Shows the ratio of floating-point to integer operations across all compiled Autoware source code. The integer-dominated mix reflects:
- ROS 2 message handling and serialization
- Data structure indexing and pointer arithmetic
- Control flow decisions (conditional branching)
- Only inner numerical loops (Kalman filters, geometry) generate FP ops

## Right: Load vs Store Bytes

Shows the memory access split between loads and stores. The ~2:1 load-to-store ratio is typical for computational pipelines that read input data, process it, and produce smaller outputs.
