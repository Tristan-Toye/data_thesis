# Experiment 7: Roofline Drafting

Builds the roofline model for the NVIDIA Jetson Orin AGX 64GB using specs extracted from the official datasheet, and overlays experiment 6 parameter sweep results.

## Datasheet Sources

- `orin_datasheet/Jetson-AGX-Orin-Data-Sheet_DS-10662-001_v1.8.pdf`
- `orin_datasheet/nvidia-jetson-agx-orin-technical-brief.pdf`

See [orin_datasheet_extract.md](orin_datasheet_extract.md) for documented values and citations.

## Hardware Ceilings (Orin AGX 64GB)

| Parameter | Value |
|---|---|
| Peak FP32 SIMD | 422.4 GFLOPs/s |
| Peak FP32 scalar | 105.6 GFLOPs/s |
| Memory bandwidth | 204.8 GB/s |
| Ridge point (SIMD) | 2.06 FLOPs/byte |

## Usage

### Standalone roofline (hardware ceilings only)

```bash
python3 plot_roofline_standalone.py [--output-dir DIR]
```

### Roofline with experiment 6 data

```bash
python3 plot_roofline_with_experiment6.py [--input CSV] [--output-dir DIR]
```

- `--input`: Path to `raw_results.csv` from experiment 6 (default: `../../experiments/6_parameter_sweep/tables/raw_results.csv`)
- `--output-dir`: Output directory for PNG files (default: `../../experiments/7_roofline_drafting/graphs/`)

## Output

- `experiments/7_roofline_drafting/graphs/roofline_standalone.png` — Roofline only
- `experiments/7_roofline_drafting/graphs/roofline_with_experiment6.png` — Roofline + experiment 6 scatter points

## Experiment 6 Mapping

For each run in `raw_results.csv`:

- **Performance (GFLOPs/s)** = `instructions / total_time_sec / 1e9` (1 instruction ≈ 1 FLOP)
- **Total time** = `latency_mean_us * callback_count / 1e6` seconds
- **Arithmetic Intensity** = `instructions / (cache_misses * 64)` FLOPs/byte (64-byte cache line)

Rows with `callback_count == 0`, `latency_mean_us == 0`, or `cache_misses == 0` are excluded.
