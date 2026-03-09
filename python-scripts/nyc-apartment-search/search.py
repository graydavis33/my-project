#!/usr/bin/env python3
"""
NYC Apartment Search Tool
Opens pre-filtered apartment searches across StreetEasy, Zillow,
Apartments.com, Craigslist, and Facebook Marketplace — then generates
a dark-themed HTML dashboard with commute guide, checklist, and a
manual tracker to save listings you find.

Usage:
    python3 search.py

No API keys needed. Just run it.
"""

import webbrowser
from datetime import datetime
from pathlib import Path

# ─── YOUR SETTINGS ─────────────────────────────────────────────────────────────
# Edit this section to change your search. These settings control:
#   - which browser tabs open
#   - what numbers appear in the dashboard

CONFIG = {
    "work_location": "Hell's Kitchen, NYC",  # Where you're commuting to

    # Each row = one "mode" that opens a set of tabs
    "searches": [
        {
            "label":    "Studio  (Solo)",
            "bedrooms": 0,        # 0 = studio
            "min":      1500,     # min monthly rent $
            "max":      2800,     # max monthly rent $
            "open":     True,     # Set False to skip opening tabs for this mode
        },
        {
            "label":    "1 BR  (Solo)",
            "bedrooms": 1,
            "min":      2200,
            "max":      2800,
            "open":     True,
        },
        {
            "label":    "2 BR  (Roommates)",
            "bedrooms": 2,
            "min":      2800,
            "max":      5000,
            "open":     True,
        },
        {
            "label":    "3 BR  (Roommates)",
            "bedrooms": 3,
            "min":      3500,
            "max":      7500,
            "open":     False,    # Off by default — enable if needed
        },
    ],

    # Open browser tabs automatically when you run the script?
    "auto_open_tabs": True,

    # Which platforms to open tabs for
    "platforms": ["streeteasy", "zillow", "apartments", "craigslist", "facebook"],

    # Delay between opening tabs (seconds) to avoid browser overload
    "tab_delay_seconds": 0.4,
}

# ─── COMMUTE GUIDE (to Hell's Kitchen) ────────────────────────────────────────
# Time estimates during weekday rush hour.
# Hell's Kitchen = roughly 42nd–57th St, 8th–12th Ave, Manhattan.

COMMUTE_GUIDE = [
    # (neighborhood,           est time,       transit / notes)
    ("Hell's Kitchen",         "0–5 min walk", "Live right there"),
    ("Chelsea",                "10–15 min",    "C/E train or walk"),
    ("Upper West Side",        "10–20 min",    "1/2/3 train or walk"),
    ("Midtown / Murray Hill",  "5–15 min",     "A/C/E / walk"),
    ("Harlem",                 "20–30 min",    "A/C or B/D train"),
    ("Washington Heights",     "30–40 min",    "A train"),
    ("Inwood",                 "35–45 min",    "A train, end of line"),
    ("Long Island City (LIC)", "15–20 min",    "7 train — very fast"),
    ("Astoria",                "20–30 min",    "N/W train"),
    ("Williamsburg",           "30–40 min",    "L train to 14th, transfer"),
    ("Bushwick",               "35–45 min",    "L train + walk"),
    ("Crown Heights / Prospect","35–50 min",   "2/3 or 4/5 train"),
    ("Park Slope",             "35–45 min",    "F/G or 2/3 train"),
    ("Jersey City",            "20–30 min",    "PATH train — NJ"),
    ("Hoboken",                "20–30 min",    "PATH train — NJ"),
]

# ─── PLATFORM URLS ─────────────────────────────────────────────────────────────

