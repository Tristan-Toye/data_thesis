# Roofline Plot

**File:** `roofline_plot.png`

Log-log roofline chart for the Jetson Orin AGX (ARM Cortex-A78AE, LPDDR5).

## How to read it

- **X-axis:** Arithmetic Intensity (FLOPs/byte) -- higher means more compute per memory access.
- **Y-axis:** Performance (GFLOPs/s).
- **Sloped line (left):** Memory bandwidth ceiling (204.8 GB/s). Nodes below this line are memory-bound.
- **Horizontal line (right):** Peak compute ceiling (422.4 GFLOPs/s FP32 SIMD). Nodes below this are compute-limited.
- **Ridge point (~2.06 FLOPs/byte):** The intersection where the bottleneck transitions from memory to compute.

Nodes coloured by CARET latency rank (red = highest latency). Nodes in the lower-left quadrant (low AI, low performance) are the highest-priority optimisation targets -- they are both slow and memory-bound.
