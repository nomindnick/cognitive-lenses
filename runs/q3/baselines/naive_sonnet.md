# Rio Robles / Harbor Light — § 1090, the Political Reform Act, and Common-Law Conflicts

## Bottom line up front

Recusal is necessary but **not sufficient**. Two structurally different bodies of law are in play, and they don't behave the same way:

- Under the **Political Reform Act (PRA)**, a compliant recusal by Okafor genuinely cures the problem — the rest of the council can act, full stop.
- Under **Government Code § 1090**, a financial interest held by *one member* of a contracting body can void the contract *for the whole body*, and — this is the trap in this fact pattern — **mere abstention from the vote does not fix that** unless the interest independently qualifies as a "remote interest" (§ 1091) or a "noninterest" (§ 1091.5). If it doesn't qualify, the council cannot lawfully award this contract to Harbor Light *no matter what Okafor does personally*, short of the interest itself disappearing.

On these facts, I think Okafor's board seat probably *can* be brought within a statutory noninterest, but the spouse's salary is the harder problem and probably *cannot*. That means the honest answer to "if I simply recuse, is the city safe?" is **no** — and the city attorney needs to run a real exception-by-exception analysis (with current statutory text in hand, and probably an AG opinion or FPPC advice letter) before letting this RFP proceed with Harbor Light as an eligible bidder.

---

## I. Two regimes, not one — and they don't cure the same way

§ 1090 and the PRA overlap heavily on facts but diverge sharply on remedy:

| | Gov. Code § 1090 | PRA §§ 87100–87103 |
|---|---|---|
| What's regulated | The **contract itself** — the body's power to *make* it | The official's **participation** in a governmental decision |
| Interest reaches | Direct + indirect financial interests, including via family | Direct/indirect economic interests including community-property spousal income (§ 87103(c)) and business positions (§ 87103(d)) |
| Cured by recusal? | Only if the interest is "remote" (§ 1091) or a "noninterest" (§ 1091.5) — and only with disclosure + total non-participation | Yes, generally — full recusal (disclose, don't discuss, don't vote, leave the room) lets the rest of the body act |
| Consequence of violation | Contract is **void**, not voidable (Thomson v. Call (1985) 38 Cal.3d 633) | Decision is challengeable; penalties run against the official, not automatically against the contract |
| Enforced by | DA, AG, grand jury, civil action under § 1092 — **not the FPPC** | FPPC (administrative), AG/DA (criminal misdemeanor), citizen suit (§ 91007) |
| Fairness of price/terms relevant? | No — the "no further inquiry" rule (trust-law ancestry of § 1090) makes a scrupulously fair, competitively bid contract *equally void* | Not directly relevant to the disqualification analysis |

Keep this table in mind — most of the confusion in these fact patterns comes from importing PRA intuitions ("just recuse") into § 1090 territory, where they don't automatically work.

---

## II. Government Code § 1090

### A. Is Okafor "financially interested"? Two separate interests, analyzed separately

**1. The board seat.** Uncompensated board service is not automatically outside § 1090 — "financially interested" is construed broadly to include indirect and non-cash benefits (Lexin v. Superior Court (2010) 47 Cal.4th 1050; Thomson v. Call). But § 1091.5(a) contains a specific noninterest category for **uncompensated officers/directors of nonprofit corporations**, aimed at exactly this recurring local-government pattern (councilmembers routinely sit on the boards of the nonprofits their cities fund). If Okafor takes zero compensation, per diem, or reimbursement beyond ordinary expenses, and the seat is genuinely a public-agency-designated liaison position (which the 2019 resolution supports), the board seat *by itself* likely falls within that noninterest category, meaning it would not independently bar him — **provided** he discloses it and does not use the seat to advocate for the contract. I'd want the city attorney to pull the current text of § 1091.5(a) and confirm the exact conditions (some versions of these nonprofit-officer noninterests carry conditions about funding concentration or officer role that could be tripped by Harbor Light's ~40% city-funding dependency) before relying on it. Resigning the seat is the cleaner move precisely because it removes the need to litigate whether the exception's conditions are met.

**2. The spouse's $95,000 salary.** This is the harder, more important problem, and it is analytically independent of the board seat. Under Family Code §§ 751 and 760, income earned by either spouse during marriage is community property in which both spouses hold a present, existing, equal interest. Courts and the Attorney General have long treated a spouse's financial stake in a contracting party as the *official's own* financial interest for § 1090 purposes (the same logic that drives the PRA's explicit imputation rule, discussed below, has been applied by analogy under § 1090 in a long line of AG opinions addressing officials whose spouses work for entities doing business with the agency). "Financially interested" under § 1090 does not require that the specific contract line-item pay the spouse directly — it's enough that the contract affects the entity's capacity to fund the position. Here that nexus is concrete and quantified: city contracts (including the very category being awarded) fund roughly 40% of Harbor Light's operating budget, out of which the spouse is paid. A $2.3M award (or its loss) materially affects the organization's solvency and, derivatively, the durability, growth, and continued existence of the spouse's job.

