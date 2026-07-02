"""CLI: python3 -m lenses <run|report|ablate|selftest> ..."""
from __future__ import annotations

import argparse
import sys

from .common import RUNS_DIR, all_question_ids, load_config, log


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="lenses", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("run", help="run question(s) end-to-end")
    p.add_argument("qids", nargs="+", help="question ids (e.g. q1 q3) or 'all'")
    p.add_argument("--force", action="store_true", help="redo stages even if artifacts exist")
    p.add_argument("--mock", action="store_true", help="use the offline MockBackend")
    p.add_argument("--config", default=None)

    p = sub.add_parser("report", help="rebuild question reports + index from artifacts")
    p.add_argument("qids", nargs="*", help="default: all")

    p = sub.add_parser("ablate", help="leave-one-out ablation for a question")
    p.add_argument("qid")
    p.add_argument("--force", action="store_true")
    p.add_argument("--config", default=None)

    p = sub.add_parser("verify", help="auto cite-check flagged authorities via search-enabled workers")
    p.add_argument("qid")
    p.add_argument("--max", type=int, default=14, help="max authority groups to check")
    p.add_argument("--config", default=None)

    sub.add_parser("selftest", help="exercise the full pipeline offline (mock backend)")

    args = ap.parse_args(argv)

    if args.cmd == "run":
        from .runner import run_question
        cfg = load_config(args.config)
        qids = all_question_ids() if args.qids == ["all"] else args.qids
        failed = []
        for qid in qids:
            try:
                run_question(qid, cfg, force=args.force, mock=args.mock)
            except Exception as e:
                log(f"[{qid}] RUN FAILED: {e}")
                failed.append(qid)
        from .report import build_index
        build_index(all_question_ids())
        return 1 if failed else 0

    if args.cmd == "report":
        from .report import build_index, build_question_report
        qids = args.qids or all_question_ids()
        for qid in qids:
            if (RUNS_DIR / qid).exists():
                build_question_report(qid)
                log(f"rebuilt {qid}")
        build_index(all_question_ids())
        return 0

    if args.cmd == "ablate":
        from .ablate import run_ablation
        cfg = load_config(args.config)
        run_ablation(args.qid, cfg, force=args.force)
        from .report import build_index
        build_index(all_question_ids())
        return 0

    if args.cmd == "verify":
        from .backend import make_backend
        from .report import build_question_report
        from .verify import run_verify
        cfg = load_config(args.config)
        backend = make_backend(cfg, RUNS_DIR / args.qid / "verify-calls")
        run_verify(args.qid, cfg, backend, max_targets=args.max)
        build_question_report(args.qid)
        return 0

    if args.cmd == "selftest":
        return selftest()
    return 2


def selftest() -> int:
    """Full pipeline against the MockBackend into runs/_selftest — no tokens."""
    import shutil

    from .runner import run_question
    cfg = load_config()
    cfg["lenses"] = {**cfg["lenses"], "delphi": {"panelists": 3, "max_rounds": 2}}
    rd = RUNS_DIR / "_selftest"
    shutil.rmtree(rd, ignore_errors=True)  # stale artifacts would mask failures
    run_question("q1", cfg, force=True, mock=True, run_dir=rd)
    expected = ["lenses/delphi.md", "lenses/tetlock.md", "lenses/dialectic.md",
                "lenses/premortem.md", "lenses/steelman.md", "lenses/structural.md",
                "baselines/naive_sonnet.md", "baselines/naive_fable.md",
                "aggregate.md", "judge.json", "metrics.json", "report.html"]
    missing = [p for p in expected if not (rd / p).exists()]
    if missing:
        log(f"SELFTEST FAIL — missing artifacts: {missing}")
        return 1
    log("SELFTEST PASS — full pipeline produced all artifacts offline")
    return 0


if __name__ == "__main__":
    sys.exit(main())
