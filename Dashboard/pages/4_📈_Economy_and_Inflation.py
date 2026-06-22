import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import (load_macro, load_electricity, load_pricing, chart_notes,
                   page_header, missing_data_notice, inject_theme, style_fig, PALETTE)

st.set_page_config(page_title="Economy & Inflation", page_icon="📈", layout="wide")
inject_theme()
page_header("📈 Economy & Inflation",
            "Does token price track inflation or electricity cost — or is something else driving it?")

macro = load_macro()
elec = load_electricity()
pricing = load_pricing()
if macro is None or elec is None:
    missing_data_notice("macro.csv / electricity_price_national.csv"); st.stop()

with st.container(border=True):
    c1, c2 = st.columns(2)
    with c1:
        start = st.slider("From year", 2010, 2025, 2020)
    with c2:
        show_price = st.checkbox("Overlay cheapest OpenAI token price", value=pricing is not None)

macro = macro[macro["date"].dt.year >= start]
elec = elec[elec["period"].dt.year >= start]

with st.container(border=True):
    st.markdown("**Inflation, electricity price & token price over time**")
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=macro["date"], y=macro["all_items_cpi"], name="CPI (all items)",
                             line=dict(color=PALETTE[6])), secondary_y=False)
    fig.add_trace(go.Scatter(x=macro["date"], y=macro["energy_cpi"], name="Energy CPI",
                             line=dict(color=PALETTE[3])), secondary_y=False)
    fig.add_trace(go.Scatter(x=elec["period"], y=elec["price_cents_per_kwh"], name="Electricity ¢/kWh",
                             line=dict(color=PALETTE[2], dash="dot")), secondary_y=True)
    if show_price and pricing is not None:
        oai = pricing[pricing.provider == "openai"].dropna(subset=["output_price_per_1m"])
        if len(oai):
            g = oai.groupby("date")["output_price_per_1m"].min().reset_index()
            fig.add_trace(go.Scatter(x=g["date"], y=g["output_price_per_1m"],
                                     name="Cheapest OpenAI $/1M", line=dict(color=PALETTE[0], width=3)),
                          secondary_y=True)
    fig.update_yaxes(title_text="Index (CPI)", secondary_y=False)
    fig.update_yaxes(title_text="¢/kWh & $/1M", secondary_y=True)
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(style_fig(fig, height=520), use_container_width=True)

    chart_notes(
        what="Macro context — overall inflation (CPI), energy CPI, real U.S. electricity price — optionally "
             "overlaid with token price, to eyeball whether they move together.",
        why="Tests whether 'credit price' changes are explained by inflation or energy cost. If token prices fall "
            "while energy rises, the driver is something else (competition, efficiency gains).",
        how="Inflation/energy CPI from FRED; electricity from EIA (sales-weighted national avg); token price is the "
            "cheapest OpenAI output price per snapshot.",
        limitations="**Correlation is not causation.** Series have different frequencies and share a time axis but are "
                    "not statistically joined. Dual axis means visual 'crossings' are meaningless — compare *trends*, not levels.",
        source_keys=["fred", "eia", "wayback"],
        quality="Official — FRED and EIA government statistical series.",
    )
