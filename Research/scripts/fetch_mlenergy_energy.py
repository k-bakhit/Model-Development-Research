"""
fetch_mlenergy_energy.py
------------------------
Pulls measured inference-energy data from the ML.Energy benchmark and produces
the `energy_wh_per_1k` column (watt-hours of GPU energy per 1,000 output tokens).

WHY this is a separate script: it needs network access to Hugging Face, which the
main build can't assume. Run this once (or whenever ML.Energy updates), it writes
two CSVs into processed/, and then build_dataset.py picks them up automatically.

PREREQUISITE (run once in your environment):
    pip install "mlenergy-data" "httpx[socks]" socksio pandas

Run:
    python scripts/fetch_mlenergy_energy.py

Outputs:
    processed/mlenergy_energy_by_task.csv   one row per (model, task, gpu) — detailed
    processed/mlenergy_energy_by_model.csv   one row per model — mean across tasks (for the join)
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd

from mlenergy.data import LLMRuns

ROOT = Path(__file__).resolve().parent.parent          
OUT_DIR = ROOT / "processed"
OUT_BY_TASK = OUT_DIR / "mlenergy_energy_by_task.csv"
OUT_BY_MODEL = OUT_DIR / "mlenergy_energy_by_model.csv"


J_PER_TOKEN_TO_WH_PER_1K = 1000.0 / 3600.0


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Downloading ML.Energy benchmark from Hugging Face ...")
    runs = LLMRuns.from_hf()                 
    df = runs.to_dataframe()
    print(f"Loaded {len(df)} runs. Columns:\n  {list(df.columns)}\n")

    # MANDATORY calculation
    df["energy_wh_per_1k"] = df["energy_per_token_joules"] * J_PER_TOKEN_TO_WH_PER_1K

    # table
    detail_cols = [
        "model_id", "nickname", "task", "gpu_model", "weight_precision",
        "total_params_billions", "activated_params_billions",
        "energy_per_token_joules", "energy_wh_per_1k",
        "avg_power_watts", "output_throughput_tokens_per_sec",
        "total_output_tokens", "is_stable",
    ]
    detail_cols = [c for c in detail_cols if c in df.columns]
    by_task = df[detail_cols].copy()
    by_task.to_csv(OUT_BY_TASK, index=False)

    # summary table
    by_model = (
        by_task.groupby(["model_id", "nickname"], as_index=False)
        .agg(
            energy_wh_per_1k=("energy_wh_per_1k", "mean"),
            energy_wh_per_1k_min=("energy_wh_per_1k", "min"),
            energy_wh_per_1k_max=("energy_wh_per_1k", "max"),
            tasks_measured=("task", "nunique"),
            gpus=("gpu_model", lambda s: ",".join(sorted(set(s.dropna())))),
            total_params_billions=("total_params_billions", "first"),
        )
    )
    by_model["source_quality"] = "measured"      
    by_model.to_csv(OUT_BY_MODEL, index=False)

    print(f"Wrote {OUT_BY_TASK}  ({len(by_task)} rows)")
    print(f"Wrote {OUT_BY_MODEL}  ({len(by_model)} models)")
    print("\nTop 5 most efficient models (Wh per 1k output tokens):")
    print(
        by_model.sort_values("energy_wh_per_1k")[["nickname", "energy_wh_per_1k", "gpus"]]
        .head(5).to_string(index=False)
    )


if __name__ == "__main__":
    main()
