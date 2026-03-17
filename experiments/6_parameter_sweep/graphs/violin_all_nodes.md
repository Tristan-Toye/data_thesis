# Violin Plot: All Nodes Parameter Sensitivity

## Description

This violin plot displays the latency distribution for each of the 15 Autoware nodes across all parameter sweep configurations. Each "violin" represents how much the node's mean callback latency varies when different parameter values are applied.

## How to Read

- **Width** of each violin indicates the density of latency observations at that level — wider sections mean more parameter configurations result in latencies near that value.
- **Yellow line**: Mean latency across all configurations.
- **Red line**: Median latency.
- **Tall, narrow violins**: The node's latency is relatively stable regardless of parameter settings.
- **Wide, spread-out violins**: The node is highly sensitive to parameter changes — a prime candidate for tuning.

## Key Insight

This is the primary "deviation graph" — it focuses on showing how much latency varies rather than the absolute latency value. Nodes with wide distributions are the most performance-tunable.
