# Normalized Sensitivity: Top 20 Parameters

## Description

Shows the percentage change in latency when each parameter is set to its low or high value, relative to the default. This normalizes across nodes with different baseline latencies, allowing fair comparison of parameter sensitivity.

## How to Read

- **Teal bars** (left): % change from default when parameter is set to its LOW value.
- **Red bars** (right): % change from default when parameter is set to its HIGH value.
- **Yellow dashed line**: The default baseline (0% change).
- Parameters with large bars in both directions are the most impactful for tuning.
- Parameters with bars in only one direction suggest a monotonic relationship with latency.
