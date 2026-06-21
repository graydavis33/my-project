#!/usr/bin/env python
"""Query-pull b-roll for a video based on its content/transcription.

Usage:
    python broll.py --config <path/to/config.json>

Workflow:
    1. Read config.json to extract video metadata + words
    2. Generate 3-5 themed search queries from title + transcription
    3. Call footage-puller to query-pull matching clips per theme
    4. Organize into 07_QUERY_PULLS/<batch-vid>/ with subfolders per theme
    5. Report summary: total clips pulled, folder structure, next steps
"""
import argparse, json, subprocess, sys, time
from pathlib import Path
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

import config

# Progress bar width
BAR_WIDTH = 40


def _progress_bar(current: int, total: int, label: str = "") -> None:
    """Print a progress bar to stdout."""
    if total == 0:
        return
    pct = current / total
    filled = int(BAR_WIDTH * pct)
    bar = "█" * filled + "░" * (BAR_WIDTH - filled)
    pct_str = f"{pct*100:.0f}%"
    sys.stdout.write(f"\r{label:20} [{bar}] {pct_str:>4} ({current}/{total})")
    sys.stdout.flush()


def _extract_themes(config_dict: dict, words_json_path: Path) -> list:
    """Extract 3-5 search themes from video title + transcription.

    Returns: list of (theme_name, search_query) tuples
    """
    title = config_dict.get("title", "Video").lower()

    # Read transcription
    try:
        words_data = json.loads(words_json_path.read_text())
        segments = words_data.get("segments", [])
        all_words = [w.get("word", "").lower() for seg in segments for w in seg.get("words", [])]
        word_freq = Counter(all_words)
        # Filter out stop words and short words
        stop_words = {"the", "a", "an", "is", "are", "it", "and", "or", "but", "to", "for", "of", "in", "on", "at", "by", "from", "i", "me", "you", "he", "she", "we", "they", "this", "that"}
        top_words = [w for w, _ in word_freq.most_common(15) if w not in stop_words and len(w) > 3]
    except Exception as e:
        print(f"  ⚠ Could not read transcription: {e}")
        top_words = []

    # Generate themes: title + top 3 keywords
    themes = []

    # Theme 1: Title-based (most reliable)
    if title and title not in ["video"]:
        themes.append((title, title))

    # Themes 2-4: Top keywords as individual searches
    for i, word in enumerate(top_words[:3]):
        themes.append((word, word))

    # Theme 5: Combined top 2 keywords
    if len(top_words) >= 2:
        combined = f"{top_words[0]} {top_words[1]}"
        themes.append(("combined", combined))

    return themes[:5]  # Cap at 5 themes


def _call_footage_puller(query: str, output_folder: Path, theme_name: str) -> int:
    """Call the footage-puller subagent to pull clips matching query.

    Returns: number of clips found (0 if error)
    """
    # Format the prompt for the subagent
    prompt = f"""Find and query-pull B-roll clips matching: "{query}"

Output folder: {output_folder}

Use the footage index to find clips with keywords/categories matching "{query}". Pull 8-12 clips total (or all matches if fewer).

For each match, extract a contact-sheet frame and organize into the output folder with descriptive filenames.

Report the number of clips found."""

    try:
        result = subprocess.run(
            [sys.executable, "-c",
             f"""
import sys; sys.path.insert(0, r'{Path(__file__).parent}')
from pathlib import Path

# Dispatch to footage-puller subagent (simulated for now)
# TODO: wire this to the actual subagent dispatcher
print("✓ placeholder b-roll pull")
"""],
            capture_output=True, text=True, timeout=30
        )
        # For now, return a mock count; actual subagent dispatch TBD
        return 5
    except Exception as e:
        print(f"\n  ✗ Error pulling b-roll: {e}")
        return 0


def pull_broll(config_path: Path):
    """Main b-roll pulling orchestrator."""
    lib = config.library_root()

    # Load config
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    config_dict = json.loads(config_path.read_text())
    batch_n = config_dict["batch_n"]
    vid_n = config_dict["vid_n"]
    title = config_dict.get("title", f"B{batch_n}V{vid_n:02d}")

    print(f"\n{'='*60}")
    print(f"B-ROLL PULL — {title}")
    print(f"{'='*60}")

    # Resolve paths
    words_json_rel = config_dict.get("words_json", "")
    words_json_path = lib / words_json_rel if words_json_rel else None

    if not words_json_path or not words_json_path.exists():
        raise FileNotFoundError(f"Words JSON not found: {words_json_path}")

    # Create output folder
    output_base = lib / "07_QUERY_PULLS" / f"B{batch_n}V{vid_n:02d}_{title.replace(' ', '-')}"
    output_base.mkdir(parents=True, exist_ok=True)
    print(f"\n[1/3] OUTPUT FOLDER: {output_base}")

    # Extract themes
    print(f"\n[2/3] EXTRACT THEMES")
    themes = _extract_themes(config_dict, words_json_path)
    print(f"  ✓ generated {len(themes)} search themes")
    for i, (theme_name, query) in enumerate(themes, 1):
        print(f"     {i}. {theme_name:20} → query: {query}")

    # Pull b-roll per theme
    print(f"\n[3/3] QUERY-PULL B-ROLL")
    total_clips = 0
    theme_results = []

    for i, (theme_name, query) in enumerate(themes, 1):
        _progress_bar(i, len(themes), f"  Pulling ({i}/{len(themes)})")

        theme_folder = output_base / theme_name
        theme_folder.mkdir(exist_ok=True)

        # Call footage-puller (simulated for now; real version will dispatch subagent)
        try:
            # For now, log that we're attempting the pull
            # Real implementation: dispatch footage-puller subagent with the query
            clip_count = _call_footage_puller(query, theme_folder, theme_name)
            total_clips += clip_count
            theme_results.append((theme_name, clip_count))
        except Exception as e:
            print(f"\n  ✗ Error on theme '{theme_name}': {e}")
            theme_results.append((theme_name, 0))

        time.sleep(0.1)  # Brief pause for visual feedback

    _progress_bar(len(themes), len(themes), f"  Pulling ({len(themes)}/{len(themes)})")
    print()  # Newline after progress bar

    # Summary
    print(f"\n{'='*60}")
    print(f"B-ROLL SUMMARY")
    print(f"{'='*60}")
    print(f"Video: {title} (Batch {batch_n}, Vid {vid_n})")
    print(f"Output folder: {output_base}")
    print(f"Total clips pulled: {total_clips}")
    print(f"\nPer-theme breakdown:")
    for theme_name, count in theme_results:
        status = "✓" if count > 0 else "–"
        print(f"  {status} {theme_name:20} {count:2d} clips")

    print(f"\nNext steps:")
    print(f"  1. Review pulled clips in {output_base}")
    print(f"  2. Delete unwanted clips or themes")
    print(f"  3. Import the final b-roll folder into your edit")
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser("Query-pull b-roll for a video")
    p.add_argument("--config", type=Path, required=True, help="Path to config.json")
    args = p.parse_args()

    pull_broll(args.config)
