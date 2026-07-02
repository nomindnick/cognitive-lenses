# FINDINGS — the honest verdict

*Written 2026-07-01 after the full instrumented run: 5 contested CA public-agency hypotheticals × (6-lens panel + naive Sonnet pass + naive Fable pass), scored by a Fable coverage judge instructed to be adversarial toward the panel; leave-one-out ablation on q1; live FPPC cite-check on q3. 180 model calls, ~$67 API-equivalent, ~30 min wall-clock per question. All numbers below come from `runs/*/metrics.json`; quotes from the judge outputs.*

## TL;DR

1. **The panel reliably beats its own worker model.** On all five questions, the Sonnet-worker panel out-covered naive Sonnet on substantive angles (138 vs 113 total; +2 to +8 per question). Structure buys a mid-tier model real coverage.
2. **The panel roughly ties a naive frontier pass** (138 vs 139 for naive Fable) — but they win *different territory*. The panel wins risk-surface, adversarial symmetry, and investigation/negotiation moves; Fable wins black-letter depth, statutory machinery, and deal design. A Sonnet panel is not a substitute for a strong doctrinal pass; it is a different instrument.
3. **The panel found 26 substantive angles that BOTH naive passes missed** — mostly from premortem and structural. That's the exploration payoff: ~5 genuinely new lines of inquiry per question that a lawyer reading two strong memos would still not have.
4. **The night's best result is the guardrail, not the panel.** On q3, naive Fable confidently asserted § 1091.5(a)(6) as the case-deciding safe harbor; the coverage judge (also Fable) crowned it "the fact that decides the case." The FPPC cite-check found the subsection's scope is at best contested — and surfaced the actually-on-point authority (FPPC 15-059-1090, § 1091(b)(1) remote interest) which cuts the other way *and* undercuts the panel's own Delphi median. The flag-then-verify architecture out-performed every model in the pipeline on the single highest-stakes citation of the night.
5. **Word-salad exists and is quantifiable but modest**: judge-rated noise was 0–8% of panel angles per question. The real inefficiency is redundancy, not nonsense (≈70% of Delphi's final-round text is restatement; q2's verdict: "a poor signal-to-text ratio").
6. **Would I run it again?** As a *pre-work risk-and-angle sweep feeding a verification list*, yes — that's what it's actually good at. As a replacement for one strong analytical pass, no, and it was never supposed to be that.

## The coverage experiment

Angle extraction and classification by a Fable judge told to count an angle only where a document actually develops it, and to be adversarial toward the panel's volume.

| Q | Substantive angles (total) | Panel | Naive Sonnet | Naive Fable | Panel-only | Panel missed | Panel noise |
|---|---|---|---|---|---|---|---|
| q1 Brown Act / AI intermediary | 38 | 31 | 23 | 32 | 4 | 7 | 0% |
| q2 Prop 218 surcharge | 32 | 29 | 23 | 26 | 5 | 3 | 5% |
| q3 § 1090 / spouse's nonprofit | 27 | 21 | 19 | 23 | 1 | 6 | 8% |
| q4 CPRA / Signal chats | 34 | 27 | 25 | 26 | 7 | 7 | 2% |
| q5 Surplus Land / $1 deal | 43 | 30 | 23 | 32 | 9 | 13 | 8% |
| **Total** | **174** | **138** | **113** | **139** | **26** | **36** | — |

Reading the pattern honestly:

- The panel's edge is **largest where the question is novel or sprawls across doctrines** (q4, q5, q1 — no controlling authority, many interacting exposures) and **smallest where the question is doctrine-dense** (q3 — conflicts law, where the analysis is a catalog of statutory exceptions the worker model simply doesn't hold as reliably as Fable does). Procedure cannot conjure missing knowledge.
- The 36 substantive angles the panel *missed* are not all Fable's doctrinal depth: the q3 judge caught the aggregator failing to retain angles Sonnet's own naive pass had produced ("the panel failed to retain angles its own worker model produced unstructured"). **Aggregation is a lossy bottleneck** — the neutral aggregator compresses ~30k words of lens output and drops real material. This is the clearest tool defect the experiment exposed (see "What I'd change").
- Judge verdicts, condensed: q1 "a risk-spotting supplement to a strong single-pass memo, not a replacement"; q2 "yes, but narrowly and at a poor signal-to-text ratio"; q3 "no — not in the way a lawyer would pay for"; q4 "partial yes… the panel's real, payable edge is adversarial symmetry — both naive passes wrote one-sided 'city loses' memos"; q5 "the panel earned its keep on strategic and operational risk but lost on law."

