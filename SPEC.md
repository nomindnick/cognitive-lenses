# cognitive-lenses — SPEC

**One-line:** An exploration layer for hard legal questions that runs a configurable panel of independent *cognitive operations* ("lenses") over the question, neutrally aggregates the results into an argument map, and hands back to a human lawyer — instrumented to measure whether the panel actually out-covers a naive single pass.

**Status:** Built autonomously overnight 2026-07-01. Read `FINDINGS.md` for the honest verdict.

---

## What this is (and is not)

LLMs give cheap, fast breadth — you can run many genuinely different reasoning procedures for near-free — but they carry sycophancy, anchoring, and confident confabulation. This tool borrows non-advocacy truth-finding methods (Delphi panels, forecasting-tournament decomposition, dialectic, pre-mortems, steelmanning, structural analysis) as an *exploration layer*: it surfaces the argument space and blind spots, then hands back to a human's legal reasoning.

- **Not a chatbot.** It's a batch pipeline: question in, argument map + verification list out.
- **Not a legal-answer engine.** It generates *angles to pursue and things to verify*, never conclusions to rely on.
- **Public-safe.** All test questions are invented hypotheticals; no client facts.

## Non-negotiable design principles

1. **Lenses are cognitive operations, not personas.** We never instantiate "a sociologist." We ask for the operation directly ("run a pre-mortem," "apply a structural/incentives analysis"). Each lens is a genuinely different *procedure* — different call graph, different inputs, different output schema — not one model in different costumes.
2. **Independent generation → neutral aggregation.** Each lens (and each Delphi panelist) runs in a fresh, isolated model context — a separate `claude -p` process — and never sees other lenses' outputs. Lenses do not debate or collaborate; that would trade away the uncorrelated-error benefit. A separate neutral aggregator (a stronger model, prompted to organize, not advocate) de-dupes, maps convergence/conflict, and prioritizes. Generation is advocacy; aggregation must not be.
3. **Guardrail the known weakness.** Every specific authority a lens cites (statute, regulation, case, FPPC opinion) is extracted deterministically (regex, not a model) and flagged **UNVERIFIED — check before relying**. The tool never asserts black-letter law as settled. The failure mode we defend against is confident mischaracterization on top of plausible-looking cites. An optional *verifier adapter* can upgrade specific flags (this run: a manual cite-check of FPPC-adjacent authorities against the real FPPC opinion database, recorded in the report).

## Model policy (per Nick's instruction)

- **Workers (all lens/panelist/baseline generation):** Claude Sonnet 5 (`claude-sonnet-5`).
- **Judges (Delphi facilitation, aggregation, coverage scoring):** Claude Fable 5 (`claude-fable-5`), fallback Opus 4.8.
- Part of the experiment: *can a structured harness make a mid-tier model out-cover both its own naive pass and a frontier model's naive pass?* So each question also gets a naive **Fable** single pass as a reference ceiling (evaluation infrastructure, not a worker).

## The lens set (each a distinct procedure; configurable in `config/default.json`)

| Lens | Procedure (call graph) |
|---|---|
| **delphi** (featured) | N=7 independent panelists → each returns structured JSON: probability (0–100) that a defined *proposition* holds, confidence, top rationales, authorities, biggest uncertainty. Code computes anonymized stats (median/IQR/spread); a judge-model facilitator clusters rationale themes without attribution. Each panelist then independently revises seeing only (their own prior answer + the anonymized summary). Up to 3 rounds, early stop on convergence. Output: trajectory, final spread, and **persistent disagreements reported as signal, not noise**. |
| **tetlock** | Decompose the question into sub-questions/cruxes ("what would have to be true") → each crux estimated in a *fresh context* that sees only that crux + facts → recompose call names the decisive crux. |
| **dialectic** | Strongest thesis (fresh) → strongest *steelmanned* antithesis (sees thesis; must be endorsable by its best proponent) → synthesis that resolves the tension or names it irreducible + what evidence would resolve it. |
| **premortem** | Fresh call establishes the position the agency would most likely adopt → second call: "18 months later it failed badly — write the retrospective," enumerate distinct failure causes ranked by likelihood × severity. |
| **steelman** | Fresh call identifies which pole conventional analysis disfavors → second fresh call constructs that disfavored position to pass an ideological Turing test. |
| **structural** | Single call, *forbidden* from doctrinal argument: actors, incentives, power, repeat-player dynamics, enforcement economics, who wins under ambiguity. Surfaces non-doctrinal drivers. |

