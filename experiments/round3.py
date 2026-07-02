#!/usr/bin/env python3
"""Round 3 experiment driver.

  informed-delphi <qid>  fresh Delphi round-1 with the verified-authority annex;
                         compare distribution to the original rounds
  impact <qid>           judge memo: which panel claims change given verification
  hier <qid>             v4 = hierarchical aggregate (group -> merge -> completeness),
                         re-judged; compare to v2/v3
  summary                print v2/v3/v4 + delphi-informed comparisons

Usage: python3 experiments/round3.py <cmd> <qid>
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lenses.aggregate import run_aggregate_hierarchical  # noqa: E402
from lenses.backend import make_backend  # noqa: E402
from lenses.common import (RUNS_DIR, Question, load_config, log, read_json,  # noqa: E402
                           write_json, write_text)
from lenses.judge import compute_metrics, run_judge  # noqa: E402
from lenses.lens_delphi import (ENTRY_POINTS, PANELIST_SCHEMA, PANELIST_SYSTEM,  # noqa: E402
                                _ask_validated, _stats)

IMPACT_SYSTEM = """You assess the impact of a live cite-check on a legal-exploration \
report. Given the aggregated report and the verification results (statuses per authority), \
write a short memo for the lawyer: (1) which report claims are STRENGTHENED (their load-bearing \
authority verified), (2) which are WEAKENED or must be re-argued (authority mischaracterized, \
not found, or contested), (3) which verification results change what looks decisive, and \
(4) the one-line bottom line on whether the report's lean survives verification. Cite the \
report's own provenance tags. Add no new legal analysis beyond connecting verification \
results to report claims."""


def _verification_block(rd: Path) -> str:
    v = read_json(rd / "verification.json")
    lines = ["| Authority | Status | Note |", "|---|---|---|"]
    for k, d in sorted(v.items()):
        if k == "_meta":
            continue
        lines.append(f"| {k} | {d['status']} | {d['note'][:300].replace('|', '/')} |")
    return "\n".join(lines)


def informed_delphi(qid: str, cfg: dict) -> None:
    q = Question.load(qid)
    rd = RUNS_DIR / qid
    r3 = rd / "round3"
    backend = make_backend(cfg, r3 / "calls")
    ver = _verification_block(rd)
    n = 7
    prompt = (
        f"{q.block()}\n## Proposition to assess\n\n\"{q.proposition}\"\n\n"
        f"## Verified-authority annex\n\nA live cite-check (existence, citation form, "
        f"characterization — not good-law review) of the authorities most cited in prior "
        f"analysis of this question returned:\n\n{ver}\n\n"
        "Estimate the probability (0–100) that the proposition is correct, with your "
        "reasoning. rationales = your independent load-bearing reasons, one sentence each. "
        "authorities = authorities you actually rely on. biggest_uncertainty = the single "
        "thing you are least sure of. Treat the annex as evidence about the authorities, "
        "not as anyone's opinion on the answer."
    )

    def ask(i: int) -> dict:
        entry = f"\n\nAnalytical starting point for you: {ENTRY_POINTS[i % len(ENTRY_POINTS)]}"
        return _ask_validated(backend, prompt + entry,
                              model=cfg.get("worker_model", "claude-sonnet-5"),
                              schema=PANELIST_SCHEMA, label=f"delphi-informed-p{i + 1}")

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=n) as ex:
        panel = list(ex.map(ask, range(n)))
    stats = _stats([float(p["probability"]) for p in panel])
    baseline = read_json(rd / "lenses" / "delphi.meta.json")["stats_by_round"]
    out = {"stats_informed": stats, "stats_baseline_rounds": baseline, "panel": panel}
    write_json(r3 / "delphi_informed.json", out)
    log(f"[{qid}] informed delphi: median {stats['median']} (baseline rounds: "
        + " -> ".join(str(s['median']) for s in baseline) + ")")


def impact(qid: str, cfg: dict) -> None:
    q = Question.load(qid)
    rd = RUNS_DIR / qid
    r3 = rd / "round3"
    backend = make_backend(cfg, r3 / "calls")
    agg_path = rd / "round2" / "aggregate_v2.md"
    if not agg_path.exists():
        agg_path = rd / "aggregate.md"
    memo = backend.complete(
        f"{q.block()}\n\n# The aggregated report\n\n{agg_path.read_text(encoding='utf-8')}\n\n"
        f"---\n\n# Verification results\n\n{_verification_block(rd)}\n\n"
        "Write the impact memo per your instructions.",
        model=cfg.get("judge_model", "claude-fable-5"), system=IMPACT_SYSTEM,
        fallback_model=cfg.get("fallback_judge_model"), label="verification-impact").text
    write_text(r3 / "verification_impact.md", memo)
    log(f"[{qid}] verification impact memo written")


def hier(qid: str, cfg: dict) -> None:
    q = Question.load(qid)
    rd = RUNS_DIR / qid
    r3 = rd / "round3"
    backend = make_backend(cfg, r3 / "calls")
    lens_mds = {p.stem: p.read_text(encoding="utf-8")
                for p in sorted((rd / "lenses").glob("*.md"))}
    mach = rd / "round2" / "machinery.md"
    if mach.exists():
        lens_mds["machinery"] = mach.read_text(encoding="utf-8")
    v4_path = r3 / "aggregate_v4.md"
    if v4_path.exists():
        v4 = v4_path.read_text(encoding="utf-8")
    else:
        v4 = run_aggregate_hierarchical(q, lens_mds, backend, cfg, label="aggregate-v4")
        write_text(v4_path, v4)
    log(f"[{qid}] aggregate v4 (hierarchical): done")
    jp = r3 / "judge_v4.json"
    if not jp.exists():
        naive_s = (rd / "baselines" / "naive_sonnet.md").read_text(encoding="utf-8")
        naive_f = (rd / "baselines" / "naive_fable.md").read_text(encoding="utf-8")
        data = run_judge(q, v4, naive_s, naive_f, backend, cfg)
        write_json(jp, data)
        write_json(r3 / "metrics_v4.json", compute_metrics(data))
    log(f"[{qid}] judge v4: done")


HEADLINE = ["panel_substantive", "naive_sonnet_substantive", "naive_fable_substantive",
            "panel_only_substantive", "missed_by_panel_substantive", "panel_noise_rate"]


def summary() -> None:
    for qdir in sorted(RUNS_DIR.glob("q[0-9]")):
        rows = {}
        for tag, path in (("v2", qdir / "round2" / "metrics_v2.json"),
                          ("v3", qdir / "round2" / "metrics_v3.json"),
                          ("v4", qdir / "round3" / "metrics_v4.json")):
            if path.exists():
                m = read_json(path)
                rows[tag] = {k: m.get(k) for k in HEADLINE}
        di = qdir / "round3" / "delphi_informed.json"
        if rows or di.exists():
            print(f"== {qdir.name}")
            for tag, r in rows.items():
                print(f"  {tag} panel={r['panel_substantive']} fable={r['naive_fable_substantive']} "
                      f"panel-only={r['panel_only_substantive']} missed={r['missed_by_panel_substantive']} "
                      f"noise={r['panel_noise_rate']}")
            if di.exists():
                d = read_json(di)
                print(f"  delphi informed: median {d['stats_informed']['median']} iqr "
                      f"{d['stats_informed']['iqr']} | baseline rounds: "
                      + " -> ".join(str(s['median']) for s in d["stats_baseline_rounds"]))


def main() -> int:
    cmd = sys.argv[1]
    if cmd == "summary":
        summary()
        return 0
    cfg = load_config()
    qid = sys.argv[2]
    {"informed-delphi": informed_delphi, "impact": impact, "hier": hier}[cmd](qid, cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
