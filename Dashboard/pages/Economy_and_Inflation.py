import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import load_macro, load_electricity, load_pricing, chart_notes, page_header, missing_data_notice

st.set_page_config(page_title="Economy & Inflation", page_icon="📈", layout="wide")
page_header("📈 Economy & Inflation",
            "Does token price track inflation or electricity cost — or is something else driving it?")

macro = load_macro()
elec = load_electricity()
pricing = load_pricing()
if macro is None or elec is None:
    missing_data_notice("macro.csv / electricity_price_national.csv"); st.stop()

c1, c2 = st.columns([1, 1])
with c1:
    start = st.slider("From year", 2010, 2025, 2020)
with c2:
    show_price = st.checkbox("Overlay a model's token price", value=pricing is not None)

macro = macro[macro["date"].dt.year >= start]
elec = elec[elec["period"].dt.year >= start]

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Scatter(x=macro["date"], y=macro["all_items_cpi"], name="CPI (all items)",
                         line=dict(color="#64748b")), secondary_y=False)
fig.add_trace(go.Scatter(x=macro["date"], y=macro["energy_cpi"], name="Energy CPI",
                         line=dict(color="#f59e0b")), secondary_y=False)
fig.add_trace(go.Scatter(x=elec["period"], y=elec["price_cents_per_kwh"], name="Electricity (¢/kWh)",
                         line=dict(color="#10b981", dash="dot")), secondary_y=True)

if show_price and pricing is not None:
    oai = (pricing[(pricing.provider == "openai")]
           .dropna(subset=["output_price_per_1m"]).sort_values("date"))
    if len(oai):
        g = oai.groupby("date")["output_price_per_1m"].min().reset_index()
        fig.add_trace(go.Scatter(x=g["date"], y=g["output_price_per_1m"],
                                 name="Cheapest OpenAI output $/1M", line=dict(color="#2563eb", width=3)),
                      secondary_y=True)

fig.update_layout(height=520, hovermode="x unified", legend=dict(orientation="h", y=-0.2))
fig.update_yaxes(title_text="Index (CPI)", secondary_y=False)
fig.update_yaxes(title_text="¢/kWh  &  $/1M tokens", secondary_y=True)
st.plotly_chart(fig, use_container_width=True)

chart_notes(
    what="Macro-economic context — overall inflation (CPI), energy CPI, and real U.S. electricity price — "
         "optionally overlaid with a model's token price, so you can eyeball whether they move together.",
    why="Answers the guiding question: is the change in 'credit price' explained by inflation or energy cost? "
        "If token prices fall while energy rises, the driver is something else (competition, efficiency gains).",
    how="Inflation/energy CPI from FRED; electricity price from the EIA (sales-weighted national average). "
        "Token price is the cheapest OpenAI output price per snapshot, from the cleaned pricing history.",
    limitations="**Correlation is not causation.** Different series have different frequencies (monthly CPI vs. "
                "quarterly electricity vs. per-release pricing) and are shown on a shared time axis, not statistically "
                "joined. Token price uses dual axis, so visual 'crossings' are not meaningful — compare *trends*, not levels.",
    source_keys=["fred", "eia", "wayback"],
    quality="Measured/official — FRED and EIA are government statistical series.",
)
