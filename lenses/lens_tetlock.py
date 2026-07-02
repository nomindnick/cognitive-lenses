"""Forecasting-tournament decomposition (Tetlock).

Procedure: decompose the question into sub-questions/cruxes ("what would have
to be true") → estimate each crux in a FRESH context that sees only that crux
plus the facts (estimates cannot contaminate each other) → recompose and name
the decisive crux.
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

from .common import Question, WORKER_PREAMBLE
from .lens_base import Lens, LensResult

DECOMP_SCHEMA = {
    "type": "object",
    "properties": {
        "subquestions": {
            "type": "array", "minItems": 3, "maxItems": 6,
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "text": {"type": "string",
                             "description": "a crisply answerable sub-question phrased as a PROPOSITION that is true or false (e.g. 'A court would hold X'), so that a probability estimate is meaningful — never an open 'what/which/how' question"},
                    "why_it_matters": {"type": "string"},
                    "what_would_have_to_be_true": {"type": "string"},
                },
                "required": ["id", "text", "why_it_matters", "what_would_have_to_be_true"],
            },
        },
    },
    "required": ["subquestions"],
}

ESTIMATE_SCHEMA = {
    "type": "object",
    "properties": {
        "probability": {"type": "number", "description": "0-100"},
        "key_considerations": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 5},
        "what_evidence_would_change_this": {"type": "string"},
    },
    "required": ["probability", "key_considerations", "what_evidence_would_change_this"],
}

DECOMP_SYSTEM = WORKER_PREAMBLE + """

Operation: forecasting-tournament DECOMPOSITION only. Break the big contested
question into the smallest set of separately-answerable sub-questions (cruxes)
such that answering all of them substantially answers the big question. Each
sub-question must be something a researcher could investigate on its own, and
each MUST be phrased as a proposition that is true or false — a probability on
an open 'what/which/how' question is meaningless, and instrumentation showed
earlier versions of this lens producing exactly that noise. Do not answer any
of them."""

ESTIMATE_SYSTEM = WORKER_PREAMBLE + """

Operation: estimate ONE sub-question in isolation. You see only the facts and
this sub-question; you must not analyze the broader dispute. Give a calibrated
probability and the few considerations doing the real work."""

RECOMPOSE_SYSTEM = WORKER_PREAMBLE + """

Operation: RECOMPOSITION. Given a decomposition and independent estimates of
each crux, put the answer back together: how the cruxes combine (conjunctive?
disjunctive? conditional?), an overall read with the arithmetic or logic shown,
and — most importantly — name the single DECISIVE crux: the sub-question whose
resolution moves the overall answer the most, and what resolving it would take."""


class TetlockLens(Lens):
    name = "tetlock"
    blurb = ("Decompose into independently-estimated cruxes, recompose, and name the "
             "decisive crux (forecasting-tournament style).")

    def run(self, q: Question, backend, cfg: dict) -> LensResult:
        worker = self.worker(cfg)
        dec = backend.complete(
            f"{q.block()}\nDecompose this into sub-questions/cruxes.",
            model=worker, system=DECOMP_SYSTEM, schema=DECOMP_SCHEMA, label="tetlock-decompose",
        ).data
        subs = dec["subquestions"][: int(self.params.get("max_subquestions", 6))]

        def estimate(sub: dict) -> dict:
            c = backend.complete(
                f"{q.block()}\n## Sub-question to estimate (in isolation)\n\n"
                f"**{sub['text']}**\n\nWhat would have to be true: {sub['what_would_have_to_be_true']}",
                model=worker, system=ESTIMATE_SYSTEM, schema=ESTIMATE_SCHEMA,
                label=f"tetlock-est-{sub['id']}",
            )
            return {**sub, "estimate": c.data}

        with ThreadPoolExecutor(max_workers=len(subs)) as ex:
            estimated = list(ex.map(estimate, subs))

        recompose = backend.complete(
            f"{q.block()}\n## Decomposition with independent estimates\n\n"
            f"```json\n{json.dumps(estimated, indent=2)}\n```\n\n"
            "Recompose: combination logic, overall read, decisive crux.",
            model=worker, system=RECOMPOSE_SYSTEM, label="tetlock-recompose",
        ).text

        out = [f"### Operation\n{self.blurb}\n", "### Cruxes and independent estimates\n",
               "| Crux | P (0–100) | Why it matters |", "|---|---|---|"]
        for s in estimated:
            out.append(f"| **{s['id']}**: {s['text'].replace('|', '/')} "
                       f"| {s['estimate']['probability']} | {s['why_it_matters'].replace('|', '/')} |")
        out.append("\n### Recomposition and decisive crux\n")
        out.append(recompose)
        out.append("\n<details><summary>Per-crux considerations</summary>\n")
        for s in estimated:
            out.append(f"\n**{s['id']}** — {s['text']} (P={s['estimate']['probability']})")
            for k in s["estimate"]["key_considerations"]:
                out.append(f"- {k}")
            out.append(f"- *Would change on:* {s['estimate']['what_evidence_would_change_this']}")
        out.append("\n</details>")
        return LensResult(self.name, "\n".join(out) + "\n", meta={"subquestions": estimated})
