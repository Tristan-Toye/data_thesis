# Pie Chart – All Nodes Latency Contribution

**File:** `piechart_all_nodes.png`

Pie chart showing the measured callback-latency contribution of every node in the Autoware stack, extracted from the CARET LTTng trace (`caret_trace_20260305_130449`, 142M events). The top 20 nodes are labelled individually; the remaining 286 nodes are aggregated into an "Other" slice.

## Key takeaway
The `map_based_prediction` node dominates with ~25% of total callback latency, followed by system-level nodes (`hazard_status_converter`, `diagnostics`, `converter`). The long tail of transform listeners and infrastructure nodes collectively accounts for a minor fraction.
