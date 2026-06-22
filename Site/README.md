# AI Model Dashboard — static site

A self-contained, responsive dashboard (royal-blue/silver, light + dark mode, real-time
controls). No server, no Streamlit. `index.html` is fully self-contained — the data is
baked in.

## Files
- `template.html` — the app (HTML/CSS/JS). Edit this to change design or charts.
- `build.py` — reads the cleaned CSVs in `../Research/processed/` + `artificial_analysis.json`,
  packs them into JSON, and injects into the template to produce `index.html`.
- `index.html` — the built, deployable site (generated; don't edit by hand).

## See it now (no deploy)
Just **double-click `index.html`** — it opens in your browser and works offline,
on desktop or mobile. That's the real thing.

## Rebuild after data changes
```bash
cd Site
python build.py        # regenerates index.html from the latest CSVs
```

## Deploy free on GitHub Pages
1. Commit and push the site:
   ```bash
   git add Site && git commit -m "Add static dashboard site" && git push
   ```
2. On GitHub: **Settings → Pages**.
3. Under **Build and deployment → Source**, pick **Deploy from a branch**.
4. Branch **main**, folder **/ (root)**, **Save**.
5. Your site appears at `https://k-bakhit.github.io/Model-Development-Research/Site/index.html`
   within a minute or two. (To get a cleaner root URL, move `index.html` to the repo root,
   or set the Pages source to the `Site` folder if offered.)

Every `git push` that changes `index.html` auto-updates the live site.

### Alternative hosts (all free, drag-and-drop `index.html`)
- **Netlify Drop** — netlify.com/drop
- **Cloudflare Pages**
- **Vercel** (static)

## Notes
- Responsive: works on phone, tablet, desktop (one column on narrow screens).
- Light/dark choice is remembered in the browser (localStorage).
- Charts are Plotly.js loaded from a CDN; everything else is inline.
