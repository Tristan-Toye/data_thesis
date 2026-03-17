#!/usr/bin/env python3
"""
Analyze LLVM IR files generated with the miniperf Clang plugin to extract
per-function operation counts and compute arithmetic intensity for the
architecture-agnostic roofline model.

Outputs to experiments/5_miniperf_roofline/
"""

import csv
import re
import os
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

SCRIPT_DIR = Path(__file__).parent
IR_DIR = SCRIPT_DIR.parent / "experiments" / "5_miniperf_roofline" / "ir_output"
TABLES_DIR = SCRIPT_DIR.parent / "experiments" / "5_miniperf_roofline" / "tables"
GRAPHS_DIR = SCRIPT_DIR.parent / "experiments" / "5_miniperf_roofline" / "graphs"

TABLES_DIR.mkdir(parents=True, exist_ok=True)
GRAPHS_DIR.mkdir(parents=True, exist_ok=True)

PEAK_FP32_GFLOPS = 105.6
PEAK_FP32_SIMD_GFLOPS = 422.4
PEAK_FP64_GFLOPS = 52.8
PEAK_MEM_BW_GBPS = 204.8

RE_FADD = re.compile(r"\b(fadd|fsub)\b")
RE_FMUL = re.compile(r"\bfmul\b")
RE_FDIV = re.compile(r"\bfdiv\b")
RE_FREM = re.compile(r"\bfrem\b")
RE_FMA = re.compile(r"\b(llvm\.fmuladd|llvm\.fma)\b")
RE_FCMP = re.compile(r"\bfcmp\b")
RE_LOAD = re.compile(r"= load\b")
RE_STORE = re.compile(r"\bstore\b.*,")
RE_INTOP = re.compile(r"\b(add|sub|mul|shl|lshr|ashr|and|or|xor)\b\s+(nsw\s+|nuw\s+)*i\d+")
RE_FUNC_DEF = re.compile(r"^define\b.*@([^\(]+)\(")
RE_LOAD_TYPE = re.compile(r"= load\s+(\S+),")
RE_STORE_TYPE = re.compile(r"store\s+(\S+)\s+")
RE_VEC_TYPE = re.compile(r"<(\d+)\s+x\s+(float|double|i\d+)>")

TYPE_SIZES = {
    "i1": 1, "i8": 1, "i16": 2, "i32": 4, "i64": 8, "i128": 16,
    "float": 4, "double": 8, "half": 2, "bfloat": 2, "ptr": 8,
}


def get_type_bytes(type_str: str) -> int:
    vec_m = RE_VEC_TYPE.match(type_str)
    if vec_m:
        return int(vec_m.group(1)) * TYPE_SIZES.get(vec_m.group(2), 4)
    for k, v in TYPE_SIZES.items():
        if type_str.startswith(k):
            return v
    return 4


def analyze_ir_file(ir_path: Path) -> list[dict]:
    results = []
    current_func = None
    func_stats = {}

    with open(ir_path) as f:
        for line in f:
            func_m = RE_FUNC_DEF.match(line)
            if func_m:
                if current_func and func_stats:
                    results.append({"function": current_func, **func_stats})
                current_func = func_m.group(1).strip('"')
                func_stats = {
                    "fp_add_sub": 0, "fp_mul": 0, "fp_div": 0, "fp_fma": 0,
                    "fp_cmp": 0, "fp_rem": 0, "int_ops": 0,
                    "load_bytes": 0, "store_bytes": 0,
                    "load_count": 0, "store_count": 0,
                }
                continue

            if current_func is None:
                continue
            if line.strip().startswith(";") or line.strip() == "":
                continue
            if line.startswith("}"):
                if current_func and func_stats:
                    results.append({"function": current_func, **func_stats})
                current_func = None
                func_stats = {}
                continue

            func_stats["fp_add_sub"] += len(RE_FADD.findall(line))
            func_stats["fp_mul"] += len(RE_FMUL.findall(line))
            func_stats["fp_div"] += len(RE_FDIV.findall(line))
            func_stats["fp_rem"] += len(RE_FREM.findall(line))
            func_stats["fp_fma"] += len(RE_FMA.findall(line))
            func_stats["fp_cmp"] += len(RE_FCMP.findall(line))
            func_stats["int_ops"] += len(RE_INTOP.findall(line))

            for load_m in RE_LOAD_TYPE.finditer(line):
                func_stats["load_bytes"] += get_type_bytes(load_m.group(1))
                func_stats["load_count"] += 1
            for store_m in RE_STORE_TYPE.finditer(line):
                func_stats["store_bytes"] += get_type_bytes(store_m.group(1))
                func_stats["store_count"] += 1

    return results


