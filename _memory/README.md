# Memory Sync Folder

This folder is a **mirror of Mac's Claude Code memory files** so they travel between devices via GitHub.

## Source of truth (Mac)
`~/.claude/projects/-Users-graydavis28/memory/`

## How it works

- **Mac → GitHub:** before pushing, run `cp ~/.claude/projects/-Users-graydavis28/memory/*.md ~/Desktop/my-project/_memory/`
- **Windows → reads:** Claude Code on Windows can read these files directly from the repo to get full context from Mac sessions
- **Windows → writes back:** if Windows updates anything, commit those changes here, then on next Mac session copy them back into `~/.claude/projects/.../memory/`

## Why not auto-sync?

Memory files live outside the repo by design (Claude Code's local state folder). Until a proper sync script exists, this folder is the manual bridge.

## To read on Windows

Just open these `.md` files. Each one has frontmatter (`name`, `description`, `type`) and the actual memory content below.
