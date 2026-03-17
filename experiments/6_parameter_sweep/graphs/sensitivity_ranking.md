# Sensitivity Ranking

## Description

Horizontal bar chart ranking all (node, parameter) pairs by their latency range — the difference between the highest and lowest mean latency observed across the 3 sweep values. This identifies which specific parameter changes have the greatest impact on performance.

## How to Read

- **Bar length**: Latency range in microseconds (max − min across parameter values). Longer bars indicate more impactful parameters.
- **Percentage labels** (yellow): The latency range as a percentage of the mean, providing normalized sensitivity.
- **Color coding**: Bars are colored by node to show clustering of sensitive parameters within specific nodes.
- The top entries are the parameters that offer the most "tuning headroom" for latency optimization.
