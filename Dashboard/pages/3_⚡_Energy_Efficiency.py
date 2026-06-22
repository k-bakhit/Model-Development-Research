import streamlit as st
import plotly.express as px
from utils import (load_energy, chart_notes, page_header, missing_data_notice,
                   inject_theme, style_fig)

st.set_page_config(page_title="Energy Efficiency", page_icon="⚡", layout="wide")
inject_theme()
page_header("⚡ Energy Efficiency", "Measured inference energy per N tokens — comparing models on equal footing.")

energy = load_energy()
if energy is None:
    missing_data_notice("mlenergy_energy_by_model.csv"); st.stop()

st.warning(
    "**Measured** figures for **open-weight models only** (Llama, Qwen, Mistral…). Closed models "
    "(GPT, Claude, Gemini) are **not** shown — their inference energy is never disclosed or independently "
    "measured. Any closed-model energy would be an estimate (see Sources & Methodology).",
    icon="⚠️",
)

with st.container(border=True):
    c1, c2 = st.columns(2)
    with c1:
        unit = st.selectbox("Energy per", ["1,000 tokens", "10,000 tokens",
                                           "100,000 tokens", "1,000,000 tokens"], index=0)
    with c2:
        n_show = st.slider("Models to show (most efficient first)", 5, len(energy), min(20, len(energy)))

unit_factor = {"1,000 tokens": 1, "10,000 tokens": 10, "100,000 tokens": 100, "1,000,000 tokens": 1000}[unit]
e = energy.copy()
e["wh"] = e["energy_wh_per_1k"] * unit_factor
e = e.dropna(subset=["wh"]).sort_values("wh").head(n_show)

with st.container(border=True):
    st.markdown(f"**Energy to generate {unit}** · color = model size (B params)")
    fig = px.bar(e, x="wh", y="nickname", orientation="h", color="total_params_billions",
                 color_continuous_scale="Blues",
                 labels={"wh": f"Wh per {unit}", "nickname": "", "total_params_billions": "Params (B)"})
    fig.update_layout(yaxis={"categoryorder": "total descending"})
    st.plotly_chart(style_fig(fig, height=28 * len(e) + 130, legend_bottom=False), use_container_width=True)

    chart_notes(
        what=f"Watt-hours of GPU energy to generate {unit}, per model, most-efficient first. Color = model size.",
        why="Energy per token is the core efficiency metric. Shows which models do the most work per unit of energy.",
        how="Measured by ML.Energy (GPU energy via Zeus). Headline = median across the model's tasks; energy-per-token "
            "(J) converted to Wh per 1k (÷3600 ×1000), then rescaled to your unit.",
        limitations="**Open models only.** Energy depends on hardware/batch size; figures mix GPUs, so treat gaps under "
                    "~2× as noise. The median hides real per-run variance (up to ~10× under load).",
        source_keys=["mlenergy"],
        quality="Measured — independent GPU-level measurement.",
    )

with st.container(border=True):
    st.markdown("**Underlying data** · with min/max range and GPUs")
    st.dataframe(energy[["nickname", "total_params_billions", "energy_wh_per_1k",
                         "energy_wh_per_1k_min", "energy_wh_per_1k_max", "gpus", "tasks_measured"]],
                 use_container_width=True, hide_index=True)
    st.download_button("⬇ Download energy data (CSV)", energy.to_csv(index=False),
                       "energy_by_model.csv", "text/csv")
