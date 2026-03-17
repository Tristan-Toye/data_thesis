# ROS 2 Node Inventory

**File:** `ros2_node_inventory.csv`

Raw node metadata collected from a running Autoware system via `collect_node_info.sh`. Lists every profiled node's short name, namespace, ROS 2 package, and executable name.

This table serves as the input for `merge_latency_with_info.py`, which joins it with CARET latency data to produce `merged_node_data.csv`.
