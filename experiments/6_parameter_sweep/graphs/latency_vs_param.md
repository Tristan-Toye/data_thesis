# Latency vs Parameter Value (Per-Node)

## Description

Line plots showing the relationship between parameter values and callback latency for each node. Each line represents a different parameter, with the x-axis normalized to [Low, Default, High].

## How to Read

- **Each line**: One parameter, showing how latency changes across its 3 values.
- **Annotations**: Show the actual parameter value at each point.
- **Steep lines**: Indicate strong sensitivity — the parameter significantly affects latency.
- **Flat lines**: Indicate insensitivity — changing this parameter has minimal latency impact.
- **Line direction**: Upward-sloping lines mean higher values = higher latency; downward = the opposite.

## Files

One file per node: `latency_vs_param_<node_name>.png`
