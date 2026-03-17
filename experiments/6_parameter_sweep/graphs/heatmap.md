# Latency Heatmaps (Per-Node)

## Description

One heatmap per node showing mean callback latency for each (parameter, value) combination. Rows are parameters, columns are the 3 sweep levels (Low, Default, High).

## How to Read

- **Color intensity**: Yellow-to-red scale where darker red indicates higher latency.
- **Cell labels**: Show the exact latency in µs and the parameter value used.
- Parameters where the color changes significantly across columns are the most latency-sensitive.
- Parameters where all three columns have similar colors have minimal latency impact.

## Files

One file per node: `heatmap_<node_name>.png`
