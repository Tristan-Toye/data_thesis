#!/usr/bin/env python3
"""Regenerate the cumulative latency chart with ms-based cumulative curve."""

import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

CSV = Path(__file__).parent / "results" / "node_latency_ranking.csv"
OUT = Path(__file__).parent.parent / "experiments" / "1_caret_tracing" / "graphs" / "cumulative_latency_chart.png"
OUT.parent.mkdir(parents=True, exist_ok=True)

rows = []
with open(CSV) as f:
    for r in csv.DictReader(f):
        rows.append(r)

node_names = [r["node_name"].split("/")[-1][:20] for r in rows]
latencies = [float(r["latency_ms"]) for r in rows]
percentages = [float(r["percentage_of_total"]) for r in rows]

total_ms = sum(latencies)
cumulative_ms = np.cumsum(latencies)
threshold_80 = total_ms * 0.80

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

# ── Top panel: bar chart ──────────────────────────────────────────────────
ax1.barh(range(len(node_names)), latencies, color="steelblue")
ax1.set_yticks(range(len(node_names)))
ax1.set_yticklabels(node_names)
ax1.invert_yaxis()
ax1.set_xlabel("Latency (ms)")
ax1.set_title("Top Nodes by Latency Contribution")
for i, (lat, pct) in enumerate(zip(latencies, percentages)):
    ax1.text(lat + 0.3, i, f"{pct:.1f}%", va="center", fontsize=8)

# ── Bottom panel: cumulative ms curve ─────────────────────────────────────
ax2.fill_between(range(len(node_names)), cumulative_ms, alpha=0.3, color="steelblue")
ax2.plot(range(len(node_names)), cumulative_ms, "o-", color="steelblue", markersize=5)
ax2.set_xticks(range(len(node_names)))
ax2.set_xticklabels(node_names, rotation=45, ha="right")
ax2.set_ylabel("Cumulative Latency (ms)")
ax2.set_xlabel("Nodes (sorted by latency)")
ax2.set_title("Cumulative Latency")
ax2.set_ylim(0, total_ms * 1.05)

ax2.axhline(y=threshold_80, color="r", linestyle="--", alpha=0.6,
            label=f"80% of total ({threshold_80:.1f} ms)")

# Annotate the node where the 80% line is crossed
cross_idx = int(np.searchsorted(cumulative_ms, threshold_80))
if cross_idx < len(node_names):
    ax2.plot(cross_idx, cumulative_ms[cross_idx], "ro", markersize=8, zorder=5)
    ax2.annotate(f"{cumulative_ms[cross_idx]:.1f} ms",
                 xy=(cross_idx, cumulative_ms[cross_idx]),
                 xytext=(cross_idx + 0.8, cumulative_ms[cross_idx] - total_ms * 0.07),
                 fontsize=9, color="red",
                 arrowprops=dict(arrowstyle="->", color="red", lw=1.2))

for i, val in enumerate(cumulative_ms):
    ax2.text(i, val + total_ms * 0.015, f"{val:.1f}", ha="center", fontsize=6, color="gray")

ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)

fig.tight_layout()
fig.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {OUT}")
