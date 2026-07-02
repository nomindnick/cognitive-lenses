"""Neutral aggregation. A judge-tier model reads all lens outputs and
organizes them — with mandatory per-node provenance — into an argument map,
blind spots, a lawyer hand-back, and a noise audit. It adds NO new advocacy.
Advocacy is a good generator and a bad aggregator; this component is the
opposite."""
from __future__ import annotations

from .common import Question

AGGREGATOR_SYSTEM = """You are the NEUTRAL AGGREGATOR at the end of a legal-exploration \
pipeline. Several independent cognitive operations ("lenses") analyzed the same question \
without seeing each other. Your job is to organize what they produced. Hard rules:
- You add NO new legal analysis, arguments, authorities, or opinions of your own. If a \
point appears in no lens output, it must not appear in yours.
- EVERY bullet you write ends with provenance tags naming its source lens(es), e.g. \
[delphi] or [dialectic, premortem]. A bullet without provenance is a failure.
- You de-duplicate: the same point made by three lenses becomes one bullet with three tags.
- Convergence across INDEPENDENT lenses is evidence of robustness; conflict between lenses \
is a finding to report, not a dispute to resolve. Do not adjudicate.
- Authorities cited by lenses are UNVERIFIED. Preserve that framing; never present a cite \
as settled.
- Be honest in the noise audit: if lens output is padded, duplicative, or word-salad, say \
so plainly and name the lens."""


def aggregator_prompt(q: Question, lens_outputs: dict[str, str]) -> str:
    parts = [q.block(),
             f"## Proposition several lenses assessed\n\n\"{q.proposition}\"\n",
             "## Lens outputs (independent; none saw the others)\n"]
    for name, md in lens_outputs.items():
        parts.append(f"\n---\n\n# [LENS: {name}]\n\n{md}")
    parts.append("""
---

Produce EXACTLY this structure:

## 1. Argument map

### Convergent (multiple independent lenses agree)
(bullets, each with provenance tags)

### Contested (lenses genuinely conflict)
(bullets stating BOTH sides of each conflict, tagged, plus one line on the nature of the
conflict: legal-question vs factual-assumption vs risk-tolerance)

### Unique (surfaced by a single lens)
(bullets, tagged — these are candidate blind spots or candidate noise; do not decide which)

## 2. Blind spots
(what only one or two lenses caught that the others walked past, and any angle that appears
under-explored across ALL lenses — the latter is the one place you may note an absence, not
add analysis)

## 3. For the lawyer
### Worth developing (ranked)
(the angles most worth a lawyer's next hour, ranked, each tagged, each with one sentence on
why it earns the rank)
### Must verify
(every authority or factual predicate a recommended angle depends on — all UNVERIFIED)
### What looks decisive
(the crux/cruxes that, once resolved, settle the most — tagged)

## 4. Noise audit
(where the panel produced padding, duplication, or structured word-salad — name lenses
honestly; if none, say so)""")
    return "\n".join(parts)


MERGE_SYSTEM = """You merge two partial aggregates produced by the same neutral aggregation \
step over different subsets of lenses. Produce ONE report in exactly the same section \
structure (Argument map with Convergent/Contested/Unique, Blind spots, For the lawyer, \
Noise audit). Rules: de-duplicate across the two partials; preserve every provenance tag; \
a point Convergent in either partial stays Convergent, and a point appearing in both \
partials from different lenses becomes Convergent; add NO new analysis of your own. \
Prioritize keeping content over compressing — dropping a tagged point is worse than a \
longer report."""

COMPLETENESS_SYSTEM = """You are the completeness checker for the neutral aggregation step of a \
legal-exploration pipeline. Round-1 instrumentation proved the single-pass aggregator drops real \
material: substantive angles present in lens outputs never reached the aggregate. Your job is to \
recover exactly that. Compare the DRAFT aggregate against the raw lens outputs and list every \
substantive angle, warning, authority, deadline, or actionable item that appears in a lens output \
but is absent from (or materially weakened in) the draft. Rules:
- Output ONLY the addendum bullets. Do not rewrite, summarize, or praise the draft.
- Every bullet ends with provenance tags naming its source lens(es), e.g. [premortem].
- Substantive means a practicing lawyer would act on it; do not recover padding or restatement.
- If nothing material is missing, output exactly: "Nothing material was dropped."
"""


