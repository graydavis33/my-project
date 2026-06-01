"""
Content Researcher — Agentic Outlier Video Analysis

Usage:
  python main.py "your video concept"
  python main.py                        (will prompt for input)

Claude uses tools in a loop to research outlier YouTube videos and Reddit
discussions, then writes a 10-section report with hooks, script, keywords, etc.

Results are cached for 7 days — same concept = instant re-run, no API cost.
"""
import os
import re
import sys
import io
from datetime import datetime
from dotenv import load_dotenv

# Fix Windows terminal Unicode issues (emoji in video titles)
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from agent import run_agent
from html_writer import write_html_report
from cache import get_cached


def _slug(concept: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', concept.lower().strip())
    return slug[:50].strip('-')


def _save_report(concept: str, report: str, from_cache: bool):
    """Save report as .md file in results/"""
    results_dir = os.path.join(os.path.dirname(__file__), 'results')
    os.makedirs(results_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{_slug(concept)}-{timestamp}.md"
    filepath = os.path.join(results_dir, filename)
    header = f"# Research Report: {concept}\n_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    if from_cache:
        header += " (from cache)"
    header += "_\n\n---\n\n"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(header + report)
    return filepath


def run(concept: str):
    try:
        import sys as _sys, os as _os
        _sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), '..', 'shared'))
        from usage_logger import log_run
        log_run("content-researcher")
    except Exception:
        pass
    print(f"\n{'='*60}")
    print(f"  Content Researcher")
    print(f"{'='*60}")
    print(f"  Concept: {concept}\n")

    # Check cache first — skip entire agent run if hit
    cached = get_cached(concept)
    if cached:
        print("  Using cached result (< 7 days old). Skipping API calls.\n")
        report = cached
        from_cache = True
    else:
        from_cache = False
        report = run_agent(concept)
        if report.startswith("ERROR"):
            print(f"\n{report}")
            sys.exit(1)

    # Write HTML report and open in browser
    print("\nGenerating HTML report...")
    html_path = write_html_report(concept, report)
    import webbrowser
    webbrowser.open(f'file://{html_path}')

    # Also save .md backup
    filepath = _save_report(concept, report, from_cache)

    print(f"\n{'='*60}")
    print(f"  Report opened in browser")
    print(f"  HTML: {html_path}")
    print(f"  Markdown backup: {filepath}")
    print(f"{'='*60}\n")

    # Print report to terminal
    print(report)


def main():
    if len(sys.argv) > 1:
        concept = ' '.join(sys.argv[1:]).strip()
    else:
        print("=" * 60)
        print("    Content Researcher — Outlier Video Analysis")
        print("=" * 60)
        concept = input("\nVideo concept: ").strip()
        if not concept:
            print("No concept provided. Exiting.")
            sys.exit(1)

    run(concept)


if __name__ == '__main__':
    main()
