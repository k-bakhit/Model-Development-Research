import streamlit as st
import plotly.express as px
from utils import load_models, chart_notes, page_header, missing_data_notice

st.set_page_config(page_title="Model Production", page_icon="🏭", layout="wide")
page_header("🏭 Model Production", "Who is shipping the most AI models, and how that has changed over time.")

models = load_models()
if models is None:
    missing_data_notice("master_models.csv"); st.stop()

# controls
c1, c2, c3 = st.columns([1, 1, 1])
with c1:
    yr = st.slider("Year range", 2012, int(models["year"].max()), (2018, int(models["year"].max())))
with c2:
    n_co = st.slider("Companies to show (top N)", 3, 12, 6)
with c3:
    view = st.radio("View", ["Per year", "Cumulative"], horizontal=True)

m = models[(models["year"] >= yr[0]) & (models["year"] <= yr[1])].dropna(subset=["company"])
top = m["company"].value_counts().head(n_co).index.tolist()
sub = m[m["company"].isin(top)]

counts = sub.groupby(["year", "company"]).size().reset_index(name="models")
if view == "Cumulative":
    counts["models"] = counts.sort_values("year").groupby("company")["models"].cumsum()

fig = px.line(counts, x="year", y="models", color="company", markers=True,
              labels={"models": "Models released", "year": "Year"})
fig.update_layout(height=480, legend_title_text="Company", hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

chart_notes(
    what="The number of notable AI models each company released per year (or cumulatively). "
         "Companies are merged where they're the same org under different names (e.g. Google + DeepMind).",
    why="This is the most direct read on the project's headline question — raw model *output* by company. "
        "It measures production volume, which is one half of 'developing the most.'",
    how="Counts come from the Epoch AI 'notable models' database, grouped by developer and release year. "
        "Pre-2015 data is sparse (mostly academic), so the default view starts at 2018.",
    limitations="This counts **quantity, not capability** — 20 minor models is not the same as one frontier model. "
                "The most recent year is **incomplete**, so its counts under-represent reality and should not be read as a decline. "
                "Counts also depend on Epoch's 'notable' inclusion criteria.",
    source_keys=["epoch"],
    quality="Measured/curated — Epoch's database is human-curated from papers and announcements.",
)

with st.expander("📊 Total models in selected range"):
    st.dataframe(sub["company"].value_counts().rename_axis("company").reset_index(name="models"),
                 use_container_width=True, hide_index=True)