## The verification loop (q3) — the finding that matters most

The chain of events, verbatim from the artifacts:

1. Panel lenses cited the § 1091/1091.5 exception catalog but **queued it as a must-verify item** rather than asserting how it resolves ("numbering to be confirmed"; "cite unverified" appears *inside* lens outputs — the preamble discipline held).
2. **Naive Fable asserted** § 1091.5(a)(6) as a hire-date safe harbor making the spouse's salary a noninterest — presented as dispositive.
3. **The Fable coverage judge endorsed it** as "the § 1091.5(a)(6) hire-date safe harbor (the fact that decides the case)" and scored the panel down for not having it.
4. The **verifier adapter** (me + the real FPPC corpus) found: every located application of (a)(6) involves a spouse employed by a *public agency*; the on-point nonprofit-spouse case — FPPC 15-059-1090, a councilmember whose spouse was salaried Development Director of a 501(c)(3) seeking city funds — was analyzed under the **§ 1091(b)(1) remote interest** instead: the member "stands in the shoes of his spouse," and with disclosure + noting + abstention *the city may contract*. So the "decisive" cite is at best contested, and the actually-verified authority also refutes the Delphi panel's 75-median position that the contract is void even with recusal.

Every layer of pure model opinion — worker panel, frontier baseline, frontier judge — was wrong or miscalibrated about the decisive point in some direction. The only component that produced reliable movement was the **flag → check against primary sources → annotate** loop. Design principle 3 wasn't a disclaimer; it was the value.

