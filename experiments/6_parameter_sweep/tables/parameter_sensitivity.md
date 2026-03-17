# Parameter Sensitivity Summary

## Description

Per-node aggregated statistics computed across all parameter sweep configurations. This table answers the question: "How much does each node's latency vary when its parameters are changed?"

## Columns

| Column | Unit | Description |
|--------|------|-------------|
| `node` | — | Short name of the Autoware node |
| `num_param_sets` | count | Number of (parameter, value) combinations tested |
| `latency_mean_us` | µs | Mean of all per-run mean latencies |
| `latency_min_us` | µs | Minimum observed mean latency across all runs |
| `latency_max_us` | µs | Maximum observed mean latency across all runs |
| `latency_std_us` | µs | Average per-run standard deviation |
| `latency_range_us` | µs | Max mean latency − Min mean latency |
| `latency_cv` | ratio | Coefficient of variation (std / mean) |

## Interpretation

- **`latency_range_us`**: The larger this value, the more sensitive the node is to parameter changes. Nodes with large ranges are prime candidates for performance tuning.
- **`latency_cv`**: Normalized sensitivity. A CV > 0.1 indicates meaningful parameter sensitivity; CV > 0.3 indicates high sensitivity.
- Nodes are sorted by `latency_range_us` (most sensitive first).
