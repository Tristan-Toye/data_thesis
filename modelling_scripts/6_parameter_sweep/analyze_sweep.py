#!/usr/bin/env python3
"""
Parameter Sweep Analysis & Visualization
=========================================
Reads raw_results.csv from the parameter sweep experiment, computes
summary statistics, and generates all visualizations.

Usage:
    python3 analyze_sweep.py [--input CSV] [--output-dir DIR]
"""

import argparse
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

plt.rcParams.update({
    "figure.facecolor": "#1a1a2e",
    "axes.facecolor": "#16213e",
    "axes.edgecolor": "#e0e0e0",
    "axes.labelcolor": "#e0e0e0",
    "text.color": "#e0e0e0",
    "xtick.color": "#e0e0e0",
    "ytick.color": "#e0e0e0",
    "grid.color": "#2a2a4a",
    "grid.alpha": 0.5,
    "font.family": "sans-serif",
    "font.size": 11,
    "figure.dpi": 150,
})

ACCENT_COLORS = [
    "#e94560", "#0f3460", "#533483", "#16c79a", "#f7be16",
    "#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#ffeaa7",
    "#dfe6e9", "#74b9ff", "#a29bfe", "#fd79a8", "#55efc4",
]


def load_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    for col in ["latency_mean_us", "latency_min_us", "latency_max_us",
                 "latency_std_us", "latency_p50_us", "latency_p95_us",
                 "latency_p99_us"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def compute_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Per-node aggregated stats across all parameter sets."""
    summary = df.groupby("node").agg(
        num_param_sets=("latency_mean_us", "count"),
        latency_mean_us=("latency_mean_us", "mean"),
        latency_min_us=("latency_min_us", "min"),
        latency_max_us=("latency_max_us", "max"),
        latency_std_us=("latency_std_us", "mean"),
        latency_range_us=("latency_mean_us", lambda x: x.max() - x.min()),
    ).reset_index()
    summary["latency_cv"] = summary["latency_std_us"] / summary["latency_mean_us"]
    summary = summary.sort_values("latency_range_us", ascending=False)
    return summary


def plot_violin_all_nodes(df: pd.DataFrame, output_dir: str):
    """Violin plot with all nodes showing latency distribution across parameter sweeps."""
    fig, ax = plt.subplots(figsize=(16, 8))

    nodes = df["node"].unique()
    node_order = sorted(nodes,
                        key=lambda n: df[df["node"] == n]["latency_mean_us"].median(),
                        reverse=True)

    data_per_node = [df[df["node"] == n]["latency_mean_us"].values for n in node_order]
    data_per_node = [d for d in data_per_node if len(d) > 0]
    valid_nodes = [n for n, d in zip(node_order, [df[df["node"] == n]["latency_mean_us"].values for n in node_order]) if len(d) > 0]

    if not data_per_node:
        print("  WARNING: No data for violin plot")
        plt.close()
        return

    parts = ax.violinplot(data_per_node, positions=range(len(valid_nodes)),
                          showmeans=True, showmedians=True, showextrema=True)

    for i, pc in enumerate(parts["bodies"]):
        pc.set_facecolor(ACCENT_COLORS[i % len(ACCENT_COLORS)])
        pc.set_alpha(0.7)
        pc.set_edgecolor("#ffffff")
        pc.set_linewidth(0.5)

    parts["cmeans"].set_color("#f7be16")
    parts["cmeans"].set_linewidth(1.5)
    parts["cmedians"].set_color("#e94560")
    parts["cmedians"].set_linewidth(1.5)
    parts["cmins"].set_color("#e0e0e0")
    parts["cmaxes"].set_color("#e0e0e0")
    parts["cbars"].set_color("#e0e0e0")

    ax.set_xticks(range(len(valid_nodes)))
    short_names = [n.replace("_", "\n") for n in valid_nodes]
    ax.set_xticklabels(short_names, rotation=45, ha="right", fontsize=9)
    ax.set_ylabel("Callback Latency (µs)")
    ax.set_title("Parameter Sensitivity: Latency Distribution Across All Parameter Sweeps",
                 fontsize=14, fontweight="bold", pad=15)
    ax.grid(axis="y", alpha=0.3)

    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color="#f7be16", lw=2, label="Mean"),
        Line2D([0], [0], color="#e94560", lw=2, label="Median"),
    ]
    ax.legend(handles=legend_elements, loc="upper right")

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "violin_all_nodes.png"), bbox_inches="tight")
    plt.close()
    print("  Generated: violin_all_nodes.png")


def plot_boxplot_all_nodes(df: pd.DataFrame, output_dir: str):
    """Box plot companion to the violin plot."""
    fig, ax = plt.subplots(figsize=(16, 8))

    nodes = df["node"].unique()
    node_order = sorted(nodes,
                        key=lambda n: df[df["node"] == n]["latency_mean_us"].median(),
                        reverse=True)

    data_per_node = [df[df["node"] == n]["latency_mean_us"].dropna().values for n in node_order]

    bp = ax.boxplot(data_per_node, labels=[n.replace("_", "\n") for n in node_order],
                    patch_artist=True, notch=True,
                    medianprops=dict(color="#e94560", linewidth=2),
                    whiskerprops=dict(color="#e0e0e0"),
                    capprops=dict(color="#e0e0e0"),
                    flierprops=dict(markerfacecolor="#f7be16", marker="D", markersize=4))

    for i, patch in enumerate(bp["boxes"]):
        patch.set_facecolor(ACCENT_COLORS[i % len(ACCENT_COLORS)])
        patch.set_alpha(0.7)
        patch.set_edgecolor("#ffffff")

    ax.set_xticklabels([n.replace("_", "\n") for n in node_order],
                       rotation=45, ha="right", fontsize=9)
    ax.set_ylabel("Callback Latency (µs)")
    ax.set_title("Parameter Sensitivity: Latency Box Plots Across All Parameter Sweeps",
                 fontsize=14, fontweight="bold", pad=15)
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "boxplot_all_nodes.png"), bbox_inches="tight")
    plt.close()
    print("  Generated: boxplot_all_nodes.png")


def plot_sensitivity_ranking(df: pd.DataFrame, output_dir: str):
    """Horizontal bar chart ranking (node, parameter) pairs by latency range."""
    sensitivity = []
    for (node, param), group in df.groupby(["node", "parameter"]):
        vals = group["latency_mean_us"]
        if len(vals) >= 2:
            lat_range = vals.max() - vals.min()
            lat_pct = (lat_range / vals.mean() * 100) if vals.mean() > 0 else 0
            sensitivity.append({
                "node_param": f"{node} / {param}",
                "range_us": lat_range,
                "range_pct": lat_pct,
                "node": node,
            })

    if not sensitivity:
        return

    sens_df = pd.DataFrame(sensitivity).sort_values("range_us", ascending=True)
    top_n = min(30, len(sens_df))
    sens_df = sens_df.tail(top_n)

    fig, ax = plt.subplots(figsize=(14, max(8, top_n * 0.35)))

    node_colors = {}
    unique_nodes = sens_df["node"].unique()
    for i, n in enumerate(unique_nodes):
        node_colors[n] = ACCENT_COLORS[i % len(ACCENT_COLORS)]

    colors = [node_colors[n] for n in sens_df["node"]]

    bars = ax.barh(range(len(sens_df)), sens_df["range_us"], color=colors, alpha=0.8,
                   edgecolor="#ffffff", linewidth=0.5)

    ax.set_yticks(range(len(sens_df)))
    ax.set_yticklabels(sens_df["node_param"], fontsize=8)
    ax.set_xlabel("Latency Range (µs) across parameter values")
    ax.set_title("Parameter Sensitivity Ranking\n(Largest latency impact from parameter changes)",
                 fontsize=14, fontweight="bold", pad=15)
    ax.grid(axis="x", alpha=0.3)

    for i, (_, row) in enumerate(sens_df.iterrows()):
        ax.text(row["range_us"] + ax.get_xlim()[1] * 0.01, i,
                f'{row["range_pct"]:.1f}%', va="center", fontsize=8, color="#f7be16")

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "sensitivity_ranking.png"), bbox_inches="tight")
    plt.close()
    print("  Generated: sensitivity_ranking.png")


def plot_heatmaps(df: pd.DataFrame, output_dir: str):
    """Per-node heatmap: parameters vs values, colored by latency."""
    for node in df["node"].unique():
        node_df = df[df["node"] == node]
        params = node_df["parameter"].unique()

        if len(params) == 0:
            continue

        pivot_data = []
        value_labels = {}
        for param in params:
            param_df = node_df[node_df["parameter"] == param].sort_values("value")
            values = param_df["value"].astype(str).values
            latencies = param_df["latency_mean_us"].values
            value_labels[param] = values
            pivot_data.append(latencies)

        max_cols = max(len(v) for v in value_labels.values())

        matrix = np.full((len(params), max_cols), np.nan)
        col_labels = [[] for _ in range(len(params))]
        for i, param in enumerate(params):
            vals = value_labels[param]
            lats = pivot_data[i]
            for j in range(len(vals)):
                matrix[i, j] = lats[j] if j < len(lats) else np.nan
                if j < len(vals):
                    col_labels[i].append(vals[j])

        fig, ax = plt.subplots(figsize=(max(8, max_cols * 2.5), max(4, len(params) * 0.8)))

        im = ax.imshow(matrix, cmap="YlOrRd", aspect="auto")
        cbar = plt.colorbar(im, ax=ax, label="Mean Callback Latency (µs)")

        ax.set_yticks(range(len(params)))
        ax.set_yticklabels(params, fontsize=9)
        ax.set_xticks(range(max_cols))
        ax.set_xticklabels(["Low", "Default", "High"][:max_cols], fontsize=10)
        ax.set_title(f"Latency Heatmap: {node}", fontsize=13, fontweight="bold", pad=10)

        for i in range(len(params)):
            for j in range(max_cols):
                if not np.isnan(matrix[i, j]):
                    label = col_labels[i][j] if j < len(col_labels[i]) else ""
                    text_color = "white" if matrix[i, j] > np.nanmean(matrix) else "black"
                    ax.text(j, i, f"{matrix[i,j]:.0f}\n({label})",
                            ha="center", va="center", fontsize=8, color=text_color)

        fig.tight_layout()
        fig.savefig(os.path.join(output_dir, f"heatmap_{node}.png"), bbox_inches="tight")
        plt.close()

    print(f"  Generated: heatmap_<node>.png (x{len(df['node'].unique())})")


def plot_tornado(df: pd.DataFrame, output_dir: str):
    """Per-node tornado chart: deviation from baseline (default) for low and high values."""
    for node in df["node"].unique():
        node_df = df[df["node"] == node]
        params = node_df["parameter"].unique()

        if len(params) == 0:
            continue

        tornado_data = []
        for param in params:
            param_df = node_df[node_df["parameter"] == param].sort_values("value")
            latencies = param_df["latency_mean_us"].values

            if len(latencies) < 3:
                continue

            baseline = latencies[1]
            low_dev = latencies[0] - baseline
            high_dev = latencies[2] - baseline
            tornado_data.append({
                "parameter": param,
                "low_dev": low_dev,
                "high_dev": high_dev,
                "low_val": param_df["value"].values[0],
                "high_val": param_df["value"].values[2],
                "baseline": baseline,
            })

        if not tornado_data:
            continue

        tornado_data.sort(key=lambda x: abs(x["high_dev"] - x["low_dev"]))

        fig, ax = plt.subplots(figsize=(12, max(4, len(tornado_data) * 0.6)))

        y_pos = range(len(tornado_data))
        for i, td in enumerate(tornado_data):
            ax.barh(i, td["low_dev"], height=0.4, align="center",
                    color="#4ecdc4", alpha=0.8, edgecolor="white", linewidth=0.5)
            ax.barh(i, td["high_dev"], height=0.4, align="center",
                    color="#e94560", alpha=0.8, edgecolor="white", linewidth=0.5)

        ax.set_yticks(y_pos)
        ax.set_yticklabels([td["parameter"] for td in tornado_data], fontsize=9)
        ax.axvline(x=0, color="#f7be16", linewidth=1.5, linestyle="--", label="Default")
        ax.set_xlabel("Latency Deviation from Default (µs)")
        ax.set_title(f"Tornado Chart: {node}\n(Impact of Low vs High parameter values)",
                     fontsize=13, fontweight="bold", pad=10)
        ax.grid(axis="x", alpha=0.3)

        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor="#4ecdc4", alpha=0.8, label="Low value"),
            Patch(facecolor="#e94560", alpha=0.8, label="High value"),
        ]
        ax.legend(handles=legend_elements, loc="best")

        fig.tight_layout()
        fig.savefig(os.path.join(output_dir, f"tornado_{node}.png"), bbox_inches="tight")
        plt.close()

    print(f"  Generated: tornado_<node>.png (x{len(df['node'].unique())})")


def plot_latency_vs_param(df: pd.DataFrame, output_dir: str):
    """Per-node line plots: X = parameter value, Y = latency, one line per parameter."""
    for node in df["node"].unique():
        node_df = df[df["node"] == node]
        params = node_df["parameter"].unique()

        if len(params) == 0:
            continue

        fig, ax = plt.subplots(figsize=(12, 7))

        for i, param in enumerate(params):
            param_df = node_df[node_df["parameter"] == param].copy()
            # Try numeric sort; fall back to string sort for booleans/categoricals
            try:
                param_df["_sort_val"] = param_df["value"].astype(float)
                param_df = param_df.sort_values("_sort_val")
            except (ValueError, TypeError):
                param_df = param_df.sort_values("value")
            raw_values = param_df["value"].values
            latencies = param_df["latency_mean_us"].values

            if len(raw_values) > 0:
                normalized_x = np.linspace(0, 1, len(raw_values))
                color = ACCENT_COLORS[i % len(ACCENT_COLORS)]
                ax.plot(normalized_x, latencies, marker="o", linewidth=2,
                        markersize=8, label=param, color=color)

                for j, (x, y, v) in enumerate(zip(normalized_x, latencies, raw_values)):
                    ax.annotate(f"{v}", (x, y), textcoords="offset points",
                                xytext=(0, 10), ha="center", fontsize=7,
                                color=color)

        ax.set_xticks([0, 0.5, 1.0])
        ax.set_xticklabels(["Low", "Default", "High"])
        ax.set_ylabel("Mean Callback Latency (µs)")
        ax.set_title(f"Latency vs Parameter Values: {node}",
                     fontsize=13, fontweight="bold", pad=10)
        ax.legend(loc="best", fontsize=8, framealpha=0.5)
        ax.grid(alpha=0.3)

        fig.tight_layout()
        fig.savefig(os.path.join(output_dir, f"latency_vs_param_{node}.png"), bbox_inches="tight")
        plt.close()

    print(f"  Generated: latency_vs_param_<node>.png (x{len(df['node'].unique())})")


def plot_pmu_correlation(df: pd.DataFrame, output_dir: str):
    """Scatter matrix: latency vs PMU metrics."""
    pmu_cols = {
        "instructions": "Retired Instructions",
        "l1_miss_rate": "L1 Cache Miss Rate",
        "llc_miss_rate": "LLC (L3) Miss Rate",
        "cache_miss_rate": "Overall Cache Miss Rate",
        "bus_cycles": "Bus Cycles (RAM Traffic)",
    }

    available_pmu = [c for c in pmu_cols if c in df.columns and df[c].sum() > 0]

    if not available_pmu:
        print("  SKIP: No PMU data available for correlation plot")
        return

    n_plots = len(available_pmu)
    cols = min(3, n_plots)
    rows = (n_plots + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 5 * rows))
    if n_plots == 1:
        axes = np.array([axes])
    axes = axes.flatten()

    for i, col in enumerate(available_pmu):
        ax = axes[i]
        valid = df[[col, "latency_mean_us"]].dropna()
        valid = valid[(valid[col] > 0) & (valid["latency_mean_us"] > 0)]

        if len(valid) < 3:
            ax.text(0.5, 0.5, "Insufficient data", ha="center", va="center",
                    transform=ax.transAxes, color="#e0e0e0")
            ax.set_title(pmu_cols[col])
            continue

        node_colors_map = {}
        for node in df["node"].unique():
            idx = list(df["node"].unique()).index(node)
            node_colors_map[node] = ACCENT_COLORS[idx % len(ACCENT_COLORS)]

        for node in valid.merge(df[["node"]], left_index=True, right_index=True)["node"].unique():
            node_mask = df["node"] == node
            node_data = valid.loc[valid.index.intersection(df[node_mask].index)]
            if len(node_data) > 0:
                ax.scatter(node_data[col], node_data["latency_mean_us"],
                           alpha=0.6, s=30, label=node,
                           color=node_colors_map.get(node, "#e0e0e0"))

        ax.set_xlabel(pmu_cols[col], fontsize=9)
        ax.set_ylabel("Latency (µs)", fontsize=9)
        ax.set_title(f"Latency vs {pmu_cols[col]}", fontsize=10, fontweight="bold")
        ax.grid(alpha=0.3)

    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle("PMU Counter Correlations with Callback Latency",
                 fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "pmu_correlation.png"), bbox_inches="tight")
    plt.close()
    print("  Generated: pmu_correlation.png")


def plot_normalized_sensitivity(df: pd.DataFrame, output_dir: str):
    """Normalized sensitivity: percentage change from baseline for each parameter."""
    fig, ax = plt.subplots(figsize=(16, 8))

    node_param_data = []
    for (node, param), group in df.groupby(["node", "parameter"]):
        sorted_g = group.sort_values("value")
        latencies = sorted_g["latency_mean_us"].values
        if len(latencies) >= 3 and latencies[1] > 0:
            pct_change_low = (latencies[0] - latencies[1]) / latencies[1] * 100
            pct_change_high = (latencies[2] - latencies[1]) / latencies[1] * 100
            total_swing = abs(pct_change_high - pct_change_low)
            node_param_data.append({
                "node": node,
                "parameter": param,
                "pct_low": pct_change_low,
                "pct_high": pct_change_high,
                "total_swing": total_swing,
            })

    if not node_param_data:
        plt.close()
        return

    npd = pd.DataFrame(node_param_data).sort_values("total_swing", ascending=False).head(20)

    y_pos = range(len(npd))
    for i, (_, row) in enumerate(npd.iterrows()):
        ax.barh(i, row["pct_low"], height=0.35, align="center",
                color="#4ecdc4", alpha=0.8)
        ax.barh(i, row["pct_high"], height=0.35, align="center",
                color="#e94560", alpha=0.8)

    ax.set_yticks(y_pos)
    ax.set_yticklabels([f"{r['node']} / {r['parameter']}" for _, r in npd.iterrows()], fontsize=8)
    ax.axvline(x=0, color="#f7be16", linewidth=1.5, linestyle="--")
    ax.set_xlabel("% Change from Default")
    ax.set_title("Top 20 Most Sensitive Parameters\n(% Change in Latency from Default)",
                 fontsize=14, fontweight="bold", pad=15)
    ax.grid(axis="x", alpha=0.3)

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#4ecdc4", alpha=0.8, label="Low value"),
        Patch(facecolor="#e94560", alpha=0.8, label="High value"),
    ]
    ax.legend(handles=legend_elements, loc="best")

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "normalized_sensitivity.png"), bbox_inches="tight")
    plt.close()
    print("  Generated: normalized_sensitivity.png")


def main():
    parser = argparse.ArgumentParser(description="Parameter Sweep Analysis")
    parser.add_argument("--input", "-i",
                        default=str(Path(__file__).parent.parent / "experiments" /
                                    "6_parameter_sweep" / "tables" / "raw_results.csv"),
                        help="Path to raw_results.csv")
    parser.add_argument("--output-dir", "-o",
                        default=str(Path(__file__).parent.parent / "experiments" /
                                    "6_parameter_sweep"),
                        help="Base output directory")
    args = parser.parse_args()

    csv_path = args.input
    base_dir = args.output_dir
    graph_dir = os.path.join(base_dir, "graphs")
    table_dir = os.path.join(base_dir, "tables")
    os.makedirs(graph_dir, exist_ok=True)
    os.makedirs(table_dir, exist_ok=True)

    print("=" * 60)
    print("  Parameter Sweep Analysis")
    print("=" * 60)
    print(f"  Input:  {csv_path}")
    print(f"  Output: {base_dir}")
    print()

    if not os.path.exists(csv_path):
        print(f"ERROR: Input file not found: {csv_path}")
        sys.exit(1)

    df = load_data(csv_path)
    print(f"  Loaded {len(df)} rows, {df['node'].nunique()} nodes, "
          f"{df['parameter'].nunique()} parameters")

    df_valid = df[df["latency_mean_us"] > 0].copy()
    if len(df_valid) == 0:
        print("ERROR: No valid latency data (all zeros)")
        sys.exit(1)

    print(f"  Valid rows (latency > 0): {len(df_valid)}")
    print()

    print("Computing summary statistics...")
    summary = compute_summary(df_valid)
    summary_path = os.path.join(table_dir, "parameter_sensitivity.csv")
    summary.to_csv(summary_path, index=False, float_format="%.2f")
    print(f"  Wrote: {summary_path}")
    print()

    print("Generating visualizations...")
    plot_violin_all_nodes(df_valid, graph_dir)
    plot_boxplot_all_nodes(df_valid, graph_dir)
    plot_sensitivity_ranking(df_valid, graph_dir)
    plot_heatmaps(df_valid, graph_dir)
    plot_tornado(df_valid, graph_dir)
    plot_latency_vs_param(df_valid, graph_dir)
    plot_normalized_sensitivity(df_valid, graph_dir)
    plot_pmu_correlation(df_valid, graph_dir)

    print()
    print("=" * 60)
    print("  Analysis Complete")
    print("=" * 60)
    print(f"  Summary table: {summary_path}")
    print(f"  Graphs:        {graph_dir}/")
    print()

    print("Summary by node:")
    for _, row in summary.iterrows():
        print(f"  {row['node']:40s}  "
              f"mean={row['latency_mean_us']:10.1f}µs  "
              f"range={row['latency_range_us']:10.1f}µs  "
              f"CV={row['latency_cv']:.3f}")


if __name__ == "__main__":
    main()
