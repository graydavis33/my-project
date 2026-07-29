"""Parser tests built from the two real production failures (2026-07-27 + 2026-07-28).

Run: python test_parse.py
"""

import sys

from main import parse_issue

BODY = "<div style='padding:32px'>" + ("<p>Real article text goes here.</p>" * 30) + "</div>"


def check(name, text, expect_title=None, expect_error=False):
    try:
        meta, html = parse_issue(text)
    except ValueError as err:
        if expect_error:
            print(f"ok   {name} (rejected: {err})")
            return True
        print(f"FAIL {name}: {err}")
        return False
    if expect_error:
        print(f"FAIL {name}: expected a rejection, got {meta}")
        return False
    if expect_title and meta["TITLE"] != expect_title:
        print(f"FAIL {name}: title was {meta['TITLE']!r}")
        return False
    if not html.startswith("<div"):
        print(f"FAIL {name}: html started with {html[:40]!r}")
        return False
    print(f"ok   {name}")
    return True


results = []

# The happy path the prompt asks for.
results.append(check(
    "clean format",
    f"TITLE: How Tokens Work\nCATEGORY: fundamentals\nTOPIC: tokens\n===HTML===\n{BODY}",
    expect_title="How Tokens Work",
))

# 2026-07-28 failure: chatty preamble + markdown-bolded labels + no ===HTML=== marker.
results.append(check(
    "bolded labels, preamble, no marker",
    "Now I have enough research to write a strong fundamentals issue. Here is Issue #4:\n\n"
    "---\n\n**TITLE:** Tokens and Context Windows: The Hidden Limits\n"
    "**CATEGORY:** fundamentals\n**TOPIC:** tokens-and-context-windows\n\n---\n\n"
    f"{BODY}",
    expect_title="Tokens and Context Windows: The Hidden Limits",
))

# Markdown-header labels, another plausible drift.
results.append(check(
    "header-style labels",
    f"## TITLE: A Good Read\n## CATEGORY: news\n## TOPIC: a-good-read\n===HTML===\n{BODY}",
    expect_title="A Good Read",
))

# 2026-07-27 failure: research notes only, no labels and no HTML at all.
results.append(check(
    "commentary only",
    "Good. I have solid research from my searches. Let me now write the full issue.\n\n"
    "**Research gathered:**\n- Token definitions: Couchbase, Voiceflow\n",
    expect_error=True,
))

# Labels present but the HTML got cut off mid-generation.
results.append(check(
    "truncated html",
    "TITLE: Cut Short\nCATEGORY: news\nTOPIC: cut-short\n===HTML===\n<div>oops",
    expect_error=True,
))

# Labels missing the topic slug.
results.append(check(
    "missing topic label",
    f"TITLE: No Slug\nCATEGORY: news\n===HTML===\n{BODY}",
    expect_error=True,
))

# Markdown code fences wrapped around the body.
results.append(check(
    "fenced html",
    f"TITLE: Fenced\nCATEGORY: news\nTOPIC: fenced\n===HTML===\n```html\n{BODY}\n```",
    expect_title="Fenced",
))

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
