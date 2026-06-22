"""
Shared helpers + design system for the AI Model Development & Efficiency dashboard.
Data loading (cached), company normalization, a professional theme (CSS), KPI cards,
and a unified Plotly style so every chart looks consistent and clean.
"""
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "Research" / "processed"

# ---------------------------------------------------------------- design tokens
INK = "#0f172a"          # near-black navy text
MUTED = "#64748b"        # secondary text
ACCENT = "#2563eb"       # primary blue
GOOD = "#16a34a"
BAD = "#dc2626"
CARD_BG = "#ffffff"
APP_BG = "#f4f6f9"
BORDER = "#e6e9ef"
PALETTE = ["#2563eb", "#0ea5e9", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444", "#64748b", "#14b8a6"]

COMPANY_MERGE = {
    "Google DeepMind": "Google", "DeepMind": "Google", "Google Brain": "Google",
    "Meta AI": "Meta", "Facebook AI Research": "Meta", "FAIR": "Meta",
    "Microsoft Research": "Microsoft",
}

SOURCES = {
    "epoch": ("Epoch AI – Data on AI Models", "https://epoch.ai/data/ai-models"),
    "aa": ("Artificial Analysis", "https://artificialanalysis.ai/"),
    "mlenergy": ("ML.Energy Leaderboard", "https://ml.energy/leaderboard"),
    "lifearch": ("LifeArchitect.ai Models Table", "https://lifearchitect.ai/models-table/"),
    "fred": ("FRED (St. Louis Fed)", "https://fred.stlouisfed.org/"),
    "eia": ("EIA – Electricity data", "https://www.eia.gov/opendata/"),
    "wayback": ("Internet Archive (Wayback Machine)", "https://web.archive.org/"),
}


# ============================================================ THEME (global CSS)
def inject_theme():
    st.markdown(f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

      html, body, [class*="css"], .stMarkdown, .stApp {{
          font-family: 'Inter', -apple-system, sans-serif;
          color: {INK};
      }}
      .stApp {{ background: {APP_BG}; }}

      /* hide default Streamlit chrome */
      #MainMenu, header[data-testid="stHeader"], footer {{ visibility: hidden; height: 0; }}
      [data-testid="stToolbar"], [data-testid="stDecoration"] {{ display: none; }}

      .block-container {{ padding: 1.4rem 2.2rem 3rem 2.2rem; max-width: 1400px; }}

      /* sidebar */
      [data-testid="stSidebar"] {{ background: #ffffff; border-right: 1px solid {BORDER}; }}
      [data-testid="stSidebar"] .stMarkdown {{ color: {INK}; }}

      /* headings */
      h1 {{ font-weight: 800; letter-spacing: -0.02em; font-size: 1.9rem; }}
      h2 {{ font-weight: 700; letter-spacing: -0.01em; }}
      h3 {{ font-weight: 600; }}

      /* bordered containers become cards */
      [data-testid="stVerticalBlockBorderWrapper"] {{
          background: {CARD_BG};
          border: 1px solid {BORDER} !important;
          border-radius: 14px;
          padding: 6px 14px 10px 14px;
          box-shadow: 0 1px 2px rgba(15,23,42,0.04), 0 4px 12px rgba(15,23,42,0.03);
      }}

      /* KPI cards */
      .kpi-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 16px; margin: 6px 0 4px 0; }}
      .kpi {{ background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 14px; padding: 18px 20px;
              box-shadow: 0 1px 2px rgba(15,23,42,0.04), 0 4px 12px rgba(15,23,42,0.03); }}
      .kpi .label {{ font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: .06em; color: {MUTED}; }}
      .kpi .value {{ font-size: 2.05rem; font-weight: 800; letter-spacing: -0.03em; color: {INK}; line-height: 1.1; margin-top: 4px; }}
      .kpi .delta {{ font-size: 0.8rem; font-weight: 600; margin-top: 6px; }}
      .kpi .delta.good {{ color: {GOOD}; }}
      .kpi .delta.bad {{ color: {BAD}; }}
      .kpi .sub {{ font-size: 0.72rem; color: {MUTED}; margin-top: 2px; }}

      /* widgets */
      .stButton>button, .stDownloadButton>button {{
          border-radius: 9px; border: 1px solid {BORDER}; font-weight: 600; }}
      div[data-baseweb="select"] > div {{ border-radius: 9px; border-color: {BORDER}; }}

      /* tighten metric default just in case */
      [data-testid="stMetricValue"] {{ font-weight: 800; }}

      /* hero band */
      .hero {{ background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
               color: #fff; border-radius: 16px; padding: 26px 30px; margin-bottom: 18px; }}
      .hero h1 {{ color: #fff; margin: 0 0 6px 0; }}
      .hero p {{ color: #cbd5e1; margin: 0; font-size: 0.98rem; max-width: 760px; }}
      .pill {{ display:inline-block; background: rgba(255,255,255,0.12); color:#e2e8f0;
               border-radius: 999px; padding: 3px 12px; font-size: 0.72rem; font-weight:600; margin-top:12px; }}
    </style>
    """, unsafe_allow_html=True)


def kpi_row(cards):
    """cards: list of dicts {label, value, delta(optional), delta_good(bool), sub(optional)}"""
    html = '<div class="kpi-row">'
    for c in cards:
        delta = ""
        if c.get("delta"):
            cls = "good" if c.get("delta_good", True) else "bad"
            arrow = "▲" if c.get("delta_good", True) else "▼"
            delta = f'<div class="delta {cls}">{arrow} {c["delta"]}</div>'
        sub = f'<div class="sub">{c["sub"]}</div>' if c.get("sub") else ""
        html += (f'<div class="kpi"><div class="label">{c["label"]}</div>'
                 f'<div class="value">{c["value"]}</div>{delta}{sub}</div>')
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def style_fig(fig, height=420, legend_bottom=True):
    """Unified clean Plotly look."""
    fig.update_layout(
        template="plotly_white",
        height=height,
        font=dict(family="Inter, sans-serif", size=13, color=INK),
        colorway=PALETTE,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(font_family="Inter", bgcolor="white", bordercolor=BORDER),
        title=dict(font=dict(size=15, color=INK)),
    )
    if legend_bottom:
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                      xanchor="left", x=0, title_text=""))
    fig.update_xaxes(showgrid=False, linecolor=BORDER, ticks="outside", tickcolor=BORDER)
    fig.update_yaxes(showgrid=True, gridcolor="#eef1f6", zeroline=False)
    return fig


# ============================================================ DATA LOADERS
def _safe_read(name):
    p = PROC / name
    return pd.read_csv(p) if p.exists() else None


@st.cache_data(show_spinner=False)
def load_models():
    df = _safe_read("master_models.csv")
    if df is None: return None
    df["year"] = pd.to_datetime(df["release_date"], errors="coerce").dt.year
    df["company"] = df["developer"].replace(COMPANY_MERGE)
    return df


@st.cache_data(show_spinner=False)
def load_pricing():
    df = _safe_read("pricing_history.csv")
    if df is None: return None
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def load_macro():
    df = _safe_read("macro.csv")
    if df is None: return None
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def load_electricity():
    df = _safe_read("electricity_price_national.csv")
    if df is None: return None
    df["period"] = pd.to_datetime(df["period"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def load_energy():
    return _safe_read("mlenergy_energy_by_model.csv")


# ============================================================ SHARED UI BITS
def missing_data_notice(name):
    st.warning(f"**{name}** isn't available yet. Run the matching script in "
               f"`Research/scripts/` (see Sources & Methodology), then reload.")


def source_links(*keys):
    return " · ".join(f"[{SOURCES[k][0]}]({SOURCES[k][1]})" for k in keys if k in SOURCES)


def chart_notes(what, why, how, limitations, source_keys, quality=None):
    with st.expander("About this chart — what it shows, how it was made, limitations & sources"):
        st.markdown(f"**What it shows.** {what}")
        st.markdown(f"**Why it matters.** {why}")
        st.markdown(f"**How it was built.** {how}")
        st.markdown(f"**Limitations & disclaimers.** {limitations}")
        if quality:
            st.markdown(f"**Data quality.** {quality}")
        st.markdown(f"**Sources.** {source_links(*source_keys)}")


def page_header(title, subtitle):
    st.markdown(f"<h1>{title}</h1><p style='color:{MUTED};margin-top:-6px;font-size:0.95rem'>{subtitle}</p>",
                unsafe_allow_html=True)
    st.write("")
