"""Orchestration: run one question end-to-end.

Stages (each idempotent — existing artifacts are reused unless --force):
  1. all lenses + both naive baselines, in parallel (backend caps concurrency)
  2. deterministic citation extraction
  3. neutral aggregation (judge model)
  4. coverage judge + metrics
  5. report rendering
A lens failure is recorded and the run continues without it.
"""
from __future__ import annotations

import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .aggregate import run_aggregate
from .backend import make_backend
from .baseline import run_naive
from .common import RUNS_DIR, Question, log, write_json, write_text
from .judge import compute_metrics, run_judge
from .lens_base import LensResult
from .registry import build_lenses
from . import report


def run_question(qid: str, cfg: dict, force: bool = False, mock: bool = False,
                 run_dir: Path | None = None) -> Path:
    q = Question.load(qid)
    rd = Path(run_dir) if run_dir else RUNS_DIR / q.id
    backend = make_backend(cfg, rd / "calls", mock=mock)
    t0 = time.time()
    log(f"[{q.id}] start: {q.title}")

    lens_dir, base_dir, err_dir = rd / "lenses", rd / "baselines", rd / "errors"
    lens_mds: dict[str, str] = {}
    naive: dict[str, str] = {}
    futures = {}

    lenses = build_lenses(cfg)
    with ThreadPoolExecutor(max_workers=len(lenses) + 2) as ex:
        for name, lens in lenses.items():
            f = lens_dir / f"{name}.md"
            if f.exists() and not force:
                lens_mds[name] = f.read_text(encoding="utf-8")
                log(f"[{q.id}] lens {name}: cached")
            else:
                futures[name] = ex.submit(lens.run, q, backend, cfg)
        for label, model_key in (("naive_sonnet", "worker_model"),
                                 ("naive_fable", "judge_model")):
            f = base_dir / f"{label}.md"
            if f.exists() and not force:
                naive[label] = f.read_text(encoding="utf-8")
                log(f"[{q.id}] {label}: cached")
            else:
                futures[label] = ex.submit(run_naive, q, backend, cfg[model_key], label)

        for name, fut in futures.items():
            try:
                res = fut.result()
            except Exception as e:  # keep the overnight run alive
                write_text(err_dir / f"{name}.txt", f"{e}\n\n{traceback.format_exc()}")
                log(f"[{q.id}] {name} FAILED: {e}")
                continue
            if isinstance(res, LensResult):
                lens_mds[name] = res.markdown
                write_text(lens_dir / f"{name}.md", res.markdown)
                if res.meta:
                    write_json(lens_dir / f"{name}.meta.json", res.meta)
            else:
                naive[name] = res
                write_text(base_dir / f"{name}.md", res)
            log(f"[{q.id}] {name}: done")

    if not lens_mds:
        raise RuntimeError(f"[{q.id}] every lens failed; aborting")

    agg_path = rd / "aggregate.md"
    if agg_path.exists() and not force:
        aggregate = agg_path.read_text(encoding="utf-8")
        log(f"[{q.id}] aggregate: cached")
    else:
        aggregate = run_aggregate(q, lens_mds, backend, cfg)
        write_text(agg_path, aggregate)
        log(f"[{q.id}] aggregate: done")

    judge_path = rd / "judge.json"
    judge_data = None
    if naive.get("naive_sonnet") and naive.get("naive_fable"):
        if judge_path.exists() and not force:
            from .common import read_json
            judge_data = read_json(judge_path)
            log(f"[{q.id}] judge: cached")
        else:
            judge_data = run_judge(q, aggregate, naive["naive_sonnet"],
                                   naive["naive_fable"], backend, cfg)
            write_json(judge_path, judge_data)
            log(f"[{q.id}] judge: done")
    else:
        log(f"[{q.id}] judge: skipped (missing baselines)")

    if judge_data:
        metrics = compute_metrics(judge_data)
        metrics["wall_s"] = round(time.time() - t0, 1)
        metrics["run_stats"] = report.call_stats(rd / "calls")
        write_json(rd / "metrics.json", metrics)

    out = report.build_question_report(q.id, run_dir=rd)
    log(f"[{q.id}] report: {out}")
    return out
