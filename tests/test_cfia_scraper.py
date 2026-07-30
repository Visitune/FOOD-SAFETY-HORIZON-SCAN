"""
Offline regression tests for scrapers.north_america.cfia.

WHY THIS FILE EXISTS (audit 2026-07-30)
========================================
CFIA is one of the highest-volume dedicated (non-LLM) scrapers and has the
most elaborate fallback chain in the repo (open-data JSON -> RSS -> HTML
listing) after RappelConso, with a documented incident (zero rows captured
2026-04-28 to 2026-05-07 because every RSS URL guess was a 404). None of
that logic had test coverage. This file covers the pure helpers and the
three-layer scrape() fallback with a mocked HTTP layer — no network access,
no API key required.

Run:  python -m pytest tests/test_cfia_scraper.py -v
"""
from __future__ import annotations
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scrapers.north_america.cfia import (  # noqa: E402
    CFIAScraper,
    _is_generic_url,
    _parse_pubdate,
    _is_pathogen_issue,
    _detect_outbreak,
    _split_company_brand_from_title,
)


class _MockResponse:
    """See tests/test_usda_fsis_scraper.py for why status_code must be
    present on this stand-in (its absence hid a 3-month test blackout)."""

    def __init__(self, payload=None, status_code: int = 200, content: bytes = b""):
        self._payload = payload
        self.status_code = status_code
        self.content = content
        self.text = content.decode("utf-8", "ignore") if content else ""

    def json(self):
        return self._payload


def _recent(days_ago: int = 1) -> str:
    return (datetime.utcnow() - timedelta(days=days_ago)).strftime("%Y-%m-%d")


class TestIsGenericUrl(unittest.TestCase):
    def test_bare_landing_page_is_generic(self):
        self.assertTrue(_is_generic_url("https://recalls-rappels.canada.ca/en"))

    def test_search_url_is_generic(self):
        self.assertTrue(_is_generic_url(
            "https://recalls-rappels.canada.ca/en/search/site?q=x"))

    def test_real_recall_url_not_generic(self):
        self.assertFalse(_is_generic_url(
            "https://recalls-rappels.canada.ca/en/alert-recall/some-cheese-2026"))

    def test_empty_url_is_generic(self):
        self.assertTrue(_is_generic_url(""))


class TestParsePubdate(unittest.TestCase):
    def test_rfc822_with_offset(self):
        d = _parse_pubdate("Mon, 05 May 2026 12:00:00 +0000")
        self.assertEqual((d.year, d.month, d.day), (2026, 5, 5))

    def test_rfc822_gmt_literal(self):
        d = _parse_pubdate("Mon, 05 May 2026 12:00:00 GMT")
        self.assertEqual((d.year, d.month, d.day), (2026, 5, 5))

    def test_iso8601_with_z(self):
        d = _parse_pubdate("2026-05-05T12:00:00Z")
        self.assertEqual((d.year, d.month, d.day), (2026, 5, 5))

    def test_date_only(self):
        d = _parse_pubdate("2026-05-05")
        self.assertEqual((d.year, d.month, d.day), (2026, 5, 5))

    def test_garbage_returns_none(self):
        self.assertIsNone(_parse_pubdate("not a date"))

    def test_empty_returns_none(self):
        self.assertIsNone(_parse_pubdate(""))


class TestIsPathogenIssue(unittest.TestCase):
    def test_listeria_is_pathogen(self):
        self.assertTrue(_is_pathogen_issue("Listeria"))

    def test_generic_microbiological_is_pathogen(self):
        self.assertTrue(_is_pathogen_issue("Microbiological"))

    def test_allergen_is_not_pathogen(self):
        self.assertFalse(_is_pathogen_issue("Allergen - Milk"))

    def test_extraneous_material_is_not_pathogen(self):
        self.assertFalse(_is_pathogen_issue("Extraneous Material"))

    def test_quality_spoilage_is_not_pathogen(self):
        self.assertFalse(_is_pathogen_issue("Non harmful (quality or spoilage)"))

    def test_empty_is_not_pathogen(self):
        self.assertFalse(_is_pathogen_issue(""))


class TestDetectOutbreak(unittest.TestCase):
    def test_english_outbreak_token(self):
        self.assertEqual(_detect_outbreak("linked to illness in several provinces"), 1)

    def test_french_outbreak_token(self):
        self.assertEqual(_detect_outbreak("éclosion signalée au québec"), 1)

    def test_no_outbreak_token(self):
        self.assertEqual(_detect_outbreak("recalled due to listeria contamination"), 0)


