# Deploying the dashboard

The dashboard is a multi-page **Streamlit** app in `Dashboard/`. It reads the cleaned
CSVs in `Research/processed/`. Below: run it locally first, then deploy free on
Streamlit Community Cloud.

## 1. Run locally

From the **repo root**:

```bash
# one-time setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# launch
streamlit run Dashboard/Home.py
```

Your browser opens at `http://localhost:8501`. Edit a file and it hot-reloads.

**If a page shows "data isn't available yet"**, the matching CSV in `Research/processed/`
hasn't been generated — run the relevant script in `Research/scripts/` (or the FRED notebook),
then reload.

## 2. Make sure the data is committed

Streamlit Cloud clones your GitHub repo and runs from it, so the app can only see files
that are **pushed**. Confirm these are committed (they're not gitignored):

- `Research/processed/master_models.csv`
- `Research/processed/pricing_history.csv`
- `Research/processed/macro.csv`
- `Research/processed/electricity_price_national.csv`
- `Research/processed/mlenergy_energy_by_model.csv`

```bash
git add Research/processed Dashboard requirements.txt
git commit -m "Add interactive Streamlit dashboard"
git push
```

> Your API keys stay out — the `.env` files remain gitignored. The dashboard only reads
> the already-generated CSVs, so it needs **no keys** to run.

## 3. Deploy on Streamlit Community Cloud (free)

1. Go to **https://share.streamlit.io** and sign in with GitHub.
2. Click **Create app → Deploy a public app from GitHub**.
3. Fill in:
   - **Repository:** `k-bakhit/Model-Development-Research`
   - **Branch:** `main`
   - **Main file path:** `Dashboard/Home.py`
4. Click **Deploy**. It installs `requirements.txt` (repo root) and builds — first build
   takes a few minutes.
5. You get a public URL like `https://your-app.streamlit.app`. Every `git push` to `main`
   auto-redeploys.

## 4. Updating the live site

Just push to `main`:

```bash
git add -A && git commit -m "Update dashboard" && git push
```

Streamlit Cloud redeploys automatically within a minute or two.

## Troubleshooting

- **App can't find data** → the CSV wasn't pushed (check `.gitignore`), or the path is
  wrong. The app resolves data via `Research/processed/` relative to the repo root.
- **ModuleNotFoundError** → a package is missing from the **root** `requirements.txt`.
- **Charts empty** → that source's CSV is missing or has no rows for the current filter;
  widen the filters or regenerate the CSV.
- **Resource limits** → the free tier has ~1 GB RAM. Our CSVs are small, so this is fine,
  but avoid committing the 24 MB raw HTML snapshots into the app's load path (they're not
  read by the app).

## Alternatives to Streamlit Cloud

- **Hugging Face Spaces** (Streamlit template) — also free, similar flow.
- **Render / Railway** — run `streamlit run Dashboard/Home.py --server.port $PORT`.
- Self-host anywhere that runs Python.
