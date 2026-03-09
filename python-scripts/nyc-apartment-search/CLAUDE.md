# NYC Apartment Search

Scrapes Craigslist NYC and generates a dark-themed HTML report with apartment listings,
commute times to Hell's Kitchen, and quick links to StreetEasy / Zillow / Apartments.com.

## Status
LIVE on Mac.

## How to Run
```bash
cd ~/Desktop/my-project/python-scripts/nyc-apartment-search
pip install -r requirements.txt   # first time only
python search.py
```
Report saves to `results/latest.html` and opens automatically in browser.

## Config
Edit the `CONFIG` block at the top of `search.py`:
- `searches` — budget ranges and bedroom counts for each tab
- `neighborhoods` — which areas to scrape on Craigslist
- `max_listings_per_tab` — cap per tab (default 60)

## No API Keys Needed
Pure web scraping + HTML generation. No `.env` file required.

## Output
- `results/apartments-YYYYMMDD-HHMMSS.html` — timestamped report
- `results/latest.html` — always the most recent run
