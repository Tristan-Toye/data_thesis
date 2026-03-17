# Bottleneck Agreement

**File:** `bottleneck_agreement.csv`

Pairwise agreement rates between the three profiling methodologies.

## Rows

| Comparison | Description |
|---|---|
| `perf_vs_mperf` | Fraction of nodes where perf and miniperf agree on the primary bottleneck class |
| `perf_uses_caret_top10` | Of CARET's top-10 latency nodes, fraction classified as memory/cache-bound by perf |
| `mperf_uses_caret_top10` | Of CARET's top-10 latency nodes, fraction classified as memory/cache-bound by miniperf |

## How to read it

- **>80% agreement**: Methods are highly consistent.
- **60--80%**: Broadly consistent with some edge-case divergence.
- **<60%**: Weak agreement; individual nodes should be investigated case-by-case.

In this dataset, perf vs miniperf agreement is 53.3%, indicating moderate divergence -- expected given their different measurement approaches (PMU counters vs LLVM IR instrumentation).
