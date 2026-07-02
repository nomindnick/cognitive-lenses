### Operation
Assume the likely position was adopted and failed badly 18 months later; enumerate why. Surfaces blind spots.

### The assumed position

> Counsel would likely avoid taking a firm public stance on whether this technically satisfies Gov. Code § 54952.2(b)(1), since the "communications of any kind" language and the lack of an intent requirement in the serial-meeting cases (e.g., the reasoning underlying Roberts v. City of Palmdale, cert. status/holding to be verified) make the "no one meant to communicate" and "AI isn't an intermediary" arguments too risky to rely on publicly, especially with the logs already published. Instead, the practical, risk-averse move is to treat this as a probable/arguable violation without admitting fault: respond to the § 54960.1 cure-and-correct demand within the statutory window by voluntarily "curing" — noticing and conducting a fresh, de novo Harbor Yards hearing with full disclosure of the CivicAssist logs — rather than litigating the characterization question, since re-hearing is cheap insurance against invalidation, attorney's fees exposure under § 54960.1(d), and continued DA interest. Counsel would also recommend immediately disabling the shared-memory feature, issuing a written AI-use policy barring cross-member information flow (framing it as prophylactic, not an admission the prior conduct was illegal), and would counsel strongly against any member discipline absent evidence of intentional circumvention, since criminal exposure under § 54959 requires knowing/willful conduct that appears absent here (two members reportedly didn't even know the feature existed).

### The retrospective (assumed failure)

# Pre-Mortem: Alvarado Shores / CivicAssist — Retrospective as of January 2028

*(Invented hypothetical, generated for internal issue-spotting only. Every citation below is UNVERIFIED and must be independently confirmed before any reliance. This assumes the "cure, disable, don't litigate the characterization, no discipline" position — and assumes it failed. It is not an argument that the position was wrong at the time; it is a reconstruction of how it came apart.)*

---

**Scene, 18 months out:** The Harbor Yards approval was voided a second time by writ of mandate. The city paid seven figures in combined fee awards and outside-counsel spend. Two councilmembers face a qualified recall. The DA's public-integrity unit has not closed its file. CivicAssist logs from three other matters are now in a second PRA lawsuit. Below are the distinct failure vectors, ranked by likelihood × severity.

---

### 1. The "clean" re-hearing wasn't clean — tainted-decisionmaker doctrine ate the cure
**Likelihood: H  Severity: H**

What went wrong: Voluntarily re-hearing Harbor Yards assumed a fresh vote could substitute for the tainted one. It couldn't, because the taint wasn't procedural — it was cognitive. At the redo, opposing counsel cross-examined each of the four members on the record about the AI-assembled "points of alignment" brief; two members' own hearing statements echoed language CivicAssist had attributed to "another member" weeks earlier, now preserved in a public transcript. A superior court on writ review (CCP § 1094.5, plus Brown Act §§ 54960/54960.1) held the re-hearing did not "substantially comply" because true compliance requires deliberation untainted by information obtained through the improper channel — and that taint lived in members' memories, notes, and saved chat exports, none of which had been screened before the redo. Verify whether cases addressing cure of improper closed sessions or improper serial communications (general Brown Act cure jurisprudence — pin cite TBD) support this "elimination of taint" standard, or whether it's a novel extension the court adopted here.

Early warning sign missed: Nobody checked, before scheduling the "fresh" hearing, whether members had retained personal notes, screenshots, or exported chats from their CivicAssist sessions. Several had. This was discoverable and foreseeable, and no litigation-hold/document-collection step preceded the public commitment to a redo.

---

### 2. The PRA cascade — this stopped being a Harbor Yards story
**Likelihood: H  Severity: H**

What went wrong: Once the initial logs were public, follow-on PRA requests (same reporter, then a statewide watchdog) sought all council CivicAssist logs for the prior year. They showed the shared-memory cross-pollination wasn't a one-off — it had been quietly assembling "points of alignment" briefs across multiple contested matters (a personnel appointment, a franchise renewal) for as long as the feature was enabled. The story converted from "AI mishap on one project" to "council governed by an AI-mediated shadow channel for a year," drew a civil grand jury referral, and put every other council action from that period under a validity cloud.

Early warning sign missed: The initial response was scoped to Harbor Yards and to disabling the feature prospectively. Nobody audited historical logs city-wide for other cross-contaminated matters before the second wave of PRA requests landed — a single-incident response to what was, structurally, a systemic and ongoing defect.

---

### 3. DA declines to accept "nobody knew" — because it wasn't true for everyone
**Likelihood: M  Severity: H**

What went wrong: The public-facing theory — no § 54959 exposure because the conduct wasn't knowing/willful, since "two members reportedly didn't even know the feature existed" — was extrapolated to all four members without individual verification. Discovery/interview in the DA's inquiry surfaced a vendor onboarding notice one member had received (and an internal email referencing it) suggesting at least constructive awareness that "the workspace remembers things across users." That single fact reframed the entire episode for the DA from "innocent architecture surprise" to "at least one member arguably knew and used it anyway," and kept the file open through the election cycle.

