# Miniperf Roofline (Per-Hotspot)

**File:** `miniperf_roofline.csv`

Per-loop-hotspot roofline data extracted from LLVM IR instrumentation runs. Each row represents one hotspot within a node.

## Key columns

| Column | Description |
|---|---|
| `node_name` | Autoware node |
| `hotspot` | Loop/function identifier |
| `arithmetic_intensity` | FLOPs per byte of memory traffic |
| `performance_gflops` | Measured performance in GFLOPs/s |
| `bound` | Classification: `Memory` or `Compute` |

48 hotspots across all 15 nodes are captured.
