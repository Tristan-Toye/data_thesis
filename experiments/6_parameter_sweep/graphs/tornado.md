# Tornado Charts (Per-Node)

## Description

Classic sensitivity analysis visualization showing the deviation from baseline (default parameter value) when each parameter is set to its low or high value.

## How to Read

- **Center line** (yellow dashed): Represents the latency at default parameter values.
- **Teal bars** (left of center): Latency change when the parameter is set to its LOW value.
- **Red bars** (right of center): Latency change when set to HIGH.
- Parameters are sorted by total swing (|high_dev| + |low_dev|), with the most impactful at the top.
- Bars extending to the right indicate that higher parameter values increase latency.
- Bars extending to the left indicate that higher values decrease latency.

## Files

One file per node: `tornado_<node_name>.png`
