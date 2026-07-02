"""Pre-mortem / red-team: establish the position the agency would most likely
adopt (fresh call), then assume it FAILED BADLY 18 months later and write the
retrospective. Surfaces blind spots that forward-looking analysis misses."""
from __future__ import annotations

from .common import Question, WORKER_PREAMBLE
from .lens_base import Lens, LensResult

POSITION_SCHEMA = {
    "type": "object",
    "properties": {
        "likely_position": {"type": "string",
                            "description": "the position/course of action a cautious public-agency counsel would most likely recommend, in 2-4 sentences"},
    },
    "required": ["likely_position"],
}

POSITION_SYSTEM = WORKER_PREAMBLE + """

Operation: state, in a few sentences, the position or course of action the
agency's counsel would MOST LIKELY adopt here. Not the best position — the
likely one. No analysis beyond what is needed to state it."""

PREMORTEM_SYSTEM = WORKER_PREAMBLE + """

Operation: PRE-MORTEM. You are told the position the agency adopted. Assume it
is 18 months later and the position FAILED BADLY — pick whichever failure modes
are most plausible (litigation loss, writ, enforcement action, penalties,
front-page scandal, operational collapse, political revolt) and write the
retrospective as if the failure already happened. Enumerate 5–8 DISTINCT causes
of failure. For each: **what went wrong**, **the early warning sign that was
missed**, **likelihood (H/M/L)** and **severity (H/M/L)**. Rank by likelihood ×
severity. Do not argue the position was right; it failed — explain how."""


class PremortemLens(Lens):
    name = "premortem"
    blurb = ("Assume the likely position was adopted and failed badly 18 months later; "
             "enumerate why. Surfaces blind spots.")

    def run(self, q: Question, backend, cfg: dict) -> LensResult:
        worker = self.worker(cfg)
        pos = backend.complete(
            f"{q.block()}\nWhat position would the agency's counsel most likely adopt?",
            model=worker, system=POSITION_SYSTEM, schema=POSITION_SCHEMA,
            label="premortem-position").data["likely_position"]
        retro = backend.complete(
            f"{q.block()}\n## The position the agency adopted\n\n{pos}\n\n"
            "It failed badly. Write the retrospective.",
            model=worker, system=PREMORTEM_SYSTEM, label="premortem-retro").text
        md = (f"### Operation\n{self.blurb}\n\n"
              f"### The assumed position\n\n> {pos}\n\n"
              f"### The retrospective (assumed failure)\n\n{retro}\n")
        return LensResult(self.name, md, meta={"likely_position": pos})
