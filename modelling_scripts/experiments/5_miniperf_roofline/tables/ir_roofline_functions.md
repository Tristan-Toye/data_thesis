# IR Roofline Function-Level Data — `ir_roofline_functions.csv`

## Description

Per-function static analysis from LLVM IR, listing the top 500 functions by floating-point operation count across all compiled Autoware nodes.

## Methodology

Same as `ir_roofline_nodes.md`. Each LLVM IR function (including template instantiations and inlined library code like Eigen) is independently analyzed for FP ops, integer ops, and memory bytes.

## Columns

| Column | Description |
|---|---|
| `node` | Parent Autoware node |
| `source` | Source `.cpp` file (stem) |
| `function` | Mangled C++ function name (truncated to 100 chars) |
| `total_flops` | Static FP op count in this function |
| `total_int_ops` | Static integer op count |
| `total_mem_bytes` | Load + store bytes |
| `arithmetic_intensity` | FLOPs / bytes |

## Notable Hotspots

- **Eigen GEMM kernels** (`gebp_kernel`): AI up to 2.5 FLOPs/byte — these are the only functions that cross the ridge point into the compute-bound regime. Found in `multi_object_tracker`, `ekf_localizer`, `ndt_scan_matcher`.
- **Boost.Geometry intersection/side** functions: AI ~0.36–0.68, used in `map_based_prediction` and `autonomous_emergency_braking`.
- **Kalman filter update** (`KalmanFilterTemplate::update`): AI ~0.45 in `multi_object_tracker`.
- **Covariance transforms** (`tf2::transformCovariance`): AI ~0.625 in `multi_object_tracker` and `ndt_scan_matcher`.

These hotspots represent the computationally intensive inner loops that would benefit most from architecture-specific optimization (SIMD, cache tiling).
