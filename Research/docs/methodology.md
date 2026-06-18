# Methodology

How numbers in this project are produced, and the assumptions behind them. This
document is what makes the dashboard a research artifact rather than a data dump.

## Source-quality tags

Every energy and price figure carries a `source_quality` tag:

- **measured** — directly measured on known hardware (ML.Energy benchmark of open models).
- **vendor-reported** — published by the model's developer (e.g. official API prices).
- **estimated** — inferred via a documented formula (closed-model energy). Always shown
  as a range, never a single number.

This tag drives how figures are displayed: measured values as solid bars, estimates
as dashed bars with error whiskers.

## The energy metric: `energy_wh_per_1k`

Definition: **watt-hours of GPU energy to generate 1,000 output tokens.**

Three deliberate choices keep it comparable:

1. **Watt-hours**, not Joules (1 Wh = 3600 J), because watt-hours are the unit people
   intuit for energy use.
2. **GPU energy only** — what the measurements actually capture (not datacenter overhead
   / PUE, which would require assumptions we can't verify per model).
3. **Output (decode) tokens**, because energy scales with the length of the response a
   model generates.

Computed from the ML.Energy field `energy_per_token_joules`:

```
energy_wh_per_1k = energy_per_token_joules × 1000 / 3600
```

ML.Energy measures each model across several tasks and GPUs. The per-model headline
number is the **median across runs** (robust to noisy high-load outliers); the per-task
detail is preserved separately for drill-down. Hardware (GPU) is always recorded
alongside the number, because energy/token is hardware-dependent and figures from
different GPUs are not directly comparable.

## Closed-model energy estimation

Closed models (GPT, Claude, Gemini) are never measured directly, so their energy is
**estimated**, not measured. The method is a physics-grounded formula, not machine
learning — chosen because the measured training set is small (~16 distinct models),
noisy, and the closed models are out-of-distribution, all of which make a learned
model unreliable and a transparent formula more defensible.

**Formula:** `energy_wh_per_1k ≈ k × active_params_billions`

This follows from inference physics: each token costs ~2 FLOPs per active parameter,
divided by GPU throughput and efficiency. For Mixture-of-Experts models, **active**
(not total) parameters drive per-token compute.

**Calibration:** `k` is the median of `measured_energy / active_params` across the
open models, on a fixed slice (chat task, H100 GPU) to control for task and hardware.
As of the current data, **k ≈ 0.0054 Wh per 1k tokens per billion active parameters.**

**Uncertainty band:** apply the formula to the measured models, take the ratio of
actual ÷ predicted, and use the 10th–90th percentile of those ratios as the error band
— currently roughly **÷2.4 to ×3.6**. Every closed-model estimate is reported as
`best × low_factor` to `best × high_factor`, not a point.

**Assumptions and limits (state these loudly):**

- Active-parameter counts for closed models are themselves public *estimates*.
- Energy is computed as if served on an H100 at the chat workload; real serving
  hardware is unknown.
- The error band is measured on open models and is therefore a **lower bound** on the
  true uncertainty — closed models are harder to predict, not easier.

## Joining the sources

All sources are merged onto the Epoch AI model list (the backbone) via a **normalized
name key**: lowercase, parenthetical qualifiers removed, all non-alphanumeric characters
stripped (so "Claude 3.5 Sonnet (max)" and "claude-3.5-sonnet" both become
`claude35sonnet`). Merges are **left joins** onto Epoch, so no model is dropped; sources
that don't match simply leave their columns blank. Match rates are reported in
`processed/join_report.txt` and are expected to be partial, because Epoch's notable set
skews older/research while Artificial Analysis lists current commercial endpoints.

## Macro data (price/inflation context)

Electricity price (EIA) and inflation/energy CPI (FRED) are pulled as time series and
joined to model pricing by date, to test whether credit-price changes track energy cost
or general inflation. Correlation here is **not** causation and is labeled as such.
