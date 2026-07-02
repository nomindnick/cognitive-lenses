#!/usr/bin/env python3
"""Round 2 experiment driver.

Per question, against the frozen Round-1 artifacts:
  v1 = round-1 aggregate (single-pass, 6 lenses)   [already on disk]
  v2 = two-pass aggregate, same 6 lens outputs      -> isolates the aggregation fix
  v3 = two-pass aggregate, 6 lenses + machinery     -> isolates the new lens
Each variant is re-scored by the same coverage judge against the same naive
baselines. Optional extras: --opus-judge (re-score v1 with Opus 4.8 for judge
robustness), --delphi-trim (round-1-only Delphi vs the full run, diff-judged).

Usage: python3 experiments/round2.py q1 [q2 ...] [--opus-judge] [--delphi-trim]
       python3 experiments/round2.py summary
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lenses.aggregate import run_aggregate  # noqa: E402
from lenses.backend import make_backend  # noqa: E402
from lenses.common import (RUNS_DIR, Question, load_config, log, read_json,  # noqa: E402
                           write_json, write_text)
from lenses.judge import compute_metrics, run_judge  # noqa: E402
from lenses.lens_delphi import DelphiLens  # noqa: E402
from lenses.lens_machinery import MachineryLens  # noqa: E402

DIFF_SYSTEM = """You compare two versions of the same Delphi lens report: FULL (multi-round \
with independent revision) and R1ONLY (single round plus facilitation, no revision rounds). \
Identify what the revision rounds actually added that a lawyer would act on — new arguments, \
changed cruxes, materially different probabilities or disagreement structure. Ignore \
restatement, polish, and probability drift under 5 points. Judge from a practicing lawyer's \
perspective and answer plainly whether the revision rounds were worth ~2x the panel cost."""


def _cached(path: Path, make):
    if path.exists():
        return path.read_text(encoding="utf-8")
    text = make()
    write_text(path, text)
    return text


def run_q(qid: str, cfg: dict, opus_judge: bool, delphi_trim: bool) -> None:
    q = Question.load(qid)
    rd = RUNS_DIR / q.id
    r2 = rd / "round2"
    backend = make_backend(cfg, r2 / "calls")
    lens_mds = {p.stem: p.read_text(encoding="utf-8")
                for p in sorted((rd / "lenses").glob("*.md"))}
    naive_s = (rd / "baselines" / "naive_sonnet.md").read_text(encoding="utf-8")
    naive_f = (rd / "baselines" / "naive_fable.md").read_text(encoding="utf-8")

    def judged(tag: str, panel_md: str, judge_cfg: dict) -> None:
        jp = r2 / f"judge_{tag}.json"
        if jp.exists():
            log(f"[{qid}] judge {tag}: cached")
            return
        data = run_judge(q, panel_md, naive_s, naive_f, backend, judge_cfg)
        write_json(jp, data)
        write_json(r2 / f"metrics_{tag}.json", compute_metrics(data))
        log(f"[{qid}] judge {tag}: done")

    # v2 — aggregation fix only
    v2 = _cached(r2 / "aggregate_v2.md",
                 lambda: run_aggregate(q, lens_mds, backend, cfg,
                                       label="aggregate-v2", two_pass=True))
    log(f"[{qid}] aggregate v2: done")
    judged("v2", v2, cfg)

    # machinery lens, then v3 — fix + new lens
    mach = _cached(r2 / "machinery.md",
                   lambda: MachineryLens().run(q, backend, cfg).markdown)
    log(f"[{qid}] machinery lens: done")
    v3 = _cached(r2 / "aggregate_v3.md",
                 lambda: run_aggregate(q, {**lens_mds, "machinery": mach}, backend, cfg,
                                       label="aggregate-v3", two_pass=True))
    log(f"[{qid}] aggregate v3: done")
    judged("v3", v3, cfg)

    if opus_judge:
        v1 = (rd / "aggregate.md").read_text(encoding="utf-8")
        opus_cfg = {**cfg, "judge_model": "claude-opus-4-8",
                    "fallback_judge_model": cfg.get("judge_model", "claude-fable-5")}
        judged("v1_opus", v1, opus_cfg)

    if delphi_trim:
        r1only = _cached(
            r2 / "delphi_r1only.md",
            lambda: DelphiLens({**cfg["lenses"].get("delphi", {}), "max_rounds": 1})
                    .run(q, backend, cfg).markdown)
        log(f"[{qid}] delphi r1-only: done")
        dp = r2 / "delphi_trim_diff.md"
        if not dp.exists():
            full = (rd / "lenses" / "delphi.md").read_text(encoding="utf-8")
            diff = backend.complete(
                f"{q.block()}\n\n# FULL (multi-round)\n\n{full}\n\n---\n\n"
                f"# R1ONLY (one round + facilitation)\n\n{r1only}\n\n"
                "What did the revision rounds add? Worth the cost?",
                model=cfg.get("judge_model", "claude-fable-5"), system=DIFF_SYSTEM,
                fallback_model=cfg.get("fallback_judge_model"),
                label="delphi-trim-diff").text
            write_text(dp, diff)
        log(f"[{qid}] delphi trim diff: done")
    log(f"[{qid}] round2 complete")


HEADLINE = ["panel_substantive", "naive_sonnet_substantive", "naive_fable_substantive",
            "panel_only_substantive", "missed_by_panel_substantive", "panel_noise_rate"]


def summary() -> None:
    out = {}
    for qdir in sorted(RUNS_DIR.glob("q[0-9]")):
        qid = qdir.name
        row = {}
        m1 = qdir / "metrics.json"
        if m1.exists():
            row["v1"] = {k: read_json(m1).get(k) for k in HEADLINE}
        for tag in ("v2", "v3", "v1_opus"):
            mp = qdir / "round2" / f"metrics_{tag}.json"
            if mp.exists():
                m = read_json(mp)
                row[tag] = {k: m.get(k) for k in HEADLINE}
                if tag == "v3":
                    row["v3_machinery_per_lens"] = m.get("per_lens", {}).get("machinery")
        out[qid] = row
    write_json(RUNS_DIR / "round2-summary.json", out)
    for qid, row in out.items():
        print(f"== {qid}")
        for tag in ("v1", "v2", "v3", "v1_opus"):
            if tag in row:
                r = row[tag]
                print(f"  {tag:8s} panel={r['panel_substantive']:3} "
                      f"sonnet={r['naive_sonnet_substantive']:3} "
                      f"fable={r['naive_fable_substantive']:3} "
                      f"panel-only={r['panel_only_substantive']:3} "
                      f"missed={r['missed_by_panel_substantive']:3} "
                      f"noise={r['panel_noise_rate']}")
        if row.get("v3_machinery_per_lens"):
            print(f"  machinery attribution: {row['v3_machinery_per_lens']}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("qids", nargs="+")
    ap.add_argument("--opus-judge", action="store_true")
    ap.add_argument("--delphi-trim", action="store_true")
    ap.add_argument("--config", default=None)
    args = ap.parse_args()
    if args.qids == ["summary"]:
        summary()
        return 0
    cfg = load_config(args.config)
    for qid in args.qids:
        run_q(qid, cfg, args.opus_judge, args.delphi_trim)
    return 0


if __name__ == "__main__":
    sys.exit(main())
