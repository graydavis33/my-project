"""
Content Research Agent — Claude-powered research loop with tool use.

Instead of a fixed 5-step pipeline, Claude uses tools to gather data and decides
when it has enough to write a complete research report. Adds Reddit layer on top
of YouTube outlier analysis.
"""
import os
import json
import sys
from dotenv import load_dotenv
import anthropic

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
from usage_logger import track_response

from searcher import generate_queries, search_videos, fetch_subscriber_counts
from outlier import score_and_rank
from transcript import enrich_with_hooks


_TOOLS = [
    {
        "name": "generate_search_queries",
        "description": (
            "Generate 4 YouTube search query variants from a video concept. "
            "Call this first to expand the concept into search-friendly queries."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "concept": {"type": "string", "description": "The video concept to research"}
            },
            "required": ["concept"]
        }
    },
    {
        "name": "search_youtube",
        "description": (
            "Search YouTube using a list of queries. Returns video metadata including "
            "title, views, channel, duration, and subscriber count. "
            "If results are thin (fewer than 5 outliers after scoring), call again with broader queries."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "queries": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of search queries to run"
                }
            },
            "required": ["queries"]
        }
    },
    {
        "name": "score_outliers",
        "description": (
            "Score and rank videos by outlier score (views / subscribers). "
            "Filters to Shorts only (under 3 min, over 1k views). Returns top N outliers. "
            "Call after search_youtube."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "videos": {
                    "type": "array",
                    "description": "Video list from search_youtube"
                },
                "top_n": {
                    "type": "integer",
                    "description": "How many top outliers to return (default 10)"
                }
            },
            "required": ["videos"]
        }
    },
    {
        "name": "fetch_transcripts",
        "description": (
            "Fetch the first 90 seconds of transcripts from outlier videos for hook analysis. "
            "Some videos won't have transcripts — that's fine, they'll be skipped. "
            "Call on the scored outliers list."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "videos": {
                    "type": "array",
                    "description": "Outlier video list from score_outliers"
                }
            },
            "required": ["videos"]
        }
    },
    {
        "name": "search_reddit",
        "description": (
            "Search Reddit for real audience discussions about the video concept. "
            "Returns top posts — useful for finding what people actually struggle with, "
            "questions they ask, and the exact words they use. "
            "Use this to make the report feel grounded in real audience voice."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "concept": {
                    "type": "string",
                    "description": "Search query for Reddit"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of Reddit posts to return (default 8)"
                }
            },
            "required": ["concept"]
        }
    }
]


_SYSTEM = """You are an expert video content strategist and research agent for Gray Davis, a freelance videographer and content creator at Graydient Media.

Your job: given a video concept, research what makes similar videos go viral and produce a complete 10-section research report.

**Research process:**
1. Call `generate_search_queries` — expand the concept into 4 search query variants
2. Call `search_youtube` — find candidate videos across those queries
3. Call `score_outliers` — identify top outliers by views-to-subscriber ratio
4. If fewer than 5 outliers found, call `search_youtube` again with broader/different queries
5. Call `fetch_transcripts` — pull hook transcripts from the outliers
6. Call `search_reddit` — find real audience questions and pain points
7. Write the complete report directly in your final response

**Report format** — use these exact headers in order:

## PERFORMANCE DATA
Markdown table: Rank | Title (≤40 chars) | Views | Likes | Comments | Duration | Outlier Score | URL

## WHY EACH WAS AN OUTLIER
For each video, 2-3 sentences on what specifically drove outsized performance (hook, title angle, format, timing, emotion, etc.)

## TOP 5 HOOK PATTERNS
Name each pattern, explain why it works, give a verbatim example from the transcripts (or title if no transcript).

## FORMAT & LENGTH RECOMMENDATIONS
What formats and lengths performed best — cite specific examples from the data.

## HIGH-VALUE KEYWORDS
Bulleted list: topic keywords, emotional triggers, format indicators.

## REDDIT INSIGHTS
Top questions, pain points, and language patterns from Reddit. What does the audience actually struggle with or search for?

## 5 MINI HOOKS FOR GRAY'S CONCEPT
5 ready-to-use opening hooks for: "{concept}"
Each must work in the first 3 seconds. Label each with its hook type in bold.

## SCRIPT OUTLINE
Hook (3-10s) → Problem/Setup → Value Promise → Main Body (3-5 sub-sections) → CTA
For each section: name, purpose (1 sentence), suggested duration.

## FULL SCRIPT DRAFT
Word-for-word script in Gray's voice — casual, direct, first-person. No "hey guys welcome back."
Open with the hook. Target 3-5 minutes when spoken (~450-750 words). Include pacing cues in [brackets].

## PACING & SOUND DESIGN NOTES
Cut timing, music energy, b-roll moments, thumbnail angle — inferred from what made the outliers work.

Be specific, cite real examples from the data. No filler or generic advice."""


