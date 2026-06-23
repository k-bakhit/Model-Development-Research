# Static site: landing deck + dashboard

Two self-contained pages, no server and no Streamlit. Open either one in a browser and it
works offline, on desktop or mobile. The design is a single dark theme (black with a lime
accent), shared across both pages.

## Files

- `index.html` is the landing deck: a particle-hero presentation that introduces the project,
  the data sources, and how it was built, then links into the dashboard. Hand-authored, so
  edit it directly.
- `dashboard.html` is the interactive chart app (six tabs, live readouts, full method notes
  and disclaimers). It is **generated** by `build.py`, so do not edit it by hand.
- `template.html` is the source for the dashboard. Edit this to change the charts or styling.
- `build.py` reads the cleaned CSVs in `../Research/processed/` plus `artificial_analysis.json`,
  packs the bits each chart needs into JSON, and injects them into `template.html` to produce
  `dashboard.html`.

## See it now (no deploy)

Double-click `index.html`. It opens in your browser and runs offline. The dashboard charts
load Plotly from a CDN, so they need a connection the first time; everything else is inline.

## Rebuild after the data changes

```bash
cd Site
python build.py        # regenerates dashboard.html from the latest CSVs
```

The headline figures shown on the landing deck (models tracked, most prolific lab, measured
models) are written into `index.html` by hand. If a rebuild moves them noticeably, update
those numbers in the deck to match.

## Deploy free on GitHub Pages

1. Commit and push the site:
   ```bash
   git add Site && git commit -m "Add static site" && git push
   ```
2. On GitHub, open **Settings, then Pages**.
3. Under **Build and deployment, Source**, pick **Deploy from a branch**.
4. Choose branch **main**, folder **/ (root)**, and **Save**.
5. The site appears at `https://k-bakhit.github.io/Model-Development-Research/Site/`
   within a minute or two, with `index.html` as the front page. For a cleaner root URL, move
   the two HTML files to the repo root, or point the Pages source at the `Site` folder if the
   option is offered.

Every push that changes these files updates the live site.

### Other free hosts (drag and drop the `Site` folder)

- Netlify Drop (netlify.com/drop)
- Cloudflare Pages
- Vercel (static)

## Notes

- Responsive: both pages collapse to one column on narrow screens.
- The dashboard reads its tab from the URL, so `dashboard.html#energy` opens the Energy tab
  directly. The landing deck uses that to deep-link.
- Charts are Plotly.js from a CDN; everything else, including the particle animation, is inline.