class TestSplitCompanyBrandFromTitle(unittest.TestCase):
    def test_brand_template(self):
        co, br = _split_company_brand_from_title(
            "Auricchio brand Taleggio D.O.P. Cheese recalled due to Listeria")
        self.assertEqual(br, "Auricchio")

    def test_various_brands_template(self):
        co, br = _split_company_brand_from_title(
            "Various brands of cheese products recalled due to Listeria")
        self.assertEqual(br, "Various")

    def test_company_recalls_template(self):
        co, br = _split_company_brand_from_title(
            "Fresh Start Foods recalls salads due to Listeria")
        self.assertEqual(co, "Fresh Start Foods")

    def test_no_recognisable_template(self):
        co, br = _split_company_brand_from_title("Pistachio Kernel recalled due to Salmonella")
        self.assertEqual((co, br), ("", "—"))

    def test_empty_title(self):
        self.assertEqual(_split_company_brand_from_title(""), ("", "—"))


class TestCfiaScrapeEndToEnd(unittest.TestCase):
    """scrape() against a mocked open-data JSON / RSS — no network."""

    def setUp(self):
        self.scraper = CFIAScraper()

    def _open_data_row(self, **overrides):
        row = {
            "NID": "12345",
            "Title": "Auricchio brand Taleggio D.O.P. Cheese recalled due to Listeria",
            "URL": "https://recalls-rappels.canada.ca/en/alert-recall/auricchio-taleggio",
            "Organization": "CFIA",
            "Product": "Taleggio D.O.P. Cheese",
            "Issue": "Listeria",
            "Category": "Dairy",
            "Recall class": "Class 1",
            "Last updated": _recent(1),
            "Archived": "0",
        }
        row.update(overrides)
        return row

    def _run_l1(self, rows, since_days=30):
        with patch("scrapers.north_america.cfia.fetch",
                   return_value=_MockResponse(rows)):
            return self.scraper.scrape(since_days=since_days)

    def test_valid_row_produces_a_recall(self):
        out = self._run_l1([self._open_data_row()])
        self.assertEqual(len(out), 1)
        self.assertIn("Listeria", out[0].Pathogen)
        self.assertEqual(out[0].Country, "Canada")

    def test_non_cfia_organization_dropped(self):
        out = self._run_l1([self._open_data_row(
            Organization="Consumer product safety")])
        self.assertEqual(out, [])

    def test_archived_recall_dropped(self):
        out = self._run_l1([self._open_data_row(Archived="1")])
        self.assertEqual(out, [])

    def test_allergen_issue_dropped(self):
        out = self._run_l1([self._open_data_row(Issue="Allergen - Peanut")])
        self.assertEqual(out, [])

    def test_stale_row_dropped(self):
        out = self._run_l1([self._open_data_row(
            **{"Last updated": (datetime.utcnow() - timedelta(days=90))
               .strftime("%Y-%m-%d")})], since_days=30)
        self.assertEqual(out, [])

    def test_generic_url_dropped(self):
        out = self._run_l1([self._open_data_row(
            URL="https://recalls-rappels.canada.ca/en")])
        self.assertEqual(out, [])

    def test_l1_transport_failure_falls_through_to_l2(self):
        """None from fetch() must fall through to RSS, not be treated as
        a legit-empty result (the docstring's None vs [] distinction)."""
        rss_body = (
            b'<?xml version="1.0"?><rss><channel>'
            b'<item><title>Fresh Start Foods recalls salads due to Listeria</title>'
            b'<link>https://recalls-rappels.canada.ca/en/alert-recall/fresh-start</link>'
            b'<description>Listeria monocytogenes contamination in salads</description>'
            b'<pubDate>' + _recent(1).encode() + b'</pubDate></item>'
            b'</channel></rss>'
        )
        call_count = {"n": 0}

        def side_effect(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return None  # L1 open-data fetch fails
            return _MockResponse(content=rss_body)  # L2 RSS succeeds

        with patch("scrapers.north_america.cfia.fetch", side_effect=side_effect):
            out = self.scraper.scrape(since_days=30)
        self.assertEqual(len(out), 1)
        self.assertIn("Listeria", out[0].Pathogen)

    def test_l1_legit_empty_does_not_fall_through(self):
        """An empty-but-valid L1 JSON response ([]) must NOT trigger the
        L2/L3 fallback — only a transport/parse failure (None) should."""
        with patch("scrapers.north_america.cfia.fetch",
                   return_value=_MockResponse([])) as mock_fetch:
            out = self.scraper.scrape(since_days=30)
        self.assertEqual(out, [])
        # Only L1 was ever attempted — no fallback calls made.
        self.assertEqual(mock_fetch.call_count, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
