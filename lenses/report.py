"""Rendering: per-question report.md + report.html, cross-question index.html.
Stdlib-only, so this includes a deliberately small markdown->HTML converter —
good enough for legible reports, not a spec-complete parser."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

from .common import (RUNS_DIR, UNVERIFIED_BANNER, Question, read_json, write_text)
from . import citations

_INLINE = [
    (re.compile(r"`([^`]+)`"), r"<code>\1</code>"),
    (re.compile(r"\*\*\*([^*]+)\*\*\*"), r"<strong><em>\1</em></strong>"),
    (re.compile(r"\*\*([^*]+)\*\*"), r"<strong>\1</strong>"),
    (re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)"), r"<em>\1</em>"),
    (re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)"), r'<a href="\2">\1</a>'),
]


def _inline(s: str) -> str:
    for pat, rep in _INLINE:
        s = pat.sub(rep, s)
    return s


def _esc(raw: str) -> str:
    line = html.escape(raw, quote=False)
    for tag in ("details", "/details", "summary", "/summary"):
        line = line.replace(f"&lt;{tag}&gt;", f"<{tag}>")
    return line


def md2html(md: str) -> str:
    lines = md.split("\n")
    out: list[str] = []
    i = 0
    in_ul = in_ol = False

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    while i < len(lines):
        line = _esc(lines[i])
        stripped = line.strip()
        if stripped.startswith("```"):
            close_lists()
            code, i = [], i + 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(html.escape(lines[i], quote=False))
                i += 1
            out.append("<pre><code>" + "\n".join(code) + "</code></pre>")
            i += 1
            continue
        if stripped.startswith("|") and i + 1 < len(lines) and \
                re.match(r"^\s*\|[\s:|-]+\|?\s*$", lines[i + 1]):
            close_lists()
            hdr = [c.strip() for c in stripped.strip("|").split("|")]
            out.append("<table><thead><tr>" +
                       "".join(f"<th>{_inline(c)}</th>" for c in hdr) +
                       "</tr></thead><tbody>")
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in _esc(lines[i]).strip().strip("|").split("|")]
                out.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in cells) + "</tr>")
                i += 1
            out.append("</tbody></table>")
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            close_lists()
            out.append(f"<h{len(m.group(1))}>{_inline(m.group(2))}</h{len(m.group(1))}>")
            i += 1
            continue
        if re.match(r"^(-{3,}|\*{3,})$", stripped):
            close_lists()
            out.append("<hr>")
            i += 1
            continue
        if stripped.startswith("&gt;"):
            close_lists()
            quote = []
            while i < len(lines) and _esc(lines[i]).strip().startswith("&gt;"):
                quote.append(_esc(lines[i]).strip()[4:].strip())
                i += 1
            out.append(f"<blockquote><p>{_inline(' '.join(quote))}</p></blockquote>")
            continue
        m = re.match(r"^\s*[-*+]\s+(.*)$", line)
        if m:
            if in_ol:
                out.append("</ol>")
                in_ol = False
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{_inline(m.group(1))}</li>")
            i += 1
            continue
        m = re.match(r"^\s*\d+[.)]\s+(.*)$", line)
        if m:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if not in_ol:
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{_inline(m.group(1))}</li>")
            i += 1
            continue
        if not stripped:
            close_lists()
            i += 1
            continue
        if stripped.startswith(("<details", "</details")):
            close_lists()
            out.append(stripped)
            i += 1
            continue
        close_lists()
        out.append(f"<p>{_inline(stripped)}</p>")
        i += 1
    close_lists()
    return "\n".join(out)


_CSS = """
:root { --ink:#1a1e23; --sub:#5b6470; --line:#e3e6ea; --accent:#7a4dd8; --warn-bg:#fff7e0;
        --warn-line:#e8c76a; --card:#fafbfc; }
* { box-sizing:border-box; }
body { font:16px/1.6 -apple-system,'Segoe UI',Roboto,'Helvetica Neue',sans-serif;
       color:var(--ink); max-width:62rem; margin:0 auto; padding:2rem 1.2rem 6rem; }
h1 { font-size:1.7rem; line-height:1.25; } h2 { margin-top:2.2em; border-bottom:2px solid var(--line);
padding-bottom:.3em; } h3 { margin-top:1.6em; } h4 { margin-top:1.3em; }
a { color:var(--accent); } code { background:#f1f0f7; padding:.1em .35em; border-radius:4px;
font-size:.9em; } pre { background:#f6f6f9; border:1px solid var(--line); border-radius:8px;
padding:1em; overflow-x:auto; } pre code { background:none; padding:0; }
blockquote { margin:1em 0; padding:.6em 1em; border-left:4px solid var(--accent);
background:var(--card); border-radius:0 8px 8px 0; }
table { border-collapse:collapse; width:100%; margin:1em 0; font-size:.92em; }
th,td { border:1px solid var(--line); padding:.45em .6em; text-align:left; vertical-align:top; }
th { background:var(--card); }
details { border:1px solid var(--line); border-radius:8px; padding:.6em 1em; margin:.8em 0;
background:var(--card); } summary { cursor:pointer; font-weight:600; color:var(--sub); }
details[open] summary { margin-bottom:.6em; }
.banner { background:var(--warn-bg); border:1px solid var(--warn-line); border-radius:8px;
padding: .8em 1em; margin:1.2em 0; }
.meta { color:var(--sub); font-size:.9em; }
.chip { display:inline-block; background:#efe9fb; color:#5b3aa8; border-radius:999px;
padding:.1em .7em; font-size:.8em; margin-right:.4em; }
.card { border:1px solid var(--line); border-radius:10px; padding:1em 1.2em; margin:1em 0;
background:var(--card); }
"""


def page(title: str, body_html: str) -> str:
    return (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width, initial-scale=1'>"
            f"<title>{html.escape(title)}</title><style>{_CSS}</style></head>"
            f"<body>{body_html}</body></html>")


def call_stats(calls_dir: Path) -> dict:
    stats = {"calls": 0, "cost_usd": 0.0, "by_model": {}}
    if not calls_dir.exists():
        return stats
    for f in sorted(calls_dir.glob("*.json")):
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        u = rec.get("usage") or {}
        b = stats["by_model"].setdefault(rec.get("model", "?"), {
            "calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0})
        b["calls"] += 1
        b["input_tokens"] += (u.get("input_tokens", 0) +
                              u.get("cache_creation_input_tokens", 0) +
                              u.get("cache_read_input_tokens", 0))
        b["output_tokens"] += u.get("output_tokens", 0)
        b["cost_usd"] = round(b["cost_usd"] + (rec.get("cost_usd") or 0), 4)
        stats["calls"] += 1
        stats["cost_usd"] = round(stats["cost_usd"] + (rec.get("cost_usd") or 0), 4)
    return stats


def metrics_md(m: dict) -> str:
    lines = [
        "| | Panel (Sonnet workers) | Naive Sonnet | Naive Fable |",
        "|---|---|---|---|",
        f"| Angles found (of {m['angles_total']} total) | {m['panel_found']} "
        f"| {m['naive_sonnet_found']} | {m['naive_fable_found']} |",
        f"| Substantive angles (of {m['angles_substantive']}) | {m['panel_substantive']} "
        f"| {m['naive_sonnet_substantive']} | {m['naive_fable_substantive']} |",
        "",
        f"- **Panel-only substantive angles** (missed by BOTH naive passes): {m['panel_only_substantive']}",
        f"- Substantive angles the panel found that its own model's naive pass missed: {m['panel_beats_own_model']}",
        f"- Substantive angles the panel MISSED that a naive pass caught: {m['missed_by_panel_substantive']}",
        f"- Panel noise rate (noise / panel angles): {m['panel_noise_rate']:.0%}",
    ]
    if m.get("per_lens"):
        lines += ["", "**Per-lens contribution** (unique substantive = substantive angles only this "
                  "lens surfaced and no naive pass had):", "",
                  "| Lens | Angles | Substantive | Unique substantive | Noise |",
                  "|---|---|---|---|---|"]
        for name, d in m["per_lens"].items():
            lines.append(f"| {name} | {d['angles']} | {d['substantive']} "
                         f"| {d['unique_substantive']} | {d['noise']} |")
    return "\n".join(lines) + "\n"


def _read_if(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.exists() else None


def build_question_report(qid: str, run_dir: Path | None = None) -> Path:
    """Assemble report.md + report.html for a question from artifacts on disk."""
    q = Question.load(qid)
    rd = Path(run_dir) if run_dir else RUNS_DIR / q.id
    lens_mds = {p.stem: p.read_text(encoding="utf-8")
                for p in sorted((rd / "lenses").glob("*.md"))}
    naive_s = _read_if(rd / "baselines" / "naive_sonnet.md")
    naive_f = _read_if(rd / "baselines" / "naive_fable.md")
    aggregate = _read_if(rd / "aggregate.md")
    judge = read_json(rd / "judge.json") if (rd / "judge.json").exists() else None
    metrics = read_json(rd / "metrics.json") if (rd / "metrics.json").exists() else None
    verification = (read_json(rd / "verification.json")
                    if (rd / "verification.json").exists() else None)

    texts = dict(lens_mds)
    if aggregate:
        texts["aggregate"] = aggregate
    if naive_s:
        texts["naive_sonnet"] = naive_s
    if naive_f:
        texts["naive_fable"] = naive_f
    auths = citations.extract_by_source(texts)

    out = [f"# {q.title}", "",
           f"`{q.area}` · question id `{q.id}`" + (" · **featured**" if q.featured else ""), "",
           UNVERIFIED_BANNER, "",
           "## The question", "", q.facts, "", "**Asked:** " + q.question, "",
           f"**Delphi proposition:** \"{q.proposition}\"", "",
           f"**Why it's contested:** {q.why_contested}", ""]

    if metrics and judge:
        out += ["## Coverage experiment — panel vs naive passes", "",
                "*Scored by a Fable-tier judge instructed to be adversarial toward the "
                "panel: an angle only counts where a document actually develops it.*", "",
                metrics_md(metrics), "",
                f"**Judge's verdict:** {judge.get('verdict', '')}", "",
                f"**Panel-unique value:** {judge.get('panel_unique_assessment', '')}", "",
                f"**Noise:** {judge.get('noise_assessment', '')}", ""]

    if aggregate:
        out += ["## Aggregated argument map (the tool's deliverable)", "", aggregate, ""]

    out += ["## Authorities cited (extracted deterministically, flagged)", "",
            citations.authorities_markdown(auths, verification), ""]
    if verification:
        out += ["*Verification statuses above were applied by a verifier adapter "
                "(see verification.json); everything else remains unverified.*", ""]

    if naive_s or naive_f:
        out += ["## Naive baselines (the control arm)", ""]
        if naive_s:
            out += ["<details><summary>Naive single pass — Sonnet 5 (same model as panel "
                    "workers)</summary>", "", naive_s, "", "</details>", ""]
        if naive_f:
            out += ["<details><summary>Naive single pass — Fable 5 (reference ceiling)"
                    "</summary>", "", naive_f, "", "</details>", ""]

    out += ["## Raw lens outputs", ""]
    for name, md in lens_mds.items():
        out += [f"<details><summary>Lens: {name}</summary>", "", md, "", "</details>", ""]

    err_dir = rd / "errors"
    if err_dir.exists() and any(err_dir.iterdir()):
        out += ["## Errors during this run", ""]
        for f in sorted(err_dir.glob("*.txt")):
            out += [f"- **{f.stem}** failed; see `errors/{f.name}`"]
        out += [""]

    if metrics:
        stats = metrics.get("run_stats")
        if stats:
            out += ["## Run stats", "",
                    f"- Model calls: {stats['calls']} · reported API-equivalent cost: "
                    f"${stats['cost_usd']:.2f}", ""]
            for model, b in stats["by_model"].items():
                out += [f"- `{model}`: {b['calls']} calls, {b['input_tokens']:,} in / "
                        f"{b['output_tokens']:,} out tokens"]
            if metrics.get("wall_s"):
                out += [f"- Wall time: {metrics['wall_s']/60:.1f} min"]
            out += [""]

    md = "\n".join(out)
    write_text(rd / "report.md", md)
    write_text(rd / "report.html", page(q.title, md2html(md)))
    return rd / "report.html"


def build_index(qids: list[str]) -> Path:
    cards = ["# cognitive-lenses — run index", "",
             UNVERIFIED_BANNER, "",
             "**[Read FINDINGS — the honest verdict](../FINDINGS.html)**", "",
             "Each question was run through the full lens panel (Sonnet 5 workers), a "
             "neutral Fable 5 aggregator, and two naive baseline passes; a Fable 5 judge "
             "scored coverage. Click through for the full report.", ""]
    rows = ["| Question | Angles: panel | naive Sonnet | naive Fable | Panel-only substantive | Panel noise |",
            "|---|---|---|---|---|---|"]
    for qid in qids:
        try:
            q = Question.load(qid)
        except FileNotFoundError:
            continue
        rd = RUNS_DIR / q.id
        m = read_json(rd / "metrics.json") if (rd / "metrics.json").exists() else None
        cards += [f"## [{q.title}]({q.id}/report.html)", "",
                  f"`{q.area}`" + (" · **featured**" if q.featured else ""), "",
                  q.why_contested, ""]
        if m:
            rows.append(f"| [{q.id}]({q.id}/report.html) | {m['panel_substantive']}"
                        f"/{m['angles_substantive']} | {m['naive_sonnet_substantive']} "
                        f"| {m['naive_fable_substantive']} | {m['panel_only_substantive']} "
                        f"| {m['panel_noise_rate']:.0%} |")
    if len(rows) > 2:
        cards += ["## Cross-question coverage (substantive angles)", ""] + rows + [""]
    abl = RUNS_DIR / "q1" / "ablation" / "ablation.json"
    if abl.exists():
        a = read_json(abl)
        cards += ["## Leave-one-out ablation (featured question)", "",
                  "| Lens removed | Materiality of loss | What was lost |", "|---|---|---|"]
        for name, d in sorted(a.items()):
            lost = "; ".join(d.get("lost_points", []))[:300].replace("|", "/")
            cards += [f"| {name} | {d.get('materiality', '?')} | {lost} |"]
        cards += [""]
    md = "\n".join(cards)
    write_text(RUNS_DIR / "index.md", md)
    write_text(RUNS_DIR / "index.html", page("cognitive-lenses — runs", md2html(md)))
    findings = RUNS_DIR.parent / "FINDINGS.md"
    if findings.exists():
        write_text(RUNS_DIR.parent / "FINDINGS.html",
                   page("FINDINGS — cognitive-lenses",
                        md2html(findings.read_text(encoding="utf-8"))))
    return RUNS_DIR / "index.html"
