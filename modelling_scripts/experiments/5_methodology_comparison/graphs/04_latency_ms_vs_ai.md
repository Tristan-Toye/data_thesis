# Absolute Latency vs Arithmetic Intensity

**File:** `04_latency_ms_vs_ai.png`

Scatter plot of CARET absolute latency (ms, y-axis) against miniperf arithmetic intensity (FLOPs/byte, x-axis). Bubble size or colour may encode additional metrics.

Nodes in the **upper-left** are the most impactful to optimise: they are both slow in wall-clock terms and have low arithmetic intensity (memory-bound).
