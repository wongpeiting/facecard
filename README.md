# Face cards

An D3+Svelte interactive chart of how famous and how well-liked America's best-known
political figures are, built using [YouGov Ratings'](https://yougov.com/ratings) data and portrait images and scaffolding from a circle-packing layout found on [Observable](https://observablehq.com/@d3/zoomable-circle-packing). 

## Data

`fetch_yougov.py` pulls the Republican + Democrat rosters from YouGov's
public-data API. For each person it captures fame and popularity — overall and
for all five demographic crossbreaks — plus a fame rank, a popularity rank, and
"rising" flags, and downloads the portrait into `static/faces/<slug>.jpg`.
Output is a `party → person` hierarchy at `static/yougov.json` (366 figures),
stamped with the pull date.

```bash
pip install requests
python fetch_yougov.py
cp static/yougov.json src/lib/yougov.json
```

YouGov surveys daily but only refreshes its published ratings **quarterly**, so
`.github/workflows/update-yougov.yml` re-runs the scraper on the 1st of
Feb/May/Aug/Nov and commits only if the numbers changed.

## Run

```bash
npm install
npm run dev
```