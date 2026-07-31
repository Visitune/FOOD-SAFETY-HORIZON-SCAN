"""
update_nav_weekly_link.py
==========================
Keeps every page's "Weekly" nav link pointing at the current latest
weekly report. The nav bar (added 2026-07-31 to docs/index.html,
docs/guide.html, docs/hub.html, and every generated weekly/monthly
report page) hardcodes the latest week's filename at the time it was
written — without this script that link goes stale the moment a new
week is published.

Reads docs/data/weekly-index.json (already newest-first) for the
current filename, then rewrites the "Weekly" nav <a href="..."> on every
docs/*.html page EXCEPT the weekly report pages themselves — each
weekly report's own "Weekly" link intentionally points to itself
(dated archive, not a moving target).

Usage:
    python pipeline/update_nav_weekly_link.py

Run as the last step of .github/workflows/afts-weekly-report.yml, after
the new week's HTML has been generated and committed.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
WEEKLY_INDEX = DOCS / "data" / "weekly-index.json"

# Matches the "Weekly" nav link regardless of which icon representation
# was used (literal emoji in docs/index.html / docs/guide.html, HTML
# entity in docs/hub.html / the report generators), and regardless of
# whether it currently carries class="on".
WEEKLY_LINK_RE = re.compile(
    r'(<a href=")[^"]*("(?:\s+class="on")?>\s*(?:\U0001F4CA|&#128202;)\s*Weekly</a>)'
)

# Weekly report pages keep their own self-referencing link — skip them.
SELF_REFERENCING = re.compile(r"^2026-?W\d{2}\.html$")


def latest_weekly_filename() -> str:
    data = json.loads(WEEKLY_INDEX.read_text(encoding="utf-8"))
    return data[0]["filename"]


def update_file(path: Path, latest: str) -> bool:
    text = path.read_text(encoding="utf-8")
    new_text = WEEKLY_LINK_RE.sub(rf"\g<1>{latest}\g<2>", text)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def main() -> None:
    latest = latest_weekly_filename()
    updated = 0
    for path in sorted(DOCS.glob("*.html")):
        if SELF_REFERENCING.match(path.name):
            continue
        if update_file(path, latest):
            updated += 1
            print(f"updated: {path.name} -> Weekly link now {latest}")
    print(f"\n{updated} files updated to point Weekly at {latest}")


if __name__ == "__main__":
    main()