def compute_metrics(fd: dict) -> dict:
    flops = (fd["fp_add_sub"] + fd["fp_mul"] + fd["fp_div"] + fd["fp_rem"] +
             fd["fp_fma"] * 2 + fd["fp_cmp"])
    mem_bytes = fd["load_bytes"] + fd["store_bytes"]
    ai = flops / mem_bytes if mem_bytes > 0 else 0.0
    return {
        "total_flops": flops,
        "total_int_ops": fd["int_ops"],
        "total_mem_bytes": mem_bytes,
        "arithmetic_intensity": ai,
    }


def demangle_short(name: str) -> str:
    """Extract a readable function name from mangled C++ name."""
    parts = name.split("::")
    if len(parts) > 1:
        return parts[-1][:40]
    m = re.search(r'_Z\w*\d+(\w+)', name)
    if m:
        return m.group(1)[:40]
    return name[:40]


print("=" * 60)
print("  LLVM IR Roofline Analysis")
print("=" * 60)

# ── Analyze all IR files ──────────────────────────────────────────────
all_node_data = []
all_funcs = []

for node_dir in sorted(IR_DIR.iterdir()):
    if not node_dir.is_dir() or node_dir.name.startswith("."):
        continue

    node_name = node_dir.name
    node_flops = node_int_ops = node_mem_bytes = 0
    node_load_bytes = node_store_bytes = 0
    node_files = node_functions = 0
    fp_functions = 0

    for ir_file in sorted(node_dir.glob("*.ll")):
        funcs = analyze_ir_file(ir_file)
        node_files += 1

        for fd in funcs:
            metrics = compute_metrics(fd)
            if metrics["total_flops"] > 0 or metrics["total_int_ops"] > 0:
                node_functions += 1
                node_flops += metrics["total_flops"]
                node_int_ops += metrics["total_int_ops"]
                node_mem_bytes += metrics["total_mem_bytes"]
                node_load_bytes += fd["load_bytes"]
                node_store_bytes += fd["store_bytes"]
                if metrics["total_flops"] > 0:
                    fp_functions += 1

                if metrics["total_flops"] >= 3:
                    all_funcs.append({
                        "node": node_name,
                        "source": ir_file.stem,
                        "function": fd["function"][:100],
                        **metrics,
                    })

    if node_flops > 0 or node_int_ops > 0:
        ai = node_flops / node_mem_bytes if node_mem_bytes > 0 else 0.0
        all_node_data.append({
            "node": node_name,
            "files": node_files,
            "functions": node_functions,
            "fp_functions": fp_functions,
            "total_flops": node_flops,
            "total_int_ops": node_int_ops,
            "total_mem_bytes": node_mem_bytes,
            "load_bytes": node_load_bytes,
            "store_bytes": node_store_bytes,
            "arithmetic_intensity": ai,
        })
        print(f"  {node_name}: {node_flops} FLOPs, {node_int_ops} int ops, "
              f"{node_mem_bytes} bytes, AI={ai:.4f}, {fp_functions} FP funcs")

# ── Write per-node CSV ────────────────────────────────────────────────
csv_path = TABLES_DIR / "ir_roofline_nodes.csv"
with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=[
        "node", "files", "functions", "fp_functions", "total_flops",
        "total_int_ops", "total_mem_bytes", "load_bytes", "store_bytes",
        "arithmetic_intensity",
    ])
    w.writeheader()
    w.writerows(all_node_data)
print(f"\nWrote {csv_path} ({len(all_node_data)} nodes)")

# ── Write per-function CSV ────────────────────────────────────────────
all_funcs.sort(key=lambda x: x["total_flops"], reverse=True)
func_csv = TABLES_DIR / "ir_roofline_functions.csv"
with open(func_csv, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=[
        "node", "source", "function", "total_flops", "total_int_ops",
        "total_mem_bytes", "arithmetic_intensity",
    ])
    w.writeheader()
    w.writerows(all_funcs[:500])
