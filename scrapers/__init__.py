"""
scrapers/ package init.

STATUS (audit 2026-07-30): this file's docstring used to describe an
intended "scrapers/rss_regulators/" auto-discovered subpackage. That
subpackage was never created. The 8 BaseRegulatorRSS-based scrapers
(usda_fsis_rss.py, bvl_rss.py, efsa_rss.py, fodevarestyrelsen_rss.py,
fsai_rss.py, fsanz_rss.py, fss_scotland_rss.py, livsmedelsverket_rss.py)
sit directly at the root of scrapers/ instead, and pipeline/run_all.py's
discover_scrapers() only walks a hardcoded region-package list
(north_america, europe_eu, europe_non_eu, eu_wide, asia, oceania,
africa, latam, middle_east) — it does not scan scrapers/ root and has no
"rss_regulators" entry. Confirmed by grepping every filename above
against .github/workflows/ and pipeline/: zero matches. These 8 scrapers
are fully implemented (see scrapers/_rss_base.py — no AI/API key
required, pure RSS/XML parsing) but are currently never executed by any
workflow. Wiring them in means either moving them into a real
scrapers/rss_regulators/ subpackage and adding it to discover_scrapers()'s
pkgs list, or adding a dedicated workflow — a deliberate decision, not
done here since it would add 8 new live network calls to the production
pipeline without the ability to verify the feeds still resolve.
"""
