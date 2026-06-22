import streamlit as st
from utils import page_header, inject_theme

st.set_page_config(page_title="Sources & Methodology", page_icon="📚", layout="wide")
inject_theme()
page_header("📚 Sources & Methodology",
            "Where every dataset came from, why, its strengths and weaknesses, and all disclaimers.")

st.markdown(
    "This page is the integrity backbone of the dashboard. Every chart links here. "
    "If a number ever looks surprising, this is where you check how it was produced."
)

# source quality
st.subheader("How to read every figure: the quality tag")
st.markdown(
    "- **Measured** — directly measured on known hardware (e.g. ML.Energy GPU measurements).\n"
    "- **Vendor-reported** — published by the developer (e.g. official API prices).\n"
    "- **Estimated** — inferred via a documented formula (e.g. closed-model energy). "
    "Estimates are always shown as ranges, never single numbers."
)
st.divider()

# about sources
st.subheader("Data sources — what, why, pros & cons")

SRC = [
    ("Epoch AI — Data on AI Models", "https://epoch.ai/data/ai-models", "Model specs backbone",
     "Parameters, training compute (FLOP), training power draw, cost, country, release date for 1,000+ notable models.",
     "Best-curated public database of AI models; free and citable; consistent methodology.",
     "Closed-model parameters are estimates; 'notable' inclusion is a judgement call; skews to research/older models."),
    ("Artificial Analysis", "https://artificialanalysis.ai/", "Current pricing & benchmarks",
     "Today's API prices and independent intelligence/coding/math indices across 500+ endpoints.",
     "Comprehensive, current, independent benchmarking; clean API.",
     "Snapshot only (no history); lists currently-served commercial endpoints, so overlap with older models is small."),
    ("Internet Archive (Wayback Machine)", "https://web.archive.org/", "Historical pricing",
     "Archived snapshots of provider pricing pages, used to reconstruct price-over-time.",
     "The only way to recover historical list prices; free.",
     "Many pages are JavaScript shells that archived empty (esp. Anthropic pre-2025); requires per-provider parsing; rate-limited."),
    ("ML.Energy Leaderboard", "https://ml.energy/leaderboard", "Measured inference energy",
     "GPU energy per token for open-weight models, measured with the Zeus library.",
     "Real, independent measurement — the gold standard for inference energy.",
     "Open models only; depends on specific GPUs/batch sizes; large per-run variance; gated dataset (needs HF login)."),
    ("LifeArchitect.ai Models Table", "https://lifearchitect.ai/models-table/", "Benchmark cross-reference",
     "Benchmark scores (MMLU, GPQA), labs, release dates.",
     "Broad hand-maintained coverage; good cross-check.",
     "Compute/energy columns are paywalled (we use Epoch for those); single-maintainer."),
    ("FRED (St. Louis Fed)", "https://fred.stlouisfed.org/", "Inflation & energy CPI",
     "Overall CPI, energy CPI, electricity CPI time series.",
     "Authoritative government data; clean API; long history.",
     "Monthly frequency differs from other series; CPI is a national aggregate, not AI-specific."),
    ("EIA — Electricity data", "https://www.eia.gov/opendata/", "Electricity price",
     "U.S. retail electricity price (¢/kWh) over time, by state and sector.",
     "Authoritative; granular; free API.",
     "Per-state detail must be aggregated (we use a sales-weighted national average); U.S. only."),
]
for name, url, role, what, pro, con in SRC:
    with st.expander(f"**{name}** — {role}"):
        st.markdown(f"[{url}]({url})")
        st.markdown(f"**What we use it for.** {what}")
        st.markdown(f"**Pros.** {pro}")
        st.markdown(f"**Cons / caveats.** {con}")

st.divider()

# methodology
st.subheader("Key methods")
with st.expander("Energy metric — `energy_wh_per_1k`"):
    st.markdown(
        "Watt-hours of GPU energy per 1,000 **output** tokens. Computed from ML.Energy's measured "
        "energy-per-token in Joules: `energy_wh_per_1k = J_per_token × 1000 / 3600`. The per-model "
        "headline is the **median** across that model's measured tasks; hardware is recorded because "
        "energy/token is hardware-dependent.")
with st.expander("Closed-model energy estimation (why it's hard, and not ML)"):
    st.markdown(
        "GPT/Claude/Gemini energy is never measured. A trained ML model would be unreliable here — too "
        "few data points (~16 open models) and closed models sit outside that range. Instead we use a "
        "physics-grounded formula `energy ≈ k × active_params`, calibrated to the measured open models "
        "(**k ≈ 0.0054 Wh/1k per B active param**), and report a **range** (≈ ÷2.4 to ×3.6) measured from "
        "how far that formula misses on known models. This error band is a *lower* bound — closed models "
        "are harder, not easier, to predict. Such figures are tagged **estimated**.")
with st.expander("Pricing reconstruction & cleaning"):
    st.markdown(
        "Historical prices come from Wayback snapshots, cleaned per provider: OpenAI from inline page text; "
        "Anthropic & Google parsed **structurally** from HTML tables (flattening to text loses the input/"
        "cache/output column meaning and produces wrong numbers). All normalized to USD per 1,000,000 tokens.")
with st.expander("How model sources are joined"):
    st.markdown(
        "Sources are merged onto the Epoch backbone via a normalized name key (lowercased, punctuation "
        "stripped). Merges are left joins, so no model is dropped; unmatched sources leave blank columns. "
        "Match rates are partial by design and reported in `processed/join_report.txt`.")

st.divider()

# disclaimers
st.subheader("⚠️ Disclaimers")
st.markdown(
    "1. **Independent project, not an official source.** Figures are best-effort research.\n"
    "2. **Estimates are ranges, never exact.** Closed-model energy especially.\n"
    "3. **Correlation ≠ causation** on the Economy page.\n"
    "4. **Incomplete current year** under-counts recent models.\n"
    "5. **Prices are list/API rates**, not negotiated, batch, or cached pricing unless noted.\n"
    "6. **Energy depends on hardware/batch size** and carries large real-world variance.\n"
    "7. Data reflects the snapshot it was collected on; re-run the `Research/scripts/` to refresh."
)

st.divider()
st.subheader("Reproducibility")
st.markdown(
    "All raw data, fetch/clean scripts, and a full written methodology live in the project repo under "
    "`Research/scripts/` and `Research/docs/`. Each processed CSV is regenerable from those scripts."
)
