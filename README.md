# Santiago House Hunter

Automated daily house search and interactive map explorer for **4–6 bedroom houses** for rent between **$3,000,000 and $5,000,000 CLP/month** in **La Dehesa / Lo Barnechea** and **Alto Las Condes / Las Condes**, Santiago, Chile.

## Features
- **Live Sources**: Scrapes [TOCTOC](https://www.toctoc.com) (exact coordinates + full descriptions) and [PortalInmobiliario](https://www.portalinmobiliario.com).
- **Live UF Conversion**: Fetches the daily UF rate from `mindicador.cl/api/uf` to accurately filter UF-denominated rents.
- **Rich Attribute Extraction**: Automatically detects **pool (`piscina`)**, **estimated total rooms**, **bathrooms**, **built & lot m²**, **quincho**, **condominio**, **service room**, **furnished**, and **parking spaces**.
- **Daily History Tracking**: Tracks `first_seen`, `last_seen`, and price changes in `data/history.json`.
- **Interactive Map & Shortlist Tracker**: Generates a self-contained `output/map.html` with pan/zoom map, filters, and a persistent shortlist/notes tracker (`localStorage` + JSON export).

## Local Browser Scraping (Recommended — includes TOCTOC, MercadoLibre & PortalInmobiliario)

Run on your own computer so MercadoLibre & PortalInmobiliario open in your real local browser:

```bash
# One-time setup on your computer
git clone https://github.com/Chanicua/Santiago-House-Hunter.git
cd Santiago-House-Hunter
pip install playwright && playwright install chromium

# Run scraper using your local Chrome/Chromium + rebuild map + push to GitHub Pages
./run_daily.sh
```

- A visible browser window opens with a persistent local profile (`~/.santiago-house-hunter-browser`). If MercadoLibre or PortalInmobiliario asks you to sign in or verify, complete it in the browser window and press **Enter** in the terminal.
- `./run_daily.sh` automatically rebuilds `output/map.html` and pushes the updated listings to `main` (updating https://chanicua.github.io/Santiago-House-Hunter/) while keeping your shared `data/tracker.json` intact.
- Use `NO_PUSH=1 ./run_daily.sh` to run locally without pushing to GitHub, or `./setup_schedule.sh` to schedule a daily **4:00 AM** local run (uses `launchd` on macOS or `cron` on Linux).
