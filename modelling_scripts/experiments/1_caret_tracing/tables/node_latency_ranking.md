# Node Latency Ranking

**File:** `node_latency_ranking.csv`

Per-node callback latency statistics extracted from CARET trace data, sorted by highest latency first.

## Columns

| Column | Description |
|---|---|
| `node_name` | Fully-qualified ROS 2 node name |
| `latency_ms` | Median callback latency in milliseconds |
| `percentage_of_total` | Node's share of total system latency |
| `percentage_of_longest_path` | Node's share of the longest end-to-end path latency (0 if not on that path) |
| `in_longest_path` | Whether the node lies on the critical (longest) path |
| `num_paths` | Number of distinct data-flow paths containing this node |

## How to read it

- Nodes at the top of the table are the **highest-priority optimisation targets**.
- Red rows (>10% of total) need the most attention.
- Nodes on the longest path directly affect worst-case end-to-end latency.
- The top 8 nodes together account for roughly 80% of total latency.
