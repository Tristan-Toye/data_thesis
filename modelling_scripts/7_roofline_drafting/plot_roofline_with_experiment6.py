#!/usr/bin/env python3
"""
Roofline Model with Experiment 6 Data
======================================
Overlays experiment 6 parameter sweep results (completion times, instructions,
cache misses) onto the Jetson Orin AGX roofline model.

Each run yields (AI, Performance) where:
  AI = instructions / (cache_misses * 64)
  Performance = instructions / total_time_sec / 1e9  (GFLOPs/s, 1 instr ≈ 1 FLOP)

Usage: python3 plot_roofline_with_experiment6.py [--input CSV] [--output-dir DIR]
"""

import argparse
import sys
from pathlib import Path

try:
    import numpy as np
    import pandas as pd
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import yaml
except ImportError as e:
    print(f"ERROR: Required package not found: {e}")
    print("Install with: pip install numpy pandas matplotlib pyyaml")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent
SCRIPTS_ROOT = SCRIPT_DIR.parent.parent  # scripts/
DEFAULT_CONFIG = SCRIPT_DIR / "orin_roofline_config.yaml"
DEFAULT_INPUT = SCRIPTS_ROOT / "experiments" / "6_parameter_sweep" / "tables" / "raw_results.csv"
DEFAULT_OUTPUT = SCRIPTS_ROOT / "experiments" / "7_roofline_drafting" / "graphs"

ACCENT_COLORS = [
    "#e94560", "#0f3460", "#533483", "#16c79a", "#f7be16",
    "#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#ffeaa7",
    "#dfe6e9", "#74b9ff", "#a29bfe", "#fd79a8", "#55efc4",
]


def load_config(path: Path) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_experiment6_data(csv_path: Path) -> pd.DataFrame:
    """Load raw_results.csv and compute AI and Performance per run."""
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()

    # Filter invalid rows
    df = df[
        (df["callback_count"] > 0) &
        (df["latency_mean_us"] > 0) &
        (df["cache_misses"] > 0) &
        (df["instructions"] > 0)
    ].copy()

    # Total time in seconds
    df["total_time_sec"] = (df["latency_mean_us"] * df["callback_count"]) / 1e6

    # Performance (GFLOPs/s): instructions / time / 1e9 (1 instr ≈ 1 FLOP)
    df["performance_gflops"] = df["instructions"] / df["total_time_sec"] / 1e9

    # Bytes transferred (cache line = 64 bytes)
    df["bytes"] = df["cache_misses"] * 64

    # Arithmetic Intensity (FLOPs/byte)
    df["arithmetic_intensity"] = df["instructions"] / df["bytes"]

    return df


def _compute_roofline_curves(cfg: dict):
    hw = cfg.get("hardware", {})
    cpu = hw.get("cpu", {})
    peak_bw = cpu.get("peak_memory_bandwidth_GBps", 204.8)
    peak_flops = cpu.get("peak_fp32_simd_gflops", 422.4)
    ridge_ai = peak_flops / peak_bw

    # AI range for roofline
    ai_min, ai_max = 0.01, 100
    ai_range = np.logspace(np.log10(ai_min), np.log10(ai_max), 500)
    roofline = np.minimum(peak_flops, ai_range * peak_bw)
    return peak_bw, peak_flops, ridge_ai, ai_range, roofline