def run_aggregate(q: Question, lens_outputs: dict[str, str], backend, cfg: dict,
                  label: str = "aggregate", two_pass: bool | None = None) -> str:
    if two_pass is None:
        two_pass = bool(cfg.get("aggregate_two_pass", False))
    judge = cfg.get("judge_model", "claude-fable-5")
    fallback = cfg.get("fallback_judge_model")
    draft = backend.complete(
        aggregator_prompt(q, lens_outputs),
        model=judge, system=AGGREGATOR_SYSTEM, fallback_model=fallback, label=label,
    ).text
    if not two_pass:
        return draft
    parts = [q.block(), "## DRAFT aggregate\n", draft, "\n## Raw lens outputs\n"]
    for name, md in lens_outputs.items():
        parts.append(f"\n---\n\n# [LENS: {name}]\n\n{md}")
    parts.append("\n---\n\nList what the draft dropped, per your rules.")
    addendum = backend.complete(
        "\n".join(parts), model=judge, system=COMPLETENESS_SYSTEM,
        fallback_model=fallback, label=f"{label}-completeness",
    ).text
    return (draft + "\n\n## 5. Completeness addendum "
            "(second pass — recovered from lens outputs after the draft dropped it)\n\n"
            + addendum)


def run_aggregate_hierarchical(q: Question, lens_outputs: dict[str, str], backend,
                               cfg: dict, label: str = "aggregate-hier") -> str:
    """Capacity-constrained aggregation fix: aggregate lens groups separately
    (smaller inputs, less compression pressure), merge, then completeness-check
    against ALL raw outputs."""
    judge = cfg.get("judge_model", "claude-fable-5")
    fallback = cfg.get("fallback_judge_model")
    names = list(lens_outputs)
    # Split doctrine-leaning vs action/incentive-leaning lenses; fall back to halves.
    g1_pref = [n for n in ("delphi", "tetlock", "dialectic", "steelman") if n in names]
    g2_pref = [n for n in names if n not in g1_pref]
    if not g1_pref or not g2_pref:
        mid = len(names) // 2
        g1_pref, g2_pref = names[:mid], names[mid:]
    partials = []
    for i, group in enumerate((g1_pref, g2_pref), 1):
        partials.append(backend.complete(
            aggregator_prompt(q, {n: lens_outputs[n] for n in group}),
            model=judge, system=AGGREGATOR_SYSTEM, fallback_model=fallback,
            label=f"{label}-g{i}").text)
    merged = backend.complete(
        f"{q.block()}\n\n# PARTIAL A (lenses: {', '.join(g1_pref)})\n\n{partials[0]}\n\n---\n\n"
        f"# PARTIAL B (lenses: {', '.join(g2_pref)})\n\n{partials[1]}\n\n---\n\nMerge per your rules.",
        model=judge, system=MERGE_SYSTEM, fallback_model=fallback,
        label=f"{label}-merge").text
    parts = [q.block(), "## DRAFT aggregate\n", merged, "\n## Raw lens outputs\n"]
    for name, md in lens_outputs.items():
        parts.append(f"\n---\n\n# [LENS: {name}]\n\n{md}")
    parts.append("\n---\n\nList what the draft dropped, per your rules.")
    addendum = backend.complete(
        "\n".join(parts), model=judge, system=COMPLETENESS_SYSTEM,
        fallback_model=fallback, label=f"{label}-completeness").text
    return (merged + "\n\n## 5. Completeness addendum "
            "(second pass — recovered from lens outputs after the draft dropped it)\n\n"
            + addendum)
