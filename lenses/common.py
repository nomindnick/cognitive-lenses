"""Shared types, question/config loading, prompt fragments, small utils."""
from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_DIR = ROOT / "questions"
RUNS_DIR = ROOT / "runs"
CONFIG_DIR = ROOT / "config"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data) -> None:
    write_text(path, json.dumps(data, indent=2, ensure_ascii=False))


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass
class Question:
    id: str
    title: str
    area: str
    facts: str
    question: str
    why_contested: str
    proposition: str
    featured: bool = False

    @classmethod
    def load(cls, qid: str) -> "Question":
        matches = sorted(QUESTIONS_DIR.glob(f"{qid}*.json"))
        if not matches:
            raise FileNotFoundError(f"no question file matching {qid!r} in {QUESTIONS_DIR}")
        data = read_json(matches[0])
        return cls(**data)

    def block(self) -> str:
        """Canonical markdown block handed to every worker."""
        return (
            f"## Facts (invented hypothetical — no real parties)\n\n{self.facts}\n\n"
            f"## The question\n\n{self.question}\n"
        )


def all_question_ids() -> list[str]:
    return sorted(p.stem.split("-")[0] for p in QUESTIONS_DIR.glob("q*.json"))


def load_config(path: str | None = None) -> dict:
    p = Path(path) if path else CONFIG_DIR / "default.json"
    return read_json(p)


# Given to every worker call, in every lens. Defines the ground rules of the
# pipeline; each lens appends its own operation on top of this.
WORKER_PREAMBLE = """\
You are performing one specific cognitive operation as an isolated component of a \
legal-exploration pipeline. You never see the other components' outputs, and nobody \
sees yours until a separate neutral aggregation step. Ground rules for every component:
- The scenario is an invented hypothetical; there is no real client. Your output goes \
to a licensed California attorney who will do the actual legal reasoning. You generate \
angles to pursue and things to verify — not advice to be relied on.
- Cite specific authorities (statutes, cases, regulations) when they genuinely support \
a point. Every citation is automatically flagged UNVERIFIED for human checking, so cite \
what you believe is correct, but never fabricate quotations or pinpoint holdings you are \
unsure of. When unsure, write "verify whether X holds Y" instead of asserting it.
- Perform ONLY the operation described below. Do not produce a general-purpose legal memo."""

UNVERIFIED_BANNER = (
    "> **⚠️ Exploration output — angles, not answers.** This tool surfaces the argument "
    "space; it does not state the law. **Every authority cited anywhere below is UNVERIFIED** "
    "unless explicitly marked verified by a human or a verifier adapter. Assume citations may "
    "be wrong, mischaracterized, or invented until checked."
)
