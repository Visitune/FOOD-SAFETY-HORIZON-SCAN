"""
Offline regression tests for scrapers.europe_non_eu.fsa_uk.

WHY THIS FILE EXISTS (audit 2026-07-30)
========================================
FSA UK's own audit history documents a real production miss (only 7 of
the first 20 PRINs of 2026 captured — 35%), which is why the scraper now
carries per-row diagnostic logging (DROP-DATE / DROP-NO-URL /
DROP-NO-PATHOGEN / DROP-PARSE). None of that filtering logic had test
coverage. This file covers scrape() end-to-end against a mocked JSON feed
— no network access, no API key required.

Run:  python -m pytest tests/test_fsa_uk_scraper.py -v
"""
from __future__ import annotations
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scrapers.europe_non_eu.fsa_uk import FSAUKScraper  # noqa: E402


class _MockResponse:
    """See tests/test_usda_fsis_scraper.py for why status_code must be
    present on this stand-in (its absence hid a 3-month test blackout)."""

    def __init__(self, payload=None, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code
        self.text = ""

    def json(self):
        return self._payload


def _recent_iso(days_ago: int = 1) -> str:
    return (datetime.utcnow() - timedelta(days=days_ago)).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


class TestFsaUkScrapeEndToEnd(unittest.TestCase):
    """scrape() against a mocked FSA UK JSON API — no network."""

    def setUp(self):
        self.scraper = FSAUKScraper()

    def _base_item(self, **overrides):
        item = {
            "@id": "https://data.food.gov.uk/food-alerts/id/fsa-prin-20-2026",
            "title": "Acme Dairy recalls soft cheese because of Listeria monocytogenes",
            "description": "Acme Dairy is recalling its soft cheese due to "
                           "possible contamination with Listeria monocytogenes.",
            "created": _recent_iso(1),
            "business": {"name": "Acme Dairy"},
            "alertType": {"notation": "FAFA"},
            "notation": "FSA-PRIN-20-2026",
        }
        item.update(overrides)
        return item

    def _run(self, items, since_days=30):
        payload = {"items": items}
        with patch("scrapers.europe_non_eu.fsa_uk.fetch",
                   return_value=_MockResponse(payload)):
            return self.scraper.scrape(since_days=since_days)

    def test_valid_alert_produces_a_row(self):
        """Pathogen goes through _new_recall's normalize_pathogen(), so the
        raw matched keyword ("listeria") comes out canonicalised."""
        out = self._run([self._base_item()])
        self.assertEqual(len(out), 1)
        self.assertIn("Listeria", out[0].Pathogen)
        self.assertEqual(out[0].Company, "Acme Dairy")
        self.assertIn("fsa-prin-20-2026", out[0].URL)

    def test_missing_created_field_dropped(self):
        out = self._run([self._base_item(created="")])
        self.assertEqual(out, [])

    def test_stale_alert_dropped(self):
        out = self._run([self._base_item(
            created=_recent_iso(90))], since_days=30)
        self.assertEqual(out, [])

    def test_no_pathogen_keyword_dropped(self):
        out = self._run([self._base_item(
            title="Acme Dairy recalls soft cheese due to incorrect labelling",
            description="Missing allergen information on the label.")])
        self.assertEqual(out, [])

    def test_missing_url_dropped(self):
        out = self._run([self._base_item(**{"@id": ""})])
        self.assertEqual(out, [])

    def test_outbreak_detected_from_summary(self):
        out = self._run([self._base_item(
            description="Linked to an ongoing illness outbreak investigation "
                        "involving Listeria monocytogenes.")])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].Outbreak, 1)

    def test_no_outbreak_by_default(self):
        out = self._run([self._base_item()])
        self.assertEqual(out[0].Outbreak, 0)

    def test_company_falls_back_to_title_when_business_missing(self):
        out = self._run([self._base_item(business={})])
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0].Company)

    def test_api_failure_returns_empty_not_crash(self):
        with patch("scrapers.europe_non_eu.fsa_uk.fetch", return_value=None):
            out = self.scraper.scrape(since_days=30)
        self.assertEqual(out, [])

    def test_non_200_status_returns_empty(self):
        with patch("scrapers.europe_non_eu.fsa_uk.fetch",
                   return_value=_MockResponse({"items": []}, status_code=500)):
            out = self.scraper.scrape(since_days=30)
        self.assertEqual(out, [])

    def test_multiple_alerts_mixed_outcomes(self):
        items = [
            self._base_item(),  # kept
            self._base_item(created=""),  # dropped: no date
            self._base_item(title="Mislabelled allergen alert",
                            description="Undeclared milk allergen."),  # dropped: no pathogen
        ]
        out = self._run(items)
        self.assertEqual(len(out), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
