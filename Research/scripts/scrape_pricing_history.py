"""
scrape_pricing_history.py
-------------------------
Reconstructs HISTORICAL LLM API prices from the Internet Archive's Wayback Machine.

Why this exists: your other sources only give *today's* prices. Your questions are
about how price-per-1k-tokens changed over time, which needs history. The Wayback
Machine has archived the providers' pricing pages over the years; this script lists
those snapshots, downloads roughly one per quarter, saves the raw HTML, and makes a
best-effort attempt to pull prices out of each page.

IMPORTANT — read this about reliability:
  - Downloading the snapshots is reliable. The raw HTML is always saved to
    Model_Data/pricing_snapshots/ so you NEVER lose the data even if parsing fails.
  - PARSING prices is best-effort. Pricing pages change layout constantly and many
    are JavaScript-rendered (archived as near-empty shells). Treat the extracted CSV
    as a draft to verify by hand against the saved HTML, not as ground truth.

PREREQUISITES:
  pip install requests beautifulsoup4

Run:
  python scripts/scrape_pricing_history.py

Outputs:
  Model_Data/pricing_snapshots/<provider>_<timestamp>.html   raw archived pages (source of truth)
  Model_Data/pricing_history_extracted.csv                   best-effort parsed prices (verify by hand)
"""

from __future__ import annotations
import csv
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent              # .../Research
SNAP_DIR = ROOT / "Model_Data" / "pricing_snapshots"
OUT_CSV = ROOT / "Model_Data" / "pricing_history_extracted.csv"

# Pages to reconstruct. Add/remove freely. Use the path the provider used at the time
# (older OpenAI prices lived at /pricing, API prices later at /api/pricing).
PAGES = {
    # OpenAI — strong, server-rendered history all the way back to 2021. Keep.
    "openai": "openai.com/pricing",
    "openai_api": "openai.com/api/pricing",

    # Anthropic — the marketing page (anthropic.com/pricing) is mostly JS shells;
    # only mid-2025+ snapshots render. The DOCS pages are more static HTML, so they
    # are the best shot at recovering earlier Claude prices. Try several known paths
    # (the docs URL has changed over time); empty ones are skipped harmlessly.
    "anthropic": "anthropic.com/pricing",
    "anthropic_docs": "docs.anthropic.com/en/docs/about-claude/pricing",
    "anthropic_models": "docs.anthropic.com/en/docs/about-claude/models/overview",
    "anthropic_models_old": "docs.anthropic.com/claude/docs/models-overview",

    # Google — the old ai.google.dev/pricing path went stale after early 2025
    # (Google moved its pricing). Add the current Gemini + Vertex locations.
    "google": "ai.google.dev/pricing",
    "google_gemini_docs": "ai.google.dev/gemini-api/docs/pricing",
    "google_vertex": "cloud.google.com/vertex-ai/generative-ai/pricing",
}

CDX = "http://web.archive.org/cdx/search/cdx"
HEADERS = {"User-Agent": "Mozilla/5.0 (research; pricing-history)"}
PAUSE = 2.0                                                 # be polite to the archive
MAX_RETRIES = 5                                             # archive.org 503s a lot


def get_with_retry(url: str, params: dict | None = None) -> requests.Response:
    """GET with exponential backoff. The Wayback CDX server frequently returns
    503/429 when busy; retrying after a growing wait almost always succeeds."""
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=60)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            # "connection refused" / timeout = archive.org throttled us. Back off harder.
            wait = 15 * (attempt + 1)                       # 15s, 30s, 45s, ...
            print(f"    connection throttled ({type(e).__name__}); retrying in {wait}s "
                  f"[{attempt + 1}/{MAX_RETRIES}]")
            time.sleep(wait)
            continue
        if r.status_code in (503, 429, 502, 504):
            wait = 5 * (attempt + 1)                        # 5s, 10s, 15s, ...
            print(f"    archive busy ({r.status_code}); retrying in {wait}s "
                  f"[{attempt + 1}/{MAX_RETRIES}]")
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r
    raise RuntimeError(f"archive.org still unavailable after {MAX_RETRIES} retries: {url}")


