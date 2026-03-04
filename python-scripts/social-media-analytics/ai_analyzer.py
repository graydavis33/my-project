import os
import json
import anthropic
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

ANALYSIS_CACHE_FILE = os.path.join(os.path.dirname(__file__), '.analysis_cache.json')


def _load_analysis_cache():
    if os.path.exists(ANALYSIS_CACHE_FILE):
        try:
            with open(ANALYSIS_CACHE_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_analysis_cache(cache):
    tmp = ANALYSIS_CACHE_FILE + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(cache, f)
    os.replace(tmp, ANALYSIS_CACHE_FILE)


def _safe_title(title):
    """Sanitize video titles before inserting into Claude prompts."""
    if not isinstance(title, str):
        return ''
    return title.replace('\n', ' ').replace('\r', ' ')[:120]


def build_prompt(videos):
    total = len(videos)
    top = sorted(videos, key=lambda x: x['views'], reverse=True)[:10]
    bottom = sorted(videos, key=lambda x: x['views'])[:5]
    avg_views = sum(v['views'] for v in videos) / total if total else 0
    avg_ctr = sum(v['ctr_pct'] for v in videos) / total if total else 0
    avg_view_pct = sum(v['avg_view_pct'] for v in videos) / total if total else 0

    def fmt(v):
        return (
            f"  <title>{_safe_title(v['title'])}</title>\n"
            f"  Published: {v['published_date']} | Duration: {v['duration']}\n"
            f"  Views: {v['views']:,} | Watch Time: {v['watch_time_minutes']:,.0f} min | "
            f"Avg View: {v['avg_view_pct']}% | CTR: {v['ctr_pct']}%\n"
            f"  Likes: {v['likes']:,} | Comments: {v['comments']:,} | Shares: {v['shares']:,}\n"
        )

    return f"""You are a social media analytics expert. Analyze this YouTube channel data and provide deep, actionable insights.

CHANNEL OVERVIEW
- Total videos analyzed: {total}
- Average views per video: {avg_views:,.0f}
- Average CTR: {avg_ctr:.2f}%
- Average view percentage: {avg_view_pct:.1f}%

TOP 10 PERFORMING VIDEOS:
{''.join(fmt(v) for v in top)}
BOTTOM 5 PERFORMING VIDEOS:
{''.join(fmt(v) for v in bottom)}

Please provide a thorough analysis covering:
1. **What's Working** — Common patterns among top performers (length, topics, titles, timing)
2. **What's Not Working** — Why the low performers likely underperformed
3. **Audience Retention** — What the view % and watch time data reveals
4. **Click-Through Rate** — Are thumbnails and titles effective?
5. **Engagement Analysis** — Likes/comments/shares relative to views
6. **Top 5 Recommendations** — Specific, actionable changes to make immediately

Be specific. Reference actual video titles and numbers. Give honest, direct advice."""


def get_sheet_insights(videos):
    """Get a short dashboard summary + title pattern analysis from Claude Haiku.
    Both outputs are batched into one call and cached daily to minimize token usage."""
    api_key = os.getenv('ANTHROPIC_API_KEY', '').strip()
    if not api_key or not videos:
        return {'dashboard': '', 'title': ''}

    today = datetime.now().strftime('%Y-%m-%d')
    cache = _load_analysis_cache()
    if cache.get('sheet_insights_date') == today and 'sheet_insights' in cache:
        print("Sheet AI insights already generated today — using cache.")
        return cache['sheet_insights']

    total = len(videos)
    top5    = sorted(videos, key=lambda x: x['views'], reverse=True)[:5]
    bottom5 = sorted(videos, key=lambda x: x['views'])[:5]
    avg_eng = sum(v.get('engagement_rate', 0) for v in videos) / total if total else 0
    avg_ctr = sum(v.get('ctr_pct', 0) for v in videos) / total if total else 0
    avg_vp  = sum(v.get('avg_view_pct', 0) for v in videos) / total if total else 0

    top_titles    = '\n'.join(f'- <title>{_safe_title(v["title"])}</title>' for v in top5)
    bottom_titles = '\n'.join(f'- <title>{_safe_title(v["title"])}</title>' for v in bottom5)

    prompt = f"""You are a YouTube analytics expert. Given this channel data, provide two brief outputs.

CHANNEL STATS:
- Total videos: {total}
- Avg views: {sum(v["views"] for v in videos) / total:,.0f}
- Avg CTR: {avg_ctr:.1f}%
- Avg view %: {avg_vp:.1f}%
- Avg engagement rate: {avg_eng:.2f}%

TOP 5 TITLES (by views):
{top_titles}

BOTTOM 5 TITLES (by views):
{bottom_titles}

Respond with EXACTLY this format — no extra text before or after:

DASHBOARD_SUMMARY:
<3 sentences: overall channel health, what is working, and one key priority to focus on>

TITLE_ANALYSIS:
<3-4 bullet points on title patterns that separate top vs bottom performers>"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=400,
            messages=[{'role': 'user', 'content': prompt}]
        )
        text = response.content[0].text.strip()

        dashboard, title = '', ''
        if 'DASHBOARD_SUMMARY:' in text and 'TITLE_ANALYSIS:' in text:
            parts = text.split('TITLE_ANALYSIS:')
            dashboard = parts[0].replace('DASHBOARD_SUMMARY:', '').strip()
            title = parts[1].strip()
        else:
            dashboard = text[:300]

        result = {'dashboard': dashboard, 'title': title}
        cache['sheet_insights_date'] = today
        cache['sheet_insights'] = result
        _save_analysis_cache(cache)
        print("Sheet AI insights generated and cached.")
        return result

    except Exception as e:
        print(f"Note: Could not generate AI sheet insights: {type(e).__name__}")
        return {'dashboard': '', 'title': ''}


def write_to_notion(analysis):
    """Write AI analysis as a new page inside the Notion weekly reports page."""
    from notion_client import Client

    notion = Client(auth=os.getenv('NOTION_TOKEN'))
    parent_page_id = os.getenv('NOTION_PAGE_ID', '').strip()

    if not parent_page_id:
        print("NOTION_PAGE_ID not set in .env — skipping Notion write.")
        return

    # Page title: "Week of March 3, 2026"
    week_start = datetime.now() - timedelta(days=datetime.now().weekday())
    title = f"Week of {week_start.strftime('%B')} {week_start.day}, {week_start.year}"

    # Convert analysis text into Notion blocks
    blocks = []
    for line in analysis.split('\n'):
        if not line.strip():
            blocks.append({'object': 'block', 'type': 'paragraph',
                           'paragraph': {'rich_text': []}})
        elif line.startswith('**') and line.endswith('**'):
            blocks.append({'object': 'block', 'type': 'heading_3',
                           'heading_3': {'rich_text': [{'type': 'text',
                                                         'text': {'content': line.strip('*')}}]}})
        else:
            rich_text = []
            parts = line.split('**')
            for i, part in enumerate(parts):
                if part:
                    rich_text.append({'type': 'text', 'text': {'content': part},
                                      'annotations': {'bold': i % 2 == 1}})
            if rich_text:
                blocks.append({'object': 'block', 'type': 'paragraph',
                               'paragraph': {'rich_text': rich_text}})

    notion.pages.create(
        parent={'page_id': parent_page_id},
        properties={
            'title': {'title': [{'text': {'content': title}}]}
        },
        children=blocks[:100]
    )

    print(f"AI insights written to Notion: '{title}'")


def analyze_and_write(spreadsheet, videos):
    """Run Claude analysis and send to Notion (if configured).
    Skips the Claude call if analysis was already run today (saves tokens)."""
    api_key = os.getenv('ANTHROPIC_API_KEY', '').strip()
    if not api_key:
        print("Skipping AI analysis — ANTHROPIC_API_KEY not set in .env.")
        return

    notion_token = os.getenv('NOTION_TOKEN', '').strip()
    notion_page  = os.getenv('NOTION_PAGE_ID', '').strip()
    if not notion_token or not notion_page:
        print("Skipping AI analysis — add NOTION_TOKEN and NOTION_PAGE_ID to .env to enable.")
        return

    today = datetime.now().strftime('%Y-%m-%d')
    cache = _load_analysis_cache()
    if cache.get('last_run_date') == today:
        print(f"AI analysis already ran today ({today}). Skipping Claude call.")
        return

    print("Sending data to Claude for analysis...")
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=2000,
        messages=[{'role': 'user', 'content': build_prompt(videos)}]
    )
    analysis = response.content[0].text

    cache['last_run_date'] = today
    _save_analysis_cache(cache)
    write_to_notion(analysis)
