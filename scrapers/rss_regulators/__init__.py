"""
scrapers/rss_regulators/ — regulator RSS scrapers (BaseRegulatorRSS subclasses).

Auto-discovered by pipeline/run_all.py::discover_scrapers() like every
other region subpackage. Each module here defines a subclass of
BaseRegulatorRSS (scrapers/_rss_base.py) — pure RSS/XML parsing, no AI
call needed. Dropping a new file here with an AGENCY/COUNTRY/FEED_URL set
is enough to register a new source; no other change is required.

STATUS (audit 2026-07-30): these 8 scrapers previously sat at the root of
scrapers/ and were never discovered by anything (discover_scrapers() only
walked a hardcoded region-package list that didn't include this
directory). Moved here and wired into discover_scrapers() on 2026-07-30 —
see ARCHITECTURE.md for the full history.
"""
