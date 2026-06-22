import streamlit as st
import plotly.express as px
from utils import load_energy, chart_notes, page_header, missing_data_notice

st.set_page_config(page_title="Energy Efficiency", page_icon="⚡", layout="wide")
page_header("⚡ Energy Efficiency", "Measured inference energy per N tokens — comparing models on equal footing.")

energy = load_energy()
if energy is None:
    missing_data_notice("mlenergy_energy_by_model.csv"); st.stop()

st.warning(
    "These are **measured** energy figures for **open-weight models only** (Llama, Qwen, Mistral, etc.). "
    "Closed models (GPT, Claude, Gemini) are **not** shown because their inference energy is never disclosed "
    "or independently measured — any closed-model energy would be an estimate, covered in Sources & Methodology.",
    icon="⚠️",
)

# ---------------- controls ----------------
c1, c2 = st.columns([1, 1])
with c1:
    unit = st.selectbox("Energy per", ["1,000 tokens", "10,000 tokens",
                                       "100,000 tokens", "1,000,000 tokens"], index=0)
with c2:
    n_show = st.slider("Models to show (most efficient first)", 5, len(energy), min(20, len(energy)))

unit_factor = {"1,000 tokens": 1, "10,000 tokens": 10,
               "100,000 tokens": 100, "1,000,000 tokens": 1000}[unit]

e = energy.copy()
e["wh"] = e["energy_wh_per_1k"] * unit_factor
e = e.dropna(subset=["wh"]).sort_values("wh").head(n_show)

fig = px.bar(e, x="wh", y="nickname", orientation="h",
             color="total_params_billions",
             color_continuous_scale="Viridis",
             labels={"wh": f"Wh per {unit}", "nickname": "Model",
                     "total_params_billions": "Params (B)"})
fig.update_layout(height=28 * len(e) + 120, yaxis={"categoryorder": "total descending"})
st.plotly_chart(fig, use_container_width=True)

chart_notes(
    what=f"Watt-hours of GPU energy to generate {unit}, per model, sorted most-efficient first. "
         "Color encodes model size (billions of parameters).",
    why="Energy per token is the core efficiency metric of the project. It reveals which models do the most "
        "work per unit of energy, and how efficiency scales with model size.",
    how="Measured by the ML.Energy benchmark (GPU energy via the Zeus library). The headline figure is the "
        "median across that model's measured tasks; we convert the package's energy-per-token (Joules) to "
        "watt-hours per 1k tokens (÷3600 ×1000), then rescale to your chosen unit.",
    limitations="**Open models only** — closed models can't be measured and are excluded. Energy depends heavily "
                "on **hardware and batch size**; figures mix GPUs (H100/B200) so treat cross-model gaps of less "
                "than ~2× as noise. The median hides real per-run variance (a model can swing 10× under load).",
    source_keys=["mlenergy"],
    quality="Measured — independent GPU-level measurement on known hardware.",
)

with st.expander("📊 Underlying data (with min/max range and GPUs)"):
    st.dataframe(energy[["nickname", "total_params_billions", "energy_wh_per_1k",
                         "energy_wh_per_1k_min", "energy_wh_per_1k_max", "gpus", "tasks_measured"]],
                 use_container_width=True, hide_index=True)