(Also caught: one lens characterized *Fraser-Yamor* as a spouse's-employer case — it isn't — while itself flagging the cite unverified. Verified solid: *Thomson v. Call*'s no-cure-by-abstention holding, *Stigall*, *Honig*, § 1091.5(a)(8) for the uncompensated board seat. Full table in `runs/q3/report.html`.)

## Which lenses pull their weight

Two instruments, which disagree in an instructive way.

**Coverage-judge attribution** (which lenses sourced substantive angles; "unique" = no other lens and no naive pass had it), summed over 5 questions:

| Lens | Substantive angles | Unique-substantive | Judge-rated noise |
|---|---|---|---|
| dialectic | 94 | 2 | 1 |
| tetlock | 91 | 0 | 4 |
| premortem | 77 | **5** | 1 |
| steelman | 69 | 1 | 0 |
| delphi | 57 | 0 | 3 |
| structural | 45 | 2 | 4 |

**Leave-one-out ablation** (q1): removing *any* lens was rated a significant loss, but of different kinds — remove premortem and you lose the action items (litigation hold *before* disabling the AI feature, fee-release before voluntary cure); remove structural and you lose the only incentive/game-theoretic layer (who's actually driving the suit, what the DA letter is for); remove tetlock and "the report reads ~2:1 toward violation while the full aggregate is near even odds" (calibration!); remove steelman and the entire contest-instead-of-cure strategic branch disappears; remove dialectic and contested questions silently become consensus; remove delphi and the risk quantification and its authority-conflict flags go.

Reconciled: **premortem and structural are the unique-coverage engines** (7 of 12 attributed panel-unique angles; they generate what memo-shaped analysis structurally omits). **Dialectic and tetlock are volume workhorses** that mostly overlap with what strong naive passes also find — but they carry the *calibration and contest-preservation* function the ablation exposes. **Delphi contributed zero unique angles** — its value is not coverage at all (see below). **Steelman overlaps heavily with dialectic's antithesis** and is the first candidate to cut if trimming; the ablation's counter-argument is that it was the only lens producing a *developed strategic alternative* on q1.

## Delphi, featured lens: worth it, but not for the number

- **Panelists are correlated samples, not independent experts.** Round-1 IQRs were already 2–10 points wide on a 100-point scale. Seven samples of one model with varied analytical entry points is not seven judgments; the classic Delphi rationale (aggregate diverse private information) mostly doesn't apply.
- **Convergence is therefore cheap and fast** — every question stopped at 2 rounds under the stall/settle rule; IQR collapsed (10→3 on q3, 3→1 on q5). Movement between rounds was small and mostly toward the median, i.e., consensus-seeking, not information exchange.
- **The medians drifted high.** All five propositions were "the conduct/measure would be held unlawful" framings, and the panel put every one of them at 65–82. On the one question with a checkable answer (q3), FPPC practice says the conservative reading was wrong. I read this as the known LLM conservatism/agreeableness bias showing through — treat Delphi probabilities as *relative* signals between questions, never as calibrated risk numbers for advice.
- **What actually earned the tokens:** the facilitator's *persistent-disagreement* analysis. On q1 it isolated the volitional-"use"-vs-objective-reading fork, showed the 62–63 vs 66–68 clusters rest on incompatible readings of the same text, tagged the split as "genuinely unsettled legal question," and specified what would resolve it. That is a crux-finding machine, and the aggregator built on it. If I kept only part of Delphi, I'd keep round 1 + facilitation and drop the revision rounds.

## Where it degrades into word-salad

Named honestly, with the judge's receipts:

- **Redundancy is the dominant failure, not nonsense.** ~70% of Delphi's final-round text is restatement of round 1; q2's overall verdict was "a poor signal-to-text ratio." Panel artifacts are ~30k words/question before aggregation; nobody should read them raw (that's what the aggregate is for).
- **Tetlock attaches pseudo-probabilities to non-propositions.** "P=8" on *what are the city's procedural deadlines* is a category error — the decompose step doesn't force its sub-questions to be propositions, so some estimates are decoration. Real procedure bug; fixable in the decompose schema.
- **Steelman/antithesis double-counting**: the judge repeatedly noted the pair "invites double-count" in apparent coverage.
- **One degenerate schema submission** made it into q1's round-1 Delphi stats (a panelist emitted a literal "test … for schema validation purposes" answer that validated; the revision round self-healed it). I added an application-level sanity gate + retry mid-run; later questions ran clean. Lesson: schema validation ≠ content validation.
- **Structural has the worst signal-to-noise ratio of the set** (45 substantive / 4 noise, and its q3 output was mostly generic) — but when it hits (q1's vendor-exposure and fee-economics analysis, q5's intent-escalation dynamics), it's material nothing else produces. High-variance lens.

## Economics

~$13.50 API-equivalent and ~30 wall-minutes per question (36 calls: 31 Sonnet, 5 Fable; ~450k output tokens). Per *panel-only substantive angle*, that's roughly $2.60 of API-equivalent spend — cheap against lawyer time if even one angle matters, expensive if you only needed the doctrinal answer (in which case: one Fable pass + a citator).

## What I'd change first

1. **Fix the aggregation bottleneck** — the aggregator provably drops angles the lenses had. Give it a second pass with an explicit completeness check against a bullet-inventory of lens outputs, or aggregate hierarchically.
2. **Make verification a pipeline stage, not an annex.** The q3 loop was the tool's best moment and it was manual. A verifier adapter interface exists (`verification.json`); wire a citator/corpus API in as a first-class stage that runs on the aggregate's "Must verify" list before the report renders.
3. **Force tetlock sub-questions to be propositions** (schema-level), killing the pseudo-probability noise.
4. **Trim**: steelman → optional (dialectic's antithesis covers ~80% of it); Delphi → round 1 + facilitation by default.
5. **Add the missing lens**: a pure "statutory-machinery inventory" operation (deadlines, procedures, penalty provisions) — most of what naive Fable beat the panel with was exactly this, and it's a procedure, not a persona.

## Bottom line

The hypothesis mostly survives contact: **an exploration harness on a mid-tier model buys real, measurable coverage a strong single pass doesn't have — but its durable value is the discipline layer (independent generation, provenance, flag-then-verify), not the panel's opinions.** The tool as specced — angles to pursue and things to verify, never conclusions to rely on — turns out to be not just the safe framing but the accurate one: on the one occasion the night produced a checkable "decisive" legal conclusion, every model-opinion layer got it wrong and the verification loop got it right.
