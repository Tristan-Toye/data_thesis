# Pie Chart – All Nodes Latency Contribution

**File:** `piechart_all_nodes.png`

Pie chart showing the callback-latency contribution of every node in the Autoware stack. The top 20 nodes are labelled individually; the remaining nodes are aggregated into an "Other" slice.

## Key takeaway
A small number of perception and localisation nodes dominate overall callback latency. The long tail of infrastructure, diagnostics, and light-weight planning nodes collectively accounts for a minor fraction, confirming that optimisation effort should focus on the top contributors.
