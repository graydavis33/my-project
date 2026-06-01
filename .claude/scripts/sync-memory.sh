#!/usr/bin/env bash
# Sync Claude memory files between local (~/.claude/projects/*/memory/) and
# the my-project repo's _memory/ folder, so memory travels between Mac and
# Windows via GitHub.
#
# Usage:
#   sync-memory.sh export   # local → repo (run BEFORE git add/commit/push)
#   sync-memory.sh import   # repo → local (run AFTER git pull)
#
# Excludes files containing credentials (e.g. github.md) — see EXCLUDE list.
#
# Strategy: per-file last-write-wins by modification time. Safe as long as
# only one machine is actively writing memory at a time (typical for Gray).

set -uo pipefail

MODE="${1:-}"
if [ "$MODE" != "export" ] && [ "$MODE" != "import" ]; then
    echo "Usage: $0 {export|import}" >&2
    exit 1
fi

# Derive repo path from this script's location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPO_MEMORY="$REPO/_memory"

# Auto-detect local memory dir (handles different usernames per machine)
LOCAL_MEMORY=""
for candidate in ~/.claude/projects/*/memory; do
    if [ -d "$candidate" ]; then
        LOCAL_MEMORY="$candidate"
        break
    fi
done

if [ -z "$LOCAL_MEMORY" ]; then
    echo "[sync-memory] No local memory dir found under ~/.claude/projects/*/memory" >&2
    exit 0
fi

mkdir -p "$REPO_MEMORY"

# Files NEVER to sync (contain credentials or device-local state)
EXCLUDE=(
    "github.md"
)

is_excluded() {
    local name="$1"
    for ex in "${EXCLUDE[@]}"; do
        [ "$name" = "$ex" ] && return 0
    done
    return 1
}

# Copy file ONLY if source is newer than destination (or destination missing).
# Preserves mtime so the comparison stays meaningful across syncs.
sync_if_newer() {
    local src="$1"
    local dst="$2"
    if [ ! -f "$dst" ]; then
        cp -p "$src" "$dst"
        echo "  + $(basename "$src") (new)"
        return
    fi
    if [ "$src" -nt "$dst" ]; then
        cp -p "$src" "$dst"
        echo "  ~ $(basename "$src") (updated)"
    fi
}

if [ "$MODE" = "export" ]; then
    echo "[sync-memory] export: local → repo"
    for src in "$LOCAL_MEMORY"/*.md; do
        [ -f "$src" ] || continue
        name="$(basename "$src")"
        if is_excluded "$name"; then
            echo "  - $name (excluded)"
            continue
        fi
        sync_if_newer "$src" "$REPO_MEMORY/$name"
    done
fi

if [ "$MODE" = "import" ]; then
    echo "[sync-memory] import: repo → local"
    [ -d "$REPO_MEMORY" ] || { echo "  (no _memory/ in repo yet)"; exit 0; }
    for src in "$REPO_MEMORY"/*.md; do
        [ -f "$src" ] || continue
        name="$(basename "$src")"
        if is_excluded "$name"; then
            echo "  - $name (excluded)"
            continue
        fi
        sync_if_newer "$src" "$LOCAL_MEMORY/$name"
    done
fi

exit 0
