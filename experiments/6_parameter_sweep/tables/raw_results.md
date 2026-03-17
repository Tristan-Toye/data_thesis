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
| `callback_count` | count | Number of callback invocations observed (number of `ros2:callback_start` / `ros2:callback_end` pairs) |
| `latency_mean_us` | µs | Mean callback duration, defined as `t_callback_end − t_callback_start` for a single callback (from CARET’s `ros2:callback_start` to `ros2:callback_end`) |
| `latency_min_us` | µs | Minimum callback duration over all observed callbacks (min of `t_callback_end − t_callback_start`) |
| `latency_max_us` | µs | Maximum callback duration over all observed callbacks (max of `t_callback_end − t_callback_start`) |
| `latency_std_us` | µs | Standard deviation of callback duration (`t_callback_end − t_callback_start`) |
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

- **Latency**: Extracted from LTTng/CARET traces using `extract_callback_latency.py`. For each callback, CARET records `ros2:callback_start` and `ros2:callback_end`; the callback duration is `t_callback_end − t_callback_start`, covering the full execution of the callback function (including any internal publishes and post-publish work), but not the time until the next node starts processing the output.
- **PMU counters**: Collected via `perf stat` by running the node *under* `perf` (not `-p PID`). Requires `perf_event_paranoid <= 1` and `kernel.nmi_watchdog=0` during the sweep.

### perf commands used

For each run (identified as `${sweep_id}`), we record to `perf_data/${sweep_id}.txt` with:

```bash
# When CARET is enabled (LD_PRELOAD=${CARET_LIB}):
env LD_PRELOAD=${CARET_LIB} perf stat \
  -e instructions,cycles,L1-dcache-load-misses,L1-dcache-loads,LLC-load-misses,LLC-loads,cache-references,cache-misses,bus-cycles \
  -o "perf_data/${sweep_id}.txt" -- bash -c "${run_cmd}"

# When CARET is disabled:
perf stat \
  -e instructions,cycles,L1-dcache-load-misses,L1-dcache-loads,LLC-load-misses,LLC-loads,cache-references,cache-misses,bus-cycles \
  -o "perf_data/${sweep_id}.txt" -- bash -c "${run_cmd}"
```

These `perf stat` outputs are parsed inside `run_parameter_sweep.sh` by the inline `parse_perf_stat` Python helper, which fills the `instructions`, `cycles`, cache, and `bus_cycles` columns.

## Notes

- Rows with `latency_mean_us = 0` indicate failed runs (node didn't start, no callbacks observed, etc.)
- PMU columns are 0 when `perf stat` was not available or the run failed
- Each parameter is swept independently while all others remain at their default values
