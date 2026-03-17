# Bottleneck Distribution

**File:** `03_bottleneck_distribution.png`

Stacked or grouped bar chart showing how many nodes each method classifies into each bottleneck category (memory, compute, cache, branches, unknown).

Highlights systematic differences: for example, perf tends to classify more nodes as memory/cache-bound due to its PMU-based heuristics, while miniperf's LLVM IR approach is more granular.