Early warning sign missed: The "no intent" narrative was built on two members' say-so and generalized to four, without privileged individual interviews of all four members and IT/vendor onboarding records before the city took a public position on intent.

---

### 4. Fee-shifting hit anyway — "cheap insurance" wasn't
**Likelihood: H  Severity: M**

What went wrong: The theory that a voluntary cure avoids Gov. Code § 54960.1(d) fee exposure assumed the demanding party would treat the redo as resolving the matter. Instead, they treated the city's compliance as catalyst-driven relief and pursued fees on a "prevailing party"/catalyst theory (§ 54960.1(d); potentially CCP § 1021.5 private-attorney-general fees in a parallel declaratory action) — arguing the redo was compelled by litigation threat, not volunteered, and that the case wasn't moot because no settlement or dismissal-with-prejudice had been secured in exchange for curing.

Early warning sign missed: The city treated the cure as self-executing and never got a signed release, stipulated dismissal, or fee waiver from the demanding party before conducting the redo — leaving the fee question open and litigated on the city's dime regardless.

---

### 5. Self-investigation read as cover-up — political revolt
**Likelihood: M  Severity: M–H**

What went wrong: "No discipline absent evidence of intentional circumvention," paired with the same four members adopting their own AI-use policy and blessing their own "no intent" conclusion, was portrayed as the council investigating and clearing itself. A recall qualified against two members; the city manager (who'd overseen CivicAssist's procurement without any data-governance review) resigned under pressure. Whatever the eventual Harbor Yards outcome, it was permanently attached to "the AI scandal council."

Early warning sign missed: Nobody proposed independent/outside counsel or a neutral fact-finder for the internal review before the council concluded, in effect, that its own members' conduct was innocent — self-clearance is precisely the pattern that becomes a bigger story than the underlying Brown Act question.

---

### 6. Disabling the feature without a litigation hold looked like spoliation
**Likelihood: M  Severity: M**

What went wrong: IT "immediately disabled shared memory" per counsel's instruction, and in doing so altered/purged parts of the workspace memory store, before a formal preservation notice went to IT and the vendor. Opposing counsel in the civil action sought (and partly obtained) an adverse-inference argument tied to the timing of the deletion relative to the DA's letter of inquiry and the PRA lawsuit.

Early warning sign missed: The prophylactic fix (disable the feature) and the evidentiary duty (preserve everything relevant to pending/threatened claims) were treated as one instruction instead of two. No hold letter preceded the technical change.

---

### 7. The legal premise itself was never verified — and that became public
**Likelihood: M  Severity: M**

What went wrong: Internal risk calculus leaned on Roberts v. City of Palmdale for the "no intent required" serial-meeting premise without confirming what that case actually holds or whether it addresses serial meetings/intent at all (flagged as unverified from the start — verify whether Roberts addresses § 54952.2 serial-meeting intent, or whether it's a different Brown Act/referendum question entirely). When the underlying legal memo's reasoning surfaced (via the cure letter's own recitations, or discovery), opposing counsel and a good-government amicus (e.g., a CalAware-type group) showed the citation didn't support the weight it was given. The resulting "counsel didn't actually know the law" narrative damaged credibility independent of the merits.

Early warning sign missed: No second-chair task to pull, read, and Shepardize the actual opinion before the reasoning was relied on in a public-facing strategy document.

---

### 8. Curing under § 54960.1 before any "action" existed became its own trap
**Likelihood: M  Severity: M**

What went wrong: Because the Harbor Yards appeal hadn't yet been decided when the cure-and-correct demand arrived, there arguably was no completed "action" under Gov. Code § 54952.6 for § 54960.1 to reach in the first place (verify whether pre-decision serial deliberation without a vote/collective commitment qualifies as "action taken" for § 54960.1 purposes, or whether the correct vehicle was injunctive relief under § 54960 instead). Proceeding straight to a full voluntary cure — rather than first testing ripeness — was later read as an implicit concession that a violation and an "action" had already occurred, which became the anchor for a separate, forward-looking declaratory action about AI-mediated deliberation generally, a theory the city had no ready defense to because its own cure letter had already conceded "arguable violation."

Early warning sign missed: No one separately assessed procedural ripeness of the § 54960.1 remedy before responding — the abundance-of-caution posture functioned, in hindsight, as a usable concession.

---

## Ranking (likelihood × severity, high to low)

1. #1 Tainted redo — H/H
2. #2 PRA cascade — H/H
3. #3 DA escalation — M/H
4. #4 Fee-shifting anyway — H/M
5. #5 Political revolt — M/M–H
6. #6 Spoliation exposure — M/M
7. #7 Unverified precedent surfaces — M/M
8. #8 Remedy/ripeness mismatch — M/M

**Common thread across #1, #6, #7, #8:** each failure traces to something *assumed* rather than *checked* — taint in members' retained notes, litigation-hold timing, the actual holding of a cited case, and the ripeness of the chosen statutory remedy — before the city committed publicly to a strategy built on those assumptions.
