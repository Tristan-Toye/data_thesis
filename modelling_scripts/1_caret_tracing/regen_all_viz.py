#!/usr/bin/env python3
"""
Regenerate all-nodes visualizations from the real all_nodes_latency.csv.
"""

import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

CSV_PATH = (
    Path(__file__).parent.parent
    / "experiments/1_caret_tracing/tables/all_nodes_latency.csv"
)
GRAPHS_DIR = (
    Path(__file__).parent.parent
    / "experiments/1_caret_tracing/graphs"
)
GRAPHS_DIR.mkdir(parents=True, exist_ok=True)

rows = []
with open(CSV_PATH) as f:
    for row in csv.DictReader(f):
        rows.append({
            "node_name": row["node_name"],
            "latency_ms": float(row["latency_ms"]),
            "pct_of_total": float(row["pct_of_total"]),
        })

grand_total = sum(r["latency_ms"] for r in rows)


def short_name(n: str) -> str:
    return n.split("/")[-1]


def make_colours(n, cmap_name="tab20"):
    cmap = plt.cm.get_cmap(cmap_name, max(n, 20))
    return [cmap(i) for i in range(n)]


# -- 1. Pie chart: ALL nodes (show top 20 + Other) ----------------------------
fig, ax = plt.subplots(figsize=(12, 10))

display_top = 20
pie_labels, pie_values = [], []
for r in rows[:display_top]:
    pie_labels.append(f"{short_name(r['node_name'])} ({r['pct_of_total']:.1f}%)")
    pie_values.append(r["latency_ms"])

other_val = sum(r["latency_ms"] for r in rows[display_top:])
if other_val > 0:
    n_rest = len(rows) - display_top
    pie_labels.append(f"Other ({n_rest} nodes, {other_val/grand_total*100:.1f}%)")
    pie_values.append(other_val)

colours = make_colours(len(pie_values))
wedges, _ = ax.pie(
    pie_values, labels=None, colors=colours, startangle=140,
    wedgeprops=dict(edgecolor="white", linewidth=0.5),
)
ax.legend(wedges, pie_labels, title="Nodes", loc="center left",
          bbox_to_anchor=(1.0, 0.5), fontsize=8)
ax.set_title("Latency Contribution – All Nodes (measured)", fontsize=14, fontweight="bold")
fig.tight_layout()
out = GRAPHS_DIR / "piechart_all_nodes.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Wrote {out}")

# -- 2. Pie chart: Top 15 + Other ---------------------------------------------
fig, ax = plt.subplots(figsize=(12, 10))

top15 = rows[:15]
top15_total = sum(r["latency_ms"] for r in top15)
pie15_labels, pie15_values = [], []
for r in top15:
    pct = r["latency_ms"] / grand_total * 100
    pie15_labels.append(f"{short_name(r['node_name'])} ({pct:.1f}%)")
    pie15_values.append(r["latency_ms"])

other_val = grand_total - top15_total
if other_val > 0:
    n_rest = len(rows) - 15
    pct_other = other_val / grand_total * 100
    pie15_labels.append(f"Other ({n_rest} nodes, {pct_other:.1f}%)")
    pie15_values.append(other_val)

colours15 = make_colours(len(pie15_values))
explode = [0.03] * len(top15) + ([0.06] if other_val > 0 else [])
wedges, _ = ax.pie(
    pie15_values, labels=None, colors=colours15, startangle=140,
    explode=explode,
    wedgeprops=dict(edgecolor="white", linewidth=0.5),
)
ax.legend(wedges, pie15_labels, title="Nodes", loc="center left",
          bbox_to_anchor=(1.0, 0.5), fontsize=8)
ax.set_title("Latency Contribution – Top 15 Nodes + Other (measured)",
             fontsize=14, fontweight="bold")
fig.tight_layout()
out = GRAPHS_DIR / "piechart_top15_other.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Wrote {out}")

# -- 3. Pie chart: Selected (top 15) vs Other ---------------------------------
fig, ax = plt.subplots(figsize=(10, 8))

selected_total = top15_total
other_total = grand_total - selected_total

labels = [
    f"Top 15 nodes\n{selected_total:.3f} ms ({selected_total/grand_total*100:.1f}%)",
    f"Other ({len(rows)-15} nodes)\n{other_total:.3f} ms ({other_total/grand_total*100:.1f}%)",
]
sizes = [selected_total, other_total]
colors = ["#3182bd", "#bdd7e7"]
wedges, texts, _ = ax.pie(sizes, labels=labels, colors=colors, startangle=90,
                          autopct=" ", wedgeprops=dict(edgecolor="white", linewidth=1))
ax.set_title("Selected Nodes vs Other (measured)", fontsize=14, fontweight="bold")
fig.tight_layout()
out = GRAPHS_DIR / "piechart_selected_vs_other.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Wrote {out}")

# -- 4. Horizontal bar: ALL nodes ---------------------------------------------
top15_names = {r["node_name"] for r in top15}
fig, ax = plt.subplots(figsize=(14, max(8, len(rows) * 0.18)))

names = [short_name(r["node_name"]) for r in rows]
lats = [r["latency_ms"] for r in rows]
bar_colours = ["#3182bd" if r["node_name"] in top15_names else "#bdd7e7"
               for r in rows]

y_pos = range(len(names))
ax.barh(y_pos, lats, color=bar_colours, edgecolor="white", linewidth=0.3)
ax.set_yticks(y_pos)
ax.set_yticklabels(names, fontsize=5)
ax.invert_yaxis()
ax.set_xlabel("Callback Latency (ms)")
ax.set_title("All Nodes – Measured Callback Latency (dark = top 15)",
             fontsize=13, fontweight="bold")

for i, (lat, pct) in enumerate(zip(lats, [r["pct_of_total"] for r in rows])):
    if pct >= 1.0:
        ax.text(lat + 0.005, i, f"{pct:.1f}%", va="center", fontsize=5)

fig.tight_layout()
out = GRAPHS_DIR / "all_nodes_bar.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Wrote {out}")

print("\nDone – all visualizations regenerated with measured data.")
