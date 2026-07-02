"""Delphi elicitation (featured lens).

Procedure:
  Round 1: N independent panelists (fresh contexts) each return a structured
  position: probability the proposition holds, confidence, rationales,
  authorities, biggest uncertainty.
  Facilitation: code computes anonymized statistics; a judge-model facilitator
  clusters rationale themes WITHOUT evaluating or hinting at an answer.
  Round k+1: each panelist sees ONLY (their own previous answer + the
  anonymized summary) and independently revises. No panelist ever sees another
  panelist's output directly.
  Stop: after round 2 unless positions are still moving; max 3 rounds.
  Output: trajectory, final spread, and persistent disagreement reported as
  signal, not noise.
"""
from __future__ import annotations

import json
import statistics
from concurrent.futures import ThreadPoolExecutor

from .common import Question, WORKER_PREAMBLE
from .lens_base import Lens, LensResult

PANELIST_SCHEMA = {
    "type": "object",
    "properties": {
        "probability": {"type": "number", "description": "0-100 probability the proposition is correct"},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
        "position_summary": {"type": "string"},
        "rationales": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 5},
        "authorities": {"type": "array", "items": {"type": "string"}},
        "biggest_uncertainty": {"type": "string"},
    },
    "required": ["probability", "confidence", "position_summary", "rationales", "biggest_uncertainty"],
}

REVISE_SCHEMA = {
    "type": "object",
    "properties": {
        **PANELIST_SCHEMA["properties"],
        "changed": {"type": "boolean"},
        "response_to_panel": {"type": "string",
                              "description": "which panel consideration moved you, or why none did"},
    },
    "required": PANELIST_SCHEMA["required"] + ["changed", "response_to_panel"],
}

# Different analytical entry points de-correlate anchoring across panelists.
# These are procedural starting points, not personas (configurable off).
ENTRY_POINTS = [
    "Begin from the text of the governing statute or constitutional provision, read closely.",
    "Begin from the leading cases and how courts have actually applied the rule to messy facts.",
    "Begin from enforcement realities: who would sue, what remedies exist, what actually happens in practice.",
    "Begin from the strongest available argument that the conduct or measure is LAWFUL, then evaluate it.",
    "Begin from the strongest available argument that the conduct or measure is UNLAWFUL, then evaluate it.",
    "Begin from close analogies: how have adjacent or analogous situations been treated?",
    "Begin from the advice a cautious public-agency counsel would give, then ask whether caution is legally required or merely prudent.",
]

PANELIST_SYSTEM = WORKER_PREAMBLE + """

Operation: you are ONE independent panelist in a Delphi elicitation. There is no
discussion; you answer alone. Give your honest probability, not a diplomatic one.
Do not hedge toward 50 to be safe — commit to your analysis."""

FACILITATOR_SYSTEM = """You are the neutral facilitator of a Delphi panel on a legal question.
You NEVER evaluate arguments, take positions, or hint at a correct answer. You only
organize what panelists said, anonymously. Any editorializing is a failure."""


def _stats(probs: list[float]) -> dict:
    qs = statistics.quantiles(probs, n=4) if len(probs) >= 2 else [probs[0]] * 3
    return {
        "n": len(probs),
        "median": round(statistics.median(probs), 1),
        "mean": round(statistics.fmean(probs), 1),
        "stdev": round(statistics.pstdev(probs), 1),
        "min": min(probs), "max": max(probs),
        "q1": round(qs[0], 1), "q3": round(qs[2], 1),
        "iqr": round(qs[2] - qs[0], 1),
    }


def _stats_block(s: dict) -> str:
    return (f"Panel of {s['n']}. Probability that the proposition is correct: "
            f"median {s['median']}, mean {s['mean']}, std dev {s['stdev']}, "
            f"range {s['min']}–{s['max']}, middle 50% of panel between {s['q1']} and {s['q3']}.")


