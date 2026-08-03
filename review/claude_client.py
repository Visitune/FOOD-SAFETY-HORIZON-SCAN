"""
review/claude_client.py — inert stub (2026-08-03: Anthropic removed).

This project no longer calls the Anthropic API — there is no
ANTHROPIC_API_KEY and none will be configured. The three public
functions below (`review_tier1`, `review_batch`, `extract_recalls_from_html`)
always return an empty result, and `_call_claude` always returns None.

Kept as a module (rather than deleted) because several other reviewers
reuse its prompt constants and monkey-patch pattern instead of duplicating
them: pipeline/claude_check.py (patched by pipeline/gemini_check.py to run
entirely on Gemini — see that module's docstring), review/openrouter_client.py,
review/gemini_reviewer.py, pipeline/url_guardian.py, and the FSIS-LM
reviewer (.github/workflows/fsis-lm-reviewer.yml). None of those call
_call_claude — they only import the REVIEW_PROMPT / REVIEW_BATCH_SYSTEM /
EXTRACTION_SYSTEM / EXTRACTION_PROMPT text below, or patch a different
function onto pipeline.claude_check at runtime.
"""
from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional

log = logging.getLogger(__name__)

ENABLED = False  # permanently off — this project does not use Claude/Anthropic


def last_call_error() -> Optional[str]:
    """Always None — no Anthropic calls are ever made."""
    return None


def _call_claude(prompt: str, max_tokens: int = 4000,
                 system: Optional[str] = None,
                 cache_system: bool = True) -> Optional[str]:
    """Inert — Anthropic is not used in this project. Always returns None."""
    return None


def _strip_fences(txt: str) -> str:
    """Remove ```json / ``` wrappers, kept for callers that reuse this helper
    on text from other providers (Gemini/OpenRouter/etc.)."""
    txt = txt.strip()
    if txt.startswith("```"):
        txt = txt.split("\n", 1)[-1] if "\n" in txt else txt[3:]
        if "```" in txt:
            txt = txt.rsplit("```", 1)[0]
    return txt.strip()


# ===========================================================================
# Prompt constants — reused by other (non-Claude) reviewers, see module
# docstring. Kept verbatim so those callers' behavior doesn't change.
# ===========================================================================
REVIEW_PROMPT = """Review these Tier-1 critical food recalls (Listeria/STEC/Botulinum/cereulide/biotoxins).

For each row, verify:
1. Pathogen classification is correct (Tier-1 vs Tier-2)
2. Outbreak flag accuracy (illness/cases reported = 1, single detection = 0)
3. URL points to a specific recall page, not a homepage/category
4. Critical info present: Company, Product, lot/batch identifier in Notes

Return strict JSON:
{"flags": [{"row_index": <int>, "severity": "high|medium|low", "issue": "...", "suggested_fix": {...}}]}
Only flag rows with real issues. Empty array if all clean.

Rows to review:
"""


def review_tier1(rows: List[Dict[str, Any]], batch_size: int = 15) -> List[Dict[str, Any]]:
    """Inert — always returns []. Kept for call-site compatibility."""
    return []


REVIEW_BATCH_SYSTEM = """You are a senior food safety analyst reviewing recall records for accuracy.
For each record, flag issues:
  - URL_INVALID: URL is a homepage, category page, or generic landing (not a specific recall)
  - URL_MISMATCH: URL likely doesn't match the described recall
  - MISSING_FIELD: required field empty (Date, Company, Product, Pathogen, URL)
  - PATHOGEN_INCONSISTENT: Pathogen value is contradicted by Reason text — e.g. Pathogen="Listeria monocytogenes" but Reason describes a Salmonella outbreak. Distinct from HALLUCINATED_PATHOGEN below: this flags ROWS WITH CONFLICTING evidence; HALLUCINATED flags rows with NO evidence.
  - DATE_FORMAT: date not in YYYY-MM-DD or seems wrong
  - COUNTRY_INCONSISTENT: Country doesn't match Source agency
  - DUPLICATE_RISK: looks like a duplicate of another recent recall
  - HALLUCINATED_PATHOGEN: Pathogen field is non-empty but neither the value NOR any source-language equivalent appears in the Reason or Notes fields (case-insensitive substring match). Source-language equivalents you must recognize:
      "Salmonella" ↔ "salmonella" / "salmonellen" (DE) / "salmonelle" (FR) / "salmonelas" (PT) / "salmonelosis" (ES)
      "Listeria monocytogenes" ↔ "listeria" / "listerien" (DE) / "listéria" (FR) / "l. monocytogenes"
      "Shiga toxin-producing E. coli (STEC)" ↔ "stec" / "vtec" / "ehec" / "shiga" / "shigatoxin" / "e. coli o157" / "escherichia coli"
      "Ochratoxin" ↔ "ochratoxin" / "ochratoxine" (FR) / "ocratoxina" (IT/ES)
      "Aflatoxin" ↔ "aflatoxin" / "aflatoxine" (FR/DE) / "aflatossina" (IT)
      "Clostridium botulinum" ↔ "botulinum" / "botulism" / "botulisme" (FR) / "botulismus" (DE)
      "Undeclared meat" ↔ "fleisch" (DE) / "viande" (FR) / "carne" (IT/ES) / "meat"
      "Undeclared allergen" ↔ "allergen" / "allergie" / "allergène" / "allergeen"
      "Foreign body" ↔ "fremdkörper" (DE) / "corps étranger" (FR) / "corpo estraneo" (IT) / "metal" / "plastic" / "glass"
      "Mislabeling" ↔ "falschdeklaration" (DE) / "étiquetage erroné" (FR) / "mislabel" / "mislabelled"
    Skip this check (do NOT flag) if Reason+Notes combined is shorter than 20 characters — absence of detail is not evidence of hallucination. This catches Gemini fabricating a pathogen unsupported by any other text in the row (e.g. Pathogen="Ochratoxin" while Reason describes undeclared meat).
  - EXTRACTION_GARBAGE: any of (a) Company == Brand byte-for-byte AND Company contains >5 whitespace-separated words; (b) Product is just a bare domain like "canada.ca", "fda.gov", "fsis.usda.gov"; (c) any of Company / Brand / Product contains an HTML or JS artifact: "{socials", "window.", "querySelector", "&nbsp;", "<title>", "</title>", "[data-progress-bar]", "(function", "document.cookie", "addEventListener".

Return strictly as JSON: {"reviews": [{"row_index": <int>, "issues": ["CODE",...], "suggested_fixes": {"FieldName": "value"}, "confidence": 0.0-1.0}]}
Only include rows with issues. Empty array if all clean."""


