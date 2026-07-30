"""
Offline regression tests for scrapers.europe_eu.rappelconso.

WHY THIS FILE EXISTS (audit 2026-07-30)
========================================
RappelConso is the single largest data source in production (535 of 1280
rows), and its scraper carries the most intricate field-probing / fallback
/ French-to-English translation logic in the whole repo (see the module's
own audit history from 2026-05-06 through 2026-05-18). None of that logic
had test coverage. This file covers the pure helpers and the three-layer
scrape() fallback path with a mocked HTTP layer — no network access, no
API key required.

Run:  python -m pytest tests/test_rappelconso_scraper.py -v
"""
from __future__ import annotations
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scrapers.europe_eu.rappelconso import (  # noqa: E402
    RappelConsoScraper,
    _is_no_brand,
    _translate_reason_fr_to_en,
    _extract_firm_from_text,
)


class _MockResponse:
    """See tests/test_usda_fsis_scraper.py for why status_code must be
    present on this stand-in (its absence hid a 3-month test blackout)."""

    def __init__(self, payload, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code
        self.text = ""

    def json(self):
        return self._payload


def _recent(days_ago: int = 1) -> str:
    return (datetime.utcnow() - timedelta(days=days_ago)).strftime("%Y-%m-%d")


class TestIsNoBrand(unittest.TestCase):
    def test_empty_is_no_brand(self):
        self.assertTrue(_is_no_brand(""))
        self.assertTrue(_is_no_brand("   "))

    def test_exact_token_match(self):
        self.assertTrue(_is_no_brand("Sans marque"))
        self.assertTrue(_is_no_brand("N/A"))

    def test_prefix_with_separator_matches(self):
        """The 2026-05-18 fix: 'Sans Marque - Rayon Boucherie
        Traditionnelle' must reduce to Unbranded, not leak through."""
        self.assertTrue(_is_no_brand(
            "Sans Marque - Rayon Boucherie Traditionnelle"))

    def test_real_brand_not_flagged(self):
        self.assertFalse(_is_no_brand("Nutella"))
        self.assertFalse(_is_no_brand("Saint-Albray"))

    def test_prefix_without_separator_not_falsely_matched(self):
        """A real brand that merely starts with the same letters as a
        no-brand token must not be caught — guards the prefix rule from
        being too aggressive."""
        self.assertFalse(_is_no_brand("Sans Frontieres Gourmet"))


class TestTranslateReasonFrToEn(unittest.TestCase):
    def test_presence_de(self):
        self.assertEqual(
            _translate_reason_fr_to_en("Présence de salmonelles"),
            "Presence of Salmonella")

    def test_presence_possible_de(self):
        self.assertEqual(
            _translate_reason_fr_to_en(
                "Présence possible de listeria monocytogenes"),
            "Possible presence of Listeria monocytogenes")

    def test_contamination_par(self):
        self.assertEqual(
            _translate_reason_fr_to_en("Contamination par Escherichia coli"),
            "Contamination with E. coli")

    def test_elided_apostrophe_form(self):
        self.assertEqual(
            _translate_reason_fr_to_en("Présence d'Escherichia coli"),
            "Presence of E. coli")

    def test_unmatched_text_passed_through_unchanged(self):
        """Narrow by design — must never invent meaning for text it
        doesn't recognise."""
        text = "Défaut d'étiquetage du produit"
        self.assertEqual(_translate_reason_fr_to_en(text), text)

    def test_empty_input(self):
        self.assertEqual(_translate_reason_fr_to_en(""), "")


class TestExtractFirmFromText(unittest.TestCase):
    def test_recovers_two_word_company_name(self):
        text = "rappel des produits de la société Pierre Sajous suite à une analyse"
        self.assertEqual(_extract_firm_from_text(text), "Pierre Sajous")

    def test_no_plausible_name_returns_empty(self):
        self.assertEqual(_extract_firm_from_text("suite à une analyse de routine"), "")

    def test_empty_input(self):
        self.assertEqual(_extract_firm_from_text(""), "")

    def test_regulatory_boilerplate_not_mistaken_for_a_firm(self):
        text = "Suite à un contrôle de la DGCCRF en France"
        self.assertEqual(_extract_firm_from_text(text), "")


class TestRappelConsoScrapeEndToEnd(unittest.TestCase):
    """scrape() against a mocked API response — no network."""

    def setUp(self):
        self.scraper = RappelConsoScraper()

    def _base_record(self, **overrides):
        rec = {
            "date_de_publication": _recent(1),
            "categorie_de_produit": "Viandes",
            "marque_produit": "NUTREL",
            "modeles_ou_references": "Jambon blanc tranché 4 tranches",
            "motif_rappel": "Présence de Listeria monocytogenes",
            "risques_encourus_par_le_consommateur": "Listeria monocytogenes",
            "nature_juridique_rappel": "Rappel volontaire",
            "identifiant_unique_de_l_alerte": "22184",
            "lien_vers_la_fiche_rappel": "",
        }
        rec.update(overrides)
        return rec

    def _run_l1(self, records, since_days=30):
        payload = {"results": records}
        with patch("scrapers.europe_eu.rappelconso.fetch",
                   return_value=_MockResponse(payload)):
            return self.scraper.scrape(since_days=since_days)

    def test_valid_record_produces_a_row(self):
        out = self._run_l1([self._base_record()])
        self.assertEqual(len(out), 1)
        self.assertIn("Listeria", out[0].Pathogen)
        self.assertEqual(out[0].Country, "France")

    def test_url_built_from_fid_when_missing(self):
        out = self._run_l1([self._base_record()])
        self.assertEqual(
            out[0].URL, "https://rappel.conso.gouv.fr/fiche-rappel/22184/Interne")

    def test_non_pathogen_record_dropped(self):
        out = self._run_l1([self._base_record(
            motif_rappel="Défaut d'étiquetage",
            risques_encourus_par_le_consommateur="Non-conformité administrative")])
        self.assertEqual(out, [])

    def test_stale_record_dropped(self):
        out = self._run_l1([self._base_record(
            date_de_publication=(datetime.utcnow() - timedelta(days=90))
            .strftime("%Y-%m-%d"))], since_days=30)
        self.assertEqual(out, [])

    def test_no_brand_field_falls_back_to_unbranded(self):
        out = self._run_l1([self._base_record(marque_produit="Sans marque")])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].Brand, "Unbranded")

    def test_reason_translated_to_english(self):
        out = self._run_l1([self._base_record(
            motif_rappel="Présence de salmonelles")])
        self.assertEqual(len(out), 1)
        self.assertIn("Salmonella", out[0].Reason)

    def test_all_layers_fail_returns_empty_not_crash(self):
        with patch("scrapers.europe_eu.rappelconso.fetch", return_value=None):
            out = self.scraper.scrape(since_days=30)
        self.assertEqual(out, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