print(f"Wrote {func_csv} ({min(len(all_funcs), 500)} functions)")

if not all_node_data:
    print("No data for plots.")
    exit(0)

ridge_fp32_scalar = PEAK_FP32_GFLOPS / PEAK_MEM_BW_GBPS
ridge_fp64 = PEAK_FP64_GFLOPS / PEAK_MEM_BW_GBPS

# ── Plot 1: Roofline with per-function hotspots ──────────────────────
fig, ax = plt.subplots(figsize=(14, 9))
fig.patch.set_facecolor("#1a1a2e")
ax.set_facecolor("#16213e")

ai_range = np.logspace(-3, 2, 500)

roof_fp32 = np.minimum(PEAK_MEM_BW_GBPS * ai_range, PEAK_FP32_GFLOPS)
roof_simd = np.minimum(PEAK_MEM_BW_GBPS * ai_range, PEAK_FP32_SIMD_GFLOPS)
roof_fp64 = np.minimum(PEAK_MEM_BW_GBPS * ai_range, PEAK_FP64_GFLOPS)

ax.plot(ai_range, roof_simd, color="#ff6b6b", lw=2, ls="--", alpha=0.6,
        label=f"FP32 SIMD ceiling ({PEAK_FP32_SIMD_GFLOPS} GFLOP/s)")
ax.plot(ai_range, roof_fp32, color="#feca57", lw=2.5,
        label=f"FP32 scalar ceiling ({PEAK_FP32_GFLOPS} GFLOP/s)")
ax.plot(ai_range, roof_fp64, color="#48dbfb", lw=2, ls="-.",
        label=f"FP64 scalar ceiling ({PEAK_FP64_GFLOPS} GFLOP/s)")

ax.axvline(x=ridge_fp32_scalar, color="#feca57", ls=":", alpha=0.4)
ax.text(ridge_fp32_scalar * 1.1, 0.05, f"Ridge FP32\n({ridge_fp32_scalar:.2f})",
        color="#feca57", fontsize=7, alpha=0.7)

node_colors = {}
cmap = plt.cm.get_cmap("tab20", len(all_node_data))
for i, nd in enumerate(sorted(all_node_data, key=lambda x: x["total_flops"], reverse=True)):
    node_colors[nd["node"]] = cmap(i)

fp_funcs = [f for f in all_funcs if f["total_flops"] >= 10 and f["total_mem_bytes"] > 0]

for fd in fp_funcs:
    ai = fd["arithmetic_intensity"]
    if ai <= 0:
        continue
    attainable = min(PEAK_MEM_BW_GBPS * ai, PEAK_FP64_GFLOPS)
    color = node_colors.get(fd["node"], "white")
    size = max(20, min(200, fd["total_flops"] * 0.8))
    ax.scatter(ai, attainable * 0.5, s=size, color=color,
               edgecolors="white", linewidth=0.3, alpha=0.7, zorder=4)

for nd in all_node_data:
    ai = nd["arithmetic_intensity"]
    if ai <= 0:
        ai = 0.0005
    attainable = min(PEAK_MEM_BW_GBPS * ai, PEAK_FP64_GFLOPS)
    color = node_colors[nd["node"]]
    ax.scatter(ai, attainable * 0.3, s=200, color=color,
               edgecolors="white", linewidth=1.5, marker="D", zorder=6)
    ax.annotate(nd["node"].replace("_", " "), (ai, attainable * 0.3),
                textcoords="offset points", xytext=(8, 5),
                fontsize=7, color="white", alpha=0.9,
                fontweight="bold")

handles = [mpatches.Patch(color=node_colors[nd["node"]], label=nd["node"])
           for nd in sorted(all_node_data, key=lambda x: x["total_flops"], reverse=True)[:10]]
legend1 = ax.legend(handles=handles, loc="lower right", fontsize=7,
                    title="Nodes", title_fontsize=8,
                    facecolor="#1a1a2e", edgecolor="#555", labelcolor="white")
