# Derived Metrics

**File:** `derived_metrics.csv`

Computed ratios and per-kilo-instruction metrics derived from raw perf counters.

## Key columns

| Metric | Description |
|---|---|
| `IPC` | Instructions Per Cycle -- higher is better (max ~4 on this core) |
| `L1D_miss_rate_%` | L1 data cache miss rate |
| `L1I_miss_rate_%` | L1 instruction cache miss rate |
| `LLC_miss_rate_%` | Last-level cache miss rate |
| `branch_miss_rate_%` | Branch misprediction rate |
| `dTLB_miss_rate_%` | Data TLB miss rate |
| `MPKI_*` | Misses Per Kilo-Instruction variants (L1D, L1I, LLC, branch) |

## How to read it

Low IPC combined with high miss rates indicates memory-bound behaviour. High IPC with low miss rates indicates compute-bound. Nodes with MPKI_LLC > 10 are strong candidates for cache optimisation.