def _build_urls(s: dict) -> dict:
    """Return a dict of {platform: url} for one search config."""
    br    = s["bedrooms"]
    min_p = s["min"]
    max_p = s["max"]

    # StreetEasy — best NYC-specific site
    # beds=0 for studio, beds=1 for 1BR, etc.
    streeteasy = (
        f"https://streeteasy.com/for-rent/nyc"
        f"?price={min_p}%2C{max_p}&beds={br}&sort_by=listed_desc"
    )

    # Zillow
    beds_min = max(br, 1) if br > 0 else 0
    zillow = (
        f"https://www.zillow.com/new-york-ny/rentals/"
        f"?searchQueryState=%7B%22filterState%22%3A%7B"
        f"%22price%22%3A%7B%22min%22%3A{min_p}%2C%22max%22%3A{max_p}%7D%2C"
        f"%22beds%22%3A%7B%22min%22%3A{beds_min}%7D%7D%7D"
    )

    # Apartments.com
    br_slug = {0: "studios", 1: "1-bedrooms", 2: "2-bedrooms", 3: "3-bedrooms"}.get(br, "1-bedrooms")
    apartments = (
        f"https://www.apartments.com/new-york-ny/{br_slug}/?min={min_p}&max={max_p}"
    )

    # Craigslist NYC housing/apts
    craigslist = (
        f"https://newyork.craigslist.org/search/aap"
        f"?min_price={min_p}&max_price={max_p}"
        f"&min_bedrooms={br}&max_bedrooms={br if br > 0 else 1}"
    )

    # Facebook Marketplace (can't deep-filter by price via URL, open general)
    facebook = "https://www.facebook.com/marketplace/new-york-city/propertyrentals"

    return {
        "streeteasy": streeteasy,
        "zillow":     zillow,
        "apartments": apartments,
        "craigslist": craigslist,
        "facebook":   facebook,
    }


# ─── HTML GENERATOR ────────────────────────────────────────────────────────────

def _make_commute_rows() -> str:
    rows = []
    for neighborhood, est_time, transit in COMMUTE_GUIDE:
        rows.append(
            f"<tr>"
            f"<td>{neighborhood}</td>"
            f"<td class='ct-time'>{est_time}</td>"
            f"<td class='ct-transit'>{transit}</td>"
            f"</tr>"
        )
    return "\n".join(rows)


def _make_search_cards() -> str:
    """Build one card per search config with platform buttons."""
    cards = []
    for s in CONFIG["searches"]:
        label = s["label"].strip()
        urls  = _build_urls(s)
        br    = s["bedrooms"]
        br_label = "Studio" if br == 0 else f"{br} Bedroom"

        btn_html = ""
        platform_names = {
            "streeteasy": ("StreetEasy", "#c0392b"),
            "zillow":     ("Zillow",     "#006aff"),
            "apartments": ("Apartments.com", "#e67e22"),
            "craigslist": ("Craigslist", "#6c3aed"),
            "facebook":   ("Facebook",   "#1877f2"),
        }
        for key in CONFIG["platforms"]:
            pname, color = platform_names.get(key, (key, "#333"))
            url = urls.get(key, "#")
            btn_html += (
                f'<a class="sc-btn" href="{url}" target="_blank" rel="noopener" '
                f'style="background:{color}">{pname}</a>'
            )

        cards.append(f"""
      <div class="search-card">
        <div class="sc-label">{label}</div>
        <div class="sc-meta">{br_label} &nbsp;·&nbsp; ${s['min']:,}–${s['max']:,}/mo</div>
        <div class="sc-buttons">{btn_html}</div>
      </div>""")

    return "\n".join(cards)


def _make_checklist() -> str:
    items = [
        ("Budget", [
            "Total move-in cost: first month + security deposit + broker fee (often 1 month's rent) = 3× rent",
            "Budget for furniture, movers, and setup costs",
            "Check if utilities (heat, electric, internet) are included",
        ]),
        ("The Commute", [
            "Take the actual train during rush hour (8–9am weekday) before signing",
            "Google Maps is optimistic — add 10 minutes for delays",
            "Check if your boss needs you there early on short notice (proximity matters)",
        ]),
        ("The Apartment", [
            "Laundry: in-unit / in building / laundromat nearby",
            "Heat and hot water included in rent?",
            "Internet: Spectrum or Verizon available?",
            "Cell signal inside the apartment (check multiple rooms)",
            "Natural light — visit during the day",
            "Storage: closet space, basement?",
            "Noise: street level vs. higher floors",
        ]),
        ("The Lease", [
            "Read the full lease before signing — every page",
            "Lease length: 12 months? Month-to-month option after?",
            "Subletting rules (important if you travel for work)",
            "Pet policy (if applicable)",
            "No-broker-fee listings can save you $2,500–$4,000",
        ]),
        ("The Neighborhood", [
            "Walk the area at night, not just during the day",
            "Nearest grocery store and how far",
            "Nearest subway entrance and which lines",
            "Visit on a weekend too — noise levels change",
        ]),
        ("After You Sign", [
            "Renters insurance: ~$15–$20/month (worth it)",
            "Roommate agreement in writing if splitting with friends",
            "Change of address: bank, IDs, subscriptions",
        ]),
    ]

    sections = []
    for section_title, checks in items:
        lis = "\n".join(
            f'<li><label><input type="checkbox"> {c}</label></li>'
            for c in checks
        )
        sections.append(f"""
        <div class="cl-section">
          <div class="cl-section-title">{section_title}</div>
          <ul class="checklist">{lis}</ul>
        </div>""")

    return "\n".join(sections)


