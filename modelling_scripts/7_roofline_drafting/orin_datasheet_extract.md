# Orin Datasheet Extract for Roofline Model

Values extracted from the NVIDIA Jetson AGX Orin datasheets for building the roofline model.
All values are for the **Jetson AGX Orin 64GB** (JAO 64GB) configuration.

## Source Files

- `orin_datasheet/Jetson-AGX-Orin-Data-Sheet_DS-10662-001_v1.8.pdf`
- `orin_datasheet/nvidia-jetson-agx-orin-technical-brief.pdf`

---

## Direct Extractions from Datasheet

| Roofline parameter | Value | Source (datasheet) |
|---|---|---|
| Memory bandwidth | 204.8 GB/s | DS-10662-001: "Maximum Memory Bus Bandwidth (up to) 204.8 GB/s" (Section 4.10 Jetson AGX Orin SOM Memory, LPDDR5 section) |
| LPDDR5 config | 256-bit, 3200 MHz | DS-10662-001: "64GB 256-bit LPDDR5 DRAM", "Maximum operating frequency: 3200 MHz" (Table 1-2, Section 4.10) |
| CPU | 12x Arm Cortex-A78AE | DS-10662-001: "JAO 64GB: Arm® v8.2 (64-bit) \| 12x (up to 6× lock step) Arm Cortex-A78AE cores \| three CPU clusters (four cores/cluster)" (Table 1-2) |
| CPU max frequency | 2.2 GHz | DS-10662-001: "Maximum Operating Frequency: 2.2 GHz" (JAO 64GB, Table 1-2) |

---

## Derived Values (ARM Cortex-A78AE + datasheet frequency)

The ARM Cortex-A78AE supports NEON (ASIMD) with 2×128-bit SIMD units per core.
FMA (Fused Multiply-Add) delivers 2 FLOPs per element per cycle.

| Parameter | Value | Derivation |
|---|---|---|
| Peak FP32 scalar (GFLOPs/s) | 105.6 | 12 cores × 2.2 GHz × 4 FLOPs/cycle (ASIMD 2×128-bit FMA, 4 floats) |
| Peak FP32 SIMD (GFLOPs/s) | 422.4 | 12 cores × 2.2 GHz × 16 FLOPs/cycle (full NEON FMA) |
| Ridge point (FP32 scalar) | 0.52 FLOPs/byte | 105.6 / 204.8 |
| Ridge point (FP32 SIMD) | 2.06 FLOPs/byte | 422.4 / 204.8 |

---

## Roofline Model Usage

- **Memory-bound regime** (AI < ridge): Performance = AI × Peak_BW
- **Compute-bound regime** (AI ≥ ridge): Performance = Peak_FLOPS
- **Ridge point**: AI = Peak_FLOPS / Peak_BW = 2.06 FLOPs/byte (SIMD)