## The neutral aggregator (not a lens)

Reads all lens outputs (labeled), then produces — with **mandatory per-node provenance** (which lens(es) support each point):

- **(a) Argument map** — nodes marked `CONVERGENT` (multiple independent lenses), `CONTESTED` (lenses conflict), or `UNIQUE` (one lens only).
- **(b) Blind spots** — angles only some lenses caught.
- **(c) For the lawyer** — hand-back: angles worth developing, what must be verified (with the UNVERIFIED flags), what looks decisive.
- **(d) Noise audit** — anything that reads as structured word-salad, called out honestly.

It organizes and prioritizes; it adds no new advocacy. Provenance tags are what make the ablation cheap (see below).

## The experiment (instrumented, not vibes)

Per question:
1. Run the full lens panel → aggregate.
2. Run **naive-sonnet** (same worker model, "just give the best analysis you can") and **naive-fable** (frontier ceiling).
3. A judge-model **coverage scorer** extracts discrete angles from each artifact and classifies every angle: found by panel / naive-sonnet / naive-fable (any subset), with panel angles attributed to source lenses (via aggregator provenance) and quality-rated `substantive | marginal | noise`.
4. Code computes the metrics: coverage counts, panel-only substantive angles (the payoff), panel noise rate (the cost), unique-angle counts per lens (the ablation).

**Hypothesis under test:** the exploration layer buys *coverage* a strong single pass doesn't. **Ablation:** per-lens unique-substantive-angle counts across all questions, plus a leave-one-out re-aggregation on the featured question.

## Test questions (invented; California public-agency; chosen to be genuinely contested)

1. **q1-brown-act** *(featured — full ablation)* — Council members serially consulting a shared AI assistant with persistent cross-user memory about a pending zoning appeal: serial-meeting problem under Gov. Code § 54952.2(b)?
2. **q2-prop218** — Drought surcharge on top water-rate tiers funding low-income conservation rebates: cost-of-service problem under Art. XIII D § 6 / *Capistrano*?
3. **q3-conflicts** — Councilmember whose spouse directs programs at a nonprofit seeking city homelessness funds, where the member sits on the nonprofit board as city liaison: § 1090 / Political Reform Act? *(Gets the live FPPC cite-check.)*
4. **q4-cpra** — Councilmembers coordinating with a franchise bidder via auto-deleting Signal chats on personal phones: CPRA / *City of San Jose* / retention?
5. **q5-surplus-land** — Nominal-price conveyance of surplus city land to a private developer for mixed-income housing with a local-preference covenant: Surplus Land Act / gift clause / fair-housing tension?

Each question file defines the facts, the question, why it's contested, and a clean **proposition** for Delphi probability elicitation.

## Architecture

Python 3.14, stdlib only (no install step). The model seam is one protocol:

```
ModelBackend.complete(prompt, *, model, system, schema, label) -> Completion
```

- `ClaudeCLIBackend` — spawns `claude -p --model <m> --tools "" --no-session-persistence --output-format json [--json-schema ...]` per call. Fresh process = structural independence. Captures usage/cost per call into an audit log (`runs/<q>/calls/*.json`).
- `MockBackend` — deterministic canned outputs for the offline selftest.

```
lenses/            the package (backend, lens_*, aggregate, baseline, judge, citations, runner, report, cli)
config/default.json  lens set, panel size, rounds, models, concurrency — add/drop lenses here
questions/*.json   the five hypotheticals
runs/<qid>/        lenses/*.md|json, baselines/, aggregate.md, judge.json, metrics.json, report.html, calls/
```

CLI: `python3 -m lenses run <qid|all>` · `report` (index.html + cross-question metrics) · `ablate q1` · `selftest` (mock backend, no tokens). Stages are idempotent — existing outputs are skipped unless `--force`.

## Deliverables

1. The runnable tool (this repo).
2. `runs/` — full per-lens raw outputs + aggregated reports for all five questions, as readable HTML + markdown.
3. `FINDINGS.md` — honest verdict: does the panel beat the naive passes on coverage; which lenses pull their weight; where it degrades into word-salad.
