import os
import anthropic
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

# Set to True once NOTION_TOKEN and NOTION_PAGE_ID are in .env
NOTION_ENABLED = False


def build_prompt(videos):
    total = len(videos)
    top = sorted(videos, key=lambda x: x['views'], reverse=True)[:10]
    bottom = sorted(videos, key=lambda x: x['views'])[:5]
    avg_views = sum(v['views'] for v in videos) / total if total else 0
    avg_ctr = sum(v['ctr_pct'] for v in videos) / total if total else 0
    avg_view_pct = sum(v['avg_view_pct'] for v in videos) / total if total else 0

    def fmt(v):
        return (
            f"  \"{v['title']}\"\n"
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
    title = f"Week of {week_start.strftime('%B %-d, %Y')}"

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
            # Bold inline markers
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
        children=blocks[:100]  # Notion API limit per request
    )

    print(f"AI insights written to Notion: '{title}'")


def analyze_and_write(spreadsheet, videos):
    """Run Claude analysis. Writes to Notion if enabled, otherwise skips."""
    api_key = os.getenv('ANTHROPIC_API_KEY', '').strip()
    if not api_key:
        print("Skipping AI analysis — ANTHROPIC_API_KEY not set in .env.")
        return

    if not NOTION_ENABLED:
        print("Notion insights ready but not yet activated. (Set NOTION_ENABLED=True in ai_analyzer.py when ready)")
        return

    print("Sending data to Claude for analysis...")
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=2000,
        messages=[{'role': 'user', 'content': build_prompt(videos)}]
    )
    analysis = response.content[0].text

    write_to_notion(analysis)