**Critical factual gap to close:** what does "Director of Programs" actually *do*? If her duties include any oversight of the programs this RFP funds, or any role in preparing Harbor Light's proposal, that converts a passive community-property interest into something close to direct involvement — strengthening the § 1090 case considerably and creating a parallel procurement-integrity problem (a competing organization effectively has an insider married to the decision-maker). This should be nailed down before anything else.

Is there a statutory escape valve for this interest? I don't have confident recall of a clean § 1091(b) remote-interest or § 1091.5(a) noninterest category that squarely covers "spouse holds a fixed, non-commission salaried position with a contracting nonprofit." There may be a narrow provision addressing a relative's fixed salary that isn't contingent on the contract and whose duties don't touch the contract — the city attorney should check current § 1091(b)/§ 1091.5(a) text closely for this. But even if such a provision exists, I doubt it rescues this fact pattern for two independent reasons: (1) the 40%-of-budget dependency undercuts any "not affected by the contract" element, and (2) exceptions to § 1090 are construed *narrowly* against the interested official (Thomson v. Call; Lexin), precisely because courts are reluctant to expand the enumerated statutory list. My working assumption, subject to that verification, is that **the spousal-salary interest is a direct, non-remote financial interest that § 1091/§ 1091.5 do not cure.**

One genuine (if partial) lever: if Okafor and spouse have — or execute — a valid interspousal transmutation agreement under Family Code § 850 et seq. characterizing her earnings as separate property, that removes the community-property basis for imputation *on a going-forward basis*. This is a recognized move in PRA practice and would meaningfully help the PRA analysis. It is a weaker fix for § 1090, though, because § 1090's "indirectly interested" concept has historically been read more functionally (does the official have a real practical stake?) than as a formal community-property title question — a transmutation agreement helps but I would not represent it as a clean cure standing alone.

### B. Does the interest reach the framework vote too, not just the award?

Yes, and this is worth stating plainly because it's often missed. "Making" a contract under § 1090 is read expansively to include the preparatory stages — drafting specifications, setting eligibility and scoring criteria, negotiating terms — not just the final award vote (Stigall v. City of Taft (1962) 58 Cal.2d 565; Millbrae Assn. for Residential Survival v. City of Millbrae (1968) 262 Cal.App.2d 222; People v. Honig (1996) 48 Cal.App.4th 289). Scoring criteria that reward, e.g., "established local track record" or "existing city relationships" would tend to advantage the 60%-win incumbent — Okafor cannot touch the framework decision any more than the award. He needs to be walled off from the *entire* process, from initial drafting forward, not just the dais vote.

### C. Does recusal cure it for the body? — the core trap

Generally, **no**, not for a member whose interest is direct (non-remote, non-noninterest). § 1090 attaches to contracts "made by [officers] in their official capacity, or by any body or board of which they are members." Courts have squarely held that an interested member's abstention does not save the contract, because the statute is prophylactic — it doesn't ask whether the interested member actually influenced the outcome, only whether the interest existed (Thomson v. Call; Stigall). The rationale courts give is that conflicts create subtle, often unconscious pressures on colleagues and staff that abstention alone can't neutralize, and that a fairness-in-fact inquiry would gut the statute's deterrent purpose — this is the "no further inquiry" rule inherited from English trust law: even a scrupulously fair, competitively priced, best-value contract is void if a body member had a disqualifying interest. "But Harbor Light might genuinely be the best bidder" is not a defense.

The *only* statutory escape hatches are:
- **§ 1091 remote interests** — if the interest fits an enumerated category, the *other* members can validly act, but only if (1) Okafor discloses the interest and it's noted in the official record *before* the contract is approved, and (2) Okafor does not participate in *any* way — no discussion, no negotiation, no informal advocacy, no vote — at any stage.
- **§ 1091.5 noninterests** — certain categories (like the uncompensated-nonprofit-officer category discussed above) are deemed not to be disqualifying interests at all, again usually conditioned on disclosure.

If neither fits, the body **cannot** lawfully make the contract with Harbor Light while Okafor sits on the council and the interest exists — regardless of recusal, walls, or good intentions. That is very likely where the spousal-salary interest lands here.

### D. Consequences of getting it wrong

