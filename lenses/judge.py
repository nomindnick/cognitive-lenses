"""Coverage judge: the instrumentation that makes the experiment real.

A judge-tier model reads (a) the panel's aggregated report, (b) the naive
worker-model pass, (c) the naive judge-tier pass, extracts every discrete
ANGLE across all three, and classifies where each was found and how good it
is. Code then computes coverage metrics and per-lens unique-angle counts."""
from __future__ import annotations

from .common import Question

ANGLES_SCHEMA = {
    "type": "object",
    "properties": {
        "angles": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "the angle in one sentence"},
                    "in_panel": {"type": "boolean"},
                    "in_naive_sonnet": {"type": "boolean"},
                    "in_naive_fable": {"type": "boolean"},
                    "panel_lenses": {"type": "array", "items": {"type": "string"},
                                     "description": "source lenses per the panel report's provenance tags; empty if not in panel"},
                    "quality": {"type": "string", "enum": ["substantive", "marginal", "noise"]},
                },
                "required": ["summary", "in_panel", "in_naive_sonnet", "in_naive_fable",
                             "panel_lenses", "quality"],
            },
        },
        "panel_unique_assessment": {"type": "string",
                                    "description": "of the angles ONLY the panel found: which are genuinely valuable to a lawyer and which are padding"},
        "noise_assessment": {"type": "string",
                             "description": "where the panel added noise or structured word-salad relative to the naive passes"},
        "verdict": {"type": "string",
                    "description": "2-4 sentences: did the panel out-cover the naive passes in ways a lawyer would pay for?"},
    },
    "required": ["angles", "panel_unique_assessment", "noise_assessment", "verdict"],
}

JUDGE_SYSTEM = """You are scoring an experiment, not doing legal analysis. You will read three \
documents analyzing the same hypothetical legal question: [PANEL] (a multi-lens exploration \
pipeline's aggregated report), [NAIVE-SONNET] (one unstructured pass by the same worker \
model the panel used), and [NAIVE-FABLE] (one unstructured pass by a stronger model).

An ANGLE is a distinct argument, counterargument, risk, procedural move, factual \
investigation, remedy, or framing that a competent lawyer would treat as a separate line of \
inquiry. Extract the union of angles across ALL THREE documents — enumerate from each \
document, not just the panel. Merge duplicates into one angle (different wording, same line \
of inquiry). For each angle record where it appears and its quality FOR A PRACTICING LAWYER: \
substantive (worth real time), marginal (true but thin), noise (padding, word-salad, or too \
obvious to state).

Be adversarial toward the panel: it produces more text, so mere verbosity must not be \
credited as coverage. An angle counts as "in" a document only if that document actually \
develops or distinctly flags it — a passing half-sentence mention does not count. Attribute \
panel angles to lenses using the [provenance tags] in the panel report."""


def judge_prompt(q: Question, panel_md: str, naive_sonnet: str, naive_fable: str) -> str:
    return (
        f"{q.block()}\n\n---\n\n# [PANEL]\n\n{panel_md}\n\n---\n\n"
        f"# [NAIVE-SONNET]\n\n{naive_sonnet}\n\n---\n\n"
        f"# [NAIVE-FABLE]\n\n{naive_fable}\n\n---\n\n"
        "Extract and classify all angles per your instructions, then give the assessments "
        "and verdict."
    )


def run_judge(q: Question, panel_md: str, naive_sonnet: str, naive_fable: str,
              backend, cfg: dict) -> dict:
    c = backend.complete(
        judge_prompt(q, panel_md, naive_sonnet, naive_fable),
        model=cfg.get("judge_model", "claude-fable-5"),
        system=JUDGE_SYSTEM, schema=ANGLES_SCHEMA,
        fallback_model=cfg.get("fallback_judge_model"),
        label="coverage-judge", timeout_s=1800,
    )
    return c.data


def compute_metrics(judge_data: dict) -> dict:
    angles = judge_data.get("angles", [])
    n = len(angles)

    def count(pred):
        return sum(1 for a in angles if pred(a))

    sub = [a for a in angles if a["quality"] == "substantive"]
    panel_angles = [a for a in angles if a["in_panel"]]
    m = {
        "angles_total": n,
        "angles_substantive": len(sub),
        "panel_found": count(lambda a: a["in_panel"]),
        "naive_sonnet_found": count(lambda a: a["in_naive_sonnet"]),
        "naive_fable_found": count(lambda a: a["in_naive_fable"]),
        "panel_substantive": sum(1 for a in sub if a["in_panel"]),
        "naive_sonnet_substantive": sum(1 for a in sub if a["in_naive_sonnet"]),
        "naive_fable_substantive": sum(1 for a in sub if a["in_naive_fable"]),
        "panel_only_substantive": sum(
            1 for a in sub if a["in_panel"] and not a["in_naive_sonnet"] and not a["in_naive_fable"]),
        "panel_beats_own_model": sum(
            1 for a in sub if a["in_panel"] and not a["in_naive_sonnet"]),
        "missed_by_panel_substantive": sum(
            1 for a in sub if not a["in_panel"] and (a["in_naive_sonnet"] or a["in_naive_fable"])),
        "panel_noise": sum(1 for a in panel_angles if a["quality"] == "noise"),
        "panel_noise_rate": round(
            sum(1 for a in panel_angles if a["quality"] == "noise") / len(panel_angles), 3)
            if panel_angles else 0.0,
    }
    per_lens: dict[str, dict] = {}
    for a in angles:
        if not a["in_panel"]:
            continue
        lenses = a.get("panel_lenses") or ["(untagged)"]
        for ln in lenses:
            d = per_lens.setdefault(ln, {"angles": 0, "substantive": 0,
                                         "unique_substantive": 0, "noise": 0})
            d["angles"] += 1
            if a["quality"] == "substantive":
                d["substantive"] += 1
                if len(lenses) == 1 and not a["in_naive_sonnet"] and not a["in_naive_fable"]:
                    d["unique_substantive"] += 1
            if a["quality"] == "noise":
                d["noise"] += 1
    m["per_lens"] = dict(sorted(per_lens.items()))
    return m
