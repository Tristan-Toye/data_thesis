# All Nodes Latency Table

**File:** `all_nodes_latency.csv`

Complete table listing every Autoware node with its estimated callback latency and percentage of total system latency.

## Columns

| Column | Description |
|--------|-------------|
| `rank` | Rank by latency (1 = highest) |
| `node_name` | Fully qualified ROS 2 node name |
| `latency_ms` | Estimated median callback latency in milliseconds |
| `pct_of_total` | Percentage contribution to grand total latency |

## Notes
- The top 15 nodes have latency values measured directly from CARET trace analysis.
- Remaining nodes have estimated latencies proportional to typical callback overhead, collectively representing ~13 % of the total.
- Nodes are sorted highest-latency first.
