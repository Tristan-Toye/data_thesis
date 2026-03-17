# PMU Counter Correlations

## Description

Scatter plots showing the relationship between callback latency and hardware performance counters (PMU metrics). This helps identify whether latency is primarily driven by compute intensity or memory access patterns.

## How to Read

- Each subplot shows latency vs one PMU metric, with points colored by node.
- **Strong positive correlation with instructions**: Latency is compute-bound (more work = more time).
- **Strong positive correlation with cache miss rate**: Latency is memory-bound (cache misses are the bottleneck).
- **Strong positive correlation with bus cycles**: Latency is driven by RAM bandwidth.
- **Weak/no correlation**: The metric is not a primary driver of latency for these parameter ranges.

## Prerequisites

PMU data requires `perf_event_paranoid <= 1`. If this was not available during the sweep, this plot will not be generated.

## Metrics

- **Retired Instructions**: Total instructions executed
- **L1 Cache Miss Rate**: Data cache misses at L1 level
- **LLC (L3) Miss Rate**: Last-level cache misses
- **Overall Cache Miss Rate**: Combined cache miss rate
- **Bus Cycles**: Proxy for memory bus / RAM traffic