def _base_roofline_axes(peak_bw, peak_flops, ridge_ai, ai_range, roofline, title_suffix: str = ""):
    """Create a roofline figure/axes with shared styling."""

    # Dark theme
    fig, ax = plt.subplots(figsize=(14, 9))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    # Draw roofline
    ax.plot(ai_range, roofline, color="#00d4ff", linewidth=2.5,
            label=f"Peak FP32 SIMD: {peak_flops:.0f} GFLOPs/s", zorder=3)

    # Ridge point
    ax.axvline(ridge_ai, color="#f39c12", linewidth=1.2, linestyle=":",
               alpha=0.7, zorder=2)
    ax.text(ridge_ai * 1.05, peak_flops * 0.6,
            f"Ridge\n{ridge_ai:.2f} FLOPs/B",
            color="#f39c12", fontsize=9, va="center")

    # Memory BW label
    slope_x = ai_range[int(len(ai_range) * 0.05)]
    slope_y = slope_x * peak_bw
    ax.text(slope_x * 1.5, slope_y * 0.7,
            f"Memory BW\n{peak_bw:.0f} GB/s",
            color="#00d4ff", fontsize=9, alpha=0.8, rotation=30)

    # Axes & styling
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Arithmetic Intensity (FLOPs / byte)", color="white", fontsize=12, labelpad=8)
    ax.set_ylabel("Performance (GFLOPs/s)", color="white", fontsize=12, labelpad=8)
    title = "Roofline Model — Jetson Orin AGX"
    if title_suffix:
        title += f"  |  {title_suffix}"
    ax.set_title(title, color="white", fontsize=13, pad=14)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#444466")
    ax.grid(True, which="both", color="#2a2a4a", linewidth=0.5, alpha=0.6)
    return fig, ax


def plot_roofline_with_data(df: pd.DataFrame, output_dir: Path, cfg: dict) -> None:
    peak_bw, peak_flops, ridge_ai, ai_range, roofline = _compute_roofline_curves(cfg)

    # ── All-nodes plot ─────────────────────────────────────────────────────
    fig, ax = _base_roofline_axes(
        peak_bw, peak_flops, ridge_ai, ai_range, roofline,
        title_suffix="Experiment 6 Parameter Sweep",
    )

    # Scatter: experiment 6 points by node
    nodes = df["node"].unique()
    node_to_color = {n: ACCENT_COLORS[i % len(ACCENT_COLORS)] for i, n in enumerate(nodes)}

    for node in nodes:
        node_df = df[df["node"] == node]
        color = node_to_color[node]
        ax.scatter(
            node_df["arithmetic_intensity"],
            node_df["performance_gflops"],
            s=50, color=color, alpha=0.7, edgecolors="white",
            linewidths=0.5, zorder=5, label=node,
        )

    # Legend: roofline + nodes (compact)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc="lower right", facecolor="#1a1a2e",
              edgecolor="#555577", labelcolor="white", fontsize=7, ncol=2)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "roofline_with_experiment6.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Saved: {out_path}")

    # ── Per-node plots ─────────────────────────────────────────────────────
    for node in nodes:
        node_df = df[df["node"] == node]
        if node_df.empty:
            continue

        fig_n, ax_n = _base_roofline_axes(
            peak_bw, peak_flops, ridge_ai, ai_range, roofline,
            title_suffix=f"Experiment 6 — {node}",
        )

        color = node_to_color[node]
        ax_n.scatter(
            node_df["arithmetic_intensity"],
            node_df["performance_gflops"],
            s=60, color=color, alpha=0.9, edgecolors="white",
            linewidths=0.6, zorder=5, label=node,
        )

        # Simple legend for the node
        ax_n.legend(loc="lower right", facecolor="#1a1a2e",
                    edgecolor="#555577", labelcolor="white", fontsize=8)

        plt.tight_layout()
        safe_node = node.replace("/", "_")
        node_out = output_dir / f"roofline_with_experiment6_{safe_node}.png"
        plt.savefig(node_out, dpi=180, bbox_inches="tight", facecolor=fig_n.get_facecolor())
        plt.close()
        print(f"  Saved: {node_out}")


def main():
    parser = argparse.ArgumentParser(description="Plot roofline with experiment 6 data")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="YAML config file with hardware ceilings",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Path to raw_results.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output directory for graphs",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Roofline Model with Experiment 6 Data")
    print("=" * 60)

    if not args.input.exists():
        print(f"ERROR: Input file not found: {args.input}")
        sys.exit(1)

    cfg = load_config(args.config)
    print(f"\nConfig:  {args.config}")
    print(f"Loading: {args.input}")
    df = load_experiment6_data(args.input)
    print(f"  Valid rows: {len(df)}")
    print(f"  Nodes: {df['node'].nunique()}")

    print("\nGenerating roofline + experiment 6 plot...")
    plot_roofline_with_data(df, args.output_dir, cfg)
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