def generate_html() -> str:
    now          = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    commute_rows = _make_commute_rows()
    search_cards = _make_search_cards()
    checklist    = _make_checklist()
    active_count = sum(1 for s in CONFIG["searches"] if s.get("open", True))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>NYC Apartment Search — {now}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #0d0d0d;
      color: #e8e8e8;
      line-height: 1.55;
    }}

    /* ── HEADER ── */
    .header {{
      background: linear-gradient(135deg, #0a0a1a 0%, #0f1a2e 60%, #091524 100%);
      border-bottom: 1px solid #1e3a5f;
      padding: 36px 40px 30px;
    }}
    .header h1 {{ font-size: 26px; font-weight: 700; color: #fff; margin-bottom: 4px; }}
    .header h1 span {{ color: #60a5fa; }}
    .header .sub {{ color: #888; font-size: 13px; margin-bottom: 18px; }}
    .badges {{ display: flex; gap: 10px; flex-wrap: wrap; }}
    .badge {{
      background: rgba(96,165,250,0.1);
      border: 1px solid rgba(96,165,250,0.25);
      color: #93c5fd;
      padding: 5px 12px; border-radius: 20px;
      font-size: 12px; font-weight: 500;
    }}

    /* ── LAYOUT ── */
    .container {{ max-width: 1200px; margin: 0 auto; padding: 28px 24px; }}
    .section {{
      background: #111;
      border: 1px solid #222;
      border-radius: 10px;
      padding: 24px;
      margin-bottom: 24px;
    }}
    .section-title {{
      font-size: 13px; font-weight: 700;
      color: #888;
      margin-bottom: 20px;
      padding-bottom: 12px;
      border-bottom: 1px solid #1e1e1e;
      text-transform: uppercase; letter-spacing: 0.8px;
    }}

    /* ── TIP BOX ── */
    .tip {{
      background: rgba(96,165,250,0.07);
      border-left: 3px solid #3b82f6;
      padding: 12px 16px;
      border-radius: 0 6px 6px 0;
      font-size: 13px; color: #93c5fd;
      margin-bottom: 20px;
    }}

    /* ── SEARCH CARDS ── */
    .search-cards {{ display: flex; flex-direction: column; gap: 16px; }}
    .search-card {{
      border: 1px solid #222;
      border-radius: 8px;
      padding: 16px 20px;
      background: #0f0f0f;
    }}
    .sc-label {{ font-size: 15px; font-weight: 700; color: #e8e8e8; margin-bottom: 4px; }}
    .sc-meta {{ font-size: 12px; color: #666; margin-bottom: 12px; }}
    .sc-buttons {{ display: flex; gap: 8px; flex-wrap: wrap; }}
    .sc-btn {{
      display: inline-block;
      padding: 8px 16px;
      border-radius: 6px;
      text-decoration: none;
      font-size: 13px; font-weight: 600;
      color: #fff;
      transition: opacity 0.15s;
    }}
    .sc-btn:hover {{ opacity: 0.8; }}

    /* ── COMMUTE TABLE ── */
    .ct-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    .ct-table thead th {{
      padding: 9px 12px; text-align: left;
      color: #666; font-size: 12px;
      text-transform: uppercase; letter-spacing: 0.5px;
      border-bottom: 1px solid #1e1e1e;
    }}
    .ct-table tbody tr {{ border-bottom: 1px solid #161616; }}
    .ct-table tbody tr:hover {{ background: #161616; }}
    .ct-table td {{ padding: 9px 12px; }}
    .ct-time {{ color: #60a5fa; font-weight: 600; white-space: nowrap; }}
    .ct-transit {{ color: #888; font-size: 12px; }}

    /* ── TRACKER ── */
    .tracker-tip {{
      font-size: 13px; color: #666; margin-bottom: 16px;
    }}
    #tracker-table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 16px; }}
    #tracker-table thead th {{
      padding: 9px 12px; text-align: left;
      color: #666; font-size: 12px;
      text-transform: uppercase; letter-spacing: 0.5px;
      border-bottom: 1px solid #1e1e1e;
    }}
    #tracker-table tbody tr {{ border-bottom: 1px solid #161616; }}
    #tracker-table td {{ padding: 8px 12px; vertical-align: top; }}
    .tracker-link {{ color: #60a5fa; font-size: 12px; word-break: break-all; }}
    .tracker-input {{
      width: 100%; background: #1a1a1a; border: 1px solid #333;
      color: #e8e8e8; padding: 6px 10px; border-radius: 5px;
      font-size: 13px; font-family: inherit;
    }}
    .tracker-input:focus {{ outline: none; border-color: #60a5fa; }}
    .tracker-status {{
      display: inline-block; padding: 3px 8px;
      border-radius: 4px; font-size: 11px; font-weight: 600;
      cursor: pointer; border: none; transition: all 0.15s;
    }}
    .status-new       {{ background:#1e3a5f; color:#60a5fa; }}
    .status-interested{{ background:#1a3320; color:#4ade80; }}
    .status-toured    {{ background:#3a2a00; color:#fbbf24; }}
    .status-pass      {{ background:#2a1a1a; color:#f87171; }}
    .delete-btn {{
      background: none; border: 1px solid #333; color: #666;
      padding: 4px 10px; border-radius: 5px; cursor: pointer;
      font-size: 12px; transition: all 0.15s;
    }}
    .delete-btn:hover {{ border-color: #f87171; color: #f87171; }}
    .add-row-btn {{
      background: #1e3a5f; border: none; color: #60a5fa;
      padding: 8px 18px; border-radius: 6px;
      font-size: 13px; font-weight: 600; cursor: pointer;
      transition: opacity 0.15s;
    }}
    .add-row-btn:hover {{ opacity: 0.8; }}
    .export-btn {{
      background: #1a1a1a; border: 1px solid #333; color: #888;
      padding: 8px 18px; border-radius: 6px;
      font-size: 13px; cursor: pointer; margin-left: 8px;
      transition: all 0.15s;
    }}
    .export-btn:hover {{ border-color: #60a5fa; color: #60a5fa; }}

    /* ── CHECKLIST ── */
    .cl-section {{ margin-bottom: 20px; }}
    .cl-section-title {{
      font-size: 13px; font-weight: 700; color: #60a5fa;
      margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px;
    }}
    .checklist {{ list-style: none; }}
    .checklist li {{ padding: 7px 0; border-bottom: 1px solid #161616; font-size: 14px; }}
    .checklist li label {{ cursor: pointer; display: flex; align-items: flex-start; gap: 10px; }}
    .checklist li input[type="checkbox"] {{ margin-top: 3px; accent-color: #60a5fa; flex-shrink: 0; }}
  </style>
</head>
<body>

<div class="header">
  <h1>NYC <span>Apartment Search</span></h1>
  <p class="sub">Generated {now} &nbsp;·&nbsp; Commuting to {CONFIG['work_location']}</p>
  <div class="badges">
    <span class="badge">{active_count} search modes active</span>
    <span class="badge">5 platforms</span>
    <span class="badge">Commute guide included</span>
    <span class="badge">Built-in tracker</span>
  </div>
</div>

<div class="container">

  <!-- ── PLATFORM QUICK LAUNCH ── -->
  <div class="section">
    <div class="section-title">Open Searches on Each Platform</div>
    <div class="tip">
      Click any button to open a pre-filtered search matching that budget and bedroom count.
      <strong>StreetEasy</strong> is the best NYC-specific site — check it daily, good listings
      disappear within hours. <strong>Facebook Marketplace</strong> often has no-fee listings.
    </div>
    <div class="search-cards">
      {search_cards}
    </div>
  </div>

  <!-- ── APARTMENT TRACKER ── -->
  <div class="section">
    <div class="section-title">Your Apartment Tracker</div>
    <p class="tracker-tip">
      Found a listing you like? Add it here to keep track. Your data stays in this file — nothing is sent anywhere.
    </p>
    <table id="tracker-table">
      <thead>
        <tr>
          <th style="width:30%">Address / Name</th>
          <th style="width:22%">Link</th>
          <th style="width:10%">Price</th>
          <th style="width:12%">Status</th>
          <th>Notes</th>
          <th style="width:60px"></th>
        </tr>
      </thead>
      <tbody id="tracker-body">
        <!-- rows added by JS -->
      </tbody>
    </table>
    <button class="add-row-btn" onclick="addRow()">+ Add Listing</button>
    <button class="export-btn" onclick="exportCSV()">Export CSV</button>
  </div>

  <!-- ── COMMUTE GUIDE ── -->
  <div class="section">
    <div class="section-title">Commute Guide — to Hell's Kitchen</div>
    <div class="tip">
      Always test the real commute during weekday rush hour (8–9am) before you sign anything.
      These are estimates — NYC subway delays can add 10–20 minutes.
    </div>
    <table class="ct-table">
      <thead>
        <tr>
          <th>Neighborhood</th>
          <th>Est. Commute</th>
          <th>How to Get There</th>
        </tr>
      </thead>
      <tbody>
        {commute_rows}
      </tbody>
    </table>
  </div>

  <!-- ── CHECKLIST ── -->
  <div class="section">
    <div class="section-title">Apartment Hunting Checklist</div>
    {checklist}
  </div>

</div>

<script>
  const STATUSES = ['new', 'interested', 'toured', 'pass'];
  const STATUS_LABELS = {{
    'new': 'New',
    'interested': 'Interested',
    'toured': 'Toured',
    'pass': 'Pass'
  }};

  let rowCount = 0;

  function addRow(addr='', link='', price='', status='new', notes='') {{
    rowCount++;
    const id = rowCount;
    const tbody = document.getElementById('tracker-body');
    const tr = document.createElement('tr');
    tr.id = `row-${{id}}`;
    tr.innerHTML = `
      <td><input class="tracker-input" value="${{addr}}" placeholder="e.g. 123 W 45th St, Apt 4B" oninput="save()"></td>
      <td>
        <input class="tracker-input" value="${{link}}" placeholder="Paste listing URL" oninput="save()" id="link-${{id}}">
        ${{link ? `<br><a class="tracker-link" href="${{link}}" target="_blank">open ↗</a>` : ''}}
      </td>
      <td><input class="tracker-input" value="${{price}}" placeholder="$2,400/mo" oninput="save()" style="width:90px"></td>
      <td>
        <button class="tracker-status status-${{status}}" id="status-${{id}}"
          onclick="cycleStatus(${{id}})" data-status="${{status}}">
          ${{STATUS_LABELS[status]}}
        </button>
      </td>
      <td><input class="tracker-input" value="${{notes}}" placeholder="Notes..." oninput="save()"></td>
      <td><button class="delete-btn" onclick="deleteRow(${{id}})">✕</button></td>
    `;
    tbody.appendChild(tr);
    save();
  }}

  function cycleStatus(id) {{
    const btn = document.getElementById(`status-${{id}}`);
    const current = btn.dataset.status;
    const next = STATUSES[(STATUSES.indexOf(current) + 1) % STATUSES.length];
    btn.dataset.status = next;
    btn.className = `tracker-status status-${{next}}`;
    btn.textContent = STATUS_LABELS[next];
    save();
  }}

  function deleteRow(id) {{
    document.getElementById(`row-${{id}}`).remove();
    save();
  }}

  function getRows() {{
    const rows = [];
    document.querySelectorAll('#tracker-body tr').forEach(tr => {{
      const inputs = tr.querySelectorAll('input');
      const statusBtn = tr.querySelector('[data-status]');
      rows.push({{
        addr:   inputs[0]?.value || '',
        link:   inputs[1]?.value || '',
        price:  inputs[2]?.value || '',
        status: statusBtn?.dataset.status || 'new',
        notes:  inputs[3]?.value || '',
      }});
    }});
    return rows;
  }}

  function save() {{
    localStorage.setItem('nyc_tracker', JSON.stringify(getRows()));
  }}

  function load() {{
    try {{
      const saved = JSON.parse(localStorage.getItem('nyc_tracker') || '[]');
      saved.forEach(r => addRow(r.addr, r.link, r.price, r.status, r.notes));
    }} catch(e) {{}}
    if (document.querySelectorAll('#tracker-body tr').length === 0) {{
      addRow(); // start with one empty row
    }}
  }}

  function exportCSV() {{
    const rows = getRows();
    const header = 'Address,Link,Price,Status,Notes\\n';
    const lines = rows.map(r =>
      [r.addr, r.link, r.price, r.status, r.notes]
        .map(v => `"${{v.replace(/"/g, '""')}}"`)
        .join(',')
    );
    const csv = header + lines.join('\\n');
    const blob = new Blob([csv], {{ type: 'text/csv' }});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'apartment-tracker.csv';
    a.click();
  }}

  // Load tracker data when page opens
  load();
</script>

</body>
</html>"""


# ─── OPEN BROWSER TABS ─────────────────────────────────────────────────────────

def open_browser_tabs():
    """Open one tab per platform per active search config."""
    import time

    platform_names = {
        "streeteasy": "StreetEasy",
        "zillow":     "Zillow",
        "apartments": "Apartments.com",
        "craigslist": "Craigslist",
        "facebook":   "Facebook",
    }

    opened = 0
    for s in CONFIG["searches"]:
        if not s.get("open", True):
            continue
        label = s["label"].strip()
        urls  = _build_urls(s)

        print(f"\n  [{label}]")
        for platform in CONFIG["platforms"]:
            url = urls.get(platform, "")
            if not url:
                continue
            pname = platform_names.get(platform, platform)
            print(f"    Opening {pname}...")
            webbrowser.open(url)
            time.sleep(CONFIG["tab_delay_seconds"])
            opened += 1

    return opened


# ─── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print()
    print("=" * 60)
    print("  NYC APARTMENT SEARCH TOOL")
    print(f"  Commuting to: {CONFIG['work_location']}")
    print("=" * 60)

    # Generate the HTML dashboard
    print("\nBuilding dashboard...")
    html = generate_html()

    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)

    timestamp    = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path  = results_dir / f"apartments-{timestamp}.html"
    latest_path  = results_dir / "latest.html"

    output_path.write_text(html, encoding="utf-8")
    latest_path.write_text(html, encoding="utf-8")

    print(f"Saved: results/apartments-{timestamp}.html")

    # Open the dashboard first
    print("\nOpening dashboard in browser...")
    webbrowser.open(latest_path.as_uri())

    import time; time.sleep(1.5)  # Let dashboard load before tabs flood in

    # Open platform search tabs
    if CONFIG["auto_open_tabs"]:
        active = [s for s in CONFIG["searches"] if s.get("open", True)]
        n_tabs = len(active) * len(CONFIG["platforms"])
        print(f"\nOpening {n_tabs} search tabs across {len(CONFIG['platforms'])} platforms...")
        opened = open_browser_tabs()
        print(f"\n{opened} tabs opened.")
    else:
        print("\nauto_open_tabs is off — dashboard only.")

    print()
    print("=" * 60)
    print("  Done!")
    print("  Dashboard: results/latest.html")
    print("  Tip: Use the tracker in the dashboard to save listings.")
    print("  Re-run any time — tracker data is saved in your browser.")
    print("=" * 60)


if __name__ == "__main__":
    main()
