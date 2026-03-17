#!/usr/bin/env python3
"""
Single-pass extraction of per-node callback latencies from a CARET LTTng trace
using bt2 (babeltrace2) Python bindings. Builds handle maps and computes
callback durations simultaneously to minimize I/O.
"""

import bt2
import csv
import sys
import numpy as np
from collections import defaultdict
from pathlib import Path

TRACE_DIR = str(
    Path(__file__).parent
    / "trace_data/caret_trace_20260305_130449/lttng/ust"
)
OUT_CSV = (
    Path(__file__).parent.parent
    / "experiments/1_caret_tracing/tables/all_nodes_latency.csv"
)
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

print("Single-pass extraction from trace …")
print(f"  Trace: {TRACE_DIR}")

node_handle_map: dict[int, str] = {}
sub_to_node: dict[int, int] = {}
sub_ptr_to_handle: dict[int, int] = {}
timer_to_node: dict[int, int] = {}
svc_to_node: dict[int, int] = {}
cb_to_node: dict[int, int] = {}

cb_start_ts: dict[int, int] = {}
node_durations: dict[str, list[float]] = defaultdict(list)

# Deferred callback events: (callback_handle, start_ts, end_ts)
# for callbacks we saw before their mapping was established
deferred: list[tuple[int, float]] = []

msg_it = bt2.TraceCollectionMessageIterator(TRACE_DIR)
n_events = 0
n_cb_matched = 0
n_cb_deferred = 0

INIT_EVENTS = frozenset([
    "ros2_caret:rcl_node_init", "ros2:rcl_node_init",
    "ros2_caret:rcl_subscription_init", "ros2:rcl_subscription_init",
    "ros2_caret:rclcpp_subscription_init",
    "ros2_caret:rclcpp_subscription_callback_added",
    "ros2_caret:rclcpp_timer_link_node",
    "ros2_caret:rclcpp_timer_callback_added",
    "ros2_caret:rcl_service_init", "ros2:rcl_service_init",
    "ros2_caret:rclcpp_service_callback_added", "ros2:rclcpp_service_callback_added",
])

CB_START = frozenset(["ros2:callback_start", "ros2_caret:callback_start"])
CB_END = frozenset(["ros2:callback_end", "ros2_caret:callback_end"])

for msg in msg_it:
    if type(msg) is not bt2._EventMessageConst:
        continue

    ev = msg.event
    name = ev.name
    n_events += 1

    if name in INIT_EVENTS:
        if name in ("ros2_caret:rcl_node_init", "ros2:rcl_node_init"):
            h = int(ev["node_handle"])
            ns = str(ev["namespace"])
            nn = str(ev["node_name"])
            node_handle_map[h] = f"{ns}/{nn}".replace("//", "/")

        elif name in ("ros2_caret:rcl_subscription_init", "ros2:rcl_subscription_init"):
            sub_to_node[int(ev["subscription_handle"])] = int(ev["node_handle"])

        elif name == "ros2_caret:rclcpp_subscription_init":
            sub_ptr_to_handle[int(ev["subscription"])] = int(ev["subscription_handle"])

        elif name == "ros2_caret:rclcpp_subscription_callback_added":
            sub_ptr = int(ev["subscription"])
            cb_h = int(ev["callback"])
            real_sub_h = sub_ptr_to_handle.get(sub_ptr)
            if real_sub_h is not None and real_sub_h in sub_to_node:
                cb_to_node[cb_h] = sub_to_node[real_sub_h]

        elif name == "ros2_caret:rclcpp_timer_link_node":
            timer_to_node[int(ev["timer_handle"])] = int(ev["node_handle"])

        elif name == "ros2_caret:rclcpp_timer_callback_added":
            timer_h = int(ev["timer_handle"])
            cb_h = int(ev["callback"])
            if timer_h in timer_to_node:
                cb_to_node[cb_h] = timer_to_node[timer_h]

        elif name in ("ros2_caret:rcl_service_init", "ros2:rcl_service_init"):
            svc_to_node[int(ev["service_handle"])] = int(ev["node_handle"])

        elif name in ("ros2_caret:rclcpp_service_callback_added", "ros2:rclcpp_service_callback_added"):
            svc_h = int(ev["service_handle"])
            cb_h = int(ev["callback"])
            if svc_h in svc_to_node:
                cb_to_node[cb_h] = svc_to_node[svc_h]

    elif name in CB_START:
        cb_h = int(ev["callback"])
        cb_start_ts[cb_h] = msg.default_clock_snapshot.ns_from_origin

    elif name in CB_END:
        cb_h = int(ev["callback"])
        start = cb_start_ts.pop(cb_h, None)
        if start is not None:
            dur_ms = (msg.default_clock_snapshot.ns_from_origin - start) / 1e6
            if dur_ms > 0:
                if cb_h in cb_to_node:
                    node_h = cb_to_node[cb_h]
                    node_name = node_handle_map.get(node_h)
                    if node_name:
                        node_durations[node_name].append(dur_ms)
                        n_cb_matched += 1

    if n_events % 5_000_000 == 0:
        print(f"  {n_events / 1e6:.0f}M events | "
              f"{len(node_handle_map)} nodes, {len(cb_to_node)} cb maps, "
              f"{n_cb_matched} cb durations", flush=True)

print(f"\n  Total events:      {n_events / 1e6:.1f}M")
print(f"  Nodes:             {len(node_handle_map)}")
print(f"  Mapped callbacks:  {len(cb_to_node)}")
print(f"  Duration samples:  {n_cb_matched}")
print(f"  Nodes w/ data:     {len(node_durations)}")

# Write CSV
rows = []
for node_name, durs in node_durations.items():
    rows.append({
        "node_name": node_name,
        "latency_ms": float(np.median(durs)),
        "n_callbacks": len(durs),
    })

rows.sort(key=lambda r: r["latency_ms"], reverse=True)
grand_total = sum(r["latency_ms"] for r in rows)

with open(OUT_CSV, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["rank", "node_name", "latency_ms", "pct_of_total", "n_callbacks"])
    for i, r in enumerate(rows, 1):
        pct = r["latency_ms"] / grand_total * 100 if grand_total else 0
        w.writerow([i, r["node_name"], f"{r['latency_ms']:.4f}",
                    f"{pct:.3f}", r["n_callbacks"]])

print(f"\nWrote {OUT_CSV}")
print(f"  Nodes with data: {len(rows)}")
print(f"  Grand total:     {grand_total:.2f} ms")
if rows:
    print(f"  Top 10:")
    for r in rows[:10]:
        print(f"    {r['node_name']}: {r['latency_ms']:.2f} ms "
              f"({r['latency_ms']/grand_total*100:.1f}%, "
              f"n={r['n_callbacks']})")
