#!/bin/bash
# Flip Claude's voice on or off. Speaks a short confirmation either way.
# Bound to a global hotkey via the "Toggle Claude Voice" Quick Action.

OFF_SWITCH="$HOME/.claude/voice-off"

# forget the remembered voice so newly downloaded Premium voices get picked up
rm -f "$HOME/.claude/.voice-cache"

if [ -f "$OFF_SWITCH" ]; then
    rm -f "$OFF_SWITCH"
    /usr/bin/say -v Samantha -r 200 "Voice on" &
    MSG="Claude voice: ON"
else
    touch "$OFF_SWITCH"
    pkill -f "^/usr/bin/say"          # cut off anything mid-sentence
    MSG="Claude voice: OFF"
fi

# banner notification so you get visual confirmation too
/usr/bin/osascript -e "display notification \"$MSG\" with title \"Claude Code\"" 2>/dev/null

echo "$MSG"
