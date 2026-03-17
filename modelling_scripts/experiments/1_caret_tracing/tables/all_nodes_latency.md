# All Nodes Latency Table

**File:** `all_nodes_latency.csv`

Complete table listing every Autoware node with its measured callback latency extracted from the CARET LTTng trace.

## Columns

| Column | Description |
|--------|-------------|
| `rank` | Rank by latency (1 = highest) |
| `node_name` | Fully qualified ROS 2 node name |
| `latency_ms` | Measured median callback latency in milliseconds |
| `pct_of_total` | Percentage contribution to grand total latency |
| `n_callbacks` | Number of callback invocations observed in the trace |

## Notes
- All 306 nodes have latency values measured directly from the CARET LTTng trace (`caret_trace_20260305_130449`).
- Latency is calculated as the median duration of `callback_start` → `callback_end` event pairs per node.
- Callback-to-node mapping uses `rcl_node_init`, `rcl_subscription_init`, `rclcpp_subscription_callback_added`, `rclcpp_timer_link_node`, and `rclcpp_timer_callback_added` trace events.
- 937 nodes were discovered in the trace; 306 had matched callback duration data.
- Nodes are sorted highest-latency first.
