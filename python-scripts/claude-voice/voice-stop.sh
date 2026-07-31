#!/bin/bash
# Kill any speech still playing the instant Gray sends a new message.
# Wired as a UserPromptSubmit hook so the voice never lags a turn behind.
pkill -f '^/usr/bin/say' 2>/dev/null
exit 0
