# Latency Rank vs Arithmetic Intensity

**File:** `01_latency_rank_vs_ai.png`

Scatter plot with CARET latency rank on the y-axis (1 = highest latency) and miniperf arithmetic intensity (FLOPs/byte) on the x-axis.

Nodes in the **top-left quadrant** (high latency + low AI) are the highest-priority targets: they are both slow and memory-bound, meaning memory access optimisations (cache blocking, prefetching, data layout) are likely to have the most impact.
