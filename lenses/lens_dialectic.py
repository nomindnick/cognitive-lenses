"""Dialectic: strongest thesis → strongest STEELMANNED antithesis → synthesis
that resolves the tension or names it irreducible. Three sequential calls; the
antithesis sees the thesis by design (that is the procedure), nothing else."""
from __future__ import annotations

from .common import Question, WORKER_PREAMBLE
from .lens_base import Lens, LensResult

THESIS_SYSTEM = WORKER_PREAMBLE + """

Operation: THESIS. Construct the strongest affirmative case for the stated
proposition — the best version a first-rate advocate would actually file, with
its strongest authorities and its most honest treatment of weak points. Do not
argue the other side; that happens elsewhere."""

ANTITHESIS_SYSTEM = WORKER_PREAMBLE + """

Operation: ANTITHESIS (steelmanned). You are given a thesis. Construct the
strongest opposing case — one the best advocate AGAINST the proposition would
endorse as a fair statement of their position. Strawmanning is failure: engage
the thesis's strongest points, not its weakest. Where the thesis is right about
something, concede it and show why you still win."""

SYNTHESIS_SYSTEM = WORKER_PREAMBLE + """

Operation: SYNTHESIS. Given a thesis and its steelmanned antithesis, do exactly
one of two things and say which: (a) resolve the tension — show a framework,
distinction, or reading under which both sides' valid points survive and the
question has an answer; or (b) declare the tension IRREDUCIBLE — identify the
precise crux on which they part ways, and what (new fact, higher-court ruling,
legislative fix) would resolve it. Do not split the difference for comfort."""


class DialecticLens(Lens):
    name = "dialectic"
    blurb = ("Strongest thesis → strongest steelmanned antithesis → synthesis that "
             "resolves the tension or names it irreducible.")

    def run(self, q: Question, backend, cfg: dict) -> LensResult:
        worker = self.worker(cfg)
        prop = f"## Proposition\n\n\"{q.proposition}\"\n"
        thesis = backend.complete(
            f"{q.block()}\n{prop}\nConstruct the strongest case FOR the proposition.",
            model=worker, system=THESIS_SYSTEM, label="dialectic-thesis").text
        antithesis = backend.complete(
            f"{q.block()}\n{prop}\n## The thesis you must answer\n\n{thesis}\n\n"
            "Construct the strongest steelmanned case AGAINST the proposition.",
            model=worker, system=ANTITHESIS_SYSTEM, label="dialectic-antithesis").text
        synthesis = backend.complete(
            f"{q.block()}\n{prop}\n## Thesis\n\n{thesis}\n\n## Antithesis\n\n{antithesis}\n\n"
            "Synthesize: resolve or declare irreducible.",
            model=worker, system=SYNTHESIS_SYSTEM, label="dialectic-synthesis").text

        md = (f"### Operation\n{self.blurb}\n\n"
              f"### Thesis — strongest case FOR\n\n{thesis}\n\n"
              f"### Antithesis — strongest steelmanned case AGAINST\n\n{antithesis}\n\n"
              f"### Synthesis\n\n{synthesis}\n")
        return LensResult(self.name, md)
