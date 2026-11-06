# Evergreen Econ Dashboards

A single public page of macro and micro economic dashboards that updates itself.
Every series comes from FRED (Federal Reserve Bank of St. Louis), which mirrors
BLS, BEA, Treasury, Census, Federal Reserve, Eurostat and World Bank releases.

- `catalog.json` – the list of dashboards, panels and FRED series IDs. This is the
  only file you edit to add or change a dashboard.
- `scripts/fetch_fred.py` – downloads every series in the catalog to `data/*.csv`
  and writes `data/manifest.json`. Standard-library Python, no installs.
- `index.html` – the hub page. Reads `catalog.json` and `data/`, draws the charts
  with Plotly, and routes `#dashboard-id` links to individual dashboards.
- `.github/workflows/update-data.yml` – runs the fetcher on the 1st and 15th of
  each month, commits the data, and deploys the site to GitHub Pages. It also has
  a manual "Run workflow" trigger, which is what the page's **Refresh data now**
  button links to.

## Publish on GitHub Pages (one time, about 3 minutes)

1. Create an empty public repository on GitHub named `econ-dashboards`
   (or any name: then change `site.repo` in `catalog.json` to match).
2. In the repo: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. Push this folder:

```bash
cd econ-dashboards
git init -b main
git add .
git commit -m "Evergreen econ dashboards"
git remote add origin https://github.com/mfenickfau/econ-dashboards.git
git push -u origin main
```

The push triggers the workflow (it is also triggered by changes to the catalog).
A minute later the site is live at `https://mfenickfau.github.io/econ-dashboards/`.
Individual dashboards are addressable, for example
`https://mfenickfau.github.io/econ-dashboards/#labor-underutilization`.

## Refreshing

- Automatic: the 1st and 15th of every month at 13:20 UTC.
- On demand: the **Refresh data now** button opens the workflow page; click
  **Run workflow**. Or locally: `python3 scripts/fetch_fred.py` then commit `data/`.

## Adding a dashboard

Append an object to `dashboards` in `catalog.json`:

```json
{
  "id": "oil", "group": "macro", "topic": "Prices",
  "title": "Oil prices",
  "blurb": "WTI and Brent crude, dollars per barrel.",
  "panels": [
    {"title": "Crude oil", "units": "Dollars per barrel", "default_transform": "level",
     "series": [{"id": "DCOILWTICO", "label": "WTI"}, {"id": "DCOILBRENTEU", "label": "Brent"}]}
  ]
}
```

Rules of thumb: one unit per panel (never two y-axes), at most eight series per
panel, `default_transform` of `level`, `yoy` (percent change from a year ago) or
`index` (100 at the start of the selected range), optional `scale` to convert
units (for example `0.001` for millions to billions) and `zero_line: true` for
series that cross zero. Find series IDs at https://fred.stlouisfed.org.

## Tableau Public, if you still want it

Tableau Public can connect to a Google Sheet and refreshes it daily. Put
`=IMPORTDATA("https://raw.githubusercontent.com/mfenickfau/econ-dashboards/main/data/UNRATE.csv")`
in a sheet and point an existing Tableau workbook at it, and that workbook stops
needing manual spreadsheet updates too.
