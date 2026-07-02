"""Deterministic authority extraction + UNVERIFIED flagging.

Principle 3 of the SPEC: the guardrail must not itself depend on a model. Every
authority-looking string in any lens/baseline/aggregate output is extracted by
regex and flagged UNVERIFIED. A verifier adapter (human or tool) may later
upgrade individual flags; nothing else may.
"""
from __future__ import annotations

import re

_CODE = (
    r"(?:Gov(?:'t|t)?\.?|Government|Civ(?:il)?\.?|Pen(?:al)?\.?|Elec(?:tions)?\.?|"
    r"Wat(?:er)?\.?|Educ?\.?|Education|Lab(?:or)?\.?|Veh(?:icle)?\.?|"
    r"Health\s*(?:&|and)\s*Saf(?:ety)?\.?|Rev(?:enue)?\.?\s*(?:&|and)\s*Tax(?:ation)?\.?|"
    r"Bus(?:iness)?\.?\s*(?:&|and)\s*Prof(?:essions)?\.?|"
    r"Pub(?:lic)?\.?\s*(?:Res(?:ources)?|Util(?:ities)?|Cont(?:ract)?s?)\.?|"
    r"Welf(?:are)?\.?\s*(?:&|and)\s*Inst(?:itutions)?\.?)"
)

PATTERNS: list[tuple[str, re.Pattern]] = [
    ("statute", re.compile(
        rf"(?:Cal(?:ifornia|\.)?\s+)?{_CODE}\s*Code\s*,?\s*(?:Ann\.\s*)?"
        rf"(?:§{{1,2}}|[Ss]ections?)\s*\d[\d.]*(?:\([a-zA-Z0-9]{{1,3}}\))*"
        rf"(?:\s*(?:,|and|&)\s*\d[\d.]*(?:\([a-zA-Z0-9]{{1,3}}\))*)*", re.I)),
    ("statute", re.compile(r"§{1,2}\s*\d{3,6}(?:\.\d+)?(?:\([a-zA-Z0-9]{1,3}\))*")),
    ("case", re.compile(
        r"\b[A-Z][\w'’.&\- ]{1,60}?\s+v\.\s+[A-Z][\w'’.&\- ]{1,60}?(?=[,.;:)\n(])")),
    ("reporter", re.compile(r"\b\d{1,3}\s+Cal\.\s*(?:App\.\s*)?(?:2d|3d|4th|5th)\s+\d+")),
    ("reporter", re.compile(r"\b\d{1,3}\s+U\.S\.\s+\d+")),
    ("const", re.compile(
        r"[Aa]rt(?:icle|\.)?\s+[IVXL]+\s*[A-D]?\s*,?\s*(?:§{1,2}|[Ss]ec(?:tion|\.)?)\s*\d+[A-Za-z0-9().]*")),
    ("prop", re.compile(r"\bProp(?:osition|\.)?\s+\d{1,3}\b")),
    ("fppc", re.compile(
        r"\bFPPC\s+(?:Adv(?:ice)?\.?\s*(?:Ltr\.?|Letter)?|Op(?:inion|\.)?s?|File)?\s*"
        r"(?:No\.\s*)?[A-Za-z]{0,2}-?\d{2}-\d{1,4}", re.I)),
    ("reg", re.compile(
        r"\b(?:Cal\.\s*Code\s*(?:of\s*)?Regs\.?|C\.?C\.?R\.?)\s*,?\s*"
        r"(?:tit(?:le|\.)\s*\d+\s*,?\s*)?§{1,2}?\s*\d{4,5}(?:\.\d+)?", re.I)),
    ("reg", re.compile(r"\b(?:2|14|25)\s+C\.?C\.?R\.?\s*§?\s*\d{4,5}", re.I)),
]

_JUNK = re.compile(r"^(?:see|see also|e\.g|cf|compare|but see)\b", re.I)


def extract(text: str) -> list[dict]:
    """Return deduped authorities: [{kind, cite, count}]."""
    found: dict[str, dict] = {}
    for kind, pat in PATTERNS:
        for m in pat.finditer(text):
            cite = re.sub(r"\s+", " ", m.group(0)).strip(" ,.;:*_([")
            if len(cite) < 4 or _JUNK.match(cite):
                continue
            key = cite.lower()
            if key in found:
                found[key]["count"] += 1
            else:
                found[key] = {"kind": kind, "cite": cite, "count": 1}
    # Drop case-name fragments fully contained in a longer case name.
    items = list(found.values())
    case_keys = [i["cite"].lower() for i in items if i["kind"] == "case"]
    out = []
    for i in items:
        k = i["cite"].lower()
        if i["kind"] == "case" and any(k != o and k in o for o in case_keys):
            continue
        out.append(i)
    return sorted(out, key=lambda i: (i["kind"], i["cite"].lower()))


def extract_by_source(texts: dict[str, str]) -> list[dict]:
    """Extract across labeled documents; track which sources cite each authority."""
    merged: dict[str, dict] = {}
    for source, text in texts.items():
        for item in extract(text or ""):
            key = item["cite"].lower()
            if key not in merged:
                merged[key] = {**item, "sources": [], "status": "UNVERIFIED"}
            merged[key]["sources"] = sorted(set(merged[key]["sources"]) | {source})
    return sorted(merged.values(), key=lambda i: (i["kind"], i["cite"].lower()))


def authorities_markdown(auths: list[dict], verification: dict | None = None) -> str:
    """Render the flagged-authorities table. `verification` maps cite(lower) ->
    {status, note} from a verifier adapter; everything else stays UNVERIFIED."""
    if not auths:
        return "_No specific authorities detected._\n"
    lines = [
        "| Authority | Kind | Cited by | Status |",
        "|---|---|---|---|",
    ]
    for a in auths:
        v = (verification or {}).get(a["cite"].lower())
        if v:
            status = f"**{v['status']}** — {v.get('note', '')}"
        else:
            status = "⚠️ UNVERIFIED — check before relying"
        lines.append(f"| {a['cite']} | {a['kind']} | {', '.join(a.get('sources', []))} | {status} |")
    return "\n".join(lines) + "\n"