def _search_reddit(concept: str, limit: int = 8) -> list[dict]:
    """Search Reddit using the public JSON API. No auth needed."""
    import requests

    headers = {"User-Agent": "ContentResearcher/1.0 (educational tool)"}
    params = {
        "q": concept,
        "type": "link",
        "sort": "relevance",
        "t": "year",
        "limit": limit
    }

    try:
        resp = requests.get(
            "https://www.reddit.com/search.json",
            params=params,
            headers=headers,
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        posts = []
        for item in data.get("data", {}).get("children", []):
            p = item.get("data", {})
            posts.append({
                "title": p.get("title", ""),
                "subreddit": p.get("subreddit_name_prefixed", ""),
                "score": p.get("score", 0),
                "num_comments": p.get("num_comments", 0),
                "selftext": (p.get("selftext", "") or "")[:400],
                "url": f"https://reddit.com{p.get('permalink', '')}",
            })
        return posts
    except Exception as e:
        print(f"  [reddit] Search failed: {e}")
        return []


def _execute_tool(name: str, inputs: dict) -> str:
    """Execute a tool call and return result as a JSON string."""
    try:
        if name == "generate_search_queries":
            queries = generate_queries(inputs["concept"])
            return json.dumps({"queries": queries})

        elif name == "search_youtube":
            queries = inputs["queries"]
            videos = search_videos(queries)
            videos = fetch_subscriber_counts(videos)
            print(f"  [tool] search_youtube → {len(videos)} videos found")
            # Trim description to keep context window manageable
            compact = [{
                "video_id": v["video_id"],
                "channel_id": v["channel_id"],
                "channel_name": v["channel_name"],
                "title": v["title"],
                "duration": v["duration"],
                "duration_seconds": v["duration_seconds"],
                "views": v["views"],
                "likes": v["likes"],
                "comments": v["comments"],
                "subscribers": v["subscribers"],
                "published_at": v["published_at"],
                "url": v["url"],
            } for v in videos]
            return json.dumps({"videos": compact, "count": len(compact)})

        elif name == "score_outliers":
            videos = inputs["videos"]
            top_n = inputs.get("top_n", 10)
            outliers = score_and_rank(videos, top_n=top_n)
            print(f"  [tool] score_outliers → {len(outliers)} outliers identified")
            return json.dumps({"outliers": outliers, "count": len(outliers)})

        elif name == "fetch_transcripts":
            videos = inputs["videos"]
            enriched = enrich_with_hooks(videos)
            print(f"  [tool] fetch_transcripts → done")
            return json.dumps({"videos": enriched})

        elif name == "search_reddit":
            concept = inputs["concept"]
            limit = inputs.get("limit", 8)
            posts = _search_reddit(concept, limit)
            print(f"  [tool] search_reddit → {len(posts)} posts found")
            return json.dumps({"posts": posts})

        else:
            return json.dumps({"error": f"Unknown tool: {name}"})

    except Exception as e:
        print(f"  [tool] ERROR in {name}: {e}")
        return json.dumps({"error": str(e)})


def run_agent(concept: str) -> str:
    """
    Run the Content Research Agent.
    Claude uses tools in a loop to gather data, then writes the full report.
    Returns the final report as a markdown string.
    """
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set in .env")

    client = anthropic.Anthropic(api_key=api_key)
    system = _SYSTEM.replace('"{concept}"', f'"{concept}"')

    messages = [
        {
            "role": "user",
            "content": (
                f'Research this video concept: "{concept}"\n\n'
                "Use the available tools to gather YouTube outlier data and Reddit insights, "
                "then write the complete 10-section research report."
            )
        }
    ]

    print(f"\n  [agent] Starting research loop...")

    iteration = 0
    max_iterations = 12  # safety cap — should never hit this

    while iteration < max_iterations:
        iteration += 1
        print(f"  [agent] Iteration {iteration}...")

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=6000,
            system=system,
            tools=_TOOLS,
            messages=messages
        )

        track_response(response)

        # Append assistant response to conversation
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Agent finished — extract the text report
            for block in response.content:
                if hasattr(block, "text") and block.text.strip():
                    print(f"  [agent] Complete after {iteration} iteration(s).")
                    return block.text
            break

        if response.stop_reason == "tool_use":
            # Execute all tool calls in this response
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  [agent] → {block.name}")
                    result = _execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            messages.append({"role": "user", "content": tool_results})

        else:
            print(f"  [agent] Unexpected stop_reason: {response.stop_reason}")
            break

    return "ERROR: Agent did not produce a report within the iteration limit."
