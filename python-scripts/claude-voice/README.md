# Claude Voice — read responses out loud (Mac only)

Makes Claude Code speak its answers instead of Gray having to read them.
Built 2026-07-29. Uses macOS built-in `say` — no API key, no cost, no internet.

## Current settings

- Voice: `Ava (Premium)`
- Speed: 150 words per minute
- Hotkey: **Control + Option + V** (toggles voice on/off, also kills speech mid-sentence)

## The files here are BACKUP COPIES

The live files that actually run are:

| Live location (this is what runs) | Backup in this folder |
|---|---|
| `~/.claude/hooks/speak-response.py` | `speak-response.py` |
| `~/.claude/hooks/voice-toggle.sh` | `voice-toggle.sh` |
| `~/Library/Services/Toggle Claude Voice.workflow` | `quick-action/Toggle Claude Voice.workflow` |

Edit the live copies, then re-copy here before pushing. Editing this folder alone
changes nothing.

## How it works

1. `speak-response.py` runs as a **Stop hook** (wired in `~/.claude/settings.json`)
   — it fires every time Claude finishes a response.
2. It reads the session transcript, pulls the last assistant message, strips out
   code blocks / file paths / URLs / markdown symbols / emoji, then pipes the
   remaining plain text to `say` in the background.
3. It kills any still-playing speech first, so responses never overlap.
4. If `~/.claude/voice-off` exists, it stays silent.

`voice-toggle.sh` creates or deletes that `voice-off` file, shows a notification
banner, and clears `~/.claude/.voice-cache` so newly downloaded voices get picked up.
The Quick Action bundle is what lets a global hotkey run that script.

## Changing things

Both settings are at the top of `~/.claude/hooks/speak-response.py`:

- `VOICE` — exact voice name. Run `say -v '?'` for the full list.
  Set to `"auto"` to auto-pick the best installed voice (prefers Ava > Zoe > Evan).
- `RATE` — words per minute. 150 = slow/deliberate, 185 = natural, 250 = fast.
- `MAX_CHARS` — 1200; longer responses get cut at the last sentence.

**Gotcha:** asking for a voice that isn't installed does NOT error. macOS silently
falls back to Samantha. So if it sounds wrong, the voice probably isn't downloaded.
Get Premium voices at System Settings > Accessibility > Spoken Content >
System Voice (ⓘ) > Manage Voices > English (US). Pick the **Premium** tier —
the plain and Enhanced versions of the same name sound worse.

## Rebuilding on a fresh Mac

```bash
mkdir -p ~/.claude/hooks
cp speak-response.py voice-toggle.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/voice-toggle.sh
cp -R "quick-action/Toggle Claude Voice.workflow" ~/Library/Services/
/System/Library/CoreServices/pbs -flush && /System/Library/CoreServices/pbs -update
```

Then add to the `Stop` hooks array in `~/.claude/settings.json`:

```json
{ "type": "command",
  "command": "python3 ~/.claude/hooks/speak-response.py 2>/dev/null || true",
  "statusMessage": "Speaking response..." }
```

Re-assign the hotkey by writing `NSServicesStatus` in `~/Library/Preferences/pbs.plist`
(key `"(null) - Toggle Claude Voice - runWorkflowAsService"`, `key_equivalent` `"^~v"`
where `^`=Control `~`=Option `@`=Command `$`=Shift), then `killall cfprefsd` and
**log out and back in** — running apps cache the Services menu at launch.

## Windows

Does not work. `say` and Automator are Mac-only. A Windows version would need
PowerShell `System.Speech` instead — not built.

## Known limits

- Services hotkeys can be unreliable in Electron apps (VS Code). If ⌃⌥V does
  nothing after a logout, switch to Karabiner-Elements or skhd for a truly
  global hotkey.
- Only the last text block is spoken; if Claude ends a turn with only tool calls
  and no text, nothing is said.
