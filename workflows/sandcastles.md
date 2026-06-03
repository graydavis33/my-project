# Workflow: Sandcastles Research MCP

**Status:** LIVE on Windows (Claude Code / VS Code extension) — Beta, hosted MCP
**Cost:** Subscription (Sandcastles plan; currently 1-month paid). MCP itself adds no Anthropic cost beyond the tokens of each chat. Public API path is locked behind the **Titan** plan.
**Script:** N/A — hosted MCP at `https://mcp.sandcastles.ai/`. Plugin source archived at `references/sandcastles-claude-plugin/`.

---

## Objective

Pull Sandcastles' short-form research data — outlier videos, hook patterns, formats, trending topics, channel intel across **Instagram / TikTok / YouTube Shorts** — directly into Claude Code, so research output can flow into the `scriptwriter` subagent, Obsidian, Slack, or content-pipeline draft folders without copy-pasting from their dashboard. Fills the cross-platform gap that `content-researcher` (YouTube-leaning) and `creator-intel` don't cover.

---

## When to Run

- Daily/weekly content planning for Sai or Graydient — "what should the next short be about?"
- Hook/format research before drafting a script
- Vetting or discovering new channels to track in a niche
- Deep-analyzing a specific viral video (paste the URL)

---

## Commands

Slash commands live in `.claude/commands/sandcastles/` (namespaced `/sandcastles:*`):

```
/sandcastles:topics              # trending topics in your watchlist niche
/sandcastles:video-suggest       # ranked recommendation for what to make next
/sandcastles:hooks-watchlist     # hook patterns among channels you follow
/sandcastles:hooks-global        # hook patterns across all of Sandcastles
/sandcastles:formats-watchlist   # top formats in your watchlist
/sandcastles:formats-global      # top formats globally
/sandcastles:videos-watchlist    # top videos from your watchlist
/sandcastles:videos-global [q]   # top videos globally for a topic
/sandcastles:analyze [url]       # deep-analyze one TikTok/IG/Shorts video
/sandcastles:channels-search [q] # find channels in a topic/niche
/sandcastles:channels-suggest    # recommend channels from your watchlist
/sandcastles:channels-add [id]   # add channel(s) to watchlist
/sandcastles:channels-recap [id] # recap one channel's recent activity
/sandcastles:rules               # show your auto-analyze automation rules
```

Or just ask in plain English — the underlying MCP tools fire either way.

---

## Underlying MCP Tools

| Tool | Purpose |
|------|---------|
| `top_topics` | Trending topics (watchlist) |
| `top_hooks` | Hook patterns — `scope: "watchlist"` / `"all"`; reads `spoken_hook_category` + `spoken_hook_madlib` |
| `top_formats` | Formats — `scope: "watchlist"` / `"all"`; groups by `format_category` |
| `search_all_videos` | Top videos globally (query required) |
| `search_my_videos` | Top videos from watchlist (query optional) |
| `discover_channels` | With `query` = smart search; no query = recommend from watchlist |
| `add_channels_to_watchlist` | Accepts UUIDs, handles, URLs, or a list |
| `channel_recap` | Recent activity + top videos for one channel |
| `analyze_video` | Single-video deep analysis (URL or `video_uuid`) |
| `list_automation_rules` | Auto-analyze rules in the workspace |

---

## Setup Checklist (First-Time Use)

- [x] MCP registered in `~/.claude.json` as `sandcastles` → `{"type":"http","url":"https://mcp.sandcastles.ai/"}`
- [x] Slash commands copied to `.claude/commands/sandcastles/`
- [ ] **Reload the VS Code window** (or restart Claude Code) so `--strict-mcp-config` picks up the new server
- [ ] Complete **OAuth** on first tool call (browser opens, log in with the paid Sandcastles account)
- [ ] Confirm with `/mcp` — should show `sandcastles` connected (9 total: 8 user-scope + filesystem at project scope)
- [ ] Build a watchlist: `/sandcastles:channels-add` Sai's competitors / founder-content creators, so watchlist-scoped tools have data

---

## How to Handle Failures

| Problem | Fix |
|---------|-----|
| `sandcastles` tools not available after editing config | Reload window — VS Code extension only reads `~/.claude.json` at startup |
| OAuth loop / 401 | Re-trigger any `/sandcastles:*` command to re-auth; confirm the subscription is active in Settings → Subscription |
| Watchlist tools return empty | No channels tracked yet — run `/sandcastles:channels-add` first |
| "API access requires Titan" | That's the **Public API**, not the MCP. The MCP works on the current plan; ignore unless building a standalone script |
| Config edit broke `~/.claude.json` | Restore from `~/.claude.json.bak` (created 2026-06-02 during install) |

---

## Known Constraints / Notes

- **Hosted MCP** — Sandcastles' servers must be up; no offline mode. Beta.
- **Overlaps** `content-researcher` + `creator-intel` by design (build-discipline §1) — kept because the **cross-platform IG/TikTok/Shorts outlier data** is a genuine gap those YouTube-leaning tools don't fill. Re-evaluate at subscription renewal.
- **Public API (Titan-only)** is the path for a standalone Python tool later; the MCP is the no-code path that works now.
- Plugin also ships its own `.mcp.json` pointing at the same URL, but the VS Code extension's `--strict-mcp-config` ignores plugin-bundled MCP servers — that's why it's registered directly in `~/.claude.json` instead.
