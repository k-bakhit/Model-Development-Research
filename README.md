# AI Model Development & Efficiency Dashboard

Tracking which companies are developing AI models the fastest, and how efficient
those models are — in energy and cost per unit of work — over time.

## The question

**Which company is developing the most, in terms of model production and efficiency?**

Guiding sub-questions:

- How have token/credit price (per 1,000 tokens) and energy consumption changed over time?
  - the same model over time (e.g. GPT-3 then vs. GPT-3 later)
  - a model lineage over time (e.g. GPT-3 → GPT-5)
  - company vs. company (e.g. OpenAI's GPT vs. Anthropic's Claude)
- How have inflation and the price of energy changed, and do they explain credit-price changes?
- Which company outputs the most models?
- (stretch) Has the token/energy cost of a given *task* changed — e.g. solving the same
  math problem then vs. now?

## Data sources

| Source | What it provides | How it's pulled |
|--------|------------------|-----------------|
| Epoch AI | Model specs: parameters, training compute, training power draw, cost, country, date | CSV download |
| Artificial Analysis | Current pricing, intelligence/coding/math index, benchmarks, speed | API (`scripts`, key required) |
| ML.Energy | **Measured** inference energy for open models | `mlenergy-data` package (HF, gated) |
| LifeArchitect.ai | Benchmark scores (MMLU, GPQA) | CSV (free columns only) |
| FRED | Inflation (CPI), energy & electricity CPI | API (key required) |
| EIA | U.S. electricity retail price over time | API (key required) |

Full provenance and links: see [`Research/docs/sources.md`](Research/docs/sources.md).

## Repository structure

```
Research/
├── Model_Data/              raw model data (Epoch CSVs, Artificial Analysis, LifeArchitect)
├── Energy_Consumption_Data/ energy + macro data (ML.Energy, EIA, FRED, OWID)
├── scripts/                 fetch + build pipeline
│   ├── fetch_eia.py             electricity prices  -> processed/
│   ├── fetch_mlenergy_energy.py measured energy     -> processed/
│   └── build_dataset.py         joins everything    -> processed/master_models.csv
├── processed/              analysis-ready outputs (built by scripts, gitignored where large)
├── docs/                   methodology.md, sources.md
└── requirements.txt
```

## How to run

```bash
# 1. set up environment
python -m venv .venv && source .venv/bin/activate
pip install -r Research/requirements.txt

# 2. add API keys to gitignored .env files (see .env.example files)
#    - Artificial Analysis, FRED, EIA keys
#    - run `hf auth login` for the gated ML.Energy dataset

# 3. fetch data + build the master table
python Research/scripts/fetch_eia.py
python Research/scripts/fetch_mlenergy_energy.py
python Research/scripts/build_dataset.py
```

Output: `Research/processed/master_models.csv` — one row per model with specs,
pricing, benchmarks, and measured energy joined together.

## Status

- [x] Data pipeline: model specs, pricing, measured energy, electricity prices
- [x] Join into a single analysis-ready table
- [x] Historical pricing (price over time)
- [x] Inflation/energy macro series (FRED)
- [x] Dashboard (charts + web interface) — see `Site/` (open `Site/index.html`)
- [ ] Closed-model energy estimates
- [ ] Per-task token experiments

## A note on data integrity

Every energy figure is tagged by how it was obtained: `measured` (open models on
known hardware), `vendor-reported`, or `estimated` (closed models, via the method
in `docs/methodology.md`). Estimates are shown as ranges, never as exact numbers.
This distinction is deliberate and central to the project.
