"""
clean_pricing.py
----------------
Turns the scraped pricing data into one clean time series:
  processed/pricing_history.csv  ->  model, date, input_price_per_1m, output_price_per_1m, provider

Two techniques, because the providers format prices differently:
  - OpenAI: parsed from the flattened pricing_history_extracted.csv (its pages list
    "model $price / 1k tokens" inline, which the text extraction captures well).
  - Anthropic & Google: parsed STRUCTURALLY from the raw HTML tables in
    pricing_snapshots/, because their pages are tables — flattening them to text
    loses the column meaning (input vs cache vs output) and produces wrong numbers.

All prices are normalized to USD per 1,000,000 tokens.
NOTE: Google's tables mix modalities/context tiers; its output is a best-effort
draft that should be spot-checked. OpenAI and Anthropic are reliable.

Run:  python scripts/clean_pricing.py
"""
from __future__ import annotations
import re, glob, os
from pathlib import Path
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
EXTRACTED = ROOT / "Model_Data" / "pricing_history_extracted.csv"
SNAP = ROOT / "Model_Data" / "pricing_snapshots"
OUT = ROOT / "processed" / "pricing_history.csv"

PRICE_RE = re.compile(r"\$\s?([\d.]+)")
def first_price(s):
    m = PRICE_RE.search(s or "")
    return float(m.group(1)) if m else None
def date_from_name(fn):
    m = re.search(r"(\d{14})", fn)
    return pd.to_datetime(m.group(1)[:8], format="%Y%m%d") if m else None


# ---------------------------------------------------------------- OpenAI
OAI_MODELS = ["gpt-4o-mini","gpt-4o","gpt-4-turbo","gpt-4-32k","gpt-4-vision","gpt-4",
              "gpt-3.5-turbo-16k","gpt-3.5-turbo","davinci","curie","babbage","ada"]

def clean_openai() -> pd.DataFrame:
    df = pd.read_csv(EXTRACTED)
    df["ctx"] = df.context.str.lower()
    df["price_num"] = df.price.str.replace("$","",regex=False).str.replace(",","",regex=False).astype(float)
    df["date"] = pd.to_datetime(df.snapshot_date, errors="coerce")
    df = df[df.provider.isin(["openai","openai_api"])]
    df = df[df.ctx.str.contains("1k tokens|1m tokens|/ 1k|/ 1m", regex=True)].copy()

    def nearest(row):
        i = row.ctx.find(row.price.lower()); pre = row.ctx[:i] if i > 0 else row.ctx
        best, bp = None, -1
        for m in OAI_MODELS:
            p = pre.rfind(m)
            if p > bp: best, bp = m, p
        return best
    df["model"] = df.apply(nearest, axis=1)
    df = df.dropna(subset=["model"])
    df["per_1m"] = np.where(df.ctx.str.contains("1k"), df.price_num*1000, df.price_num)
    df = df[(df.per_1m >= 0.05) & (df.per_1m <= 200)].drop_duplicates(["model","date","per_1m"])

    def assign(g):
        v = sorted(g.per_1m.unique())
        return pd.Series({"input_price_per_1m": v[0], "output_price_per_1m": v[-1]})
    out = df.groupby(["model","date"]).apply(assign, include_groups=False).reset_index()
    out["provider"] = "openai"
    return out


# ---------------------------------------------------------------- Anthropic (structural)
def clean_anthropic() -> pd.DataFrame:
    rows = []
    files = glob.glob(f"{SNAP}/anthropic/*.html") + glob.glob(f"{SNAP}/anthropic_*.html")
    for f in files:
        date = date_from_name(os.path.basename(f))
        soup = BeautifulSoup(open(f, encoding="utf-8").read(), "html.parser")
        for t in soup.find_all("table"):
            trs = t.find_all("tr")
            if not trs: continue
            head = [c.get_text(" ",strip=True).lower() for c in trs[0].find_all(["th","td"])]
            in_col = next((i for i,h in enumerate(head) if "input" in h), None)
            out_col = next((i for i,h in enumerate(head) if "output" in h), None)
            if in_col is None or out_col is None: continue
            for tr in trs[1:]:
                cells = [c.get_text(" ",strip=True) for c in tr.find_all(["th","td"])]
                if len(cells) <= max(in_col, out_col): continue
                model = cells[0].lower()
                if "claude" not in model: continue
                rows.append({"provider":"anthropic","model":model,"date":date,
                             "input_price_per_1m":first_price(cells[in_col]),
                             "output_price_per_1m":first_price(cells[out_col])})
    df = pd.DataFrame(rows).dropna(subset=["input_price_per_1m"])
    # collapse batch (half-price) duplicates -> keep standard = higher price
    return df.groupby(["provider","model","date"], as_index=False).agg(
        input_price_per_1m=("input_price_per_1m","max"),
        output_price_per_1m=("output_price_per_1m","max"))


# ---------------------------------------------------------------- Google (structural, best-effort)
def clean_google() -> pd.DataFrame:
    rows = []
    files = glob.glob(f"{SNAP}/google/google_vertex_*.html") + glob.glob(f"{SNAP}/google/google_gemini_docs_*.html")
    for f in files:
        date = date_from_name(os.path.basename(f))
        soup = BeautifulSoup(open(f, encoding="utf-8").read(), "html.parser")
        for t in soup.find_all("table"):
            trs = t.find_all("tr")
            if not trs: continue
            head = " ".join(c.get_text(" ",strip=True).lower() for c in trs[0].find_all(["th","td"]))
            if "token" not in head: continue                 # per-token tables only
            current = None
            for tr in trs:
                cells = [c.get_text(" ",strip=True) for c in tr.find_all(["th","td"])]
                if not cells: continue
                joined = " ".join(cells).lower()
                if len(cells) == 1 and "gemini" in cells[0].lower():
                    current = cells[0].lower(); continue
                if current and "input" in joined and "text" in joined:
                    rows.append({"provider":"google","model":current,"date":date,
                                 "input_price_per_1m":first_price(joined),"output_price_per_1m":None})
                elif current and "output" in joined:
                    for r in reversed(rows):
                        if r["model"]==current and r["date"]==date and r["output_price_per_1m"] is None:
                            r["output_price_per_1m"]=first_price(joined); break
    df = pd.DataFrame(rows).dropna(subset=["input_price_per_1m"]).drop_duplicates()
    return df


def main():
    parts = [clean_openai(), clean_anthropic(), clean_google()]
    allp = pd.concat(parts, ignore_index=True)
    allp["model"] = allp.model.str.strip()
    allp = allp.sort_values(["provider","model","date"]).reset_index(drop=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    allp.to_csv(OUT, index=False)
    print(f"Wrote {OUT}  ({len(allp)} rows)")
    for p, g in allp.groupby("provider"):
        print(f"  {p}: {len(g)} rows, {g.model.nunique()} models, "
              f"{g.date.min().date()} -> {g.date.max().date()}")


if __name__ == "__main__":
    main()
