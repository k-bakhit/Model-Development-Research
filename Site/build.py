"""
build.py — generates the self-contained dashboard `index.html`.

Reads the cleaned CSVs in ../Research/processed/, packs the bits each chart needs
into a compact JSON, and injects it into template.html (replacing __DATA__).
The result, index.html, is fully self-contained: open it by double-clicking, or
host it anywhere static (GitHub Pages). No server, no Streamlit.

Run:  python build.py
"""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
PROC = ROOT.parent / "Research" / "processed"
AA = ROOT.parent / "Research" / "Model_Data" / "artificial_analysis.json"

MERGE = {"Google DeepMind": "Google", "DeepMind": "Google", "Google Brain": "Google",
         "Meta AI": "Meta", "Facebook AI Research": "Meta", "FAIR": "Meta",
         "Microsoft Research": "Microsoft"}


def rd(name):
    p = PROC / name
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def main():
    data = {}

    # ---- model production (ALL companies) ----
    m = rd("master_models.csv")
    m["year"] = pd.to_datetime(m["release_date"], errors="coerce").dt.year
    m["company"] = m["developer"].replace(MERGE)
    prod = m.dropna(subset=["year", "company"])
    prod = prod[(prod.year >= 2012) & (prod.year <= 2026)]
    counts = prod.groupby(["company", "year"]).size().reset_index(name="n")
    data["production"] = counts.to_dict("records")
    data["companies"] = (prod["company"].value_counts().rename_axis("company")
                         .reset_index(name="total").to_dict("records"))

    # ---- pricing history (OpenAI / Anthropic / Google) ----
    pr = rd("pricing_history.csv")
    if not pr.empty:
        pr["date"] = pd.to_datetime(pr["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        data["pricing"] = pr.rename(columns={"input_price_per_1m": "inp",
                                             "output_price_per_1m": "out"}).to_dict("records")
    else:
        data["pricing"] = []

    # ---- CURRENT pricing across MANY companies (from Artificial Analysis) ----
    current = []
    if AA.exists():
        for x in json.load(open(AA)).get("data", []):
            pricing = x.get("pricing") or {}
            evals = x.get("evaluations") or {}
            creator = (x.get("model_creator") or {}).get("name")
            out = pricing.get("price_1m_output_tokens")
            if creator and out is not None:
                current.append({
                    "model": x.get("name"), "company": MERGE.get(creator, creator),
                    "out": out, "inp": pricing.get("price_1m_input_tokens"),
                    "intel": evals.get("artificial_analysis_intelligence_index"),
                })
    data["current"] = current

    # ---- energy (many open-weight models / companies) ----
    en = rd("mlenergy_energy_by_model.csv")
    if not en.empty:
        en = en.dropna(subset=["energy_wh_per_1k"])
        data["energy"] = en.rename(columns={
            "nickname": "name", "energy_wh_per_1k": "wh",
            "energy_wh_per_1k_min": "lo", "energy_wh_per_1k_max": "hi",
            "total_params_billions": "params"})[
            ["name", "wh", "lo", "hi", "params", "gpus"]].to_dict("records")
    else:
        data["energy"] = []

    # ---- macro + electricity ----
    mac = rd("macro.csv")
    if not mac.empty:
        mac["date"] = pd.to_datetime(mac["date"], errors="coerce")
        mac = mac[mac.date.dt.year >= 2010]
        mac["date"] = mac.date.dt.strftime("%Y-%m-%d")
        data["macro"] = mac.rename(columns={"all_items_cpi": "cpi",
                                            "energy_cpi": "ecpi"})[["date", "cpi", "ecpi"]].to_dict("records")
    el = rd("electricity_price_national.csv")
    if not el.empty:
        el["period"] = pd.to_datetime(el["period"], errors="coerce")
        el = el[el.period.dt.year >= 2010]
        el["period"] = el.period.dt.strftime("%Y-%m-%d")
        data["elec"] = el.rename(columns={"period": "date",
                                          "price_cents_per_kwh": "price"}).to_dict("records")

    # cheapest output price per date, per provider (economy overlay — selectable)
    data["provider_price"] = {}
    if data["pricing"]:
        p = pd.DataFrame(data["pricing"])
        for prov in sorted(p.provider.unique()):
            s = p[p.provider == prov].dropna(subset=["out"])
            if len(s):
                data["provider_price"][prov] = (s.groupby("date")["out"].min().reset_index()
                                                .rename(columns={"out": "price"}).to_dict("records"))

    # ---- headline numbers ----
    data["meta"] = {
        "models": int(len(m)),
        "top_company": (data["companies"][0]["company"] if data["companies"] else "—"),
        "price_points": int(len(data["pricing"])),
        "energy_models": int(len(data["energy"])),
        "companies_priced": int(len({c["company"] for c in current})),
    }

    # ---- inject into template ----
    tpl = (ROOT / "template.html").read_text(encoding="utf-8")
    out = tpl.replace("__DATA__", json.dumps(data, separators=(",", ":")))
    (ROOT / "index.html").write_text(out, encoding="utf-8")
    print(f"Wrote index.html  ({len(out)//1024} KB)")
    print(f"  production rows: {len(data['production'])}, current-priced companies: {data['meta']['companies_priced']}, "
          f"energy models: {len(data['energy'])}")


if __name__ == "__main__":
    main()
