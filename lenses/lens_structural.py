"""Structural lens: analyze the situation as a system of incentives, power,
and institutional structure — doctrinal argument is forbidden. Surfaces the
non-doctrinal drivers a doctrinal analysis would miss."""
from __future__ import annotations

from .common import Question, WORKER_PREAMBLE
from .lens_base import Lens, LensResult

STRUCTURAL_SYSTEM = WORKER_PREAMBLE + """

Operation: STRUCTURAL ANALYSIS. Doctrinal analysis is FORBIDDEN in this
component — do not analyze what the law says or how a court would rule. Analyze
the situation as a system:
- Actors and their actual interests (including the ones nobody states aloud).
- Who bears the costs and who captures the benefits of each possible resolution.
- Repeat players vs one-shotters; who can wait, who can appeal, who can lobby.
- Enforcement economics: who would sue, whether they can afford to, what they win,
  who never gets sued and why.
- Institutional capacity and incentives of the enforcers/regulators themselves.
- What behavior each candidate rule would actually produce once actors adapt to it.
- Where the formal rules and the incentive structure point in different directions.
End with a section titled "Non-doctrinal drivers a doctrinal analysis would miss"."""


class StructuralLens(Lens):
    name = "structural"
    blurb = ("Incentives / power / institutional structure instead of doctrine; "
             "surfaces the non-doctrinal drivers.")

    def run(self, q: Question, backend, cfg: dict) -> LensResult:
        text = backend.complete(
            f"{q.block()}\nAnalyze this structurally, per your operation.",
            model=self.worker(cfg), system=STRUCTURAL_SYSTEM, label="structural").text
        md = f"### Operation\n{self.blurb}\n\n{text}\n"
        return LensResult(self.name, md)
