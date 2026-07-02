"""Leave-one-out ablation: for each lens, re-run the neutral aggregation with
that lens's output removed, then have a judge diff the full aggregate against
the ablated one. Reuses the stored lens outputs — no worker calls, only
aggregator/judge calls. Answers: which lenses pull their weight?"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from .aggregate import run_aggregate
from .backend import make_backend
from .common import RUNS_DIR, Question, log, write_json, write_text

DIFF_SCHEMA = {
    "type": "object",
    "properties": {
        "lost_points": {"type": "array", "items": {"type": "string"},
                        "description": "substantive content present in FULL but absent or materially weakened in ABLATED; empty if none"},
        "materiality": {"type": "string", "enum": ["none", "minor", "significant"]},
        "note": {"type": "string"},
    },
    "required": ["lost_points", "materiality", "note"],
}

DIFF_SYSTEM = """You compare two aggregated reports from the same legal-exploration pipeline: \
FULL (all lenses) and ABLATED (one lens removed before aggregation). Identify substantive \
content — angles, cruxes, warnings, verification items — present in FULL but absent or \
materially weakened in ABLATED. Ignore rewording, reordering, and formatting. Judge \
materiality from a practicing lawyer's perspective: 'significant' means a lawyer would \
plausibly act differently without the lost content."""


def run_ablation(qid: str, cfg: dict, force: bool = False) -> dict:
    q = Question.load(qid)
    rd = RUNS_DIR / q.id
    lens_dir = rd / "lenses"
    lens_mds = {p.stem: p.read_text(encoding="utf-8") for p in sorted(lens_dir.glob("*.md"))}
    if len(lens_mds) < 2:
        raise RuntimeError(f"[{qid}] need >=2 lens outputs to ablate")
    full = (rd / "aggregate.md").read_text(encoding="utf-8")
    backend = make_backend(cfg, rd / "calls")
    abl_dir = rd / "ablation"

    def one(name: str) -> tuple[str, dict]:
        loo_path = abl_dir / f"wo-{name}.md"
        if loo_path.exists() and not force:
            loo = loo_path.read_text(encoding="utf-8")
        else:
            loo = run_aggregate(q, {k: v for k, v in lens_mds.items() if k != name},
                                backend, cfg, label=f"aggregate-wo-{name}")
            write_text(loo_path, loo)
        log(f"[{qid}] ablation aggregate without {name}: done")
        c = backend.complete(
            f"# FULL\n\n{full}\n\n---\n\n# ABLATED (lens `{name}` removed)\n\n{loo}\n\n"
            "What substantive content did removing this lens cost?",
            model=cfg.get("judge_model", "claude-fable-5"), system=DIFF_SYSTEM,
            schema=DIFF_SCHEMA, fallback_model=cfg.get("fallback_judge_model"),
            label=f"ablation-diff-{name}")
        return name, c.data

    with ThreadPoolExecutor(max_workers=len(lens_mds)) as ex:
        results = dict(ex.map(one, sorted(lens_mds)))
    write_json(abl_dir / "ablation.json", results)
    log(f"[{qid}] ablation complete -> {abl_dir / 'ablation.json'}")
    return results
