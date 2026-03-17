# AI Method Comparison

**File:** `02_ai_method_comparison.png`

Scatter plot comparing arithmetic intensity estimates from perf (ops/byte, x-axis) and miniperf (LLVM IR FLOPs/byte, y-axis).

- Points near the **diagonal** indicate agreement between the two methods.
- Points **above** the diagonal: miniperf sees higher compute intensity than perf.
- Points **below**: perf overestimates memory intensity.

Green markers indicate matching bottleneck classifications; red markers indicate disagreement.
