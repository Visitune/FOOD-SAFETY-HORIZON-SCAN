"""
Food Safety Horizon Scanning Theme — shared CSS/JS/config pour tous les générateurs de rapports.
Single source of truth pour couleurs, badges pathogènes, palettes sources.
"""
from __future__ import annotations

from typing import Any

# ── Couleurs sources ( badges ) ─────────────────────────────────────────────
SRC_CSS: dict[str, str] = {
    "FDA":      "background:rgba(91,155,213,.12);color:#5b9bd5;border:1px solid rgba(91,155,213,.25);",
    "USDA":     "background:rgba(91,155,213,.12);color:#5b9bd5;border:1px solid rgba(91,155,213,.25);",
    "USDA-FSIS":"background:rgba(91,155,213,.12);color:#5b9bd5;border:1px solid rgba(91,155,213,.25);",
    "RASFF":    "background:rgba(76,175,128,.12);color:#80d4a8;border:1px solid rgba(76,175,128,.25);",
    "RASFF (EU)":"background:rgba(76,175,128,.12);color:#80d4a8;border:1px solid rgba(76,175,128,.25);",
    "EFET_GR":  "background:rgba(30,136,229,.12);color:#64b5f6;border:1px solid rgba(30,136,229,.25);",
    "AFSCA_BE": "background:rgba(255,193,7,.12);color:#ffd54f;border:1px solid rgba(255,193,7,.25);",
    "BVL_DE":   "background:rgba(244,67,54,.12);color:#ef9a9a;border:1px solid rgba(244,67,54,.25);",
    "RAPPELCONSO_FR":"background:rgba(206,147,216,.12);color:#ce93d8;border:1px solid rgba(206,147,216,.25);",
    "CFIA":     "background:rgba(255,112,67,.12);color:#ffab91;border:1px solid rgba(255,112,67,.25);",
    "FSANZ":    "background:rgba(77,182,172,.12);color:#80cbc4;border:1px solid rgba(77,182,172,.25);",
    "FSA_UK":   "background:rgba(158,158,158,.12);color:#bdbdbd;border:1px solid rgba(158,158,158,.25);",
    "FSN":      "background:rgba(255,255,255,.05);color:#777;border:1px solid #2a2a2a;",
    "NEWS":     "background:rgba(255,255,255,.05);color:#777;border:1px solid #2a2a2a;",
}

# ── Badges pathogènes (classes CSS) ────────────────────────────────────────
PBADGE: dict[str, str] = {
    "Listeria monocytogenes": "b-l", "Listeria": "b-l",
    "Salmonella": "b-s", "E. coli": "b-e", "STEC": "b-e",
    "E. coli O157": "b-e", "C. botulinum": "b-b",
    "Norovirus": "b-n", "Aflatoxin": "b-a", "Cereulide": "b-c",
    "Bacillus cereus": "b-c",
}

# ── Tier de sévérité ───────────────────────────────────────────────────────
TIER: dict[str, int] = {
    "Clostridium botulinum": 1, "C. botulinum": 1, "Botulinum": 1,
    "E. coli O157": 1, "E. coli O157:H7": 1, "STEC": 1,
    "Listeria monocytogenes": 1, "Aflatoxin B1": 1, "Aflatoxin": 1,
    "BSE": 1, "Hepatitis A": 1, "Cereulide": 1,
    "Salmonella": 2, "Listeria": 2, "Campylobacter": 2, "Vibrio": 2,
    "Norovirus": 2, "Cyclospora": 2, "Bacillus cereus": 2,
    "E. coli": 3, "Shigella": 3, "Yersinia": 3,
}

# ── Couleurs pathogènes (inline) ───────────────────────────────────────────
PATHOGEN_COLORS: dict[str, str] = {
    "listeria": "#ff8c5a",
    "salmonella": "#7ab8e8",
    "e. coli": "#f0c040",
    "stec": "#f0c040",
    "o157": "#f0c040",
    "botulinum": "#ce93d8",
    "norovirus": "#80d4a8",
    "aflatoxin": "#ffcc80",
    "mycotoxin": "#ffcc80",
    "cereulide": "#f48fb1",
    "bacillus": "#f48fb1",
    "campylobacter": "#f48fb1",
}


def esc(s: Any) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def pathogen_color(p: str) -> str:
    p_lower = (p or "").lower()
    for key, color in PATHOGEN_COLORS.items():
        if key in p_lower:
            return color
    return "#888"


def pathogen_badge_class(p: str) -> str:
    p_lower = (p or "").lower()
    if "listeria" in p_lower:
        return "b-l"
    if "salmonella" in p_lower:
        return "b-s"
    if "e. coli" in p_lower or "stec" in p_lower or "o157" in p_lower:
        return "b-e"
    if "botulinum" in p_lower or "botulism" in p_lower:
        return "b-b"
    if "norovirus" in p_lower:
        return "b-n"
    if "aflatoxin" in p_lower or "mycotoxin" in p_lower:
        return "b-a"
    if "cereulide" in p_lower or "bacillus" in p_lower:
        return "b-c"
    return "b-o"


def tier_number(p: str) -> int:
    p_lower = (p or "").strip().lower()
    for key, val in TIER.items():
        if key.lower() in p_lower:
            return val
    return 3


