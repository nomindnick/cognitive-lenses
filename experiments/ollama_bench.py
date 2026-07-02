#!/usr/bin/env python3
"""Local-model feasibility benchmark (pre-step for the ollama-panel experiment).

Per candidate model, two probes built from the REAL q1 Delphi round-1 panelist
prompt (same construction as DelphiLens.run, entry point #1):
  speed   free-form, num_predict-capped: measures load time, prompt tok/s,
          decode tok/s — the numbers that decide overnight-run feasibility.
  schema  grammar-constrained against PANELIST_SCHEMA, then the lens's own
          _sane() gate: measures whether the model can actually be a panelist.

retries=0 throughout: a benchmark that retries past failures reports the
pipeline's resilience, not the model's first-attempt reliability. Failures are
recorded, not masked. ONE exception: a warmup call retries on Ollama's
server-side load timeout (observed: cold-loading 65GB at ~140MB/s blows the
default 5-minute OLLAMA_LOAD_TIMEOUT; the page cache from the failed attempt
makes the retry succeed). That is disk/server infrastructure, not model
quality — it is measured and reported as cold-load time, not as a failure.
Models run serially and are unloaded between candidates (two 70GB+ models do
not co-fit next to their KV caches).

Full call transcripts land in experiments/ollama-bench/calls/ via the standard
audit log; the table goes to experiments/ollama-bench/results.md.

Usage: python3 experiments/ollama_bench.py [model ...]
       (default: the six candidates named in the round-4 plan)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lenses.backend import AuditLog, BackendError, OllamaBackend  # noqa: E402
from lenses.common import Question, log, write_json, write_text  # noqa: E402
from lenses.lens_delphi import ENTRY_POINTS, PANELIST_SCHEMA, PANELIST_SYSTEM, _sane  # noqa: E402

BENCH_DIR = Path(__file__).resolve().parent / "ollama-bench"

DEFAULT_MODELS = [
    "gpt-oss:120b",            # MoE ~5B active — predicted fastest big model
    "qwen3.5:122b",            # biggest brain on disk, MoE-or-bust
    "mistral-medium-3.5:128b", # decode rate will settle dense-vs-MoE empirically
    "gemma4:31b",              # dense mid-tier, the user's named candidate
    "qwen3.6:27b",             # dense mid-tier comparison
    "gemma4:12b",              # cheap probe: is there a floor below the floor?
]

NUM_CTX = 16384          # panelist prompts are small; keeps KV light for big models
SPEED_CAP = 700          # tokens — enough to measure decode rate, not an essay
SCHEMA_CAP = 6000        # runaway bound; thinking models burn tokens before JSON
TIMEOUT_S = 1800


def panelist_prompt(q: Question) -> str:
    """Mirror DelphiLens.run's round-1 prompt, pinned to entry point #1."""
    return (
        f"{q.block()}\n## Proposition to assess\n\n\"{q.proposition}\"\n\n"
        "Estimate the probability (0–100) that this proposition is correct, with your "
        "reasoning. rationales = your independent load-bearing reasons, one sentence each. "
        "authorities = specific authorities you are actually relying on (they will be "
        "flagged for human verification). biggest_uncertainty = the single thing you are "
        "least sure of."
        f"\n\nAnalytical starting point for you: {ENTRY_POINTS[0]}"
    )


def model_sizes() -> dict[str, str]:
    out = subprocess.run(["ollama", "list"], capture_output=True, text=True).stdout
    sizes = {}
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 4:
            sizes[parts[0]] = f"{parts[2]} {parts[3]}"
    return sizes


def unload(model: str) -> None:
    subprocess.run(["ollama", "stop", model], capture_output=True, text=True)


def unload_all() -> None:
    out = subprocess.run(["ollama", "ps"], capture_output=True, text=True).stdout
    for line in out.splitlines()[1:]:
        if line.strip():
            unload(line.split()[0])


def probe(backend: OllamaBackend, model: str, prompt: str, *, schema=None, label="") -> dict:
    t0 = time.time()
    try:
        c = backend.complete(prompt, model=model, system=PANELIST_SYSTEM,
                             schema=schema, label=label)
    except BackendError as e:
        return {"ok": False, "error": str(e)[:300], "wall_s": round(time.time() - t0, 1)}
    r = {"ok": True, "wall_s": round(time.time() - t0, 1), **c.usage}
    if schema:
        r["schema_valid"] = True  # complete() raises otherwise
        r["sane"] = _sane(c.data)
        r["probability"] = c.data.get("probability")
        r["n_authorities"] = len(c.data.get("authorities") or [])
    return r


def warmup(backend: OllamaBackend, model: str) -> dict:
    """Get the model resident, tolerating (and timing) slow cold loads."""
    t0 = time.time()
    for attempt in range(3):
        try:
            backend.complete("Say OK.", model=model, label=f"bench-{model}-warmup")
            return {"ok": True, "cold_load_s": round(time.time() - t0, 1)}
        except BackendError as e:
            if "llama-server" not in str(e):
                return {"ok": False, "error": str(e)[:300],
                        "cold_load_s": round(time.time() - t0, 1)}
            log(f"    server load timeout (attempt {attempt + 1}); "
                "retrying — page cache is warming")
    return {"ok": False, "error": "did not load within 3 server load-timeout windows",
            "cold_load_s": round(time.time() - t0, 1)}


