"""
fetch_eia.py
------------
Pulls U.S. electricity retail-sales data (price, revenue, sales, customers) from
the EIA v2 API and saves clean CSVs for the project.

Produces a national quarterly ELECTRICITY PRICE series (cents/kWh) — the macro
input you join to model-pricing-over-time to ask "did energy cost drive credit
price?" — plus the full per-state all-sectors table for drill-down.

PREREQUISITES:
  pip install requests pandas python-dotenv
  A free EIA key from https://www.eia.gov/opendata/register.php, stored in a
  gitignored env file (default: Energy_Consumption_Data/EIA_API_Key.env) as:
      EIA_API_KEY=your-key-here

Run:
  python scripts/fetch_eia.py

Outputs:
  processed/electricity_retail_sales.csv   full all-sectors table (per state, per quarter)
  processed/electricity_price_national.csv  one national price per quarter (for joins)
"""

from __future__ import annotations
import os
import sys
from pathlib import Path

import requests
import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent             
ENV_FILE = ROOT / "Energy_Consumption_Data" / "EIA_API_Key.env"
OUT_DIR = ROOT / "processed"
OUT_FULL = OUT_DIR / "electricity_retail_sales.csv"
OUT_NATIONAL = OUT_DIR / "electricity_price_national.csv"

API_URL = "https://api.eia.gov/v2/electricity/retail-sales/data/"
PAGE = 5000                                               


def get_key() -> str:
    """Load the EIA key, tolerating a few common name spellings."""
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE)
    for name in ("EIA_API_KEY", "EIA_API_Key", "EIA_KEY"):
        if os.environ.get(name):
            return os.environ[name]
    sys.exit(
        f"No EIA key found. Put it in {ENV_FILE} as 'EIA_API_KEY=your-key' "
        f"(or set the EIA_API_KEY environment variable)."
    )


def fetch_all(api_key: str) -> pd.DataFrame:
    """Page through every all-sectors row (offset += 5000 until exhausted)."""
    base_params = {
        "api_key": api_key,
        "frequency": "quarterly",
        "data[0]": "customers",
        "data[1]": "price",
        "data[2]": "revenue",
        "data[3]": "sales",
        "facets[sectorid][]": "ALL",          
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": PAGE,
    }

    rows, offset = [], 0
    while True:
        params = {**base_params, "offset": offset}
        resp = requests.get(API_URL, params=params, timeout=60)
        resp.raise_for_status()
        chunk = resp.json()["response"]["data"]
        if not chunk:
            break
        rows.extend(chunk)
        print(f"  fetched {len(rows)} rows...")
        if len(chunk) < PAGE:                 
            break
        offset += PAGE
    return pd.DataFrame(rows)


def build_national(df: pd.DataFrame) -> pd.DataFrame:
    """One national price per quarter.

    Prefer EIA's own national row (stateid == 'US'); if absent, fall back to a
    SALES-WEIGHTED average across states (correct way to average prices — a plain
    mean would over-weight tiny states)."""
    df = df.copy()
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["sales"] = pd.to_numeric(df["sales"], errors="coerce")

    if "US" in set(df.get("stateid", [])):
        nat = (df[df["stateid"] == "US"][["period", "price"]]
               .rename(columns={"price": "price_cents_per_kwh"}))
    else:
        df["_price_x_sales"] = df["price"] * df["sales"]
        g = df.groupby("period").agg(pw=("_price_x_sales", "sum"), w=("sales", "sum"))
        g["price_cents_per_kwh"] = g["pw"] / g["w"]
        nat = g.reset_index()[["period", "price_cents_per_kwh"]]

    nat["period"] = pd.PeriodIndex(nat["period"].str.replace("-", ""), freq="Q").to_timestamp()
    return nat.sort_values("period").reset_index(drop=True)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    key = get_key()

    print("Fetching EIA electricity retail-sales (all sectors, quarterly)...")
    df = fetch_all(key)
    print(f"Total rows: {len(df)}")

    df.to_csv(OUT_FULL, index=False)
    national = build_national(df)
    national.to_csv(OUT_NATIONAL, index=False)

    print(f"Wrote {OUT_FULL}  ({len(df)} rows)")
    print(f"Wrote {OUT_NATIONAL}  ({len(national)} quarters)")
    print("\nMost recent national electricity price:")
    print(national.tail(3).to_string(index=False))


if __name__ == "__main__":
    main()
