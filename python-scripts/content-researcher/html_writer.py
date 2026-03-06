"""
html_writer.py
Converts the research report to a styled HTML file matching the dashboard design.
Saves to results/ folder and auto-opens in the browser.
"""
import os
import re
import webbrowser
from datetime import datetime


_RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')


def _md_inline(text: str) -> str:
    """Convert inline markdown (bold, italic, links) to HTML."""
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    return text


def _parse_table(block_lines: list) -> str:
    """Convert markdown table lines to an HTML table."""
    html = '<div class="table-wrap"><table><thead>'
    header_done = False
    for line in block_lines:
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r'^\|[\s\-:|]+\|', stripped):
            if not header_done:
                html += '</thead><tbody>'
                header_done = True
            continue
        cells = [c.strip() for c in stripped.strip('|').split('|')]
        cells_html = ''.join(
            f'<{"th" if not header_done else "td"}>{_md_inline(c)}<{"th" if not header_done else "td"}>'
            .replace(f'<{"th" if not header_done else "td"}>', f'<{"th" if not header_done else "td"}>')
            for c in cells
        )
        if not header_done:
            html += '<tr>' + ''.join(f'<th>{_md_inline(c)}</th>' for c in cells) + '</tr>'
        else:
            html += '<tr>' + ''.join(f'<td>{_md_inline(c)}</td>' for c in cells) + '</tr>'
    if not header_done:
        html += '</thead><tbody>'
    html += '</tbody></table></div>'
    return html


def _render_section_body(lines: list) -> str:
    """Render a list of content lines to HTML."""
    html = ''
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # Table
        if stripped.startswith('|'):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1
            html += _parse_table(table_lines)
            continue

        # H3
        if stripped.startswith('### '):
            html += f'<h3>{_md_inline(stripped[4:])}</h3>'
            i += 1
            continue

        # Bullet list
        if stripped.startswith(('- ', '* ', '• ')):
            html += '<ul>'
            while i < len(lines) and lines[i].strip().startswith(('- ', '* ', '• ')):
                item = lines[i].strip()[2:]
                html += f'<li>{_md_inline(item)}</li>'
                i += 1
            html += '</ul>'
            continue

        # Numbered list
        if re.match(r'^\d+\.', stripped):
            html += '<ol>'
            while i < len(lines) and re.match(r'^\d+\.', lines[i].strip()):
                item = re.sub(r'^\d+\.\s*', '', lines[i].strip())
                html += f'<li>{_md_inline(item)}</li>'
                i += 1
            html += '</ol>'
            continue

        # Horizontal rule
        if stripped.startswith('---'):
            i += 1
            continue

        # Regular paragraph
        html += f'<p>{_md_inline(stripped)}</p>'
        i += 1

    return html


def write_html_report(concept: str, report: str) -> str:
    """
    Convert the research report to a styled HTML file.
    Returns the file path.
    """
    os.makedirs(_RESULTS_DIR, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    date_str = datetime.now().strftime('%B %d, %Y · %I:%M %p')
    slug = re.sub(r'[^a-z0-9]+', '-', concept.lower().strip())[:50].strip('-')
    filename = f'{slug}-{timestamp}.html'
    filepath = os.path.join(_RESULTS_DIR, filename)

    # Split report into sections by ## headers
    sections = []
    current_title = None
    current_lines = []

    for line in report.splitlines():
        if line.startswith('## '):
            if current_title is not None:
                sections.append((current_title, current_lines))
            current_title = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_title is not None:
        sections.append((current_title, current_lines))

    # Build section cards
    cards_html = ''
    for title, lines in sections:
        body = _render_section_body(lines)
        if not body.strip():
            continue
        cards_html += f'''
    <div class="section-card">
      <div class="section-title">{title}</div>
      <div class="section-body">{body}</div>
    </div>'''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Research: {concept}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #0d0d0d;
      color: #e8e8e8;
      min-height: 100vh;
      padding: 32px 24px 80px;
    }}

    .header {{
      max-width: 880px;
      margin: 0 auto 36px;
      border-bottom: 1px solid #222;
      padding-bottom: 20px;
    }}
    .header-top {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 8px;
    }}
    .header h1 {{
      font-size: 22px;
      font-weight: 700;
      color: #fff;
      letter-spacing: -0.4px;
      line-height: 1.3;
    }}
    .header h1 span {{ color: #555; font-weight: 400; font-size: 16px; display: block; margin-top: 3px; }}
    .badge {{
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.5px;
      padding: 4px 10px;
      border-radius: 4px;
      background: #0c2340;
      color: #60a5fa;
      white-space: nowrap;
      flex-shrink: 0;
    }}
    .meta {{
      font-size: 12px;
      color: #444;
    }}

    .content {{
      max-width: 880px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}

    .section-card {{
      background: #141414;
      border: 1px solid #222;
      border-radius: 12px;
      padding: 24px 28px;
    }}
    .section-card:hover {{ border-color: #2a2a2a; }}

    .section-title {{
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 1px;
      text-transform: uppercase;
      color: #555;
      margin-bottom: 16px;
      padding-bottom: 10px;
      border-bottom: 1px solid #1e1e1e;
    }}

    .section-body h3 {{
      font-size: 14px;
      font-weight: 600;
      color: #ddd;
      margin: 18px 0 8px;
    }}
    .section-body h3:first-child {{ margin-top: 0; }}

    .section-body p {{
      font-size: 13.5px;
      color: #aaa;
      line-height: 1.7;
      margin-bottom: 10px;
    }}
    .section-body p:last-child {{ margin-bottom: 0; }}

    .section-body ul,
    .section-body ol {{
      padding-left: 18px;
      margin-bottom: 10px;
    }}
    .section-body li {{
      font-size: 13px;
      color: #999;
      line-height: 1.65;
      margin-bottom: 4px;
    }}
    .section-body strong {{ color: #ddd; }}
    .section-body em {{ color: #888; font-style: italic; }}
    .section-body a {{ color: #60a5fa; text-decoration: none; }}
    .section-body a:hover {{ text-decoration: underline; }}

    /* Table */
    .table-wrap {{
      overflow-x: auto;
      margin-bottom: 10px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12.5px;
    }}
    th {{
      text-align: left;
      padding: 8px 12px;
      background: #1a1a1a;
      color: #666;
      font-weight: 600;
      font-size: 11px;
      letter-spacing: 0.4px;
      border-bottom: 1px solid #222;
      white-space: nowrap;
    }}
    td {{
      padding: 8px 12px;
      color: #bbb;
      border-bottom: 1px solid #1a1a1a;
      vertical-align: top;
    }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: #181818; }}
  </style>
</head>
<body>

  <div class="header">
    <div class="header-top">
      <h1>{concept}<span>Content Research Report</span></h1>
      <div class="badge">RESEARCH REPORT</div>
    </div>
    <div class="meta">Generated {date_str} &nbsp;·&nbsp; Gray Davis</div>
  </div>

  <div class="content">
    {cards_html}
  </div>

</body>
</html>'''

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)

    return filepath
