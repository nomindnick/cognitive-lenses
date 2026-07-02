"""Naive baselines: the control arm of the experiment. One unstructured pass
("just give the best analysis you can") on the worker model, and one on the
judge-tier model as a reference ceiling. Deliberately no scaffolding."""
from __future__ import annotations

from .common import Question

NAIVE_SYSTEM = ("You are assisting a California public-agency lawyer with a hard question. "
                "The scenario is an invented hypothetical; there is no real client.")


def run_naive(q: Question, backend, model: str, label: str) -> str:
    c = backend.complete(
        f"{q.block()}\nGive the best, most complete legal analysis you can.",
        model=model, system=NAIVE_SYSTEM, label=label,
    )
    return c.text
