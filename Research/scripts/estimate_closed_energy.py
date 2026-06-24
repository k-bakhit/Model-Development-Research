"""
estimate_closed_energy.py
-------------------------
Estimates inference energy for CLOSED models (GPT, Gemini, Grok, PaLM, ...) that
nobody measures directly. This is the "estimated" tier of the project, distinct
from the "measured" ML.Energy numbers.

Method (physics-grounded, not ML — too few points and out-of-distribution targets):
  energy_wh_per_1k ~= k * active_params_billions
  k is calibrated as the median of (measured energy / active params) across the
  open models, on a fixed slice (chat task, H100) to hold task and hardware constant.
  A range is carried from the 10th-90th percentile of how far that formula misses
  on the measured models.

IMPORTANT CAVEAT, written into the output:
  Closed models publish TOTAL parameters, not ACTIVE. For sparse Mixture-of-Experts
  models (modern GPT/Gemini/Grok) active << total, so using total params makes these
  estimates an UPPER BOUND that overestimates real energy, sometimes by a lot. That
  is why they are tagged 'estimated' and shown as a wide range, never as a point.

Run:  python scripts/estimate_closed_energy.py
Output: processed/closed_model_energy_estimates.csv
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "processed"
CLOSED_LABS = ["OpenAI", "Anthropic", "Google", "Google DeepMind", "DeepMind", "xAI"]


def calibrate():
    d = pd.read_csv(PROC / "mlenergy_energy_by_task.csv")
    d = d[(d.task == "lm-arena-chat") & (d.gpu_model == "H100")]
    d = d[(d.energy_wh_per_1k > 0) & d.activated_params_billions.notna()]
    per = d.groupby("nickname").agg(active=("activated_params_billions", "first"),
                                    energy=("energy_wh_per_1k", "median"))
    k = (per.energy / per.active).median()
    ratio = per.energy / (k * per.active)
    return k, ratio.quantile(0.10), ratio.quantile(0.90), len(per)


def main():
    k, low_f, high_f, n = calibrate()
    m = pd.read_csv(PROC / "master_models.csv")
    closed = m[m.energy_wh_per_1k.isna()].copy()
    closed["active_params_est_b"] = closed["parameters"] / 1e9
    # >=1B params excludes the labs' non-LLM research (RL agents, vision nets);
    # every closed LLM of interest is far above this floor.
    closed = closed[closed.active_params_est_b.notna()
                    & (closed.active_params_est_b >= 1.0)
                    & closed.developer.isin(CLOSED_LABS)]

    closed["energy_best_wh_per_1k"] = k * closed.active_params_est_b
    closed["energy_low_wh_per_1k"] = closed.energy_best_wh_per_1k * low_f
    closed["energy_high_wh_per_1k"] = closed.energy_best_wh_per_1k * high_f
    closed["source_quality"] = "estimated"
    closed["method"] = (f"k={k:.5f} Wh/1k per B active param (H100, chat); "
                        f"range x{low_f:.2f}-x{high_f:.2f} from {n} measured models; "
                        f"uses TOTAL params -> upper bound for MoE models")

    out = closed[["model_name", "developer", "release_date", "active_params_est_b",
                  "energy_low_wh_per_1k", "energy_best_wh_per_1k", "energy_high_wh_per_1k",
                  "source_quality", "method"]].sort_values("energy_best_wh_per_1k")
    dest = PROC / "closed_model_energy_estimates.csv"
    out.to_csv(dest, index=False)
    print(f"k={k:.5f}  range x{low_f:.2f}-x{high_f:.2f}")
    print(f"Wrote {dest}  ({len(out)} closed models)")
    print(out[["model_name", "active_params_est_b", "energy_low_wh_per_1k",
               "energy_best_wh_per_1k", "energy_high_wh_per_1k"]].head(12).to_string(index=False))


if __name__ == "__main__":
    main()
