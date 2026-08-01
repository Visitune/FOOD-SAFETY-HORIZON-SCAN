"""
update_nav_weekly_link.py

SUPERSEDED (2026-08-01): the "Weekly" nav link across the site now
points at the static docs/weekly.html archive page instead of a
specific week's filename, so it never goes stale and this script is
no longer invoked by any workflow (removed from
.github/workflows/afts-weekly-report.yml). Left in place for
reference only — do not wire it back into a workflow; it would
overwrite the intentional "weekly.html" links with a specific week's
filename again.

============================================================================
ORIGINAL PURPOSE (kept for context)
============================================================================
Kept every page's "Weekly" nav link pointing at the current latest
weekly report. The nav bar hardcoded the latest week's filename at the
time it was written — without this script that link went stale the
moment a new week was published.

Reads docs/data/weekly-index.json (already newest-first) for the
current filename, then rewrites the "Weekly" nav <a href="..."> on every
docs/*.html page EXCEPT the weekly report pages themselves.

Usage (historical):
    python pipeline/update_nav_weekly_link.py
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
