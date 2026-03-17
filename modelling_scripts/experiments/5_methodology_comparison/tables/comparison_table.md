# Cross-Methodology Comparison Table

**File:** `comparison_table.csv`

Side-by-side per-node metrics from all three profiling methods.

## Key columns

| Column group | Columns | Source |
|---|---|---|
| CARET | `caret_latency_ms`, `caret_pct_total`, `caret_rank` | Experiment 1 |
| perf | `perf_ops_per_byte`, `perf_cache_hit_rate`, `perf_bottleneck` | Experiment 3 |
| miniperf | `mperf_arithmetic_intensity`, `mperf_peak_gflops`, `mperf_bottleneck`, `mperf_n_hotspots` | Experiment 4 |

## How to read it

Nodes that rank high in CARET latency **and** are classified as memory-bound by both perf and miniperf are the strongest, highest-confidence optimisation targets. Look for rows where `caret_rank` is low (1 = highest latency), `perf_bottleneck` is `memory` or `cache`, and `mperf_bottleneck` is `Memory`.
