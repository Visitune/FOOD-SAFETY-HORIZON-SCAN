"""
Offline regression tests for scrapers.eu_wide.rasff.

WHY THIS FILE EXISTS (audit 2026-07-30)
========================================
RASFF is described in the project's own evaluation notes as the most mature,
highest-volume scraper (417 of 1280 production rows come from it), yet it had
zero test coverage before this file — the same blind spot that let the FSIS
scraper silently zero out for three months (see tests/test_usda_fsis_scraper.py
and tests/README.md). This file covers the pure parsing helpers and the
end-to-end scrape() path with a mocked HTTP layer — no network access, no API
key required.

Run:  python -m pytest tests/test_rasff_scraper.py -v
"""
from __future__ import annotations
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scrapers.eu_wide.rasff import (  # noqa: E402
    RASFFScraper,
    _parse_rasff_date,
    _correct_rasff_typos,
    _extract_pathogen,
    _country_names,
    _classify,
    _build_company_field,
    _reason_text,
)


class _MockResponse:
    """Stand-in for requests.Response — see tests/test_usda_fsis_scraper.py
    for why status_code must be present (AttributeError killed that whole
    module silently for months when it was missing)."""

    def __init__(self, payload, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code
        self.text = ""

    def json(self):
        return self._payload


def _recent(days_ago: int = 1) -> str:
    """RASFF date format: 'DD-MM-YYYY HH:MM:SS'."""
    d = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return d.strftime("%d-%m-%Y %H:%M:%S")


class TestParseRasffDate(unittest.TestCase):
    def test_full_datetime(self):
        d = _parse_rasff_date("01-05-2026 22:54:51")
        self.assertEqual((d.year, d.month, d.day, d.hour), (2026, 5, 1, 22))

    def test_date_only_fallback(self):
        d = _parse_rasff_date("01-05-2026")
        self.assertEqual((d.year, d.month, d.day), (2026, 5, 1))

    def test_garbage_returns_none(self):
        self.assertIsNone(_parse_rasff_date("not-a-date"))

    def test_empty_returns_none(self):
        self.assertIsNone(_parse_rasff_date(""))


class TestRasffTypoFixes(unittest.TestCase):
    """The two documented production typos (audit 2026-05-04)."""

    def test_cerulide_missing_e(self):
        self.assertEqual(
            _correct_rasff_typos("Cerulide in infant formula"),
            "cereulide in infant formula")

    def test_aflotoxin_o_for_a(self):
        self.assertEqual(
            _correct_rasff_typos("Aflotoxins in hazelnuts"),
            "aflatoxin in hazelnuts")

    def test_already_correct_gets_lowercased_by_belt_and_braces_rule(self):
        """The second typo-fix pattern (`cereuli?de`) is a belt-and-braces
        catch-all that matches case-insensitively but replaces with a
        lowercase literal — so even correctly-spelled input gets
        lowercased. This pins that (real, current) behaviour rather than
        assuming case-preservation that the code doesn't implement."""
        self.assertEqual(
            _correct_rasff_typos("Cereulide in infant formula"),
            "cereulide in infant formula")


class TestExtractPathogen(unittest.TestCase):
    def test_known_pathogen_in_subject(self):
        self.assertTrue(_extract_pathogen(
            "Listeria monocytogenes in soft cheese from France"))

    def test_no_pathogen_in_subject(self):
        self.assertEqual(_extract_pathogen("Undeclared allergen (gluten) in bread"), "")

    def test_empty_subject(self):
        self.assertEqual(_extract_pathogen(""), "")


class TestCountryNames(unittest.TestCase):
    def test_list_of_dicts(self):
        self.assertEqual(
            _country_names([{"organizationName": "France"},
                             {"organizationName": "Belgium"}]),
            "France, Belgium")

    def test_single_dict(self):
        self.assertEqual(_country_names({"organizationName": "Ireland"}), "Ireland")

    def test_empty_input(self):
        self.assertEqual(_country_names([]), "")
        self.assertEqual(_country_names(None), "")


class TestClassify(unittest.TestCase):
    def test_alert(self):
        self.assertEqual(_classify("alert notification"), "Alert")

    def test_border_rejection(self):
        self.assertEqual(_classify("border rejection notification"), "Border Rejection")

    def test_information(self):
        self.assertEqual(_classify("information notification for attention"), "Information")

    def test_unknown_defaults_to_recall(self):
        self.assertEqual(_classify("something else"), "Recall")


class TestBuildCompanyField(unittest.TestCase):
    def test_both_present(self):
        self.assertEqual(
            _build_company_field("Ireland", "Ireland"),
            "Origin: Ireland | Notifying: Ireland")

    def test_missing_origin_says_unknown(self):
        self.assertEqual(
            _build_company_field("", "France"),
            "Origin: unknown | Notifying: France")


class TestReasonText(unittest.TestCase):
    def test_avoids_duplicate_info(self):
        text = _reason_text("Listeria in cheese", "alert notification",
                             "serious", "milk and milk products")
        self.assertIn("Listeria in cheese", text)
        self.assertIn("risk: serious", text)
        self.assertIn("category: milk and milk products", text)

    def test_respects_length_cap(self):
        long_subject = "x" * 1000
        text = _reason_text(long_subject, "alert", "serious", "category")
        self.assertLessEqual(len(text), 500)


class TestRasffScrapeEndToEnd(unittest.TestCase):
    """scrape() against a mocked API response — no network."""

    def setUp(self):
        self.scraper = RASFFScraper()

    def _run(self, notifications, since_days=7):
        payload = {"totalPages": 1, "totalElements": len(notifications),
                   "notifications": notifications}
        with patch("scrapers.eu_wide.rasff.fetch",
                   return_value=_MockResponse(payload)):
            return self.scraper.scrape(since_days=since_days)

    def _base_notif(self, **overrides):
        n = {
            "notifId": 841474,
            "reference": "2026.3863",
            "ecValidationDate": _recent(1),
            "subject": "Listeria monocytogenes in soft cheese from France",
            "notifyingCountry": {"organizationName": "France", "isoCode": "FR"},
            "originCountries": [{"organizationName": "France"}],
            "productCategory": {"description": "milk and milk products"},
            "productType": {"description": "food"},
            "notificationClassification": {"description": "alert notification"},
            "riskDecision": {"description": "serious"},
            "published": False,
        }
        n.update(overrides)
        return n

    def test_valid_notification_produces_a_row(self):
        out = self._run([self._base_notif()])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].Pathogen, "Listeria monocytogenes")
        self.assertIn("webgate.ec.europa.eu/rasff-window/screen/notification/841474",
                       out[0].URL)

    def test_non_food_type_dropped(self):
        out = self._run([self._base_notif(
            productType={"description": "feed"})])
        self.assertEqual(out, [])

    def test_unmonitored_classification_dropped(self):
        out = self._run([self._base_notif(
            notificationClassification={"description": "news"})])
        self.assertEqual(out, [])

    def test_no_pathogen_in_subject_dropped(self):
        out = self._run([self._base_notif(
            subject="Undeclared allergen (peanut) in chocolate bar")])
        self.assertEqual(out, [])

    def test_duplicate_reference_deduped(self):
        out = self._run([self._base_notif(), self._base_notif()])
        self.assertEqual(len(out), 1)

    def test_row_older_than_cutoff_dropped(self):
        stale = self._base_notif(
            reference="2026.0001",
            ecValidationDate=(datetime.now(timezone.utc) - timedelta(days=30))
            .strftime("%d-%m-%Y %H:%M:%S"))
        out = self._run([stale], since_days=7)
        self.assertEqual(out, [])

    def test_empty_page_returns_no_rows(self):
        out = self._run([])
        self.assertEqual(out, [])

    def test_api_failure_returns_empty_not_crash(self):
        with patch("scrapers.eu_wide.rasff.fetch", return_value=None):
            out = self.scraper.scrape(since_days=7)
        self.assertEqual(out, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
