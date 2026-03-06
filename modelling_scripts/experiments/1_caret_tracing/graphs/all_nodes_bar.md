# All Nodes – Horizontal Bar Chart

**File:** `all_nodes_bar.png`

Horizontal bar chart displaying the callback latency (ms) for every node in the Autoware stack, sorted from highest to lowest.

- **Dark bars** highlight the top 15 nodes selected for deeper profiling.
- **Light bars** show the remaining nodes.
- Percentage labels appear next to bars with >= 1 % contribution.

## Key takeaway
The chart visually confirms the heavy-tail distribution: a handful of nodes have latencies in the 10–45 ms range, while the vast majority sit below 1 ms. This Pareto-like pattern underpins the decision to focus subsequent experiments on the top contributors.
