"""AI Model Development & Efficiency Dashboard — Home. Run: streamlit run Dashboard/Home.py"""
import streamlit as st
import plotly.express as px
from utils import (inject_theme, kpi_row, style_fig, page_header,
                   load_models, load_pricing, load_energy, load_electricity, ACCENT)

st.set_page_config(page_title="AI Model Development & Efficiency", page_icon="🤖", layout="wide")
inject_theme()

# ---------------- hero ----------------
st.markdown("""
<div class="hero">
  <h1>AI Model Development &amp; Efficiency</h1>
  <p>Tracking which company is developing the most — in model <b>production</b> and
  <b>efficiency</b> — and how token price and energy use have shifted over time.</p>
  <span class="pill">Independent research · every figure tagged measured / vendor-reported / estimated</span>
</div>
""", unsafe_allow_html=True)

models = load_models()
pricing = load_pricing()
energy = load_energy()
elec = load_electricity()

# ---------------- KPI cards ----------------
top_company = models["company"].value_counts().idxmax() if models is not None else "—"
yrs = f"{int(elec['period'].dt.year.min())}–{int(elec['period'].dt.year.max())}" if elec is not None else "—"
kpi_row([
    {"label": "Models tracked", "value": f"{len(models):,}" if models is not None else "—",
     "sub": "Epoch notable models"},
    {"label": "Most prolific company", "value": top_company, "sub": "by model count (2015–26)"},
    {"label": "Price points over time", "value": f"{len(pricing):,}" if pricing is not None else "—",
     "sub": "OpenAI · Anthropic · Google"},
    {"label": "Measured-energy models", "value": f"{len(energy):,}" if energy is not None else "—",
     "sub": "open-weight, ML.Energy"},
    {"label": "Electricity series", "value": yrs, "sub": "EIA national avg"},
])

st.write("")

# ---------------- preview charts in cards ----------------
left, right = st.columns([1.3, 1])
with left:
    with st.container(border=True):
        st.markdown("**Model output by company**")
        if models is not None:
            m = models[(models.year >= 2018) & (models.year <= 2026)].dropna(subset=["company"])
            top = m.company.value_counts().head(5).index
            cc = m[m.company.isin(top)].groupby(["year", "company"]).size().reset_index(name="models")
            fig = px.line(cc, x="year", y="models", color="company", markers=True)
            st.plotly_chart(style_fig(fig, height=320), use_container_width=True)
with right:
    with st.container(border=True):
        st.markdown("**Most efficient models** · Wh / 1k tokens")
        if energy is not None:
            e = energy.dropna(subset=["energy_wh_per_1k"]).nsmallest(8, "energy_wh_per_1k")
            fig = px.bar(e, x="energy_wh_per_1k", y="nickname", orientation="h",
                         color_discrete_sequence=[ACCENT])
            fig.update_layout(yaxis={"categoryorder": "total descending"})
            st.plotly_chart(style_fig(fig, height=320, legend_bottom=False), use_container_width=True)

# ---------------- nav + disclaimer ----------------
with st.container(border=True):
    st.markdown("**Explore**  —  use the sidebar to open each tab")
    a, b, c, d, e = st.columns(5)
    a.markdown("🏭 **Model Production**\n\nWho ships the most, over time.")
    b.markdown("💰 **Pricing Over Time**\n\nToken price trends, customizable.")
    c.markdown("⚡ **Energy Efficiency**\n\nMeasured energy per N tokens.")
    d.markdown("📈 **Economy & Inflation**\n\nPrice vs. inflation & power cost.")
    e.markdown("📚 **Sources & Methodology**\n\nProvenance, pros/cons, disclaimers.")

st.caption("⚠️ Independent project, not an official source. Estimates are shown as ranges. "
           "Closed-model energy is never measured directly. See **Sources & Methodology** for full disclaimers.")

if models is None:
    st.error("No processed data found. Generate the CSVs in `Research/processed/`, then reload.")