- **Voidness, not voidability.** A contract made in violation of § 1090 is void ab initio (Thomson v. Call). Neither the city nor Harbor Light can enforce it.
- **No quantum meruit for the contracting party.** Thomson v. Call refused to let a party to a void § 1090 contract recover in quantum meruit for services already performed — courts have generally preserved this harsh rule to protect the deterrent effect, meaning Harbor Light could be required to return money paid without any offsetting recovery for services already delivered.
- **Disgorgement/restitution.** § 1092 provides a civil avoidance action (with a limitations period, historically four years) allowing the contract to be declared void and consideration recovered; disgorgement of amounts received under a void § 1090 contract has been ordered in subsequent litigation (see, e.g., Carson Redevelopment Agency v. Padilla (2006) 140 Cal.App.4th 929, for the general remedial principle — confirm current citation before relying on it).
- **Criminal exposure.** § 1097 makes a *willful* violation a felony, with forfeiture of office and disqualification from holding public office in California — a severe, career-ending consequence. "Willful" under People v. Honig means knowledge of the underlying facts (the spouse's job, the board seat), not knowledge that those facts violate the statute — ignorance of § 1090 itself is not a defense once the facts are known.
- **Enforcement path.** This is DA/AG/grand jury/civil territory — **not** FPPC jurisdiction. The FPPC has no authority to enforce § 1090 itself.
- **State HHAP overlay.** Because part of the $2.3M is state HHAP pass-through money, a void local procurement creates an independent risk of HCD clawback/disallowance, forcing the city to repay state funds from its general fund even apart from any private civil-law consequences. HHAP grant terms may also carry their own conflict-of-interest certification requirements that should be checked separately.

---

## III. The Political Reform Act (Gov. Code §§ 87100–87103)

Running the FPPC's standard framework (Reg. 18700 et seq.):

**1. Economic interests.** Two independent hooks:
- **Source of income (§ 87103(c)):** the spouse's $95,000 salary is community-property income imputed to Okafor under Family Code §§ 751/760 and FPPC regulations treating a spouse's earnings as the official's own for conflict purposes — this dwarfs the (currently roughly $500, periodically inflation-adjusted) materiality threshold many times over.
- **Business position (§ 87103(d)):** an official has a disqualifying interest in any entity in which they hold a director/officer/employee/management position, *regardless of compensation*. Whether "business entity" under § 82005 (defined as an entity "operated for profit") technically extends to a 501(c)(3) is a real definitional wrinkle, but FPPC guidance and practice generally treat nonprofit board positions as creating a disqualifying "business position" interest for these purposes — worth confirming, but I wouldn't lean on the technical for-profit definition to escape this; the source-of-income hook alone is dispositive regardless.

**2. Foreseeability and materiality.** Harbor Light is one of three realistic, known bidders and the historical 60% winner. Once it submits (or is expected to submit) a proposal, it is "directly involved" in the decision under FPPC materiality rules, and effects on a directly involved party are treated as presumptively material — no need to run the more elaborate indirect-effect dollar/percentage tests. That covers the **award** decision cleanly. The **framework/scoring-criteria** decision is a closer call in form (Harbor Light hasn't formally "applied" yet) but not in substance: it is reasonably foreseeable that criteria governing a $2.3M award among three known, identifiable bidders will materially affect Harbor Light's prospects, satisfying § 87103's foreseeability standard even before an application is filed.

**3. Public-generally exception.** Doesn't apply. This isn't a decision of general applicability affecting a significant segment of the public — it's a targeted allocation among three identifiable entities, one of which employs the official's spouse and seats the official on its board. The exception exists for things like utility rate-setting or general tax measures, not narrow competitive procurements.

**4. Rule of necessity (§ 87101).** Doesn't apply — the council plainly has a quorum of eligible, disinterested members without Okafor.

**5. Cure.** Unlike § 1090, a fully compliant recusal *does* cure the PRA problem for the rest of the council: Okafor must publicly identify the financial interest with enough specificity for the public to understand it, not discuss or attempt to influence the matter at any stage (including informally with staff), not vote, and — per FPPC practice under Reg. 18707 — physically leave the dais/room during discussion and vote on both the framework and the award items (remaining silently in the public audience is generally not treated as sufficient for a matter like this).

**6. Consequences.** FPPC administrative enforcement (investigation, fines historically up to $5,000 per violation, subject to periodic statutory adjustment); civil penalties and injunctive/mandamus relief to set aside the decision under § 91003 (brought by the FPPC, AG, DA, or — if they decline — any resident via the citizen-suit provision, § 91007); misdemeanor criminal liability for knowing/willful violations under § 91000. Unlike § 1090's automatic voidness, invalidating a decision for a PRA violation generally requires some showing that the disqualified official's participation was consequential to the outcome — a softer standard than § 1090's per se rule, which is precisely why the PRA and § 1090 produce such different practical risk profiles even on identical facts.

---

## IV. Common-law conflict doctrine

§ 1090 is itself the statutory descendant of the common-law "no further inquiry" rule against self-dealing fiduciaries — I've folded that into the § 1090 discussion above because it does real analytical work there (fairness of price is irrelevant). Two other common-law-adjacent points worth flagging:

- **§ 1099 incompatible offices** doesn't apply here — Harbor Light's board is a private nonprofit position, not a "public office," notwithstanding the council resolution designating Okafor as liaison. Don't conflate the two doctrines.
- **Bid-protest / competitive-integrity exposure.** Even if Okafor is perfectly walled off and every conflict rule is technically satisfied, a losing bidder could still challenge the award via writ of mandate on a "tainted process" theory if the scoring criteria were shaped (even unconsciously, by staff or other members aware of Okafor's ties) to favor the historical incumbent. This is a practical litigation risk independent of § 1090/PRA liability, and argues for having the scoring rubric built by an outside consultant or drawn from a neutral HCD model rather than by staff who report, ultimately, to a council that includes Okafor.

---

## V. Synthesis — what actually works here

**Necessary but not sufficient, regardless of everything else:** Okafor must be fully excluded — no drafting input, no discussion, no informal advocacy, no vote, physically absent during deliberation — from *both* the framework and the award decisions, disclosed and minuted before any action is taken.

**Clean and recommended regardless:** Okafor should resign the Harbor Light board seat. It removes one independent interest cleanly, avoids having to rely on a contestable § 1091.5 noninterest determination, and removes the PRA § 87103(d) business-position hook. This is low-cost and should happen regardless of how the harder question resolves.

**The hard question — the spousal salary — is the one that likely can't be walled around.** If, after the city attorney checks current § 1091(b)/§ 1091.5(a) text against these facts, the spousal interest doesn't fit a remote-interest or noninterest category (my tentative view), then **the council cannot lawfully award this contract to Harbor Light while the spouse remains employed there in a budget-linked role — full stop, regardless of recusal, ethical walls, blind panels, or clean paperwork.** § 1090 is status-based, not influence-based; a perfect wall with zero actual influence doesn't matter if the underlying interest is non-remote.

Realistic paths forward, in rough order of legal cleanliness:

1. **Don't select Harbor Light** while the interest exists — award to another qualified bidder, even if Harbor Light might arguably offer better value. Unattractive programmatically, but it is the option with the least legal risk.
2. **The interest genuinely ends before the award** — spouse leaves Harbor Light, or moves to a role/organization with no nexus to city funding. This must be a real, non-sham change; a resignation timed transparently to enable the contract, with any hint of an understanding that she'll return, invites exactly the scrutiny this is meant to avoid.
3. **Full delegation away from the council** — if the city manager or an independent panel has genuine delegated authority to select and execute contracts of this size without council ratification, § 1090 arguably isn't triggered because the council itself never "makes" the contract. This is usually **not realistic at $2.3M** under most municipal codes/charters, which require council approval or appropriation for contracts of this size — and if the council must still approve or fund the specific award, that approval step is itself "making" the contract, putting you back to square one unless the interest independently qualifies for a § 1091/1091.5 exception.
4. **A valid interspousal transmutation agreement** going forward, combined with everything above, strengthens the PRA analysis meaningfully but should not be treated as a standalone § 1090 fix.

Contract structuring around the fund flow — e.g., trying to show the spouse's specific salary line isn't charged to this grant — is unlikely to help under either regime; both bodies of law look at practical economic reality (Harbor Light's overall financial dependency on city contracts), not budget-line formalism.

**Given the stakes and genuine ambiguity in how the exceptions apply, I'd recommend the city formally request an Attorney General opinion on the § 1090 question and, separately, an FPPC advice letter on the PRA question before the framework goes to a vote.** Both provide meaningful protection if followed in good faith with full facts disclosed — an FPPC advice letter generally confers immunity from FPPC enforcement, and an AG opinion, while not immunizing, is strong evidence against a finding of "willfulness" under § 1097 if things later go sideways. That is a modest cost against a $2.3M contract and career-ending downside risk.

---

## VI. Direct answers to Okafor's questions

- **May I vote on the RFP framework?** No.
- **May I vote on the award?** No — and for the same reasons you may not participate in drafting, negotiating, or informally discussing either item.
- **Must I resign the board seat?** You should, regardless of whether it's strictly required, because it removes an independent interest cleanly and avoids relying on a contestable statutory exception.
- **Must my spouse's employment change?** Quite possibly yes — this, not the board seat, is likely the real barrier. If her position (and its dependency on city funding) doesn't fit a remote-interest/noninterest exception, the council cannot lawfully award this contract to Harbor Light while she remains employed there in that capacity, no matter what you do personally.
- **If I simply recuse, is the city safe?** No. Recusal cures the PRA problem for you personally. It does **not** necessarily cure the § 1090 problem for the contract, which can be void regardless of your recusal if your interest — through your spouse's salary — is non-remote. Don't let "I recused" become the city's entire defense file; it's the PRA answer, not the § 1090 answer.