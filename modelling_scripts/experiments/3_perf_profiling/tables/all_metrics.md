# All Metrics (Raw)

**File:** `all_metrics.csv`

Combined raw `perf stat` counters for all 15 profiled nodes. Each row is a node; columns are hardware performance counter values (cycles, instructions, cache accesses/misses, branch events, TLB events, etc.).

These are the unprocessed counters parsed directly from `perf stat` output. Use `derived_metrics.csv` and `agnostic_metrics.csv` for analysed ratios and classifications.
