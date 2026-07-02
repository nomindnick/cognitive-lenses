"""Automated verification stage: the guardrail, promoted to a pipeline step.

Both experiment rounds found the flag-then-verify loop was the pipeline's most
valuable component — and it was manual. This stage automates the first tier:
search-enabled worker calls check each flagged authority for (1) existence,
(2) citation form, (3) whether it plausibly stands for what the panel used it
for. It is NOT Shepardizing and the output says so; statuses feed the same
verification.json the reports already render.
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import citations
from .common import RUNS_DIR, Question, log, read_json, write_json

VERIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string",
                   "enum": ["VERIFIED", "MISCHARACTERIZED", "NOT_FOUND", "CONTESTED", "UNCLEAR"]},
        "canonical_cite": {"type": "string",
                           "description": "the correct full citation, if determinable"},
        "note": {"type": "string",
                 "description": "1-3 sentences: what was confirmed or refuted, and the correct cite"},
        "source_urls": {"type": "array", "items": {"type": "string"},
                        "description": "pages actually relied on"},
    },
    "required": ["status", "canonical_cite", "note", "source_urls"],
}

VERIFIER_SYSTEM = """You are the citation verifier in a legal-exploration pipeline. You are \
given one authority as cited by the pipeline's components, plus snippets showing how it was \
used. Using web search (prefer primary/official sources: leginfo.legislature.ca.gov, \
courts.ca.gov, law.justia.com, casetext.com, codes.findlaw.com, fppc.ca.gov), determine:
1. Does the authority exist?
2. Is the citation form correct (reporter cite, year, section number)?
3. Does it plausibly stand for what the snippets use it for?

Statuses: VERIFIED (exists, cite essentially right, usage consistent with what you found); \
MISCHARACTERIZED (exists but does not support the claimed use, or the cite attaches to the \
wrong case/section); NOT_FOUND (cannot locate after genuine searching); CONTESTED (real \
sources point in conflicting directions, or scope is genuinely unsettled); UNCLEAR (could \
not determine within a reasonable search).

You are NOT determining whether the authority is still good law (no Shepardizing) — say what \
you actually confirmed, no more. Be strict: a close-but-wrong reporter cite or a holding \
stretched past what sources show is MISCHARACTERIZED, not VERIFIED."""

_CASE_CORE = re.compile(
    r"([A-Z][\w'’.&-]*(?:\s+[\w'’.&-]+){0,4}?)\s+v\.\s+([A-Z][\w'’.&-]*(?:\s+[\w'’.&-]+){0,4})")
_SECTION = re.compile(r"\d{3,6}(?:\.\d+)?")
_PRIORITY = {"case": 0, "reporter": 1, "statute": 2, "const": 3, "prop": 4, "fppc": 5, "reg": 6}


def _canonical_key(item: dict) -> str | None:
    cite, kind = item["cite"], item["kind"]
    if kind == "case":
        m = _CASE_CORE.search(cite)
        if not m:
            return None
        left = m.group(1).split()[-3:]  # trim leading sentence fragments
        return re.sub(r"\s+", " ", f"{' '.join(left)} v. {m.group(2)}").lower().strip(" .,")
    if kind in ("statute", "reg"):
        m = _SECTION.search(cite)
        return m.group(0) if m else None
    return re.sub(r"\s+", " ", cite).lower()


def _snippets(texts: dict[str, str], variants: list[str], per: int = 3) -> list[str]:
    out = []
    for source, text in texts.items():
        for v in variants:
            i = text.find(v)
            if i >= 0:
                out.append(f"[{source}] …{text[max(0, i - 220):i + len(v) + 220]}…")
                break
        if len(out) >= per:
            break
    return out


def collect_targets(texts: dict[str, str], max_targets: int) -> list[dict]:
    """Group extracted authorities under canonical keys, rank, cap."""
    groups: dict[str, dict] = {}
    for item in citations.extract_by_source(texts):
        key = _canonical_key(item)
        if not key:
            continue
        g = groups.setdefault(key, {"key": key, "kind": item["kind"],
                                    "variants": [], "sources": set()})
        g["variants"].append(item["cite"])
        g["sources"] |= set(item["sources"])
    ranked = sorted(groups.values(),
                    key=lambda g: (-len(g["sources"]), _PRIORITY.get(g["kind"], 9)))
    return ranked[:max_targets]


def run_verify(qid: str, cfg: dict, backend, max_targets: int = 14,
               run_dir: Path | None = None) -> dict:
    q = Question.load(qid)
    rd = Path(run_dir) if run_dir else RUNS_DIR / q.id
    texts = {p.stem: p.read_text(encoding="utf-8") for p in (rd / "lenses").glob("*.md")}
    texts |= {p.stem: p.read_text(encoding="utf-8") for p in (rd / "baselines").glob("*.md")}
    agg = rd / "aggregate.md"
    if agg.exists():
        texts["aggregate"] = agg.read_text(encoding="utf-8")

    targets = collect_targets(texts, max_targets)
    log(f"[{qid}] verifying {len(targets)} authorities (search-enabled workers)")

    def check(t: dict) -> tuple[str, dict]:
        snips = "\n\n".join(_snippets(texts, t["variants"]))
        prompt = (
            f"## Authority as cited (variants seen in the documents)\n\n"
            + "\n".join(f"- {v}" for v in sorted(set(t["variants"]))[:6])
            + f"\n\n## How the documents used it\n\n{snips}\n\n"
            f"## Context\n\nThe underlying question is a California public-agency "
            f"hypothetical: {q.title}.\n\nVerify this authority per your instructions."
        )
        # verify_model overrides worker_model here: cite-check needs web tools,
        # which local (ollama:*) workers don't have.
        c = backend.complete(prompt,
                             model=cfg.get("verify_model") or cfg.get("worker_model", "claude-sonnet-5"),
                             system=VERIFIER_SYSTEM, schema=VERIFY_SCHEMA,
                             tools="WebSearch,WebFetch",
                             label=f"verify-{re.sub(r'[^a-z0-9]+', '-', t['key'])[:40]}")
        d = c.data
        urls = "; ".join(d.get("source_urls", [])[:3])
        return t["key"], {
            "status": d["status"],
            "note": (f"(auto cite-check, web) {d['note']} "
                     f"Canonical: {d['canonical_cite']}. Sources: {urls}").strip(),
        }

    with ThreadPoolExecutor(max_workers=min(6, len(targets) or 1)) as ex:
        results = dict(ex.map(check, targets))

    vpath = rd / "verification.json"
    existing = read_json(vpath) if vpath.exists() else {}
    merged = {**results, **{k: v for k, v in existing.items() if k != "_meta"}}
    merged["_meta"] = {
        **existing.get("_meta", {}),
        "auto_adapter": ("search-enabled worker cite-check (WebSearch/WebFetch), "
                         "existence + citation form + characterization only — NOT a "
                         "good-law/Shepardizing check"),
        "auto_checked": sorted(results),
    }
    write_json(vpath, merged)
    log(f"[{qid}] verification written: "
        + ", ".join(f"{v['status']}:{k}" for k, v in sorted(results.items())))
    return results
