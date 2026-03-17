#!/usr/bin/env python3
"""
Extract callback latencies from a single-node LTTng/CARET trace.

Lightweight version of extract_all_nodes_fast.py, optimized for small
single-node traces produced during parameter sweep runs.

Usage:
    python3 extract_callback_latency.py <trace_dir> [--node-name NAME] [--output FILE]

Output (stdout or file): JSON with latency statistics.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

try:
    import bt2
except ImportError:
    print("ERROR: babeltrace2 Python bindings not found. "
          "Install with: pip install bt2 or apt install python3-bt2",
          file=sys.stderr)
    sys.exit(1)

try:
    import numpy as np
except ImportError:
    np = None


def extract_latencies(trace_dir: str, target_node: str = None) -> dict:
    """
    Parse LTTng trace and extract callback durations per node.

    Returns dict mapping node_name -> list of durations in microseconds.
    """
    node_handle_map: dict[int, str] = {}
    sub_to_node: dict[int, int] = {}
    sub_ptr_to_handle: dict[int, int] = {}
    timer_to_node: dict[int, int] = {}
    svc_to_node: dict[int, int] = {}
    cb_to_node: dict[int, int] = {}
    cb_start_ts: dict[int, int] = {}
    node_durations: dict[str, list[float]] = defaultdict(list)

    INIT_EVENTS = frozenset([
        "ros2_caret:rcl_node_init", "ros2:rcl_node_init",
        "ros2_caret:rcl_subscription_init", "ros2:rcl_subscription_init",
        "ros2_caret:rclcpp_subscription_init",
        "ros2_caret:rclcpp_subscription_callback_added",
        "ros2_caret:rclcpp_timer_link_node",
        "ros2_caret:rclcpp_timer_callback_added",
        "ros2_caret:rcl_service_init", "ros2:rcl_service_init",
        "ros2_caret:rclcpp_service_callback_added",
        "ros2:rclcpp_service_callback_added",
    ])
    CB_START = frozenset(["ros2:callback_start", "ros2_caret:callback_start"])
    CB_END = frozenset(["ros2:callback_end", "ros2_caret:callback_end"])
    RCLCPP_PUBLISH = frozenset(["ros2:rclcpp_publish"])

    trace_path = str(Path(trace_dir))
    ust_path = Path(trace_dir) / "ust"
    if ust_path.exists():
        trace_path = str(ust_path)

    msg_it = bt2.TraceCollectionMessageIterator(trace_path)

    for msg in msg_it:
        if type(msg) is not bt2._EventMessageConst:
            continue

        ev = msg.event
        name = ev.name

        if name in INIT_EVENTS:
            if name in ("ros2_caret:rcl_node_init", "ros2:rcl_node_init"):
                h = int(ev["node_handle"])
                ns = str(ev["namespace"])
                nn = str(ev["node_name"])
                node_handle_map[h] = f"{ns}/{nn}".replace("//", "/")

            elif name in ("ros2_caret:rcl_subscription_init",
                          "ros2:rcl_subscription_init"):
                sub_to_node[int(ev["subscription_handle"])] = int(ev["node_handle"])

            elif name == "ros2_caret:rclcpp_subscription_init":
                sub_ptr_to_handle[int(ev["subscription"])] = int(
                    ev["subscription_handle"])

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

            elif name in ("ros2_caret:rcl_service_init",
                          "ros2:rcl_service_init"):
                svc_to_node[int(ev["service_handle"])] = int(ev["node_handle"])

            elif name in ("ros2_caret:rclcpp_service_callback_added",
                          "ros2:rclcpp_service_callback_added"):
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
                dur_us = (msg.default_clock_snapshot.ns_from_origin - start) / 1e3
                if dur_us > 0:
                    if cb_h in cb_to_node:
                        node_h = cb_to_node[cb_h]
                        node_name = node_handle_map.get(node_h)
                        if node_name:
                            node_durations[node_name].append(dur_us)

    if target_node:
        filtered = {}
        for nname, durs in node_durations.items():
            short = nname.rsplit("/", 1)[-1]
            if target_node in nname or target_node == short:
                filtered[nname] = durs
        if filtered:
            node_durations = filtered

    return dict(node_durations)


def extract_publish_latencies(trace_dir: str, target_node: str = None) -> dict:
    """
    Parse LTTng trace and extract start-to-publish latencies per node.

    For each callback, we find rclcpp_publish events that occur between
    callback_start and callback_end on the same callback handle, and
    record (t_publish - t_callback_start). For each node we compute
    statistics over these publish-latency samples and also track the
    average number of publishes per callback.
    """
    node_handle_map: dict[int, str] = {}
    sub_to_node: dict[int, int] = {}
    sub_ptr_to_handle: dict[int, int] = {}
    timer_to_node: dict[int, int] = {}
    svc_to_node: dict[int, int] = {}
    cb_to_node: dict[int, int] = {}

    INIT_EVENTS = frozenset([
        "ros2_caret:rcl_node_init", "ros2:rcl_node_init",
        "ros2_caret:rcl_subscription_init", "ros2:rcl_subscription_init",
        "ros2_caret:rclcpp_subscription_init",
        "ros2_caret:rclcpp_subscription_callback_added",
        "ros2_caret:rclcpp_timer_link_node",
        "ros2_caret:rclcpp_timer_callback_added",
        "ros2_caret:rcl_service_init", "ros2:rcl_service_init",
        "ros2_caret:rclcpp_service_callback_added",
        "ros2:rclcpp_service_callback_added",
    ])
    CB_START = frozenset(["ros2:callback_start", "ros2_caret:callback_start"])
    CB_END = frozenset(["ros2:callback_end", "ros2_caret:callback_end"])
    RCLCPP_PUBLISH = frozenset(["ros2:rclcpp_publish"])

    trace_path = str(Path(trace_dir))
    ust_path = Path(trace_dir) / "ust"
    if ust_path.exists():
        trace_path = str(ust_path)

    # First pass: build callback intervals and node mapping
    cb_start_ts: dict[int, int] = {}
    cb_intervals: dict[int, list[tuple[int, int, str]]] = defaultdict(list)

    msg_it = bt2.TraceCollectionMessageIterator(trace_path)
    for msg in msg_it:
        if type(msg) is not bt2._EventMessageConst:
            continue
        ev = msg.event
        name = ev.name

        if name in INIT_EVENTS:
            if name in ("ros2_caret:rcl_node_init", "ros2:rcl_node_init"):
                h = int(ev["node_handle"])
                ns = str(ev["namespace"])
                nn = str(ev["node_name"])
                node_handle_map[h] = f"{ns}/{nn}".replace("//", "/")

            elif name in ("ros2_caret:rcl_subscription_init",
                          "ros2:rcl_subscription_init"):
                sub_to_node[int(ev["subscription_handle"])] = int(ev["node_handle"])

            elif name == "ros2_caret:rclcpp_subscription_init":
                sub_ptr_to_handle[int(ev["subscription"])] = int(
                    ev["subscription_handle"])

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

            elif name in ("ros2_caret:rcl_service_init",
                          "ros2:rcl_service_init"):
                svc_to_node[int(ev["service_handle"])] = int(ev["node_handle"])

            elif name in ("ros2_caret:rclcpp_service_callback_added",
                          "ros2:rclcpp_service_callback_added"):
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
            if start is None:
                continue
            if cb_h not in cb_to_node:
                continue
            node_h = cb_to_node[cb_h]
            node_name = node_handle_map.get(node_h)
            if not node_name:
                continue
            end = msg.default_clock_snapshot.ns_from_origin
            cb_intervals[cb_h].append((start, end, node_name))

    # Optional node filter on full name or short name
    if target_node:
        def node_ok(n: str) -> bool:
            short = n.rsplit("/", 1)[-1]
            return target_node in n or target_node == short
    else:
        def node_ok(n: str) -> bool:
            return True

    # Second pass: collect publish timestamps and map into intervals
    publish_latencies_by_node: dict[str, list[float]] = defaultdict(list)
    publishes_per_node: dict[str, int] = defaultdict(int)
    callbacks_per_node: dict[str, int] = defaultdict(int)

    msg_it = bt2.TraceCollectionMessageIterator(trace_path)
    for msg in msg_it:
        if type(msg) is not bt2._EventMessageConst:
            continue
        ev = msg.event
        name = ev.name

        if name in CB_START:
            cb_h = int(ev["callback"])
            # count callbacks per node for pub_count later
            for start, end, node_name in cb_intervals.get(cb_h, []):
                if node_ok(node_name):
                    callbacks_per_node[node_name] += 1

        elif name in RCLCPP_PUBLISH:
            t_pub = msg.default_clock_snapshot.ns_from_origin
            # Find all intervals whose [start, end] contain t_pub
            for cb_h, intervals in cb_intervals.items():
                for start, end, node_name in intervals:
                    if not node_ok(node_name):
                        continue
                    if start <= t_pub <= end:
                        publishes_per_node[node_name] += 1
                        publish_latencies_by_node[node_name].append(
                            (t_pub - start) / 1e3
                        )

    # Build stats per node
    publish_stats: dict[str, dict] = {}
    for node_name, samples in publish_latencies_by_node.items():
        stats = compute_stats(samples)
        cb_count = callbacks_per_node.get(node_name, 0)
        total_pubs = publishes_per_node.get(node_name, 0)
        stats["pub_count"] = (total_pubs / cb_count) if cb_count > 0 else 0.0
        publish_stats[node_name] = stats

    return publish_stats


def extract_all_metrics(trace_dir: str, target_node: str = None) -> dict:
    """
    Convenience wrapper that returns both callback and publish latency stats
    per node from a single trace directory.
    """
    callbacks = extract_latencies(trace_dir, target_node)
    publish = extract_publish_latencies(trace_dir, target_node)
    results = {}
    for node_name in set(list(callbacks.keys()) + list(publish.keys())):
        results[node_name] = {
            "callback": compute_stats(callbacks.get(node_name, [])),
            "publish": publish.get(node_name, {
                "count": 0, "mean_us": 0, "min_us": 0, "max_us": 0,
                "std_us": 0, "p50_us": 0, "p95_us": 0, "p99_us": 0,
                "pub_count": 0.0,
            }),
        }
    return results

    if target_node:
        filtered = {}
        for nname, durs in node_durations.items():
            short = nname.rsplit("/", 1)[-1]
            if target_node in nname or target_node == short:
                filtered[nname] = durs
        if filtered:
            node_durations = filtered

    return dict(node_durations)


def compute_stats(durations: list[float]) -> dict:
    """Compute latency statistics from a list of durations in microseconds."""
    if not durations:
        return {
            "count": 0, "mean_us": 0, "min_us": 0, "max_us": 0,
            "std_us": 0, "p50_us": 0, "p95_us": 0, "p99_us": 0,
        }
    if np is not None:
        arr = np.array(durations)
        return {
            "count": len(arr),
            "mean_us": float(np.mean(arr)),
            "min_us": float(np.min(arr)),
            "max_us": float(np.max(arr)),
            "std_us": float(np.std(arr)),
            "p50_us": float(np.percentile(arr, 50)),
            "p95_us": float(np.percentile(arr, 95)),
            "p99_us": float(np.percentile(arr, 99)),
        }
    durations_s = sorted(durations)
    n = len(durations_s)
    mean = sum(durations_s) / n
    variance = sum((x - mean) ** 2 for x in durations_s) / n
    return {
        "count": n,
        "mean_us": mean,
        "min_us": durations_s[0],
        "max_us": durations_s[-1],
        "std_us": variance ** 0.5,
        "p50_us": durations_s[int(n * 0.50)],
        "p95_us": durations_s[int(n * 0.95)],
        "p99_us": durations_s[min(int(n * 0.99), n - 1)],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Extract callback latencies from LTTng/CARET trace")
    parser.add_argument("trace_dir", help="Path to LTTng trace directory")
    parser.add_argument("--node-name", "-n", default=None,
                        help="Filter to specific node name (short or full)")
    parser.add_argument("--output", "-o", default=None,
                        help="Output JSON file (default: stdout)")
    parser.add_argument("--include-publish", action="store_true",
                        help="Also compute start-to-publish latency metrics")
    args = parser.parse_args()

    if args.include_publish:
        results = extract_all_metrics(args.trace_dir, args.node_name)
    else:
        node_durations = extract_latencies(args.trace_dir, args.node_name)
        results = {}
        for node_name, durs in node_durations.items():
            results[node_name] = compute_stats(durs)

    output = json.dumps(results, indent=2)
    if args.output:
        Path(args.output).write_text(output)
        print(f"Wrote latency data to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
