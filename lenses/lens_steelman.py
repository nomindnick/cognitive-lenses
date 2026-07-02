"""Steelman / ideological Turing test: identify which pole conventional
analysis disfavors, then — in a fresh context that never sees the conventional
reasoning — construct the disfavored position so well its best proponent would
endorse it."""
from __future__ import annotations

from .common import Question, WORKER_PREAMBLE
from .lens_base import Lens, LensResult

POLES_SCHEMA = {
    "type": "object",
    "properties": {
        "conventional_view": {"type": "string",
                              "description": "the conclusion most California public-agency lawyers would reach, in 1-3 sentences"},
        "disfavored_position": {"type": "string",
                                "description": "the opposing position that deserves serious construction, stated neutrally in 1-3 sentences, WITHOUT any supporting reasoning"},
    },
    "required": ["conventional_view", "disfavored_position"],
}

POLES_SYSTEM = WORKER_PREAMBLE + """

Operation: identify the poles only. State (1) the conclusion most California
public-agency lawyers would reach here, and (2) the opposing position that
deserves construction. State the disfavored position neutrally and WITHOUT
supporting reasoning — someone else will build the case and must not be
anchored by yours."""

STEELMAN_SYSTEM = WORKER_PREAMBLE + """

Operation: IDEOLOGICAL TURING TEST. You are given a position, and only the
position. Construct the case for it so faithfully and strongly that its best
actual proponent would sign it as a fair statement of their view. Requirements:
- Lead with its three strongest moves (doctrine, policy, or facts), fully developed.
- Include what its proponents genuinely worry about and how they answer those worries
  (a steelman that hides the position's known weaknesses fails the Turing test).
- No tells: do not signal distance, do not hedge on the position's behalf, do not
  conclude by evaluating it. Write as its advocate would."""


class SteelmanLens(Lens):
    name = "steelman"
    blurb = ("Identify the position conventional analysis disfavors, then construct it "
             "so its best proponent would endorse it (ideological Turing test).")

    def run(self, q: Question, backend, cfg: dict) -> LensResult:
        worker = self.worker(cfg)
        poles = backend.complete(
            f"{q.block()}\nIdentify the conventional view and the disfavored position.",
            model=worker, system=POLES_SYSTEM, schema=POLES_SCHEMA,
            label="steelman-poles").data
        steel = backend.complete(
            f"{q.block()}\n## The position to construct\n\n{poles['disfavored_position']}\n\n"
            "Construct its strongest case, to ideological-Turing-test standard.",
            model=worker, system=STEELMAN_SYSTEM, label="steelman-construct").text
        md = (f"### Operation\n{self.blurb}\n\n"
              f"### Conventional view (for orientation)\n\n> {poles['conventional_view']}\n\n"
              f"### Disfavored position\n\n> {poles['disfavored_position']}\n\n"
              f"### The steelman\n\n{steel}\n")
        return LensResult(self.name, md, meta=poles)
