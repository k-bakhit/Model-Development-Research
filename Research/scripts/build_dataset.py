"""
build_dataset.py
----------------
Joins the project's raw data sources into one analysis-ready table.

Sources (relative to the Research/ folder):
  1. Epoch AI       Model_Data/ai_models/notable_ai_models.csv      (specs: params, FLOP, training power, country, date)
  2. Artificial     Model_Data/artificial_analysis.json             (pricing + intelligence index + speed)
     Analysis
  3. ML.Energy      Energy_Consumption_Data/ml_energy_leaderboard.json  (params / precision; energy hook)
  4. LifeArchitect  Model_Data/LifeArchitect.ai Models Table (shared) - Models.csv  (benchmarks: MMLU, GPQA, ...)

Output:
  processed/master_models.csv   one wide row per model
  processed/join_report.txt     how many rows matched across sources

Join strategy: models are matched on a NORMALIZED name (lowercased, punctuation and
spacing stripped, trailing size/qualifier tags removed). Cross-source naming is messy,
so expect partial matches — the join report tells you the hit rate, and unmatched rows
are still kept (left join on the Epoch backbone) rather than dropped.

Run:  python scripts/build_dataset.py
"""

from __future__ import annotations
import json
import re
from pathlib import Path

import pandas as pd

# ----------------------------------------------------------------------------
# Paths — script lives in Research/scripts/, so the Research/ root is its parent.
# ----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent          # .../Research
EPOCH_CSV = ROOT / "Model_Data" / "ai_models" / "notable_ai_models.csv"
AA_JSON = ROOT / "Model_Data" / "artificial_analysis.json"
MLENERGY_JSON = ROOT / "Energy_Consumption_Data" / "ml_energy_leaderboard.json"
LIFEARCH_CSV = ROOT / "Model_Data" / "LifeArchitect.ai Models Table (shared) - Models.csv"

OUT_DIR = ROOT / "processed"
OUT_CSV = OUT_DIR / "master_models.csv"
OUT_REPORT = OUT_DIR / "join_report.txt"


# ----------------------------------------------------------------------------
# Name normalization — the heart of the join.
# ----------------------------------------------------------------------------
def norm(name) -> str:
    """Lowercase, drop parenthetical qualifiers, strip non-alphanumerics."""
    if not isinstance(name, str):
        return ""
    s = name.lower()
    s = re.sub(r"\(.*?\)", "", s)          # drop "(low)", "(max)", "(shared)" etc.
    s = re.sub(r"[^a-z0-9]", "", s)        # keep only letters+digits
    return s.strip()


# ----------------------------------------------------------------------------
# Loaders — each returns a tidy DataFrame with a "key" column for joining.
# ----------------------------------------------------------------------------
def load_epoch() -> pd.DataFrame:
    df = pd.read_csv(EPOCH_CSV)
    keep = {
        "Model": "model_name",
        "Organization": "developer",
        "Country (of organization)": "country",
        "Publication date": "release_date",
        "Parameters": "parameters",
        "Training compute (FLOP)": "training_compute_flop",
        "Training power draw (W)": "training_power_draw_w",
        "Training compute cost (2023 USD)": "training_cost_usd_2023",
    }
    cols = [c for c in keep if c in df.columns]
    df = df[cols].rename(columns={c: keep[c] for c in cols})
    df["key"] = df["model_name"].map(norm)
    return df


def load_artificial_analysis() -> pd.DataFrame:
    data = json.load(open(AA_JSON))["data"]
    rows = []
    for m in data:
        pricing = m.get("pricing") or {}
        evals = m.get("evaluations") or {}
        creator = (m.get("model_creator") or {}).get("name")
        rows.append({
            "aa_name": m.get("name"),
            "aa_creator": creator,
            "aa_release_date": m.get("release_date"),
            "price_1m_input": pricing.get("price_1m_input_tokens"),
            "price_1m_output": pricing.get("price_1m_output_tokens"),
            "price_1m_blended_3to1": pricing.get("price_1m_blended_3_to_1"),
            "intelligence_index": evals.get("artificial_analysis_intelligence_index"),
            "coding_index": evals.get("artificial_analysis_coding_index"),
            "math_index": evals.get("artificial_analysis_math_index"),
            "gpqa": evals.get("gpqa"),
            "mmlu_pro": evals.get("mmlu_pro"),
            "output_tokens_per_sec": m.get("median_output_tokens_per_second"),
            "time_to_first_token_s": m.get("median_time_to_first_token_seconds"),
            "key": norm(m.get("name")),
        })
    df = pd.DataFrame(rows)
    # one model can appear as several endpoints (low/high/max) -> keep cheapest output price
    df = df.sort_values("price_1m_output").drop_duplicates("key", keep="first")
    return df


