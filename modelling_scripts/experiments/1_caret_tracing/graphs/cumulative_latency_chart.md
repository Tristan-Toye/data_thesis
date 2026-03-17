# Cumulative Latency Chart

**File:** `cumulative_latency_chart.png`

Two-panel figure showing per-node latency contributions.

## Top panel: Bar chart
Horizontal bars show each node's absolute callback latency (ms), sorted highest-first. Percentage labels indicate each node's share of total system latency.

## Bottom panel: Cumulative curve
The running sum of latency percentages. The red dashed line marks the **80% threshold** -- all nodes to its left collectively account for 80% of total latency and represent the highest-value optimisation targets (Pareto principle).

## Key takeaway
The top ~8 nodes cross the 80% line, meaning a focused effort on a small fraction of the system can address the majority of callback latency.
