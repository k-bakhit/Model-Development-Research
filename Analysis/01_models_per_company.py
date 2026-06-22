"""
01_models_per_company.py
------------------------
First analysis: which companies are producing the most AI models over time?
Answers the project's headline question using the clean Epoch backbone.

Reads:  ../Research/processed/master_models.csv
Writes: models_per_company.png  (chart) and prints a summary table.

Run:  python 01_models_per_company.py
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
MASTER = ROOT.parent / "Research" / "processed" / "master_models.csv"
OUT_PNG = ROOT / "models_per_company.png"

# Merge orgs under same company
# comparison is fair (otherwise Google's output looks artificially split).
MERGE = {
    "Google DeepMind": "Google", "DeepMind": "Google", "Google Brain": "Google",
    "Meta AI": "Meta", "Facebook AI Research": "Meta", "FAIR": "Meta",
    "Microsoft Research": "Microsoft",
}

def main():
    m = pd.read_csv(MASTER)
    m["year"] = pd.to_datetime(m["release_date"], errors="coerce").dt.year
    m["company"] = m["developer"].replace(MERGE)

    # Modern era only
    m = m[(m.year >= 2015) & (m.year <= 2026)]

    # Top companies by total models
    top = m["company"].value_counts().head(6).index.tolist()
    sub = m[m["company"].isin(top)]

    # models per company per year
    pivot = (sub.groupby(["year", "company"]).size()
                .unstack("company").reindex(columns=top).fillna(0))

    # visualization
    plt.figure(figsize=(11, 6))
    for c in top:
        plt.plot(pivot.index, pivot[c], marker="o", linewidth=2, label=c)
    plt.title("AI models released per year, by company (notable models, 2015–2026)",
              fontsize=13, fontweight="bold")
    plt.xlabel("Year"); plt.ylabel("Models released")
    plt.legend(title="Company", frameon=False)
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=140)
    print(f"Saved {OUT_PNG}")

    print("\nTotal notable models 2015–2026 (top companies):")
    print(sub["company"].value_counts().to_string())

if __name__ == "__main__":
    main()
