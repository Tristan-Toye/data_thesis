# Raw Results — Parameter Sweep

## Description

This CSV file contains one row per (node, parameter, value, repetition) combination from the parameter sweep experiment. Each row captures both callback latency statistics (from CARET tracing) and hardware performance counter data (from `perf stat`, when available).

## Columns

| Column | Unit | Description |
|--------|------|-------------|
| `node` | — | Short name of the Autoware node |
| `parameter` | — | Name of the parameter being swept |
| `value` | — | The value the parameter was set to for this run |
| `run_id` | — | Repetition number (1-based) |
| `callback_count` | count | Number of callback invocations observed |
| `latency_mean_us` | µs | Mean callback duration |
| `latency_min_us` | µs | Minimum callback duration |
| `latency_max_us` | µs | Maximum callback duration |
| `latency_std_us` | µs | Standard deviation of callback duration |
| `latency_p50_us` | µs | 50th percentile (median) callback duration |
| `latency_p95_us` | µs | 95th percentile callback duration |
| `latency_p99_us` | µs | 99th percentile callback duration |
| `instructions` | count | Retired instructions (PMU) |
| `cycles` | count | CPU cycles (PMU) |
| `ipc` | ratio | Instructions per cycle |
| `l1_dcache_load_misses` | count | L1 data cache load misses |
| `l1_dcache_loads` | count | L1 data cache loads |
| `l1_miss_rate` | ratio | L1 miss rate (misses / loads) |
| `llc_load_misses` | count | Last-level cache (L3) load misses |
| `llc_loads` | count | Last-level cache loads |
| `llc_miss_rate` | ratio | LLC miss rate |
| `cache_references` | count | Total cache references |
| `cache_misses` | count | Total cache misses |
| `cache_miss_rate` | ratio | Overall cache miss rate |
| `bus_cycles` | count | Memory bus cycles |

## Measurement Method

- **Latency**: Extracted from LTTng/CARET traces using `extract_callback_latency.py`. CARET instruments ROS 2 callback start/end events at microsecond resolution.
- **PMU counters**: Collected via `perf stat` attached to the node process PID. Requires `perf_event_paranoid <= 1`.

## Notes

- Rows with `latency_mean_us = 0` indicate failed runs (node didn't start, no callbacks observed, etc.)
- PMU columns are 0 when `perf stat` was not available or the run failed
- Each parameter is swept independently while all others remain at their default values