def load_mlenergy() -> pd.DataFrame:
    """Model params/precision from the catalog, plus measured energy_wh_per_1k
    if scripts/fetch_mlenergy_energy.py has been run (it writes the energy CSV)."""
    blob = json.load(open(MLENERGY_JSON))
    rows = []
    for repo, m in blob.get("models", {}).items():
        rows.append({
            "mle_repo": repo,
            "mle_nickname": m.get("nickname"),
            "mle_total_params_b": m.get("total_params_billions"),
            "mle_active_params_b": m.get("activated_params_billions"),
            "mle_precision": m.get("weight_precision"),
            "key": norm(m.get("nickname")),
        })
    df = pd.DataFrame(rows).drop_duplicates("key", keep="first")

    # Merge measured energy if the fetch script has produced it.
    energy_csv = OUT_DIR / "mlenergy_energy_by_model.csv"
    if energy_csv.exists():
        e = pd.read_csv(energy_csv)
        e["key"] = e["nickname"].map(norm)
        e = e[["key", "energy_wh_per_1k", "energy_wh_per_1k_min",
               "energy_wh_per_1k_max", "gpus", "source_quality"]]
        e = e.rename(columns={"source_quality": "energy_source_quality"})
        df = df.merge(e.drop_duplicates("key"), on="key", how="left")
    return df


def load_lifearchitect() -> pd.DataFrame:
    # Real header is on the 2nd line of this export; first line is a banner.
    df = pd.read_csv(LIFEARCH_CSV, skiprows=1)
    rename = {}
    for col in df.columns:
        c = col.strip()
        if c == "Model":
            rename[col] = "la_model"
        elif c == "Lab":
            rename[col] = "la_lab"
        elif c.startswith("MMLU") and "Pro" not in c:
            rename[col] = "la_mmlu"
        elif "GPQA" in c:
            rename[col] = "la_gpqa"
        elif "Announced" in c:
            rename[col] = "la_announced"
    df = df.rename(columns=rename)
    keep = [v for v in ["la_model", "la_lab", "la_mmlu", "la_gpqa", "la_announced"] if v in df.columns]
    df = df[keep].copy()
    df["key"] = df["la_model"].map(norm)
    return df[df["key"] != ""].drop_duplicates("key", keep="first")


# ----------------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------------
def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    epoch = load_epoch()
    aa = load_artificial_analysis()
    mle = load_mlenergy()
    la = load_lifearchitect()

    # Left-join everything onto the Epoch backbone so no Epoch model is lost.
    master = (
        epoch
        .merge(aa.drop(columns=["aa_name"]), on="key", how="left")
        .merge(mle, on="key", how="left")
        .merge(la, on="key", how="left")
    )

    master = master.sort_values("model_name").reset_index(drop=True)
    master.to_csv(OUT_CSV, index=False)

    # ---- join report -------------------------------------------------------
    def matched(col):
        return int(master[col].notna().sum()) if col in master else 0

    lines = [
        "JOIN REPORT — master_models.csv",
        "=" * 40,
        f"Epoch backbone rows (notable models): {len(epoch)}",
        f"  with Artificial Analysis pricing  : {matched('price_1m_output')}",
        f"  with ML.Energy params             : {matched('mle_total_params_b')}",
        f"  with LifeArchitect benchmarks     : {matched('la_mmlu')}",
        "",
        f"Source pools available:  AA={len(aa)}  ML.Energy={len(mle)}  LifeArchitect={len(la)}",
        "",
        "Low match rates are expected: names differ across sources and the Epoch",
        "'notable' set skews older/research while Artificial Analysis skews to",
        "currently-served commercial endpoints. Improve matching by editing norm()",
        "or adding a manual alias map (e.g. 'gpt4' -> 'gpt-4').",
        "",
        f"Output columns ({len(master.columns)}): {', '.join(master.columns)}",
    ]
    OUT_REPORT.write_text("\n".join(lines))

    print(f"Wrote {OUT_CSV}  ({len(master)} rows, {len(master.columns)} cols)")
    print(f"Wrote {OUT_REPORT}")
    print("\n".join(lines[2:7]))


if __name__ == "__main__":
    main()
