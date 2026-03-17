# Merged Node Data

**File:** `merged_node_data.csv`

Combines CARET latency rankings (experiment 1) with the ROS 2 node inventory collected from the running Autoware system. This is the master table used by experiments 3--5 to know which nodes to profile.

## Columns

| Column | Description |
|---|---|
| `node_name` | Fully-qualified ROS 2 node path |
| `short_name` | Short node name (last component of the path) |
| `namespace` | ROS 2 namespace |
| `package` | ROS 2 package containing the node |
| `executable` | Binary/executable name |
| `latency_ms` | Median callback latency from CARET (ms) |
| `percentage_of_total` | Share of total system latency |
| `percentage_of_longest_path` | Share of longest-path latency (0 if not on that path) |
| `in_longest_path` | Whether the node is on the critical path |

## How to read it

All 15 profiled nodes were successfully matched to their ROS 2 packages. The `package` and `executable` columns are needed by the single-node replayer to isolate and record each node independently for detailed perf/miniperf profiling.
