#!/usr/bin/env python3
"""
NYC Apartment Search — Craigslist Scraper
Scrapes Craigslist NYC for apartments matching your parameters,
filters by commute distance to 50th St & 8th Ave, and builds a
clean HTML report with every result.

Usage:
    python3 search.py

No API keys needed.
"""

import re
import time
import webbrowser
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ─── YOUR PARAMETERS ────────────────────────────────────────────────────────

CONFIG = {
    "min_rent":       2000,
    "max_rent":       3000,
    "min_bedrooms":   0,       # 0 = include studios
    "max_bedrooms":   1,       # 1 = include 1BR
    "max_pages":      5,       # 120 results/page → up to 600 listings scanned
    "delay_seconds":  1.5,     # polite pause between page requests
    "open_report":    True,    # auto-open HTML when done
    "prefer_laundry": True,    # flag listings that mention washer/laundry
}

# ─── NEIGHBORHOOD TIERS ──────────────────────────────────────────────────────
# Commute to 50th St & 8th Ave (Hell's Kitchen) during weekday rush hour.
# Tier 1 = under 30 min  |  Tier 2 = 30–40 min
# Listings in EXCLUDED or unknown neighborhoods are skipped.

TIER_1 = {
    # Manhattan
    "hells kitchen", "hell's kitchen", "midtown", "midtown west", "midtown east",
    "chelsea", "upper west side", "uws", "murray hill", "kips bay",
    "gramercy", "flatiron", "union square", "greenwich village",
    "west village", "east village", "soho", "noho", "nolita", "tribeca",
    "lower east side", "les", "chinatown", "two bridges",
    "financial district", "fidi", "battery park city", "fulton",
    # Queens (7 train / E/F)
    "long island city", "lic", "sunnyside",
    # NJ (PATH — often cheaper)
    "jersey city", "hoboken", "jc downtown", "journal square",
}

TIER_2 = {
    # Manhattan
    "harlem", "east harlem", "spanish harlem", "hamilton heights",
    "washington heights", "inwood",
    "upper east side", "ues", "yorkville", "lenox hill", "carnegie hill",
    # Queens
    "woodside", "astoria", "ditmars", "jackson heights", "ridgewood",
    "elmhurst", "forest hills", "rego park",
    # Brooklyn (safer, well-connected)
    "greenpoint", "williamsburg", "bushwick", "east williamsburg",
    "park slope", "prospect heights", "crown heights",
    "boerum hill", "cobble hill", "carroll gardens", "red hook",
    "gowanus", "fort greene", "clinton hill", "bed stuy",
    "bedford stuyvesant", "dumbo", "downtown brooklyn",
    "brooklyn heights", "columbia waterfront",
}

# These get filtered out entirely — no exceptions
EXCLUDED = {
    # Bronx
    "bronx", "south bronx", "mott haven", "tremont", "fordham",
    "pelham", "riverdale", "co-op city", "hunts point",
    # Dangerous / very far Brooklyn
    "brownsville", "east new york", "canarsie", "flatlands",
    "cypress hills", "east flatbush", "new lots", "starrett city",
    # Far Queens / other
    "far rockaway", "jamaica", "springfield gardens", "howard beach",
    "ozone park", "richmond hill",
    # Staten Island
    "staten island",
}

COMMUTE_DISPLAY = {
    1: ("< 30 min",  "#22c55e"),   # green
    2: ("30–40 min", "#f59e0b"),   # amber
}

LAUNDRY_KEYWORDS = [
    "washer", "w/d", "w/d in unit", "laundry in unit",
    "laundry in building", "laundry on-site", "washing machine",
    "laundry room", "coin laundry",
]


# ─── NEIGHBORHOOD CLASSIFIER ─────────────────────────────────────────────────

def classify_neighborhood(hood_raw: str):
    """
    Returns 1 (≤30min), 2 (30-40min), or None (excluded / unknown).
    hood_raw is typically '(hell's kitchen)' or 'upper west side'.
    """
    if not hood_raw:
        return None
    text = hood_raw.lower().strip("() \t\n")

    for ex in EXCLUDED:
        if ex in text:
            return None
    for n in TIER_1:
        if n in text:
            return 1
    for n in TIER_2:
        if n in text:
            return 2
    return None   # unknown — skip