def review_batch(rows: List[Dict[str, Any]], batch_size: int = 20) -> List[Dict[str, Any]]:
    """Inert — always returns []. Kept for call-site compatibility."""
    return []


EXTRACTION_SYSTEM = (
    "You are a senior food safety analyst extracting structured recall data from "
    "regulator HTML. Return ONLY strict JSON — no markdown, no prose, no commentary."
)

EXTRACTION_PROMPT = """Source: {agency} ({country})
Language: {language}
Page URL: {source_url}
{extra_hints}

Extract food recalls/alerts where the cause is ANY of the following hazard categories:
  (a) PATHOGENS, MICROBIAL CONTAMINATION, or BIOLOGICAL TOXINS
  (b) RODENTICIDES / RAT POISON (bromadiolone, brodifacoum, difethialone,
      difenacoum, chlorophacinone — including deliberate tampering)
  (c) HEAVY METAL contamination (lead, cadmium, arsenic, mercury) at levels
      exceeding regulatory limits
  (d) PHYSICAL HAZARDS (glass fragments, metal fragments, plastic fragments,
      foreign bodies posing injury or choking risk)
  (e) MYCOTOXINS at levels exceeding regulatory limits or indicative
      values, including aflatoxins (B1/B2/G1/G2/M1), ochratoxin A, patulin,
      Alternaria toxins (alternariol/AOH/AME, tenuazonic acid), Fusarium
      toxins (fumonisin, zearalenone, deoxynivalenol/DON, nivalenol, T-2,
      HT-2), citrinin, ergot alkaloids (Claviceps)

EXCLUDE: undeclared allergens, labeling errors, mechanical/packaging issues,
and pesticide residues above MRL — unless linked to one of (a)-(e).

Canonical hazard names (use these exact strings in the Pathogen field):
  Biological — Listeria monocytogenes, Salmonella spp., E. coli O157:H7,
    STEC, Clostridium botulinum, Norovirus, Hepatitis A, Campylobacter,
    Cyclospora, Vibrio, Cronobacter sakazakii, Bacillus cereus / cereulide,
    marine biotoxins (DSP/PSP/ASP), Histamine (scombrotoxin), Shigella,
    Yersinia.
  Mycotoxins — "Aflatoxins", "Ochratoxin A", "Patulin", "Alternaria toxins",
    "Fumonisin", "Zearalenone", "Deoxynivalenol (DON)", "T-2 / HT-2 toxin",
    "Citrinin", "Ergot alkaloids", or the generic "Mycotoxin" if the specific
    toxin is not named.
  Rodenticides — "Rodenticide (rat poison)" (preferred), optionally suffixed
    with the active ingredient e.g. "Rodenticide (bromadiolone)".
  Heavy metals — "Lead (Pb) contamination", "Cadmium (Cd) contamination",
    "Arsenic (As) contamination", "Mercury (Hg) contamination", or the
    generic "Heavy metal contamination".
  Physical — "Glass fragments", "Metal fragments", "Plastic fragments",
    "Physical/foreign-body contamination".

For criminal tampering cases (e.g. rat poison deliberately added to a jar):
  - Prefix Reason with "Tampering: …"
  - Set Outbreak=1 if vulnerable consumers (infants, elderly, immuno-
    compromised) are the likely target OR illnesses are already reported.

For each recall, return:
- Date (YYYY-MM-DD; recall publication or initiation date)
- Company (firm/producer name)
- Brand (commercial brand name; "—" if not stated)
- Product (full product description with size/lot if available)
- Pathogen (canonical hazard name from the lists above)
- Reason (short cause description)
- Class (recall class: "Recall", "Alert", "Class I/II/III", "Public Health Alert", etc.)
- URL (full deep-link to the specific recall page — NOT a homepage or category page)
- Outbreak (1 if illness/outbreak mentioned OR tampering targeting vulnerable consumers, else 0)
- Notes (distribution region, batch info, additional context)

CRITICAL: URL must be a specific recall page (e.g. .../fiche-rappel/12345).
NEVER return homepage URLs, category pages, or generic listing URLs.

Only include recalls published in the last {since_days} days when dates are visible.

Return exactly this JSON shape:
{{"recalls": [{{"Date":"...","Company":"...","Brand":"...","Product":"...","Pathogen":"...","Reason":"...","Class":"...","URL":"...","Outbreak":0,"Notes":"..."}}]}}

If no in-scope hazard recalls are present, return: {{"recalls": []}}

HTML to analyze (truncated):
---
{html}
---"""


def extract_recalls_from_html(
    html: str,
    source_url: str,
    agency: str,
    country: str,
    language: str = "en",
    extra_hints: str = "",
    since_days: int = 30,
    max_tokens: int = 4000,
) -> List[Dict[str, Any]]:
    """Inert — always returns []. Kept for call-site compatibility."""
    return []
