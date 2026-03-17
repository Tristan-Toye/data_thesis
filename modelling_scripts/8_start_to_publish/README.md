Experiment 8 — Start-to-Publish Latency
======================================

Overview
--------

Experiment 8 is a **pure analysis layer** built on top of Experiment 6
(`6_parameter_sweep`). It does **not** modify or rerun the original sweep.
Instead, it:

- Reuses the existing Experiment 6 traces in
  `experiments/6_parameter_sweep/sweep_traces/`.
- Reuses the existing Experiment 6 CSV
  `experiments/6_parameter_sweep/tables/raw_results.csv`.
- Computes a new latency metric per callback:
  **start-to-publish latency**.
- Writes a new enriched CSV and new plots under
  `experiments/8_start_to_publish/`.


Latency Definitions
-------------------

- **Callback duration (Experiment 6)**  
  Defined as:
  `t_callback_end − t_callback_start`  
  using CARET events `ros2:callback_start` / `ros2:callback_end`. This covers
  the full execution of the callback function (including any internal publishes
  and post-publish work), but not the time until downstream nodes start
  processing.

- **Start-to-publish latency (Experiment 8)**  
  For each callback:

  1. Find all `ros2:rclcpp_publish` events that occur between that callback's
     `callback_start` and `callback_end` timestamps.
  2. Let `t_last_publish` be the timestamp of the **last** such publish.
  3. Define the start-to-publish latency as:
     `t_last_publish − t_callback_start`.

  This directly answers:  
  *“Given an input, how long until the node has published its last output for
  that callback?”*

For each node, we also compute `pub_count`, the average number of
`rclcpp_publish` calls per callback.


Inputs and Outputs
------------------

**Inputs (read-only):**

- `experiments/6_parameter_sweep/tables/raw_results.csv`  
  Original Experiment 6 CSV with callback latency and perf metrics.
- `experiments/6_parameter_sweep/sweep_traces/*`  
  One LTTng/CARET trace per (node, parameter, value, run_id).

**Outputs (Experiment 8):**

- `experiments/8_start_to_publish/tables/raw_results_start_to_publish.csv`  
  New CSV that:
  - Preserves **all** original Experiment 6 columns (including perf).
  - Adds:
    - `pub_count`
    - `pub_latency_mean_us`, `pub_latency_min_us`, `pub_latency_max_us`,
      `pub_latency_std_us`
    - `pub_latency_p50_us`, `pub_latency_p95_us`, `pub_latency_p99_us`
- `experiments/8_start_to_publish/graphs/`  
  Contains:
  - Tornado/sensitivity plots based on `pub_latency_mean_us`.
  - All-nodes violin plot for `pub_latency_mean_us`.
  - Other derived plots that, when possible, switch from callback latency to
    start-to-publish latency.


Usage
-----

1. **Generate the enriched CSV**

   From anywhere inside the `scripts` workspace:

   ```bash
   python3 modelling_scripts/8_start_to_publish/backfill_publish_latency.py
   ```

   This will:

   - Read `experiments/6_parameter_sweep/tables/raw_results.csv`.
   - Re-parse each corresponding trace under
     `experiments/6_parameter_sweep/sweep_traces/`.
   - Write the enriched CSV to:

     `experiments/8_start_to_publish/tables/raw_results_start_to_publish.csv`

2. **Run the Experiment 8 analysis**

   ```bash
   python3 modelling_scripts/8_start_to_publish/analyze_sweep.py
   ```

   By default this will:

   - Read `experiments/8_start_to_publish/tables/raw_results_start_to_publish.csv`.
   - Write graphs under `experiments/8_start_to_publish/graphs/`, including:
     - `violin_publish_all_nodes.png` (start-to-publish violin plot)
     - `tornado_<node>.png` (tornado plots using start-to-publish latency when
       available)
     - Other sensitivity/PMU plots adapted to use the new metric when present.

You can override the defaults with:

```bash
python3 modelling_scripts/8_start_to_publish/analyze_sweep.py \
  --input /path/to/other.csv \
  --output-dir /path/to/output_base
```


Relationship to Experiment 6
----------------------------

Experiment 8 is intentionally **additive**:

- It does not modify any files under `modelling_scripts/6_parameter_sweep/`.
- It does not modify `experiments/6_parameter_sweep/tables/raw_results.csv`.
- It does not modify or rerun the original sweep or traces.

You can continue to:

- Use Experiment 6 to reason about **callback duration**.
- Use Experiment 8 to reason about **start-to-publish latency** on top of the
  same runs.

