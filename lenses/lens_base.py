"""Lens protocol. A lens is a cognitive OPERATION with its own call graph —
not a persona. Each lens returns a readable markdown report plus structured
meta; it never sees any other lens's output."""
from __future__ import annotations

from dataclasses import dataclass, field

from .common import Question


@dataclass
class LensResult:
    lens: str
    markdown: str
    meta: dict = field(default_factory=dict)


class Lens:
    name = "base"
    blurb = ""  # one-line description of the operation, used in reports

    def __init__(self, params: dict | None = None):
        self.params = params or {}

    def worker(self, cfg: dict) -> str:
        return cfg.get("worker_model", "claude-sonnet-5")

    def judge(self, cfg: dict) -> str:
        return cfg.get("judge_model", "claude-fable-5")

    def judge_fallback(self, cfg: dict) -> str | None:
        return cfg.get("fallback_judge_model")

    def run(self, q: Question, backend, cfg: dict) -> LensResult:
        raise NotImplementedError
