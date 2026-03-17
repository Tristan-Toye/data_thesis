# Architecture-Agnostic Metrics

**File:** `agnostic_metrics.csv`

Higher-level performance characterisation that is portable across CPU architectures.

## Key columns

| Metric | Description |
|---|---|
| `ops_per_byte` | Approximate arithmetic intensity (operations per memory byte) |
| `working_set_KB` | Estimated data working set size from TLB behaviour |
| `bottleneck` | Primary bottleneck classification: `memory`, `compute`, `cache`, `branches`, or combinations |

## How to read it

- **Memory-bound** nodes (low ops/byte) benefit from cache blocking, prefetching, or data layout changes.
- **Compute-bound** nodes (high ops/byte) benefit from vectorisation or algorithmic improvements.
- 8 out of 15 nodes are classified as memory-bound; 7 as compute-bound.
