"""
Write the research report to a new Notion page.
Requires NOTION_TOKEN and NOTION_PAGE_ID in .env.
Gracefully skips (returns None) if not configured.
"""
import os
import re
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))


def _text_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}]
        }
    }


def _heading_block(text: str, level: int = 2) -> dict:
    htype = f"heading_{level}"
    return {
        "object": "block",
        "type": htype,
        htype: {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        }
    }


def _bullet_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}]
        }
    }


def _report_to_blocks(report: str) -> list[dict]:
    """Convert markdown report to Notion blocks. Max 100 blocks."""
    blocks = []
    for line in report.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('## '):
            blocks.append(_heading_block(stripped[3:], level=2))
        elif stripped.startswith('### '):
            blocks.append(_heading_block(stripped[4:], level=3))
        elif stripped.startswith(('- ', '• ', '* ')):
            blocks.append(_bullet_block(stripped[2:]))
        elif re.match(r'^\d+\.', stripped):
            blocks.append(_bullet_block(stripped))
        else:
            blocks.append(_text_block(stripped))

        if len(blocks) >= 99:
            blocks.append(_text_block("(Report truncated — see full version in results/ folder)"))
            break

    return blocks


def write_report(concept: str, report: str) -> Optional[str]:
    """
    Write research report to a new Notion page.
    Returns the Notion page URL, or None if Notion is not configured.
    """
    token = os.getenv('NOTION_TOKEN')
    parent_id = os.getenv('NOTION_PAGE_ID')

    if not token or not parent_id:
        return None

    try:
        from notion_client import Client
        notion = Client(auth=token)

        today = datetime.now().strftime('%Y-%m-%d')
        title = f"{concept[:60]} — Research Report {today}"

        blocks = _report_to_blocks(report)

        page = notion.pages.create(
            parent={"page_id": parent_id},
            properties={
                "title": {
                    "title": [{"type": "text", "text": {"content": title}}]
                }
            },
            children=blocks,
        )

        page_id = page['id'].replace('-', '')
        return f"https://notion.so/{page_id}"

    except Exception as e:
        print(f"  [notion] Write failed: {e}")
        return None