def mentions_laundry(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in LAUNDRY_KEYWORDS)


# ─── SCRAPER ─────────────────────────────────────────────────────────────────

BASE_URL = "https://newyork.craigslist.org/search/aap"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def fetch_page(offset: int, session: requests.Session) -> list[dict]:
    """Fetch one page of results and return a list of listing dicts."""
    params = {
        "min_price":        CONFIG["min_rent"],
        "max_price":        CONFIG["max_rent"],
        "min_bedrooms":     CONFIG["min_bedrooms"],
        "max_bedrooms":     CONFIG["max_bedrooms"],
        "s":                offset,
        "availabilityMode": 0,
    }

    try:
        resp = session.get(BASE_URL, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"    Warning: request failed at offset {offset}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # Try new Craigslist layout (2023+)
    items = soup.select("li.cl-static-search-result")
    if items:
        return _parse_new(items)

    # Fall back to classic layout
    items = soup.select(".result-row")
    return _parse_old(items)


def _parse_new(items) -> list[dict]:
    listings = []
    for item in items:
        try:
            title_el = (item.select_one(".posting-title .label")
                        or item.select_one("a.posting-title"))
            price_el = item.select_one(".priceinfo")
            hood_el  = item.select_one(".hood") or item.select_one(".meta .hood")
            link_el  = item.select_one("a.posting-title")
            date_el  = item.select_one("time")
            img_el   = item.select_one("img")

            title = title_el.get_text(strip=True) if title_el else "No title"
            price = price_el.get_text(strip=True) if price_el else ""
            hood  = hood_el.get_text(strip=True)  if hood_el  else ""
            link  = link_el["href"]               if link_el  else "#"
            date  = (date_el.get("datetime", "")  if date_el  else "")[:10]
            img   = img_el.get("src", "")         if img_el   else ""

            price_num = int(re.sub(r"[^\d]", "", price)) if price else 0
            tier = classify_neighborhood(hood)
            if tier is None:
                continue

            listings.append({
                "title":   title,
                "price":   price_num,
                "hood":    hood.strip("() "),
                "link":    link,
                "date":    date,
                "img":     img,
                "tier":    tier,
                "laundry": mentions_laundry(title),
            })
        except Exception:
            continue
    return listings


def _parse_old(items) -> list[dict]:
    listings = []
    for item in items:
        try:
            title_el = item.select_one(".result-title")
            price_el = item.select_one(".result-price")
            hood_el  = item.select_one(".result-hood")
            date_el  = item.select_one(".result-date")
            img_el   = item.select_one(".result-image img")

            title = title_el.get_text(strip=True) if title_el else "No title"
            price = price_el.get_text(strip=True) if price_el else ""
            hood  = hood_el.get_text(strip=True)  if hood_el  else ""
            link  = title_el["href"]               if title_el else "#"
            date  = (date_el.get("datetime", "")  if date_el  else "")[:10]
            img   = img_el.get("src", "")         if img_el   else ""

            price_num = int(re.sub(r"[^\d]", "", price)) if price else 0
            tier = classify_neighborhood(hood)
            if tier is None:
                continue

            listings.append({
                "title":   title,
                "price":   price_num,
                "hood":    hood.strip("() "),
                "link":    link,
                "date":    date,
                "img":     img,
                "tier":    tier,
                "laundry": mentions_laundry(title),
            })
        except Exception:
            continue
    return listings


def scrape_all() -> list[dict]:
    session      = requests.Session()
    all_listings = []
    seen_links   = set()

    for page in range(CONFIG["max_pages"]):
        offset = page * 120
        print(f"  Page {page + 1} (offset {offset})...", end=" ", flush=True)

        items = fetch_page(offset, session)
        new   = [l for l in items if l["link"] not in seen_links]
        for l in new:
            seen_links.add(l["link"])
            all_listings.append(l)

        print(f"{len(new)} new listings found")

        if len(new) == 0 and page > 0:
            print("  No new results — stopping early.")
            break

        if page < CONFIG["max_pages"] - 1:
            time.sleep(CONFIG["delay_seconds"])

    # Sort: tier 1 first, then by price low→high
    all_listings.sort(key=lambda x: (x["tier"], x["price"]))
    return all_listings


# ─── HTML GENERATOR ──────────────────────────────────────────────────────────

def _make_cards(listings: list[dict]) -> str:
    if not listings:
        return '<p class="empty">No listings found in this tier.</p>'

    cards = []
    for l in listings:
        tier_label, tier_color = COMMUTE_DISPLAY[l["tier"]]

        laundry_badge = (
            '<span class="badge badge-laundry">Laundry</span>'
            if l["laundry"] else ""
        )
        img_html = (
            f'<img class="card-img" src="{l["img"]}" alt="" '
            f'onerror="this.style.display=\'none\'">'
            if l["img"] else
            '<div class="card-img-blank"></div>'
        )
        price_str = f"${l['price']:,}/mo" if l["price"] else "Price unlisted"

        cards.append(f"""
    <div class="card">
      {img_html}
      <div class="card-body">
        <div class="card-top">
          <span class="card-price">{price_str}</span>
          <span class="commute-tag" style="color:{tier_color};border-color:{tier_color}44;background:{tier_color}11">{tier_label}</span>
        </div>
        <a class="card-title" href="{l['link']}" target="_blank" rel="noopener">{l['title']}</a>
        <div class="card-meta">
          <span class="hood-tag">{l['hood']}</span>
          {laundry_badge}
          {f'<span class="date-tag">{l["date"]}</span>' if l["date"] else ""}
        </div>
      </div>
    </div>""")

    return "\n".join(cards)


def generate_html(listings: list[dict]) -> str:
    now      = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    tier1    = [l for l in listings if l["tier"] == 1]
    tier2    = [l for l in listings if l["tier"] == 2]
    laundry  = sum(1 for l in listings if l["laundry"])

    t1_cards = _make_cards(tier1)
    t2_cards = _make_cards(tier2)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>NYC Apartments — {now}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #0d0d0d; color: #e8e8e8; line-height: 1.5;
    }}
    .header {{
      background: linear-gradient(135deg, #0a0a1a, #0f1a2e, #091524);
      border-bottom: 1px solid #1e3a5f;
      padding: 36px 40px 30px;
    }}
    .header h1 {{ font-size: 26px; font-weight: 700; color: #fff; margin-bottom: 4px; }}
    .header h1 span {{ color: #60a5fa; }}
    .header .sub {{ color: #888; font-size: 13px; margin-bottom: 18px; }}
    .stats {{ display: flex; gap: 10px; flex-wrap: wrap; }}
    .stat {{
      background: rgba(96,165,250,0.1); border: 1px solid rgba(96,165,250,0.25);
      color: #93c5fd; padding: 5px 14px; border-radius: 20px;
      font-size: 12px; font-weight: 600;
    }}
    .container {{ max-width: 1240px; margin: 0 auto; padding: 32px 24px; }}
    .section {{ margin-bottom: 40px; }}
    .section-header {{
      display: flex; align-items: center; gap: 12px;
      margin-bottom: 20px; padding-bottom: 12px;
      border-bottom: 1px solid #1e1e1e;
    }}
    .section-title {{
      font-size: 13px; font-weight: 700; color: #888;
      text-transform: uppercase; letter-spacing: 0.8px;
    }}
    .section-count {{
      background: #1a1a1a; border: 1px solid #333;
      color: #60a5fa; padding: 2px 10px;
      border-radius: 20px; font-size: 12px; font-weight: 700;
    }}
    /* ── GRID ── */
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
      gap: 16px;
    }}
    .card {{
      background: #111; border: 1px solid #222; border-radius: 10px;
      overflow: hidden; display: flex; flex-direction: column;
      transition: border-color 0.15s;
    }}
    .card:hover {{ border-color: #3b82f6; }}
    .card-img {{
      width: 100%; height: 175px; object-fit: cover; display: block;
      background: #1a1a1a;
    }}
    .card-img-blank {{ width: 100%; height: 40px; background: #141414; }}
    .card-body {{
      padding: 14px 16px; flex: 1;
      display: flex; flex-direction: column; gap: 8px;
    }}
    .card-top {{
      display: flex; align-items: center;
      justify-content: space-between; gap: 8px;
    }}
    .card-price {{ font-size: 19px; font-weight: 800; color: #fff; }}
    .commute-tag {{
      font-size: 11px; font-weight: 700;
      padding: 3px 9px; border-radius: 20px; border: 1px solid;
      white-space: nowrap;
    }}
    .card-title {{
      color: #93c5fd; text-decoration: none;
      font-size: 13px; font-weight: 500; line-height: 1.4;
    }}
    .card-title:hover {{ color: #60a5fa; text-decoration: underline; }}
    .card-meta {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 2px; }}
    .badge {{
      font-size: 11px; font-weight: 600; padding: 3px 8px;
      border-radius: 4px; border: 1px solid;
    }}
    .badge-laundry {{
      background: rgba(34,197,94,0.1); color: #4ade80;
      border-color: rgba(34,197,94,0.3);
    }}
    .hood-tag {{
      font-size: 12px; color: #999;
      background: #1a1a1a; padding: 3px 9px;
      border-radius: 4px; border: 1px solid #2a2a2a;
    }}
    .date-tag {{ font-size: 11px; color: #555; }}
    .empty {{ color: #666; font-size: 14px; padding: 8px 0; }}
  </style>
</head>
<body>

<div class="header">
  <h1>NYC <span>Apartment Results</span></h1>
  <p class="sub">Craigslist · {now} · $2,000–$3,000/mo · Studio – 1BR · Within 40 min of Hell's Kitchen</p>
  <div class="stats">
    <span class="stat">{len(listings)} listings found</span>
    <span class="stat">{len(tier1)} under 30 min</span>
    <span class="stat">{len(tier2)} 30–40 min</span>
    <span class="stat">{laundry} mention laundry</span>
  </div>
</div>

<div class="container">

  <div class="section">
    <div class="section-header">
      <div class="section-title">Under 30 Minutes Away</div>
      <span class="section-count">{len(tier1)}</span>
    </div>
    <div class="cards">{t1_cards}</div>
  </div>

  <div class="section">
    <div class="section-header">
      <div class="section-title">30 – 40 Minutes Away</div>
      <span class="section-count">{len(tier2)}</span>
    </div>
    <div class="cards">{t2_cards}</div>
  </div>

</div>
</body>
</html>"""


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    print()
    print("=" * 55)
    print("  NYC APARTMENT SEARCH — CRAIGSLIST SCRAPER")
    print(f"  Budget:   ${CONFIG['min_rent']:,} – ${CONFIG['max_rent']:,}/mo")
    print("  Beds:     Studio – 1BR")
    print("  Commute:  50th St & 8th Ave (Hell's Kitchen)")
    print("  Filters:  No Bronx · No dangerous Brooklyn")
    print("=" * 55)

    print("\nScraping Craigslist NYC...")
    listings = scrape_all()

    print(f"\nTotal qualifying listings: {len(listings)}")
    print(f"  Under 30 min: {sum(1 for l in listings if l['tier']==1)}")
    print(f"  30–40 min:    {sum(1 for l in listings if l['tier']==2)}")
    print(f"  Mention laundry: {sum(1 for l in listings if l['laundry'])}")

    print("\nBuilding HTML report...")
    html = generate_html(listings)

    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)

    ts          = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path    = results_dir / f"apartments-{ts}.html"
    latest_path = results_dir / "latest.html"

    out_path.write_text(html, encoding="utf-8")
    latest_path.write_text(html, encoding="utf-8")

    print(f"Saved: results/apartments-{ts}.html")

    if CONFIG["open_report"]:
        webbrowser.open(latest_path.as_uri())
        print("Report opened in browser.")

    print()
    print("=" * 55)
    print("  Done! Check results/latest.html")
    print("=" * 55)


if __name__ == "__main__":
    main()