legend1.get_title().set_color("white")
ax.add_artist(legend1)
ax.legend(loc="upper left", fontsize=8, facecolor="#1a1a2e",
          edgecolor="#555", labelcolor="white")

ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("Arithmetic Intensity (FLOPs / Byte)", fontsize=12, color="white")
ax.set_ylabel("Attainable Performance (GFLOP/s)", fontsize=12, color="white")
ax.set_title("Architecture-Agnostic Roofline Model\n"
             "Autoware Top-15 Nodes – Static LLVM IR Analysis (miniperf Plugin)\n"
             "Nvidia Jetson Orin AGX (12× Cortex-A78AE @ 2.2 GHz, LPDDR5 204.8 GB/s)",
             fontsize=11, fontweight="bold", color="white")
ax.tick_params(colors="white")
ax.grid(True, which="both", alpha=0.15, color="white")
ax.set_xlim(1e-4, 100)
ax.set_ylim(0.01, 600)
for spine in ax.spines.values():
    spine.set_color("#555")

fig.tight_layout()
out = GRAPHS_DIR / "roofline_plot.png"
fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close(fig)
print(f"\nWrote {out}")

# ── Plot 2: AI per node bar chart ─────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 7))
sorted_nodes = sorted(all_node_data, key=lambda x: x["arithmetic_intensity"], reverse=True)
names = [n["node"].replace("_", " ") for n in sorted_nodes]
ais = [n["arithmetic_intensity"] for n in sorted_nodes]

colors = ["#e74c3c" if ai > ridge_fp32_scalar else "#3498db" for ai in ais]
bars = ax.barh(range(len(names)), ais, color=colors, edgecolor="white", height=0.7)
ax.set_yticks(range(len(names)))
ax.set_yticklabels(names, fontsize=9)
ax.invert_yaxis()
ax.set_xlabel("Aggregate Arithmetic Intensity (FLOPs / Byte)", fontsize=11)
ax.set_title("Arithmetic Intensity per Node (Static LLVM IR Analysis)",
             fontsize=13, fontweight="bold")
ax.axvline(x=ridge_fp32_scalar, color="red", ls="--", alpha=0.6,
           label=f"Ridge point FP32 scalar ({ridge_fp32_scalar:.2f})")
ax.axvline(x=ridge_fp64, color="blue", ls="--", alpha=0.4,
           label=f"Ridge point FP64 ({ridge_fp64:.2f})")
ax.legend(fontsize=8)

for i, (ai_val, nd) in enumerate(zip(ais, sorted_nodes)):
    label = f"AI={ai_val:.4f}  ({nd['total_flops']}F / {nd['total_mem_bytes']}B)"
    ax.text(max(ais) * 1.02, i, label, va="center", fontsize=7)

ax.set_xlim(0, max(ais) * 1.5)
fig.tight_layout()
out = GRAPHS_DIR / "ai_per_node.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Wrote {out}")

# ── Plot 3: Ops breakdown ────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

sorted_by_ops = sorted(all_node_data, key=lambda x: x["total_flops"] + x["total_int_ops"], reverse=True)
names = [n["node"].replace("_", " ") for n in sorted_by_ops]
flops = [n["total_flops"] for n in sorted_by_ops]
int_ops = [n["total_int_ops"] for n in sorted_by_ops]
y = np.arange(len(names))

ax1.barh(y, flops, color="#e74c3c", label="FP ops", height=0.4, align="edge")
ax1.barh(y - 0.4, int_ops, color="#3498db", label="Int ops", height=0.4, align="edge")
ax1.set_yticks(y)
ax1.set_yticklabels(names, fontsize=8)
ax1.invert_yaxis()
ax1.set_xlabel("Static Operation Count")
ax1.set_title("Operation Breakdown (FP vs Int)", fontsize=12, fontweight="bold")
ax1.legend()

loads = [n["load_bytes"] for n in sorted_by_ops]
stores = [n["store_bytes"] for n in sorted_by_ops]
ax2.barh(y, loads, color="#27ae60", label="Load bytes", height=0.4, align="edge")
ax2.barh(y - 0.4, stores, color="#f39c12", label="Store bytes", height=0.4, align="edge")
ax2.set_yticks(y)
ax2.set_yticklabels(names, fontsize=8)
ax2.invert_yaxis()
ax2.set_xlabel("Memory Bytes (per compilation unit)")
ax2.set_title("Memory Access Breakdown", fontsize=12, fontweight="bold")
ax2.legend()

