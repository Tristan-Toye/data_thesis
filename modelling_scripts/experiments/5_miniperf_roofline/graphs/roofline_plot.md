# Roofline Plot — `roofline_plot.png`

## Description

Architecture-agnostic roofline model showing the performance characteristics of the top-15 Autoware nodes based on static LLVM IR analysis using the [miniperf](https://github.com/alexbatashev/miniperf) Clang plugin.

## What It Shows

- **X-axis**: Arithmetic Intensity (AI) = FLOPs / Byte — the ratio of floating-point operations to memory traffic.
- **Y-axis**: Attainable performance in GFLOP/s, bounded by either memory bandwidth (left of ridge) or compute throughput (right of ridge).
- **Roofline ceilings**: Three hardware ceilings for the Jetson Orin AGX (FP32 SIMD, FP32 scalar, FP64 scalar).
- **Diamond markers**: Aggregate per-node AI, showing where each node sits on the roofline.
- **Small circles**: Individual high-FLOP functions, color-coded by parent node.

## Key Observations

1. **All nodes are deeply memory-bound**: Every node falls far to the left of the ridge point, meaning memory bandwidth is the primary performance limiter, not compute throughput.
2. **A few Eigen GEMM hotspots approach compute-bound**: Individual functions (Kalman filter kernels) reach AI ~2.5, crossing the FP64 ridge point.
3. **The workload is integer-dominated**: Most nodes spend more operations on integer arithmetic (control flow, indexing, message handling) than floating-point math.

## Methodology

Static analysis of LLVM IR text files generated with `clang-19 -O3 -S -emit-llvm -Xclang -fpass-plugin=miniperf_plugin.so`. Operation counts are per-compilation-unit (not per-invocation), representing the code's inherent computational character.