def bench_model(model: str, q: Question, audit: AuditLog) -> dict:
    unload_all()
    prompt = panelist_prompt(q)
    mk = lambda cap: OllamaBackend(audit=audit, retries=0, num_ctx=NUM_CTX,
                                   timeout_s=TIMEOUT_S, max_parallel=1,
                                   options={"num_predict": cap})
    log(f"=== {model}: warmup (cold load)")
    warm = warmup(mk(8), model)
    log(f"    {warm}")
    if not warm["ok"]:
        return {"model": model, "warmup": warm,
                "speed": {"ok": False, "error": "warmup failed"},
                "schema": {"ok": False, "error": "warmup failed"}}
    log(f"=== {model}: speed probe (model resident)")
    speed = probe(mk(SPEED_CAP), model, prompt, label=f"bench-{model}-speed")
    speed["cold_load_s"] = warm["cold_load_s"]
    log(f"    {speed}")
    log(f"=== {model}: schema probe (PANELIST_SCHEMA, grammar-constrained)")
    schema = probe(mk(SCHEMA_CAP), model, prompt, schema=PANELIST_SCHEMA,
                   label=f"bench-{model}-schema")
    log(f"    {schema}")
    unload(model)
    return {"model": model, "warmup": warm, "speed": speed, "schema": schema}


def render(results: list[dict], sizes: dict[str, str]) -> str:
    out = [
        "# Ollama candidate benchmark",
        "",
        "Probes use the real q1 Delphi round-1 panelist prompt (entry point #1). "
        "`retries=0` for generation: failures are first-attempt failures, not "
        "exhausted retries. Cold load is measured by a warmup call that tolerates "
        "Ollama's 5-minute server load timeout (disk speed, not model quality); "
        "decode/prompt tok/s come from Ollama's own eval counters with the model "
        "resident. Schema probe is grammar-constrained (`format=PANELIST_SCHEMA`) "
        "and then gated by the lens's `_sane()`.",
        "",
        "| model | size | cold load s | prompt tok/s | decode tok/s | schema out toks | schema wall s | valid | sane | prob | notes |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        s, sc = r["speed"], r["schema"]
        if not s.get("ok"):
            why = r.get("warmup", {}).get("error") or s.get("error", "?")
            out.append(f"| {r['model']} | {sizes.get(r['model'], '?')} "
                       f"| {r.get('warmup', {}).get('cold_load_s', '—')} | — | — | — | — "
                       f"| — | — | — | FAILED: {why} |")
            continue
        notes = []
        if s.get("done_reason") == "length":
            notes.append("speed capped (expected)")
        if sc.get("ok"):
            if sc.get("done_reason") == "length":
                notes.append("schema hit token cap")
            if sc.get("thinking_chars"):
                notes.append(f"thought {sc['thinking_chars']:,} chars")
            valid, sane, prob = sc.get("schema_valid"), sc.get("sane"), sc.get("probability")
            outtoks, wall = sc.get("output_tokens"), sc.get("wall_s")
        else:
            valid = sane = prob = outtoks = wall = None
            notes.append(f"schema probe FAILED: {sc.get('error', '?')}")
        fmt = lambda v: "—" if v is None else (("✓" if v else "✗") if isinstance(v, bool) else v)
        out.append(f"| {r['model']} | {sizes.get(r['model'], '?')} | {s.get('cold_load_s', '—')} "
                   f"| {s.get('prompt_tps', '—')} | {s.get('decode_tps', '—')} "
                   f"| {fmt(outtoks)} | {fmt(wall)} | {fmt(valid)} | {fmt(sane)} "
                   f"| {fmt(prob)} | {'; '.join(notes) or '—'} |")
    out += [
        "",
        "Feasibility yardstick: a full-protocol question burned ~450k output tokens "
        "on the Claude runs. tok/s above sets the overnight-run math; `sane ✗` or a "
        "schema failure disqualifies a model as a Delphi panelist regardless of speed.",
        "",
    ]
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("models", nargs="*", default=None)
    args = ap.parse_args()
    models = args.models or DEFAULT_MODELS

    q = Question.load("q1")
    sizes = model_sizes()
    missing = [m for m in models if m not in sizes]
    if missing:
        log(f"not in `ollama list`, skipping: {missing}")
        models = [m for m in models if m in sizes]

    audit = AuditLog(BENCH_DIR / "calls")
    results = []
    for m in models:
        results.append(bench_model(m, q, audit))
        # persist incrementally: a crash on model 5 keeps models 1-4
        write_json(BENCH_DIR / "results.json", results)
        write_text(BENCH_DIR / "results.md", render(results, sizes))
    log(f"done -> {BENCH_DIR / 'results.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