fig.suptitle("Static LLVM IR Operation & Memory Analysis – Autoware Top-15 Nodes",
             fontsize=13, fontweight="bold")
fig.tight_layout()
out = GRAPHS_DIR / "ops_breakdown.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Wrote {out}")

# ── Plot 4: Top FP hotspot functions roofline ─────────────────────────
fig, ax = plt.subplots(figsize=(14, 8))

top_funcs = sorted([f for f in all_funcs if f["total_flops"] >= 20 and f["total_mem_bytes"] > 0],
                   key=lambda x: x["total_flops"], reverse=True)[:50]

for fd in top_funcs:
    ai = fd["arithmetic_intensity"]
    attainable = min(PEAK_MEM_BW_GBPS * ai, PEAK_FP64_GFLOPS)
    color = node_colors.get(fd["node"], "gray")
    size = max(30, fd["total_flops"] * 1.5)
    ax.scatter(ai, attainable * 0.5, s=size, color=color,
               edgecolors="black", linewidth=0.5, alpha=0.8, zorder=4)

ai_range2 = np.logspace(-2, 2, 500)
ax.plot(ai_range2, np.minimum(PEAK_MEM_BW_GBPS * ai_range2, PEAK_FP64_GFLOPS),
        "k-", lw=2, label=f"FP64 ceiling ({PEAK_FP64_GFLOPS} GFLOP/s)")
ax.plot(ai_range2, np.minimum(PEAK_MEM_BW_GBPS * ai_range2, PEAK_FP32_GFLOPS),
        "k--", lw=1.5, alpha=0.5, label=f"FP32 ceiling ({PEAK_FP32_GFLOPS} GFLOP/s)")

ax.axvline(x=ridge_fp64, color="gray", ls=":", alpha=0.5)
ax.text(ridge_fp64 * 1.1, 0.5, f"Ridge FP64\n({ridge_fp64:.2f})", fontsize=7, alpha=0.7)

handles = [mpatches.Patch(color=node_colors[n], label=n) for n in
           sorted(set(f["node"] for f in top_funcs))]
ax.legend(handles=handles, loc="lower right", fontsize=7, title="Node")

ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("Arithmetic Intensity (FLOPs / Byte)", fontsize=11)
ax.set_ylabel("Attainable Performance (GFLOP/s)", fontsize=11)
ax.set_title("Top-50 FP Hotspot Functions – Roofline (Static IR Analysis)",
             fontsize=12, fontweight="bold")
ax.grid(True, which="both", alpha=0.2)
ax.set_xlim(0.01, 100)
ax.set_ylim(0.1, 200)

fig.tight_layout()
out = GRAPHS_DIR / "hotspot_roofline.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Wrote {out}")

# ── Plot 5: FP/Int ratio pie chart ───────────────────────────────────
total_fp = sum(n["total_flops"] for n in all_node_data)
total_int = sum(n["total_int_ops"] for n in all_node_data)
total_load = sum(n["load_bytes"] for n in all_node_data)
total_store = sum(n["store_bytes"] for n in all_node_data)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

wedges, texts, autotexts = ax1.pie(
    [total_fp, total_int],
    labels=["Floating-Point Ops", "Integer Ops"],
    colors=["#e74c3c", "#3498db"],
    autopct="%1.1f%%", startangle=90, pctdistance=0.75
)
ax1.set_title("FP vs Integer Operations\n(All Nodes Combined)", fontweight="bold")

wedges, texts, autotexts = ax2.pie(
    [total_load, total_store],
    labels=["Load Bytes", "Store Bytes"],
    colors=["#27ae60", "#f39c12"],
    autopct="%1.1f%%", startangle=90, pctdistance=0.75
)
ax2.set_title("Load vs Store Bytes\n(All Nodes Combined)", fontweight="bold")

fig.suptitle("Aggregate Operation Mix – LLVM IR Static Analysis", fontweight="bold")
fig.tight_layout()
out = GRAPHS_DIR / "operation_mix.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Wrote {out}")

print("\nDone.")