def get_snapshots(page_url: str) -> list[tuple[str, str]]:
    """List archived snapshots of a page, collapsed to ~one per month, 200s only.
    Returns [(timestamp, original_url), ...] sorted oldest->newest."""
    params = {
        "url": page_url,
        "output": "json",
        "fl": "timestamp,original",
        "filter": "statuscode:200",
        "collapse": "timestamp:6",     # 6 digits = YYYYMM -> ~monthly
    }
    r = get_with_retry(CDX, params=params)
    rows = r.json()
    if not rows:
        return []
    rows = rows[1:]                    # first row is the column header
    return [(ts, orig) for ts, orig in rows]


def one_per_quarter(snaps: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Keep at most one snapshot per calendar quarter (timestamp is YYYYMMDD...)."""
    seen, kept = set(), []
    for ts, orig in snaps:
        year, month = ts[:4], int(ts[4:6])
        quarter = (year, (month - 1) // 3)
        if quarter not in seen:
            seen.add(quarter)
            kept.append((ts, orig))
    return kept


def fetch_snapshot(timestamp: str, original: str) -> str | None:
    """Download the raw archived page (the 'id_' suffix strips the Wayback toolbar)."""
    url = f"https://web.archive.org/web/{timestamp}id_/{original}"
    try:
        return get_with_retry(url).text
    except Exception as e:
        print(f"    ! failed {timestamp}: {e}")
        return None


# Matches "$1.50", "$0.03", optionally followed by a per-tokens unit hint nearby.
PRICE_RE = re.compile(r"\$\s?\d+(?:\.\d+)?")
UNIT_HINTS = ("1m", "1,000,000", "million", "1k", "1,000", "per token", "tokens",
              "mtok", "/ mtok", "/mtok")          # Anthropic writes "$3 / MTok"


def extract_prices(html: str) -> list[dict]:
    """Best-effort: pull every '$x.xx' that sits near a token-unit hint, with the
    surrounding text as context so you can identify the model by hand."""
    soup = BeautifulSoup(html, "html.parser")
    text = " ".join(soup.get_text(" ").split())
    found = []
    for m in PRICE_RE.finditer(text):
        window = text[max(0, m.start() - 80): m.end() + 80].lower()
        if any(h in window for h in UNIT_HINTS):
            found.append({"price": m.group(), "context": window})
    return found


def main() -> None:
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    rows = []

    for provider, page in PAGES.items():
        print(f"\n=== {provider}  ({page}) ===")
        try:
            snaps = one_per_quarter(get_snapshots(page))
        except Exception as e:
            print(f"  could not list snapshots: {e}")
            continue
        print(f"  {len(snaps)} quarterly snapshots")

        for ts, orig in snaps:
            snap_path = SNAP_DIR / f"{provider}_{ts}.html"
            # Skip snapshots already downloaded so re-runs don't re-hammer the archive
            # (and only fetch the providers that failed last time).
            if snap_path.exists():
                html = snap_path.read_text(encoding="utf-8")
                print(f"    skip {ts} (already saved)")
            else:
                html = fetch_snapshot(ts, orig)
                time.sleep(PAUSE)
                if not html:
                    continue
                snap_path.write_text(html, encoding="utf-8")  # source of truth
                print(f"    saved {ts}  ({len(extract_prices(html))} price hits)")
            # Best-effort parse (runs for both fresh and already-saved pages).
            for hit in extract_prices(html):
                rows.append({
                    "provider": provider,
                    "snapshot_date": f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}",
                    "price": hit["price"],
                    "context": hit["context"],
                    "source_url": f"https://web.archive.org/web/{ts}/{orig}",
                })

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["provider", "snapshot_date", "price", "context", "source_url"])
        w.writeheader()
        w.writerows(rows)

    print(f"\nSaved {len(rows)} price hits -> {OUT_CSV}")
    print(f"Raw pages -> {SNAP_DIR}")
    print("\nNEXT: open pricing_history_extracted.csv, use the 'context' column to identify")
    print("which model each price belongs to, and clean it into model/date/input/output.")


if __name__ == "__main__":
    main()