def source_badge_html(source: str) -> str:
    css = SRC_CSS.get(source,
                      "background:rgba(255,255,255,.05);color:#666;border:1px solid #2a2a2a;")
    label = source.replace("_GR", "").replace("_FR", "").replace("_BE", "").replace(
        "_DE", "").replace("_UK", "").replace(" (EU)", "")
    return (f'<span style="display:inline-block;padding:2px 6px;border-radius:3px;'
            f'font-size:9px;font-family:monospace;font-weight:700;{css}">{esc(label)}</span>')


def tier_badge_html(tier: int) -> str:
    if tier == 1:
        return ('<span style="background:rgba(229,57,53,.1);color:#ef5350;'
                'border:1px solid rgba(229,57,53,.25);padding:2px 6px;border-radius:3px;'
                'font-size:9px;font-family:monospace;font-weight:700;">TIER-1</span>')
    if tier == 2:
        return ('<span style="background:rgba(232,96,26,.1);color:#E8601A;'
                'border:1px solid rgba(232,96,26,.25);padding:2px 6px;border-radius:3px;'
                'font-size:9px;font-family:monospace;">TIER-2</span>')
    return ('<span style="background:rgba(212,160,23,.1);color:#d4a017;'
            'padding:2px 6px;border-radius:3px;font-size:9px;font-family:monospace;">TIER-3</span>')


# ── CSS de base (thème sombre — utilisé par dashboard, monthly, yearly) ────
FONTS_LINK = ('<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800'
              '&family=DM+Sans:wght@400;500;600'
              '&family=DM+Mono:wght@400;500;700" rel="stylesheet">')

CSS_DARK_BASE = """
*{box-sizing:border-box;margin:0;padding:0;}
body{background:#0e0e0e;color:#f0f0f0;font-family:'DM Sans',sans-serif;line-height:1.6;}
.hdr{background:#161616;border-bottom:2px solid #E8601A;padding:24px 40px;}
h1{font-family:'Syne',sans-serif;font-weight:800;}
.meta{font-family:'DM Mono',monospace;font-size:11px;color:#666;margin-top:6px;}
.wrap{max-width:960px;margin:0 auto;padding:36px 40px;}
.kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:32px;}
.kpi{background:#161616;border:1px solid #2a2a2a;border-radius:8px;padding:18px;border-top:2px solid #E8601A;}
.kpi.r{border-top-color:#ef5350;}.kpi.a{border-top-color:#d4a017;}.kpi.b{border-top-color:#5b9bd5;}
.kv{font-family:'Syne',sans-serif;font-size:36px;font-weight:800;color:#E8601A;line-height:1;}
.kpi.r .kv{color:#ef5350;}.kpi.a .kv{color:#d4a017;}.kpi.b .kv{color:#5b9bd5;}
.kl{font-size:10px;color:#666;letter-spacing:.08em;text-transform:uppercase;margin-top:5px;}
h2{font-family:'Syne',sans-serif;font-size:11px;font-weight:700;letter-spacing:.12em;color:#E8601A;text-transform:uppercase;margin-bottom:14px;padding-bottom:7px;border-bottom:1px solid #222;}
.panel{background:#161616;border:1px solid #2a2a2a;border-radius:8px;padding:22px;margin-bottom:22px;}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-bottom:22px;}
.grid-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:22px;margin-bottom:22px;}
table{width:100%;border-collapse:collapse;font-size:12px;}
thead tr{border-bottom:1px solid #2a2a2a;}
th{text-align:left;padding:8px;font-size:10px;color:#555;letter-spacing:.08em;}
td{padding:7px 8px;border-bottom:1px solid #161616;vertical-align:middle;}
tr:hover td{background:rgba(255,255,255,.025);}
.footer{text-align:center;padding:28px;font-size:11px;color:#555;border-top:1px solid #1e1e1e;font-family:monospace;}
.footer a{color:#E8601A;text-decoration:none;}
@media(max-width:600px){.kpi-row,.grid-2,.grid-3{grid-template-columns:1fr;}.wrap{padding:20px;}}
"""

# ── Header / Footer / Navigation partagés ─────────────────────────────────
def dark_header(report_type: str = "", title: str = "", meta: str = "") -> str:
    return f"""<div class="hdr">
  <div class="report-type" style="font-family:'DM Mono',monospace;font-size:11px;color:#E8601A;letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px;">{esc(report_type)}</div>
  <h1 style="font-size:32px;margin-bottom:4px;">{esc(title)}</h1>
  <div class="meta">{esc(meta)}</div>
</div>"""


def dark_footer(year: int | str = "") -> str:
    return f"""<div class="footer">
  <a href="https://advfood.tech">Food Safety Horizon Scanning &middot; Food Safety Horizon Scanning</a> &nbsp;&middot;&nbsp;
  <a href="../index.html">Live Dashboard</a> &nbsp;&middot;&nbsp;
  <a href="../weekly/">Weekly Reports</a> &nbsp;&middot;&nbsp;
  <a href="../monthly/">Monthly Reports</a> &nbsp;&middot;&nbsp;
  <a href="../yearly/">Yearly Reports</a> &nbsp;&middot;&nbsp; {year}
</div>"""
