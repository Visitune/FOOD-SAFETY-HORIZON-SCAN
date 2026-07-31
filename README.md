# Food Safety Horizon Scanning

A global food safety recall aggregator: it continuously scrapes recall and
alert notices from 90+ regulatory agencies worldwide (FDA, USDA FSIS, the
EU's RASFF network, France's RappelConso, Canada's CFIA, the UK's FSA, and
many more), verifies each record against its source, and publishes a live,
filterable dashboard.

**Live site:** https://food-safety-horizon-scan.vercel.app

## Acknowledgment

This project is derived from an earlier food-safety intelligence pipeline
originally published at
**[gstoforos/Food-Safety-Intelligence-System](https://github.com/gstoforos/Food-Safety-Intelligence-System)**.
The scraper architecture, data pipeline, and report generators in this
repository build on that original work. Credit to the original author for
the foundation this project extends.

## What it does

- **~92 scrapers** across dedicated per-agency parsers (RASFF, USDA FSIS,
  CFIA, FSA UK, RappelConso, and others) and LLM-assisted generic
  extraction (Gemini, with OpenAI and Groq fallbacks) for lower-volume
  sources.
- Every record is verified before publication and carries a **source URL**
  and an **audit trail** (which pipeline stage touched it, and why),
  so anything on the dashboard can be checked against the original
  regulator notice.
- A **live dashboard** with filters by source, country, region, product
  type, pathogen, and severity tier — plus one-click breakdown panels
  (by pathogen, source, country, product type).
- **Weekly and monthly briefings** with AI-assisted analysis (Claude), and
  an **email alert** subscription for custom watch criteria.
- Bilingual (EN/FR) toggle on the main dashboard.

See [`docs/guide.html`](docs/guide.html) for the end-user guide (how to
read the dashboard, what the severity tiers mean, how data reliability
works) and [`ARCHITECTURE.md`](ARCHITECTURE.md) for the technical pipeline
(scrape → enrich → review → publish) and where API keys live.

## Data reliability

Data is real, not a demo/sample dataset — every record traces back to an
official regulator source URL. The pipeline includes an automated
verification pass and has caught and corrected its own AI-enrichment
mistakes in production (see the guard described in
[`tests/test_hazard_class_guard.py`](tests/test_hazard_class_guard.py)).
That said, this is an aggregation tool, not the regulator itself — always
follow the source link for anything safety-critical.

## Local development

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in API keys — see .env.example for what each does
pytest -v               # 364 tests, all offline (no network/API keys needed)
```

Running the scraping/enrichment pipeline locally is optional — it's
designed to run unattended via the GitHub Actions workflows in
`.github/workflows/`, using repository secrets (`Settings → Secrets and
variables → Actions`) rather than a local `.env` file. See
`ARCHITECTURE.md` for exactly which secrets each workflow needs and how
the Gemini → OpenAI → Groq fallback chain works.

## Deployment

- **Pipeline**: GitHub Actions, scheduled (scrape, gate, review, merge,
  report-build — see `.github/workflows/`).
- **Site**: static HTML/CSS/vanilla-JS under `docs/`, deployed on
  [Vercel](https://vercel.com) (`vercel.json` serves `docs/` directly, no
  build step). The main dashboard fetches `docs/data/recalls.json` at
  runtime, so the deployed site always reflects the latest pipeline run
  without needing a redeploy.

## Contributing

Issues and pull requests welcome. If you're adding a new scraper, follow
the pattern in `scrapers/<region>/` (dedicated parser) or
`scrapers/rss_regulators/` (RSS-based, no AI needed) — see
`ARCHITECTURE.md` for the discovery mechanism.
