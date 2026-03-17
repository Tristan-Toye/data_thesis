#!/usr/bin/env python3
"""
Roofline Model — Standalone (Orin AGX)
======================================
Generates a roofline visualization using Jetson Orin AGX specs from the datasheet.
No data points — hardware ceilings only.

Usage: python3 plot_roofline_standalone.py [--output-dir DIR]
"""

import argparse
import sys
from pathlib import Path

try:
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import yaml
except ImportError as e:
    print(f"ERROR: Required package not found: {e}")
    print("Install with: pip install numpy matplotlib pyyaml")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent
SCRIPTS_ROOT = SCRIPT_DIR.parent.parent  # scripts/
CONFIG_FILE = SCRIPT_DIR / "orin_roofline_config.yaml"
DEFAULT_OUTPUT = SCRIPTS_ROOT / "experiments" / "7_roofline_drafting" / "graphs"


def load_config() -> dict:
    with open(CONFIG_FILE, "r") as f:
        return yaml.safe_load(f)


def plot_roofline(output_dir: Path) -> None:
    cfg = load_config()
    hw = cfg.get("hardware", {})
    cpu = hw.get("cpu", {})
    peak_bw = cpu.get("peak_memory_bandwidth_GBps", 204.8)
    peak_flops = cpu.get("peak_fp32_simd_gflops", 422.4)
    ridge_ai = peak_flops / peak_bw

    # AI range for roofline
    ai_min, ai_max = 0.01, 100
    ai_range = np.logspace(np.log10(ai_min), np.log10(ai_max), 500)
    roofline = np.minimum(peak_flops, ai_range * peak_bw)

    # Dark theme (match experiment 4)
    fig, ax = plt.subplots(figsize=(14, 9))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    # Draw roofline
    ax.plot(ai_range, roofline, color="#00d4ff", linewidth=2.5,
            label=f"Peak FP32 SIMD: {peak_flops:.0f} GFLOPs/s", zorder=3)

    # Ridge point annotation
    ax.axvline(ridge_ai, color="#f39c12", linewidth=1.2, linestyle=":",
               alpha=0.7, zorder=2)
    ax.text(ridge_ai * 1.05, peak_flops * 0.6,
            f"Ridge\n{ridge_ai:.2f} FLOPs/B",
            color="#f39c12", fontsize=9, va="center")

    # Memory bandwidth slope label
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
    ax.set_title(
        "Roofline Model — Jetson Orin AGX 64GB\n"
        "ARM Cortex-A78AE × 12 @ 2.2 GHz  |  LPDDR5 204.8 GB/s",
        color="white", fontsize=13, pad=14,
    )
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#444466")
    ax.grid(True, which="both", color="#2a2a4a", linewidth=0.5, alpha=0.6)
    ax.legend(loc="lower right", facecolor="#1a1a2e", edgecolor="#555577",
              labelcolor="white", fontsize=9)

    plt.tight_layout()

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "roofline_standalone.png"
    plt.savefig(out_path, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Saved: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Plot standalone roofline (Orin AGX)")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT,
                        help="Output directory for graphs")
    args = parser.parse_args()

    print("=" * 60)
    print("Roofline Model — Standalone (Orin AGX)")
    print("=" * 60)
    cfg = load_config()
    hw = cfg.get("hardware", {})
    cpu = hw.get("cpu", {})
    print(f"\nHardware: {hw.get('name', 'unknown')}")
    print(f"  Peak FP32 SIMD: {cpu.get('peak_fp32_simd_gflops', 422.4)} GFLOPs/s")
    print(f"  Peak BW: {cpu.get('peak_memory_bandwidth_GBps', 204.8)} GB/s")
    print(f"  Ridge point: {422.4 / 204.8:.2f} FLOPs/byte")
    print("\nGenerating roofline plot...")
    plot_roofline(args.output_dir)
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
