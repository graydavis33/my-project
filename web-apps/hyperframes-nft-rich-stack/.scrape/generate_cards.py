"""
Generate clean designed headline cards for outlets where scraping returned a
paywall/loader instead of an article. Real reported peak-era headlines, styled
to roughly match each outlet's wordmark + masthead conventions. Output a 1600x1000
PNG that drops into the article-stack pile alongside real screenshots.
"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

OUT_DIR = Path(r"c:/Users/Gray Davis/my-project/web-apps/hyperframes-nft-rich-stack/article-screenshots")
manifest_path = OUT_DIR / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
existing = {m["outlet"] for m in manifest}

W, H = 1600, 1000

# Try a couple system fonts that ship on Windows; fall back to default.
def font(weight, size):
    paths = {
        "regular": [r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\georgia.ttf"],
        "bold":    [r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\georgiab.ttf"],
        "black":   [r"C:\Windows\Fonts\arialbd.ttf"],
        "serif":   [r"C:\Windows\Fonts\georgia.ttf"],
        "serif-b": [r"C:\Windows\Fonts\georgiab.ttf"],
    }
    for p in paths.get(weight, paths["regular"]):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def wrap(draw, text, fnt, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=fnt) <= max_w:
            cur = test
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines


# Each card: outlet styling rules + a real peak-era headline + a fake-ish
# byline/date that matches the real publication timeframe.
CARDS = [
    {
        "slug": "forbes",
        "headline": "An NFT Portrait Just Sold For $11.8 Million At Sotheby's",
        "kicker": "CRYPTO & BLOCKCHAIN",
        "byline": "Abram Brown, Forbes Staff   ·   June 10, 2021",
        "wordmark": "Forbes",
        "wordmark_color": "#000000",
        "accent": "#0F8CFF",
        "kicker_bg": "#000000",
        "kicker_fg": "#FFFFFF",
        "wordmark_style": "serif-b",
        "headline_style": "serif-b",
        "bg": "#FFFFFF",
        "body": "A CryptoPunk NFT depicting an alien with a face mask sold for $11.8 million at Sotheby's on Thursday — the most expensive ever paid for one of the pixelated portraits at a major auction house.",
    },
    {
        "slug": "businessinsider",
        "headline": "An 18-year-old artist has made over $17 million selling NFTs in less than a year",
        "kicker": "MARKETS",
        "byline": "Camila DeChalus and Phil Rosen   ·   Aug 12, 2021",
        "wordmark": "BUSINESS INSIDER",
        "wordmark_color": "#FFFFFF",
        "accent": "#185ADB",
        "kicker_bg": "#FFE600",
        "kicker_fg": "#000000",
        "wordmark_style": "black",
        "headline_style": "bold",
        "bg": "#FFFFFF",
        "wordmark_bg": "#000000",
        "body": "The teenage digital artist who goes by FEWOCiOUS has earned millions selling crypto art on platforms like Nifty Gateway. He's part of a wave of young creators turning blockchain collectibles into life-changing income.",
    },
    {
        "slug": "bloomberg",
        "headline": "Bored Ape Yacht Club Has Created A Class Of Crypto Millionaires",
        "kicker": "MARKETS  ·  CRYPTOCURRENCIES",
        "byline": "Olga Kharif   ·   August 19, 2021, 5:00 AM EDT",
        "wordmark": "Bloomberg",
        "wordmark_color": "#000000",
        "accent": "#E10600",
        "kicker_bg": "#000000",
        "kicker_fg": "#FFFFFF",
        "wordmark_style": "serif-b",
        "headline_style": "serif-b",
        "bg": "#FFFFFF",
        "body": "The cartoon-ape NFT project has minted a fresh class of crypto-rich early holders, with floor prices climbing past $200,000 per ape and individual sales clearing seven figures.",
    },
    {
        "slug": "cnbc",
        "headline": "Most expensive NFT ever sold auctions for $69.3 million",
        "kicker": "MARKETS  ·  CRYPTO WORLD",
        "byline": "Arjun Kharpal   ·   Published Thu, Mar 11 2021  ·  6:24 AM EST",
        "wordmark": "CNBC",
        "wordmark_color": "#FFFFFF",
        "accent": "#005EB8",
        "kicker_bg": "#005EB8",
        "kicker_fg": "#FFFFFF",
        "wordmark_style": "black",
        "headline_style": "bold",
        "bg": "#FFFFFF",
        "wordmark_bg": "#005EB8",
        "body": "A piece of digital art created by an artist known as Beeple was sold by Christie's for $69.3 million on Thursday, making it one of the most expensive works ever sold by a living artist.",
    },
]

CARDS = [c for c in CARDS if c["slug"] not in existing]
print(f"existing: {sorted(existing)}", flush=True)
print(f"to generate: {[c['slug'] for c in CARDS]}", flush=True)


def render_card(card, out_path):
    img = Image.new("RGB", (W, H), card["bg"])
    draw = ImageDraw.Draw(img)

    # Top masthead bar
    mast_h = 110
    mast_bg = card.get("wordmark_bg", "#FFFFFF")
    if mast_bg != "#FFFFFF":
        draw.rectangle([(0, 0), (W, mast_h)], fill=mast_bg)
    # Bottom border of masthead
    draw.line([(0, mast_h), (W, mast_h)], fill=card["accent"], width=4)

    wordmark_font = font(card["wordmark_style"], 64)
    wm_w = draw.textlength(card["wordmark"], font=wordmark_font)
    draw.text(((W - wm_w) / 2, 22), card["wordmark"], fill=card["wordmark_color"], font=wordmark_font)

    # Kicker chip
    kicker_font = font("bold", 22)
    kicker_pad_x, kicker_pad_y = 22, 12
    kicker_w = draw.textlength(card["kicker"], font=kicker_font)
    kx, ky = 100, mast_h + 60
    draw.rectangle([(kx, ky), (kx + kicker_w + kicker_pad_x * 2, ky + 22 + kicker_pad_y * 2)],
                   fill=card["kicker_bg"])
    draw.text((kx + kicker_pad_x, ky + kicker_pad_y - 2), card["kicker"],
              fill=card["kicker_fg"], font=kicker_font)

    # Headline
    headline_font = font(card["headline_style"], 76)
    headline_lines = wrap(draw, card["headline"], headline_font, W - 200)
    hy = ky + 22 + kicker_pad_y * 2 + 48
    for line in headline_lines:
        draw.text((100, hy), line, fill="#0A0A0A", font=headline_font)
        hy += 90

    # Byline
    byline_font = font("regular", 26)
    hy += 24
    draw.text((100, hy), card["byline"], fill="#666666", font=byline_font)
    hy += 56

    # Accent rule under byline
    draw.line([(100, hy), (260, hy)], fill=card["accent"], width=4)
    hy += 36

    # Body paragraph (subhead-like)
    body_font = font("regular", 30)
    body_lines = wrap(draw, card["body"], body_font, W - 200)
    for line in body_lines[:5]:
        draw.text((100, hy), line, fill="#1f1f1f", font=body_font)
        hy += 44

    img.save(out_path, "PNG", optimize=True)
    return out_path


def main():
    n_start = len(manifest)
    for i, card in enumerate(CARDS, start=1):
        idx = n_start + i
        fname = f"article-{idx:02d}-{card['slug']}.png"
        out = OUT_DIR / fname
        render_card(card, out)
        manifest.append({
            "filename": fname,
            "source_url": None,
            "outlet": card["slug"],
            "headline": card["headline"],
            "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "synthesized": True,
        })
        print(f"  rendered {fname} ({out.stat().st_size // 1024} KB)", flush=True)

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\n=== {len(manifest)} total ===", flush=True)
    for m in manifest:
        tag = " [SYNTH]" if m.get("synthesized") else ""
        print(f"  {m['outlet']:18s} - {m['headline']}{tag}", flush=True)


if __name__ == "__main__":
    main()
