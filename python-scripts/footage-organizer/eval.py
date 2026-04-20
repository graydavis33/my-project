"""
eval.py — measure analyzer accuracy against a hand-labeled test set.

Reads a CSV of (filepath, correct_category) rows, runs the current analyzer
on each clip (BYPASSING the cache), compares predictions to labels, and
prints overall accuracy + a confusion matrix + a list of misses.

Each run is also written to eval_runs/YYYY-MM-DD_HH-MM-SS.txt so we can
track improvement across prompt iterations.

Usage:
  cd python-scripts/footage-organizer
  python eval.py test-set.csv
  python eval.py test-set.csv --label "v3-stricter-interview-prompt"
"""
import argparse
import csv
import os
import sys
from collections import defaultdict
from datetime import datetime

from config import CATEGORIES
from extractor import ffmpeg_available, get_duration, extract_frames
from analyzer import classify_video


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate analyzer accuracy against a labeled CSV.")
    parser.add_argument("csv_path", help="Path to test-set CSV with columns: filepath, correct_category")
    parser.add_argument("--label", default="", help="Short label for this run (e.g. 'v3-stricter-prompt'). Saved in the log filename.")
    return parser.parse_args()


def load_test_set(csv_path):
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header != ["filepath", "correct_category"]:
            print(f"  Error: CSV header must be exactly: filepath,correct_category")
            print(f"  Got: {header}")
            sys.exit(1)
        for row in reader:
            if not row or row[0].strip().startswith("#"):
                continue
            if len(row) < 2:
                continue
            filepath, correct = row[0].strip(), row[1].strip()
            if not filepath or not correct:
                continue
            rows.append((filepath, correct))
    return rows


def validate_labels(rows):
    bad = [(p, c) for p, c in rows if c not in CATEGORIES]
    if bad:
        print(f"  Error: {len(bad)} row(s) use a label that isn't in CATEGORIES:")
        for p, c in bad[:10]:
            print(f"    {os.path.basename(p)} → '{c}'")
        print(f"  Valid categories: {', '.join(CATEGORIES)}")
        sys.exit(1)


def run_eval(rows):
    predictions = []
    for i, (filepath, correct) in enumerate(rows, 1):
        name = os.path.basename(filepath)
        print(f"  [{i}/{len(rows)}] {name}  (label: {correct})")

        if not os.path.isfile(filepath):
            print(f"         [skip] file not found")
            continue

        try:
            duration = get_duration(filepath)
            frames = extract_frames(filepath, duration)
            predicted = classify_video(frames, name)
        except Exception as e:
            print(f"         [skip] error: {e}")
            continue

        match = "OK " if predicted == correct else "MISS"
        print(f"         {match}  predicted: {predicted}")
        predictions.append((filepath, correct, predicted))
    return predictions


def report(predictions, label):
    total = len(predictions)
    if total == 0:
        print("\n  No predictions made — nothing to report.")
        return None

    correct = sum(1 for _, c, p in predictions if c == p)
    accuracy = correct / total * 100

    confusion = defaultdict(lambda: defaultdict(int))
    for _, c, p in predictions:
        confusion[c][p] += 1

    misses = [(os.path.basename(fp), c, p) for fp, c, p in predictions if c != p]

    lines = []
    lines.append("=" * 64)
    lines.append(f"EVAL RESULTS  {label or '(unlabeled run)'}")
    lines.append("=" * 64)
    lines.append(f"Total clips:    {total}")
    lines.append(f"Correct:        {correct}")
    lines.append(f"Accuracy:       {accuracy:.1f}%")
    lines.append("")
    lines.append("Per-category accuracy (rows = correct label, cols = predicted):")
    lines.append("")

    used_categories = sorted(set([c for _, c, _ in predictions] + [p for _, _, p in predictions]))
    col_w = max(len(c) for c in used_categories) + 2

    header = " " * (col_w + 2) + "  ".join(c[:10].ljust(10) for c in used_categories) + "   total  acc"
    lines.append(header)
    for actual in used_categories:
        row_total = sum(confusion[actual].values())
        if row_total == 0:
            continue
        row_correct = confusion[actual].get(actual, 0)
        row_acc = row_correct / row_total * 100 if row_total else 0
        cells = "  ".join(str(confusion[actual].get(p, 0)).rjust(10) for p in used_categories)
        lines.append(f"{actual.ljust(col_w)}  {cells}   {str(row_total).rjust(5)}  {row_acc:5.1f}%")

    lines.append("")
    if misses:
        lines.append(f"MISSES ({len(misses)}):")
        for name, actual, predicted in misses:
            lines.append(f"  {name}    expected: {actual:<24}  predicted: {predicted}")
    else:
        lines.append("No misses — perfect run.")
    lines.append("")

    text = "\n".join(lines)
    print("\n" + text)
    return text


def save_log(text, label):
    if text is None:
        return
    runs_dir = os.path.join(os.path.dirname(__file__), "eval_runs")
    os.makedirs(runs_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    label_part = f"_{label.replace(' ', '-')}" if label else ""
    out_path = os.path.join(runs_dir, f"{stamp}{label_part}.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"  Log saved: {out_path}")


def main():
    args = parse_args()

    if not ffmpeg_available():
        print("  Error: ffmpeg and ffprobe are required.")
        sys.exit(1)

    rows = load_test_set(args.csv_path)
    if not rows:
        print(f"  Error: no usable rows in {args.csv_path}")
        sys.exit(1)

    validate_labels(rows)

    print(f"\n  Running eval on {len(rows)} clip(s)...")
    print(f"  Label: {args.label or '(none)'}")
    print(f"  Cache: BYPASSED (every clip re-analyzed)\n")

    predictions = run_eval(rows)
    text = report(predictions, args.label)
    save_log(text, args.label)


if __name__ == "__main__":
    main()
