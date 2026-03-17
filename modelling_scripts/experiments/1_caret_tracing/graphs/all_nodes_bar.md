# All Nodes – Horizontal Bar Chart

**File:** `all_nodes_bar.png`

Horizontal bar chart displaying the measured callback latency (ms) for all 306 nodes in the Autoware stack, sorted from highest to lowest. Data extracted from the CARET LTTng trace.

- **Dark bars** highlight the top 15 nodes selected for deeper profiling.
- **Light bars** show the remaining nodes.
- Percentage labels appear next to bars with >= 1% contribution.

## Key takeaway
The chart visually confirms the heavy-tail distribution: `map_based_prediction` and a few system nodes dominate callback latency, while the vast majority of nodes (transform listeners, etc.) sit well below 0.01 ms. This Pareto-like pattern underpins the decision to focus subsequent experiments on the top contributors.
