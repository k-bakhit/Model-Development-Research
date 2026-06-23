import streamlit as st
import plotly.express as px
from utils import load_pricing, chart_notes, page_header, missing_data_notice

st.set_page_config(page_title="Pricing Over Time", page_icon="💰", layout="wide")
page_header("💰 Pricing Over Time", "How the price of tokens has changed — by model, lineage, and company.")

pricing = load_pricing()
if pricing is None:
    missing_data_notice("pricing_history.csv"); st.stop()

# controls
c1, c2, c3 = st.columns([1.2, 1, 1])
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

models = st.multiselect("Models (leave empty for all)", sorted(p["model"].unique()))
if models:
    p = p[p["model"].isin(models)]

fig = px.line(p.sort_values("date"), x="date", y="price", color="model", markers=True,
              labels={"price": f"{side} price (USD / {unit})", "date": "Date"})
fig.update_layout(height=500, hovermode="x unified", legend_title_text="Model")
st.plotly_chart(fig, use_container_width=True)

chart_notes(
    what=f"{side} token price over time, expressed per {unit}. Each line is a model; toggle providers, "
         "models, input/output, and the per-token unit.",
    why="Directly answers the guiding questions on price trends — same model over time, model lineages "
        "(GPT-3 → GPT-5), and company vs. company. Token price is the clearest proxy for cost-efficiency to the user.",
    how="Prices were reconstructed from archived pricing pages (Wayback Machine) and cleaned per provider: "
        "OpenAI parsed from page text; Anthropic & Google parsed structurally from HTML tables. All normalized "
        "to USD per 1,000,000 tokens, then rescaled to your chosen unit.",
    limitations="**OpenAI** has the fullest history (2021→2026). **Anthropic** prices are correct but only cover "
                "mid-2025 onward (earlier pages were JavaScript shells with no archived prices). **Google** is recent "
                "and best-effort (its tables mix modalities/tiers). A few early points may carry small attribution "
                "errors across model variants. Prices are list/API prices, not negotiated or batch rates.",
    source_keys=["wayback", "aa"],
    quality="Vendor-reported (the prices are the providers' own), recovered via archive + parsing.",
)