class DelphiLens(Lens):
    name = "delphi"
    blurb = ("N independent panelists estimate a proposition, see only an anonymized "
             "statistical summary, and independently revise; persistent disagreement is signal.")

    def run(self, q: Question, backend, cfg: dict) -> LensResult:
        n = int(self.params.get("panelists", 7))
        max_rounds = int(self.params.get("max_rounds", 3))
        vary = bool(self.params.get("vary_entry_points", True))
        worker = self.worker(cfg)

        base_prompt = (
            f"{q.block()}\n## Proposition to assess\n\n\"{q.proposition}\"\n\n"
            "Estimate the probability (0–100) that this proposition is correct, with your "
            "reasoning. rationales = your independent load-bearing reasons, one sentence each. "
            "authorities = specific authorities you are actually relying on (they will be "
            "flagged for human verification). biggest_uncertainty = the single thing you are "
            "least sure of."
        )

        rounds: list[list[dict]] = []
        summaries: list[str] = []

        def ask_round1(i: int) -> dict:
            entry = f"\n\nAnalytical starting point for you: {ENTRY_POINTS[i % len(ENTRY_POINTS)]}" if vary else ""
            c = backend.complete(base_prompt + entry, model=worker, system=PANELIST_SYSTEM,
                                 schema=PANELIST_SCHEMA, label=f"delphi-r1-p{i + 1}")
            return c.data

        def ask_revise(i: int, rnd: int, prev: dict, summary: str) -> dict:
            prompt = (
                f"{q.block()}\n## Proposition to assess\n\n\"{q.proposition}\"\n\n"
                f"This is round {rnd} of a Delphi panel. Your previous answer:\n\n"
                f"```json\n{json.dumps(prev, indent=2)}\n```\n\n"
                f"The anonymized panel summary (statistics + themes, no attribution):\n\n{summary}\n\n"
                "Independently reconsider. Do NOT defer to the majority; update only where the "
                "summary contains reasons you judge valid, and hold your position where it does "
                "not. Explain in response_to_panel which consideration moved you or why none did."
            )
            c = backend.complete(prompt, model=worker, system=PANELIST_SYSTEM,
                                 schema=REVISE_SCHEMA, label=f"delphi-r{rnd}-p{i + 1}")
            return c.data

        with ThreadPoolExecutor(max_workers=n) as ex:
            rounds.append(list(ex.map(ask_round1, range(n))))

        for rnd in range(2, max_rounds + 1):
            prev = rounds[-1]
            summary = self._facilitate(prev, backend, cfg, rnd - 1)
            summaries.append(summary)
            with ThreadPoolExecutor(max_workers=n) as ex:
                rounds.append(list(ex.map(lambda i: ask_revise(i, rnd, prev[i], summary), range(n))))
            if rnd >= 2 and self._converged(rounds):
                break

        final = rounds[-1]
        stats_by_round = [_stats([float(p["probability"]) for p in r]) for r in rounds]
        persistent = self._persistent_disagreement(final, stats_by_round[-1], backend, cfg)

        md = self._render(q, rounds, summaries, stats_by_round, persistent)
        return LensResult(self.name, md, meta={
            "rounds": rounds, "stats_by_round": stats_by_round,
            "summaries": summaries, "persistent_disagreement": persistent,
        })

    def _converged(self, rounds) -> bool:
        s_prev = _stats([float(p["probability"]) for p in rounds[-2]])
        s_now = _stats([float(p["probability"]) for p in rounds[-1]])
        settled = abs(s_now["median"] - s_prev["median"]) <= 5 and s_now["iqr"] <= 15
        # If the spread stopped shrinking, further rounds won't converge either —
        # that residual disagreement is the finding.
        stalled = s_now["iqr"] >= s_prev["iqr"] * 0.85
        return settled or stalled

    def _facilitate(self, panel: list[dict], backend, cfg, round_no: int) -> str:
        stats = _stats([float(p["probability"]) for p in panel])
        anon = sorted(panel, key=lambda p: p["probability"])
        payload = json.dumps([{k: p.get(k) for k in
                               ("probability", "position_summary", "rationales",
                                "authorities", "biggest_uncertainty")} for p in anon], indent=2)
        prompt = (
            f"Anonymized round-{round_no} answers from a Delphi panel (sorted by probability):\n\n"
            f"```json\n{payload}\n```\n\nComputed statistics: {_stats_block(stats)}\n\n"
            "Produce the feedback summary that will be shown to every panelist:\n"
            "1. Repeat the statistics line verbatim.\n"
            "2. Cluster the rationales into named themes; for each theme give a count of how "
            "many panelists invoked it (higher- vs lower-probability panelists separately if the "
            "theme skews).\n"
            "3. List the points of genuine disagreement — where panelists rely on incompatible "
            "readings or assumptions, not merely different emphasis.\n"
            "4. List authorities cited by two or more panelists, and authorities cited by only one.\n"
            "Organize only. Do not evaluate, resolve, or weight any argument."
        )
        c = backend.complete(prompt, model=self.judge(cfg), system=FACILITATOR_SYSTEM,
                             fallback_model=self.judge_fallback(cfg),
                             label=f"delphi-facilitate-r{round_no}")
        return c.text

    def _persistent_disagreement(self, final: list[dict], stats: dict, backend, cfg) -> str:
        payload = json.dumps([{k: p.get(k) for k in
                               ("probability", "position_summary", "rationales",
                                "biggest_uncertainty", "response_to_panel")} for p in
                              sorted(final, key=lambda p: p["probability"])], indent=2)
        prompt = (
            f"Final-round anonymized Delphi answers:\n\n```json\n{payload}\n```\n\n"
            f"Statistics: {_stats_block(stats)}\n\n"
            "The panel has finished. Characterize what disagreement PERSISTS after mutual "
            "feedback: (a) the crux each side rests on, (b) whether the split traces to a "
            "genuinely unsettled legal question, a factual assumption, or differing risk "
            "tolerance, and (c) what a court or new fact would have to resolve. Persistent "
            "disagreement is signal — report it precisely; do not adjudicate it."
        )
        c = backend.complete(prompt, model=self.judge(cfg), system=FACILITATOR_SYSTEM,
                             fallback_model=self.judge_fallback(cfg),
                             label="delphi-persistent")
        return c.text

    def _render(self, q, rounds, summaries, stats_by_round, persistent) -> str:
        out = [f"### Operation\n{self.blurb}\n",
               f"**Proposition assessed:** \"{q.proposition}\"\n",
               "### Probability trajectory\n",
               "| Round | Median | Mean | Std dev | Range | IQR |",
               "|---|---|---|---|---|---|"]
        for i, s in enumerate(stats_by_round, 1):
            out.append(f"| {i} | {s['median']} | {s['mean']} | {s['stdev']} "
                       f"| {s['min']}–{s['max']} | {s['iqr']} |")
        out.append("\n### Final panel positions (anonymized)\n")
        out.append("| # | Prob. | Conf. | Position | Biggest uncertainty |")
        out.append("|---|---|---|---|---|")
        for i, p in enumerate(sorted(rounds[-1], key=lambda p: p["probability"]), 1):
            out.append(f"| {i} | {p['probability']} | {p.get('confidence', '?')} "
                       f"| {p.get('position_summary', '').replace('|', '/')} "
                       f"| {p.get('biggest_uncertainty', '').replace('|', '/')} |")
        out.append("\n### Persistent disagreement (signal, not noise)\n")
        out.append(persistent)
        for i, s in enumerate(summaries, 1):
            out.append(f"\n<details><summary>Facilitator summary after round {i}</summary>\n\n{s}\n\n</details>")
        out.append("\n<details><summary>Full final-round panelist answers</summary>\n")
        for i, p in enumerate(sorted(rounds[-1], key=lambda p: p["probability"]), 1):
            out.append(f"\n**Panelist {i}** — {p['probability']}/100, {p.get('confidence')}\n")
            for r in p.get("rationales", []):
                out.append(f"- {r}")
            if p.get("response_to_panel"):
                out.append(f"- *Response to panel:* {p['response_to_panel']}")
            if p.get("authorities"):
                out.append(f"- *Authorities:* {'; '.join(str(a) for a in p['authorities'])}")
        out.append("\n</details>")
        return "\n".join(out) + "\n"
