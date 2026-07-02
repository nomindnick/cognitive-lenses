# cognitive-lenses

An exploration layer for hard legal questions. It runs a configurable panel of
independent **cognitive operations** ("lenses") — a Delphi panel, forecasting-style
decomposition, dialectic, a pre-mortem, a steelman, a structural/incentives
analysis — over one question, then a **neutral aggregator** organizes the results
into an argument map and a hand-back for a human lawyer.

**It is not a chatbot and not a legal-answer engine.** It generates angles to
pursue and things to verify, never conclusions to rely on. Every authority any
component cites is flagged **UNVERIFIED** by a deterministic extractor.

See **[SPEC.md](SPEC.md)** for the design (and the three non-negotiable
principles), **[FINDINGS.md](FINDINGS.md)** for the honest verdict from the
instrumented experiment, and **[runs/index.html](runs/index.html)** for the
sample outputs on five invented California public-agency hypotheticals.

## Quick start

Requires Python 3.10+ (stdlib only) and the [Claude Code](https://claude.com/claude-code)
CLI logged in (each model call is a fresh `claude -p` process — no API key needed).

```bash
python3 -m lenses selftest         # exercise the whole pipeline offline, no tokens
python3 -m lenses run q1           # run one question end-to-end
python3 -m lenses run all          # run every question in questions/
python3 -m lenses report           # rebuild reports + runs/index.html from artifacts
python3 -m lenses ablate q1        # leave-one-out lens ablation (reuses lens outputs)
```

Runs are idempotent: existing artifacts are reused, so a crashed run resumes
where it stopped (`--force` redoes everything). Every model call is audited to
`runs/<qid>/calls/*.json` with full prompt, response, usage, and cost.

## Add a question

Drop a JSON file in `questions/` with `id`, `title`, `area`, `facts`,
`question`, `why_contested`, and a crisp single-sentence `proposition` for the
Delphi panel to put a probability on.

## Add / drop / tune lenses

Edit `config/default.json` (`lenses` maps lens name → params; delete a key to
drop a lens). To add a new lens, subclass `Lens` in a `lenses/lens_*.py` file,
implement `run()` as a *procedure* (its own call graph — not a persona prompt),
and register it in `lenses/registry.py`.

Models are configured there too: `worker_model` does all generation,
`judge_model` (with `fallback_judge_model`) does facilitation, aggregation, and
scoring only. The experiment in FINDINGS.md ran Sonnet 5 workers under a
Fable 5 judge.

## Layout

```
lenses/          the package — backend.py is the model seam (ClaudeCLIBackend / MockBackend)
config/          lens set + models
questions/       five invented CA public-agency hypotheticals (public-safe)
runs/<qid>/      lenses/*.md, baselines/, aggregate.md, judge.json, metrics.json, report.html
```
