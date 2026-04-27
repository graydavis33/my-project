"""
Combine crash-course.md + playbook.md into a single phone-friendly HTML file.
Self-contained (inline CSS, no external assets) — AirDrop-ready.

Run after analyze.py finishes.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

try:
    import markdown as _md
    def md_to_html(text):
        return _md.markdown(text, extensions=["extra", "tables", "fenced_code", "sane_lists"])
except ImportError:
    # Fallback minimal converter — handles headers, bold/italic, lists, code, hr, links.
    def md_to_html(text):
        out = []
        in_list = None  # 'ul' or 'ol' or None
        in_code = False
        for line in text.split("\n"):
            if line.startswith("```"):
                if in_code:
                    out.append("</code></pre>")
                    in_code = False
                else:
                    out.append("<pre><code>")
                    in_code = True
                continue
            if in_code:
                out.append(line.replace("&", "&amp;").replace("<", "&lt;"))
                continue

            stripped = line.strip()
            if not stripped:
                if in_list:
                    out.append(f"</{in_list}>")
                    in_list = None
                out.append("")
                continue
            if stripped.startswith("---"):
                out.append("<hr>")
                continue

            m = re.match(r"^(#{1,6})\s+(.+)$", stripped)
            if m:
                if in_list:
                    out.append(f"</{in_list}>")
                    in_list = None
                level = len(m.group(1))
                out.append(f"<h{level}>{_inline(m.group(2))}</h{level}>")
                continue
            m = re.match(r"^(\d+)\.\s+(.+)$", stripped)
            if m:
                if in_list != "ol":
                    if in_list:
                        out.append(f"</{in_list}>")
                    out.append("<ol>")
                    in_list = "ol"
                out.append(f"<li>{_inline(m.group(2))}</li>")
                continue
            m = re.match(r"^[-*]\s+(.+)$", stripped)
            if m:
                if in_list != "ul":
                    if in_list:
                        out.append(f"</{in_list}>")
                    out.append("<ul>")
                    in_list = "ul"
                out.append(f"<li>{_inline(m.group(1))}</li>")
                continue
            if in_list:
                out.append(f"</{in_list}>")
                in_list = None
            out.append(f"<p>{_inline(stripped)}</p>")
        if in_list:
            out.append(f"</{in_list}>")
        return "\n".join(out)

    def _inline(s):
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
        s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
        s = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', s)
        return s


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>School of Hard Knocks — Reel Study</title>
<style>
:root {{
  --bg: #fafaf7;
  --fg: #1a1a1a;
  --muted: #666;
  --accent: #F28129;
  --line: #e6e3dc;
  --card: #fff;
  --code-bg: #f3f1ec;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg: #15140f;
    --fg: #ececec;
    --muted: #999;
    --line: #2a2925;
    --card: #1d1c17;
    --code-bg: #25231d;
  }}
}}
* {{ box-sizing: border-box; }}
html {{ -webkit-text-size-adjust: 100%; }}
body {{
  margin: 0;
  font-family: -apple-system, "SF Pro Text", "Helvetica Neue", system-ui, sans-serif;
  background: var(--bg);
  color: var(--fg);
  line-height: 1.55;
  font-size: 16px;
}}
header.top {{
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--bg);
  border-bottom: 1px solid var(--line);
  padding: 12px 18px;
  padding-top: max(12px, env(safe-area-inset-top));
}}
header.top h1 {{
  margin: 0;
  font-size: 16px;
  font-weight: 700;
}}
header.top h1 .tag {{
  color: var(--accent);
  font-weight: 600;
}}
nav.tabs {{
  display: flex;
  gap: 8px;
  margin-top: 10px;
}}
nav.tabs a {{
  flex: 1;
  text-align: center;
  padding: 8px 12px;
  border-radius: 8px;
  background: var(--card);
  border: 1px solid var(--line);
  color: var(--fg);
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
}}
main {{
  max-width: 720px;
  margin: 0 auto;
  padding: 24px 20px 60px;
  padding-bottom: max(60px, env(safe-area-inset-bottom));
}}
section.report {{
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 22px 20px;
  margin-bottom: 24px;
}}
section.report > h1:first-child {{
  margin-top: 0;
}}
h1, h2, h3, h4 {{
  line-height: 1.25;
  margin-top: 1.6em;
  margin-bottom: 0.5em;
  font-weight: 700;
}}
h1 {{ font-size: 26px; border-bottom: 2px solid var(--accent); padding-bottom: 6px; }}
h2 {{ font-size: 21px; color: var(--accent); }}
h3 {{ font-size: 18px; }}
h4 {{ font-size: 16px; color: var(--muted); }}
p {{ margin: 0.8em 0; }}
ul, ol {{ padding-left: 22px; margin: 0.6em 0; }}
li {{ margin: 0.3em 0; }}
strong {{ font-weight: 700; }}
em {{ font-style: italic; }}
code {{
  background: var(--code-bg);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: "SF Mono", Menlo, monospace;
  font-size: 0.92em;
}}
pre {{
  background: var(--code-bg);
  padding: 14px;
  border-radius: 8px;
  overflow-x: auto;
  font-size: 0.9em;
}}
pre code {{ background: transparent; padding: 0; }}
blockquote {{
  border-left: 3px solid var(--accent);
  margin: 1em 0;
  padding: 0.4em 14px;
  color: var(--muted);
  background: var(--card);
}}
hr {{
  border: none;
  border-top: 1px solid var(--line);
  margin: 2em 0;
}}
a {{ color: var(--accent); }}
table {{
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
  font-size: 14px;
}}
th, td {{
  border: 1px solid var(--line);
  padding: 8px 10px;
  text-align: left;
}}
th {{ background: var(--code-bg); font-weight: 700; }}
.meta {{
  font-size: 13px;
  color: var(--muted);
  margin-top: 4px;
}}
</style>
</head>
<body>
<header class="top">
  <h1>School of Hard Knocks <span class="tag">— Reel Study</span></h1>
  <div class="meta">Generated {date} • {n_reels} reels analyzed</div>
  <nav class="tabs">
    <a href="#crash-course">Crash Course</a>
    <a href="#playbook">Playbook</a>
  </nav>
</header>
<main>
<section class="report" id="crash-course">
{crash_course_html}
</section>
<section class="report" id="playbook">
{playbook_html}
</section>
</main>
</body>
</html>
"""


def main():
    crash_md = (ROOT / "crash-course.md").read_text()
    playbook_md = (ROOT / "playbook.md").read_text()

    # Count reels from data.csv
    import csv
    n_reels = 0
    with open(ROOT / "data.csv") as f:
        n_reels = sum(1 for _ in csv.DictReader(f))

    from datetime import date
    html = HTML_TEMPLATE.format(
        date=date.today().isoformat(),
        n_reels=n_reels,
        crash_course_html=md_to_html(crash_md),
        playbook_html=md_to_html(playbook_md),
    )
    out = ROOT / "school-of-hard-knocks.html"
    out.write_text(html)
    print(f"Wrote {out}")
    print(f"Open: open '{out}'")
    print(f"AirDrop: Finder → right-click → Share → AirDrop")


if __name__ == "__main__":
    main()
