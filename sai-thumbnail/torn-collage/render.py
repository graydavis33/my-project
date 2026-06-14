import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

src = sys.argv[1] if len(sys.argv) > 1 else "thumbnail.html"
out = sys.argv[2] if len(sys.argv) > 2 else "thumbnail_preview.png"

url = Path(src).resolve().as_uri()
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=2)
    pg.goto(url)
    pg.evaluate("document.fonts.ready")
    pg.wait_for_timeout(500)
    pg.screenshot(path=out, clip={"x": 0, "y": 0, "width": 1280, "height": 720})
    b.close()
print("wrote", out)
