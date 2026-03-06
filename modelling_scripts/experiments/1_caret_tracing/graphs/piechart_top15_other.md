# Pie Chart – Top 15 Nodes + Other

**File:** `piechart_top15_other.png`

Pie chart isolating the 15 highest-latency nodes identified by CARET analysis. Each of the 15 nodes is shown as an individual slice with its percentage of total system callback latency. All remaining nodes are combined into an "Other" slice.

## Key takeaway
The top 15 nodes together account for roughly 87 % of total system callback latency. The "Other" slice (~13 %) represents over 200 nodes with individually negligible contributions. This motivates the selection of these 15 nodes as profiling targets in Experiments 2–4.
