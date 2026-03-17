#!/usr/bin/env python3
"""
Extract callback latency for ALL nodes from the CARET trace.
Writes all_nodes_latency.csv with real measured data.
"""

import csv
import sys
import os
import numpy as np
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, os.path.expanduser("~/ros2_caret_ws/build/caret_analyze"))
cpp_impl = os.path.expanduser(
    "~/ros2_caret_ws/install/caret_analyze_cpp_impl/lib/python3.10/site-packages"
)
if cpp_impl not in sys.path:
    sys.path.insert(0, cpp_impl)

from caret_analyze import Architecture, Lttng, Application  # noqa: E402

SCRIPT_DIR = Path(__file__).parent
LTTNG_PATH = str(
    SCRIPT_DIR / "trace_data/caret_trace_20260305_130449/lttng"
)
OUT_CSV = SCRIPT_DIR.parent / "experiments/1_caret_tracing/tables/all_nodes_latency.csv"
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

print("Loading LTTng trace …")
lttng = Lttng(LTTNG_PATH)

print("Building architecture from trace …")
arch = Architecture("lttng", LTTNG_PATH)

print("Creating Application object …")
app = Application(arch, lttng)

print("Extracting callback latencies for every node …")
node_latencies: dict[str, list[float]] = defaultdict(list)

nodes = app.get_nodes("*")
print(f"  Total nodes in trace: {len(nodes)}")

for node in nodes:
    name = node.node_name
    try:
        for cb in node.callbacks:
            df = cb.to_dataframe()
            if df is not None and len(df) > 0 and "latency" in df.columns:
                med = float(np.median(df["latency"].values)) / 1e6  # ns → ms
                node_latencies[name].append(med)
    except Exception:
        pass

rows = []
for name, lats in node_latencies.items():
    if lats:
        rows.append({"node_name": name, "latency_ms": float(np.mean(lats))})

rows.sort(key=lambda r: r["latency_ms"], reverse=True)
grand_total = sum(r["latency_ms"] for r in rows)

with open(OUT_CSV, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["rank", "node_name", "latency_ms", "pct_of_total"])
    for i, r in enumerate(rows, 1):
        pct = r["latency_ms"] / grand_total * 100 if grand_total else 0
        w.writerow([i, r["node_name"], f"{r['latency_ms']:.4f}", f"{pct:.3f}"])

print(f"\nWrote {OUT_CSV}")
print(f"  Nodes with data: {len(rows)}")
print(f"  Grand total:     {grand_total:.2f} ms")
if rows:
    print(f"  Top node:        {rows[0]['node_name']} ({rows[0]['latency_ms']:.2f} ms)")
