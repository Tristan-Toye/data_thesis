# Function-Level Hotspot Roofline — `hotspot_roofline.png`

## Description

Roofline plot showing the top 50 functions (by FP operation count) as individual data points, color-coded by parent node.

## What It Shows

Each circle represents a single LLVM IR function with ≥20 FP operations. The size of the circle is proportional to the function's FLOP count. The position indicates:
- X: the function's arithmetic intensity (FLOPs / byte)
- Y: the attainable performance at that AI, bounded by the hardware ceiling

## Notable Clusters

1. **Eigen GEMM kernels** (AI ~0.5–2.5): Matrix multiplication inner loops that approach or exceed the FP64 ridge point. These are the only functions that could potentially be compute-bound.
2. **Covariance transforms** (AI ~0.6): Coordinate frame transformations using 6×6 matrices.
3. **Geometric computations** (AI ~0.3–0.7): Boost.Geometry intersection and side-of-line tests.
4. **Kalman filter updates** (AI ~0.4): State estimation in `multi_object_tracker`.

Most functions cluster at very low AI (< 0.1), confirming the overall memory-bound nature of the Autoware perception/planning pipeline.
