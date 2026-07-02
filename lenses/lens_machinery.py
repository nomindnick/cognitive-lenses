"""Statutory-machinery inventory: the lens Round 1 proved was missing.

The coverage judge found most of naive Fable's edge over the panel was
procedural/statutory machinery — deadlines, vehicles, penalty and fee
provisions, safe harbors. Inventorying that machinery is a cognitive
operation (exhaustive checklist construction), not a persona, and it is
deliberately forbidden from arguing the merits."""
from __future__ import annotations

from .common import Question, WORKER_PREAMBLE
from .lens_base import Lens, LensResult

MACHINERY_SYSTEM = WORKER_PREAMBLE + """

Operation: STATUTORY MACHINERY INVENTORY. Do not argue the merits, predict outcomes,
or weigh positions — other components do that. Build the checklist of procedural and
statutory machinery that governs how this dispute actually runs, complete enough that
a lawyer could calendar and verify from it alone:
- Clocks and deadlines: response windows, cure periods, limitations periods, notice
  periods — with the provision that sets each and the trigger event that starts it.
- Procedural vehicles available to EACH side (demands, writs, validation actions,
  declaratory/injunctive relief, administrative complaints, audits, referrals), with
  prerequisites, exhaustion requirements, and standing limits.
- Penalty, fee, and cost provisions: who can recover what, under which section,
  against whom, and any offramps (unconditional commitments, safe harbors, settlement
  or cure mechanisms built into the statutes).
- Agencies and forums with jurisdiction, and what each can and cannot do.
- Insurance, indemnity, and who-pays questions if they are statutorily shaped.
For every item: the authority (it will be flagged UNVERIFIED for human checking) and
what specifically must be confirmed before relying on it. Organize by forum/track.
One line per item; completeness over analysis. End with the three items whose
deadlines or preconditions are most easily missed."""


class MachineryLens(Lens):
    name = "machinery"
    blurb = ("Exhaustive inventory of the statutory/procedural machinery — clocks, "
             "vehicles, penalties, fee provisions, safe harbors — with no merits analysis.")

    def run(self, q: Question, backend, cfg: dict) -> LensResult:
        text = backend.complete(
            f"{q.block()}\nInventory the statutory machinery, per your operation.",
            model=self.worker(cfg), system=MACHINERY_SYSTEM, label="machinery").text
        md = f"### Operation\n{self.blurb}\n\n{text}\n"
        return LensResult(self.name, md)
