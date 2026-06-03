---
description: Add channels to your watchlist
argument-hint: [channel handle, URL, or UUID — one or more]
---
Add this channel (or these channels) to my watchlist: $ARGUMENTS

Use the `add_channels_to_watchlist` tool. Pass `$ARGUMENTS` as the channel identifier(s) — accepts UUIDs, handles, URLs, or a list of any combination. Report back which channels were added, which were submitted as new to Sandcastles (and that scraping is in progress), and which were skipped (with the reason). If `$ARGUMENTS` is empty, ask the user which channel(s) they want to add.
