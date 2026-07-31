"""
apply_nav_patch.py
===================
One-off patch script that adds the site-wide navigation bar to every
already-generated weekly/monthly report page. Before this patch, only
docs/index.html and docs/guide.html had a way to navigate to the other
sections of the site (docs/hub.html, docs/alerts.html were fixed
separately by hand; the weekly/monthly report GENERATORS
docs/build_weekly_report_afts.py and docs/build_monthly_report_afts.py
were fixed separately too, so this script only needs to backfill the
files those generators already produced in the past).

Usage (run locally after cloning the repo):
    python docs/apply_nav_patch.py

Idempotent: skips any file that already contains the NAV_PATCH_V1 marker.
Zero dependencies beyond Python stdlib.

Each weekly report's own "Weekly" nav link points to itself (marked
active) — these are dated archives, so navigating "Weekly" from inside
one should not silently jump to a different week. Monthly reports'
"Weekly" nav link points to the current latest week; a separate script
(pipeline/update_nav_weekly_link.py) keeps that current going forward.
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

MARKER = "<!-- NAV_PATCH_V1 -->"

LATEST_WEEKLY = "2026-W30.html"


def nav_html(weekly_href: str, weekly_active: bool, monthly_active: bool) -> str:
    return f"""{MARKER}
<div class="site-nav">
  <div class="site-brand">Food Safety <span>&middot;</span> Horizon Scanning</div>
  <div class="links">
    <a href="index.html">&#128308; Live Dashboard</a>
    <a href="{weekly_href}"{' class="on"' if weekly_active else ''}>&#128202; Weekly</a>
    <a href="hub.html"{' class="on"' if monthly_active else ''}>&#128200; Monthly + AI</a>
    <a href="alerts.html">&#128276; Alerts</a>
    <a href="guide.html">&#128216; Guide</a>
  </div>
</div>
"""


NAV_CSS = """
.site-nav{background:#fff;border-bottom:1px solid #e5e7eb;padding:12px 24px;margin:0 0 20px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;}
.site-nav .site-brand{font-family:'Inter',sans-serif;font-weight:800;font-size:15px;color:#0B1120;}
.site-nav .site-brand span{color:#F97316;}
.site-nav .links{display:flex;gap:8px;flex-wrap:wrap;font-family:'JetBrains Mono',monospace;font-size:10px;}
.site-nav .links a{color:#6b7280;text-decoration:none;padding:4px 9px;border:1px solid #e5e7eb;border-radius:3px;}
.site-nav .links a:hover,.site-nav .links a.on{color:#F97316;border-color:#F97316;}
</style>"""


def patch_weekly(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return False
    text = text.replace("</style>", NAV_CSS, 1)
    text = re.sub(
        r"<body>\s*\n\s*<header class=\"masthead\">",
        lambda m: "<body>\n" + nav_html(path.name, True, False) + "\n<header class=\"masthead\">",
        text, count=1,
    )
    path.write_text(text, encoding="utf-8")
    return True


def patch_monthly_base(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return False
    text = text.replace("</style>", NAV_CSS, 1)
    text = text.replace(
        '</head><body><div class="page">',
        '</head><body>\n' + nav_html(LATEST_WEEKLY, False, True) + '<div class="page">',
        1,
    )
    path.write_text(text, encoding="utf-8")
    return True


def patch_monthly_all(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return False
    text = text.replace("</style>", NAV_CSS, 1)
    text = text.replace(
        '</head><body><div class="wrap">',
        '</head><body>\n' + nav_html(LATEST_WEEKLY, False, True) + '<div class="wrap">',
        1,
    )
    path.write_text(text, encoding="utf-8")
    return True


def main() -> None:
    patched = skipped = 0

    weekly_files = sorted(DOCS.glob("2026-W*.html")) + sorted(DOCS.glob("2026W*.html"))
    for p in weekly_files:
        if patch_weekly(p):
            patched += 1
            print(f"patched (weekly): {p.name}")
        else:
            skipped += 1

    for p in sorted(DOCS.glob("2026-M*-all.html")):
        if patch_monthly_all(p):
            patched += 1
            print(f"patched (monthly-all): {p.name}")
        else:
            skipped += 1

    monthly_base = [p for p in sorted(DOCS.glob("2026-M*.html")) if "-all" not in p.name]
    for p in monthly_base:
        if patch_monthly_base(p):
            patched += 1
            print(f"patched (monthly): {p.name}")
        else:
            skipped += 1

    print(f"\n{patched} files patched, {skipped} already patched/skipped")


if __name__ == "__main__":
    main()
