#!/usr/bin/env python3
"""
Backfill start-to-publish latency metrics into an enriched CSV for Experiment 8.

Reads the existing Experiment 6 raw_results.csv and, for each
(node, parameter, value, run_id) combination, re-parses the corresponding
LTTng/CARET trace to compute start-to-publish latency statistics using
extract_all_metrics() from extract_callback_latency.py.

Outputs:
    experiments/8_start_to_publish/tables/raw_results_start_to_publish.csv
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path

from extract_callback_latency import extract_all_metrics


SCRIPT_DIR = Path(__file__).resolve().parent
EXP6_TABLES_DIR = Path.home() / "scripts" / "experiments" / "6_parameter_sweep" / "tables"
INPUT_CSV = EXP6_TABLES_DIR / "raw_results.csv"
OUTPUT_CSV = Path.home() / "scripts" / "experiments" / "8_start_to_publish" / "tables" / "raw_results_start_to_publish.csv"
SWEEP_TRACES_DIR = Path.home() / "scripts" / "experiments" / "6_parameter_sweep" / "sweep_traces"


def build_trace_id(row: dict) -> str:
    return f"{row['node']}_{row['parameter']}_{row['value']}_r{row['run_id']}"


def main() -> int:
    print("starting main")
    if not INPUT_CSV.exists():
        print(f"ERROR: input CSV not found: {INPUT_CSV}", file=sys.stderr)
        return 1

    rows = []
    with INPUT_CSV.open(newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for row in reader:
            rows.append(row)

    total_rows = len(rows)
    print(f"[backfill] Loaded {total_rows} rows from {INPUT_CSV}")

    # New columns to append for Experiment 8
    new_cols = [
        "pub_count",
        "pub_latency_mean_us",
        "pub_latency_min_us",
        "pub_latency_max_us",
        "pub_latency_std_us",
        "pub_latency_p50_us",
        "pub_latency_p95_us",
        "pub_latency_p99_us",
    ]

    # Extend header if needed
    for col in new_cols:
        if col not in fieldnames:
            fieldnames.append(col)

    # If an output CSV already exists, load its rows so we can skip work
    # for sweep_ids that are already present. This makes the script restartable.
    existing_rows_by_id: dict[str, dict] = {}
    if OUTPUT_CSV.exists():
        print(f"[backfill] Found existing output CSV: {OUTPUT_CSV}, loading for restart...")
        with OUTPUT_CSV.open(newline="") as f_out:
            out_reader = csv.DictReader(f_out)
            for out_row in out_reader:
                sid = build_trace_id(out_row)
                existing_rows_by_id[sid] = out_row
        print(f"[backfill] Existing rows in output: {len(existing_rows_by_id)}")

    # Compute metrics per unique sweep_id
    metrics_cache: dict[str, dict] = {}
    processed = 0

    for row in rows:
        sweep_id = build_trace_id(row)
        if sweep_id in metrics_cache:
            continue
        if sweep_id in existing_rows_by_id:
            # Already present in output; just mark as no-op in metrics_cache.
            metrics_cache[sweep_id] = {}
            continue

        trace_dir = SWEEP_TRACES_DIR / sweep_id / "lttng"
        ust_dir = trace_dir / "ust"
        if ust_dir.exists():
            trace_path = str(trace_dir)
        elif trace_dir.exists():
            trace_path = str(trace_dir)
        else:
            # Trace missing; store zeros
            metrics_cache[sweep_id] = {
                "pub_count": 0.0,
                "pub_latency_mean_us": 0.0,
                "pub_latency_min_us": 0.0,
                "pub_latency_max_us": 0.0,
                "pub_latency_std_us": 0.0,
                "pub_latency_p50_us": 0.0,
                "pub_latency_p95_us": 0.0,
                "pub_latency_p99_us": 0.0,
            }
            continue

        node_name = row["node"]
        try:
            print(f"[backfill] Extracting metrics for {sweep_id}...")
            metrics = extract_all_metrics(trace_path, target_node=node_name)
            print(f"[backfill] Metrics extracted for {sweep_id}: {metrics}")
        except Exception as e:  # noqa: BLE001
            print(f"[backfill] WARNING: failed to extract metrics for {sweep_id}: {e}", file=sys.stderr)
            metrics_cache[sweep_id] = {
                "pub_count": 0.0,
                "pub_latency_mean_us": 0.0,
                "pub_latency_min_us": 0.0,
                "pub_latency_max_us": 0.0,
                "pub_latency_std_us": 0.0,
                "pub_latency_p50_us": 0.0,
                "pub_latency_p95_us": 0.0,
                "pub_latency_p99_us": 0.0,
            }
            continue

        # metrics is node_name -> {"callback": {...}, "publish": {...}}
        publish = metrics.get(node_name, {}).get("publish", {})
        if not publish or publish.get("count", 0) == 0:
            metrics_cache[sweep_id] = {
                "pub_count": 0.0,
                "pub_latency_mean_us": 0.0,
                "pub_latency_min_us": 0.0,
                "pub_latency_max_us": 0.0,
                "pub_latency_std_us": 0.0,
                "pub_latency_p50_us": 0.0,
                "pub_latency_p95_us": 0.0,
                "pub_latency_p99_us": 0.0,
            }
        else:
            metrics_cache[sweep_id] = {
                "pub_count": float(publish.get("pub_count", 0.0)),
                "pub_latency_mean_us": float(publish.get("mean_us", 0.0)),
                "pub_latency_min_us": float(publish.get("min_us", 0.0)),
                "pub_latency_max_us": float(publish.get("max_us", 0.0)),
                "pub_latency_std_us": float(publish.get("std_us", 0.0)),
                "pub_latency_p50_us": float(publish.get("p50_us", 0.0)),
                "pub_latency_p95_us": float(publish.get("p95_us", 0.0)),
                "pub_latency_p99_us": float(publish.get("p99_us", 0.0)),
            }

        processed += 1
        if processed % 10 == 0:
            print(f"[backfill] Processed {processed} new sweep_ids...")

    print(f"[backfill] Finished metric extraction for {processed} new sweep_ids.")

    # Write enriched CSV (merge existing rows with newly computed ones)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for idx, row in enumerate(rows, start=1):
            sweep_id = build_trace_id(row)
            # Prefer existing full row (already contains metrics) if available
            if sweep_id in existing_rows_by_id:
                writer.writerow(existing_rows_by_id[sweep_id])
                continue

            metrics = metrics_cache.get(sweep_id, {})
            for col in new_cols:
                if col in metrics:
                    row[col] = metrics[col]
                else:
                    row.setdefault(col, 0.0)
            writer.writerow(row)

            if idx % 20 == 0:
                print(f"[backfill] Wrote {idx}/{total_rows} rows to output CSV...")

    print(f"[backfill] Wrote enriched CSV with publish latency metrics to {OUTPUT_CSV}")
    return 0


if __name__ == "__main__":
    print(f"[backfill] Starting backfill for start-to-publish latency...")
    raise SystemExit(main())

