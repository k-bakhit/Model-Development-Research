# Sources

Every dataset, API, paper, and website used in this project, with links and what each
contributes. This is the content behind the dashboard's "Sources" tab.

## Model data

- **Epoch AI — Data on AI Models** — https://epoch.ai/data/ai-models
  Backbone dataset. Parameters, training compute (FLOP), training power draw (W),
  training cost, country, release date. Free, CC-BY. Downloaded as CSV
  (notable / frontier / large-scale / all variants).
- **Artificial Analysis** — https://artificialanalysis.ai/
  Current API pricing (per 1M tokens), intelligence/coding/math indices, benchmark
  scores, output speed. Free API (key required), ~1,000 requests/day.
  - API docs: https://artificialanalysis.ai/documentation
- **LifeArchitect.ai Models Table** — https://lifearchitect.ai/models-table/
  Benchmark scores (MMLU, GPQA), release dates, labs. Free columns only; compute/energy
  columns are paywalled (filled instead from Epoch AI).

## Energy data

- **ML.Energy Leaderboard** — https://ml.energy/leaderboard
  Measured inference energy (Joules/token) for open models on known GPUs.
  - Benchmark dataset (gated): `ml-energy/benchmark-v3` on Hugging Face
  - Data toolkit: `pip install mlenergy-data` — https://github.com/ml-energy/leaderboard
  - Energy measured via the Zeus library: https://github.com/ml-energy/zeus
- **Hugging Face AI Energy Score** — https://huggingface.github.io/AIEnergyScore/
  Alternative measured-energy source; 1–5 star efficiency ratings across tasks.

## Macro / economic data

- **EIA — Electricity retail sales** — https://www.eia.gov/opendata/
  U.S. electricity price (cents/kWh) over time, by state and sector. Free API (key required).
- **FRED (St. Louis Fed)** — https://fred.stlouisfed.org/
  - All-items CPI (inflation): `CPIAUCSL`
  - Energy CPI: `CPIENGSL`
  - Electricity CPI: `CUUR0000SEHF01`
  Free API (key required).

## Supporting research (energy-per-token methodology)

- "How Hungry is AI? Benchmarking Energy, Water, and Carbon Footprint of LLM Inference"
  — https://arxiv.org/pdf/2505.09598
- "TokenPowerBench: Benchmarking the Power Consumption of LLM Inference"
  — https://arxiv.org/pdf/2512.03024
- "Advocating Energy-per-Token in LLM Inference" (EuroMLSys)
  — https://euromlsys.eu/pdf/euromlsys25-27.pdf
- "The Price of Prompting: Profiling Energy Use in LLM Inference"
  — https://arxiv.org/pdf/2407.16893

## Context / cross-reference

- **Stanford AI Index** — https://hai.stanford.edu/ai-index — model counts, investment,
  environmental trends. Per-chart data published as downloadable spreadsheets.
- **Our World in Data — AI** — https://ourworldindata.org/artificial-intelligence —
  clean CSVs built on Epoch data (compute-over-time, energy).


