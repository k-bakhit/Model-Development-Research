import streamlit as st
import plotly.express as px
from utils import (load_pricing, chart_notes, page_header, missing_data_notice,
                   inject_theme, style_fig)

st.set_page_config(page_title="Pricing Over Time", page_icon="💰", layout="wide")
inject_theme()
page_header("💰 Pricing Over Time", "How the price of tokens has changed — by model, lineage, and company.")

pricing = load_pricing()
if pricing is None:
    missing_data_notice("pricing_history.csv"); st.stop()

with st.container(border=True):
    c1, c2, c3 = st.columns([1.3, 1, 1])
    with c1:
        providers = st.multiselect("Providers", sorted(pricing["provider"].unique()),
                                   default=sorted(pricing["provider"].unique()))
    with c2:
        side = st.radio("Price type", ["Output", "Input"], horizontal=True)
    with c3:
        unit = st.selectbox("Show price per", ["1,000 tokens", "10,000 tokens",
                                               "100,000 tokens", "1,000,000 tokens"], index=0)

unit_factor = {"1,000 tokens": 1/1000, "10,000 tokens": 1/100,
               "100,000 tokens": 1/10, "1,000,000 tokens": 1.0}[unit]
col = "output_price_per_1m" if side == "Output" else "input_price_per_1m"

p = pricing[pricing["provider"].isin(providers)].dropna(subset=[col]).copy()
p["price"] = p[col] * unit_factor
sel = st.multiselect("Models (leave empty for all)", sorted(p["model"].unique()))
if sel:
    p = p[p["model"].isin(sel)]

with st.container(border=True):
    st.markdown(f"**{side} token price over time** · USD per {unit}")
    fig = px.line(p.sort_values("date"), x="date", y="price", color="model", markers=True,
                  labels={"price": f"{side} $/{unit}", "date": "Date"})
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(style_fig(fig, height=500), use_container_width=True)

    chart_notes(
        what=f"{side} token price over time, per {unit}. Toggle providers, models, input/output, and unit.",
        why="Answers the price-trend questions — same model over time, lineages (GPT-3→GPT-5), company vs. company. "
            "Token price is the clearest cost-efficiency proxy to the user.",
        how="Prices reconstructed from Wayback snapshots and cleaned per provider (OpenAI from page text; Anthropic "
            "& Google from HTML tables). Normalized to USD per 1,000,000 tokens, then rescaled to your unit.",
        limitations="**OpenAI** has the fullest history (2021→2026). **Anthropic** is correct but mid-2025 onward only "
                    "(earlier pages archived empty). **Google** is recent and best-effort. List/API prices, not batch/negotiated.",
        source_keys=["wayback", "aa"],
        quality="Vendor-reported, recovered via archive + parsing.",
    )
    st.download_button("⬇ Download filtered prices (CSV)", p.to_csv(index=False),
                       "pricing_filtered.csv", "text/csv")
