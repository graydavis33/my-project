---
name: device-compatibility
description: Cross-device sync setup between Mac and Windows using GitHub as the bridge — auto pull/push hooks, memory sync strategy
type: project
---

# Device Compatibility — Mac + Windows (+ future devices)

## Goal
Keep Claude Code in sync across all devices so work never has to be repeated on another machine.

## Current Devices
- Mac (primary, graydavis28)
- Windows PC (secondary)
- Future devices may be added

## How Sync Works
GitHub repo (`graydavis33/my-project`) is the central hub. Claude Code hooks auto-sync on every session.

### Hooks configured in ~/.claude/settings.json (Mac):
- **SessionStart** → `git pull` from `~/Desktop/my-project` (gets latest from all devices)
- **Stop** → `git add . && git commit && git push` (saves everything at session end)
- **PreCompact** → same push (saves before memory compaction so nothing is lost)

**Why:** The user works on both Mac and Windows and cannot do the same work twice. GitHub is the bridge.

**How to apply:** Always assume the repo may have newer changes from another device. The hooks handle this automatically, but if the user mentions switching devices mid-task, remind them to let the session start hook pull first.

## Memory Sync Problem (Unresolved)
Claude Code memory files live in `~/.claude/projects/.../memory/` — a local system folder NOT automatically pushed to GitHub. This means memory written on Windows stays on Windows and vice versa.

### Workaround (not yet implemented)
Add a `_memory/` folder inside the GitHub repo and set up scripts to copy memory files in/out. This would allow memory to travel between devices.

### Status
- Windows memory (social media analytics plans + more) is currently inaccessible from Mac
- User needs to manually copy/paste Windows memory contents when switching devices until a full solution is built
