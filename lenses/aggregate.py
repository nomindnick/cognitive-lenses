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


def run_aggregate(q: Question, lens_outputs: dict[str, str], backend, cfg: dict,
                  label: str = "aggregate") -> str:
    c = backend.complete(
        aggregator_prompt(q, lens_outputs),
        model=cfg.get("judge_model", "claude-fable-5"),
        system=AGGREGATOR_SYSTEM,
        fallback_model=cfg.get("fallback_judge_model"),
        label=label,
    )
    return c.text
