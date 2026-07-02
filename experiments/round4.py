#!/usr/bin/env python3
"""Round 4 driver: local-model panels (Ollama) vs the Claude panels.

The variant runs (runs/<qid>-ollama-hybrid, runs/<qid>-ollama-local) score
themselves within-run, but config D's own coverage judge is a local model —
its counts are not comparable to Fable-judged runs. This driver applies the
round-2 protocol: re-judge each variant's aggregate with the SAME Fable judge
against the SAME frozen round-1 naive baselines, so the only thing that varies
is the panel document.

  rejudge <qid>   re-score each ollama variant aggregate (cached; Fable judge,
                  frozen runs/<qid>/baselines)
  summary <qid>   table: Claude v4 reference (round 3 hierarchical) vs the
                  re-judged variants

Caveat carried from round 2: the judge re-enumerates the angle universe on
every call, with measured count jitter of ±2-8. Compare patterns, not digits.

Usage: python3 experiments/round4.py rejudge q1
       python3 experiments/round4.py summary q1
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lenses.backend import make_backend  # noqa: E402
from lenses.common import RUNS_DIR, Question, load_config, log, read_json, write_json  # noqa: E402
from lenses.judge import compute_metrics, run_judge  # noqa: E402

VARIANTS = ("hybrid", "local")

HEADLINE = ["panel_substantive", "naive_sonnet_substantive", "naive_fable_substantive",
            "panel_only_substantive", "missed_by_panel_substantive", "panel_noise_rate"]


def rejudge(qid: str, cfg: dict) -> None:
    q = Question.load(qid)
    frozen = RUNS_DIR / q.id / "baselines"
    naive_s = (frozen / "naive_sonnet.md").read_text(encoding="utf-8")
    naive_f = (frozen / "naive_fable.md").read_text(encoding="utf-8")

    for variant in VARIANTS:
        vd = RUNS_DIR / f"{q.id}-ollama-{variant}"
        agg = vd / "aggregate.md"
        if not agg.exists():
            log(f"[{qid}] {variant}: no aggregate at {agg} — skipped")
            continue
        r4 = vd / "round4"
        jp = r4 / "judge_fable.json"
        if jp.exists():
            log(f"[{qid}] {variant}: cached")
            continue
        backend = make_backend(cfg, r4 / "calls")
        data = run_judge(q, agg.read_text(encoding="utf-8"), naive_s, naive_f,
                         backend, cfg)
        write_json(jp, data)
        write_json(r4 / "metrics_fable.json", compute_metrics(data))
        log(f"[{qid}] {variant}: re-judged (Fable, frozen round-1 baselines)")


def summary(qid: str) -> None:
    rows = {}
    v4 = RUNS_DIR / qid / "round3" / "metrics_v4.json"
    if v4.exists():
        rows["claude-v4"] = read_json(v4)
    for variant in VARIANTS:
        for tag, path in (
                (f"{variant}", RUNS_DIR / f"{qid}-ollama-{variant}" / "round4" / "metrics_fable.json"),
                (f"{variant}-withinrun", RUNS_DIR / f"{qid}-ollama-{variant}" / "metrics.json")):
            if path.exists():
                rows[tag] = read_json(path)
    print(f"== {qid}  (rejudged rows share judge + frozen baselines; "
          "withinrun rows do not — shown for drift only)")
    for tag, m in rows.items():
        print(f"  {tag:18s} panel={m.get('panel_substantive'):3} "
              f"sonnet={m.get('naive_sonnet_substantive'):3} "
              f"fable={m.get('naive_fable_substantive'):3} "
              f"panel-only={m.get('panel_only_substantive'):3} "
              f"missed={m.get('missed_by_panel_substantive'):3} "
              f"noise={m.get('panel_noise_rate')}")
    out = RUNS_DIR / f"{qid}-round4-summary.json"
    write_json(out, rows)
    log(f"summary -> {out}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["rejudge", "summary"])
    ap.add_argument("qid")
    ap.add_argument("--config", default=None)
    args = ap.parse_args()
    if args.cmd == "rejudge":
        rejudge(args.qid, load_config(args.config))
    else:
        summary(args.qid)
    return 0


if __name__ == "__main__":
    sys.exit(main())
