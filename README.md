# Santiago House Hunter

Automated daily house search and interactive map explorer for **4–6 bedroom houses** for rent between **$3,000,000 and $5,000,000 CLP/month** in **La Dehesa / Lo Barnechea** and **Alto Las Condes / Las Condes**, Santiago, Chile.

## Features
- **Live Sources**: Scrapes [TOCTOC](https://www.toctoc.com) (exact coordinates + full descriptions) and [PortalInmobiliario](https://www.portalinmobiliario.com).
- **Live UF Conversion**: Fetches the daily UF rate from `mindicador.cl/api/uf` to accurately filter UF-denominated rents.
- **Rich Attribute Extraction**: Automatically detects **pool (`piscina`)**, **estimated total rooms**, **bathrooms**, **built & lot m²**, **quincho**, **condominio**, **service room**, **furnished**, and **parking spaces**.
- **Daily History Tracking**: Tracks `first_seen`, `last_seen`, and price changes in `data/history.json`.
- **Interactive Map & Shortlist Tracker**: Generates a self-contained `output/map.html` with pan/zoom map, filters, and a persistent shortlist/notes tracker (`localStorage` + JSON export).

## Run Manually
```bash
./run_daily.sh
```
Open `output/map.html` in any browser.

## Daily 7:00 AM Automation (America/Santiago)

### Option A: GitHub Actions (Recommended — runs in the cloud even when your computer is off)
Push this directory to a GitHub repository. The included workflow `.github/workflows/daily_search.yml` runs every day at **7:00 AM Santiago time** (`0 10 * * *` UTC) and commits updated `data/listings.json`, `data/history.json`, and `output/map.html`. You can enable **GitHub Pages** on the repo to view `output/map.html` from anywhere.

### Option B: Local Cron (Linux / macOS)
```bash
./setup_schedule.sh
```
This installs a `0 7 * * *` cron job with `CRON_TZ=America/Santiago`.
