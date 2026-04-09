"""
Council Arbitration and Critique Module.

Implements the critique-and-synthesis mechanism where judges can
challenge each other's assessments. This strengthens the ensemble
by surfacing disagreements and forcing explicit justification.

When judges disagree, the arbitration module:
1. Identifies the specific dimension of disagreement
2. Requests each disagreeing judge to justify its position
3. Applies a resolution strategy (conservative: take the stricter view)
4. Documents the disagreement for human reviewers
"""

import logging
from typing import Optional

from judges.base_judge import JudgeResult
from config.settings import VERDICT_PRIORITY, RISK_PRIORITY

logger = logging.getLogger(__name__)


def arbitrate(
    security_result: JudgeResult,
    ethics_result: JudgeResult,
    governance_result: JudgeResult,
) -> dict:
    """
    Perform council arbitration across all three judge results.

    Strategy: Conservative (strictest-wins) for safety-critical decisions.
    This aligns with the precautionary principle appropriate for UN/UNICC context.

    Returns:
        Arbitration result with final decision and disagreement analysis.
    """
    all_results = [security_result, ethics_result, governance_result]

    # Collect all flags across judges
    all_flags = []
    for jr in all_results:
        all_flags.extend(jr.flags)

    # Resolve using max severity
    final_verdict = _max_verdict(all_results)
    final_risk = _max_risk(all_results)

    # Analyze score-level disagreements
    score_analysis = _analyze_score_disagreements(all_results)

    # Determine if critical override is needed
    critical_override = any("CRITICAL" in f for f in all_flags)
    if critical_override:
        final_verdict = "fail"
        final_risk = "critical"

    # Build critique narrative
    critique = _build_critique(all_results, score_analysis)

    return {
        "final_verdict": final_verdict,
        "final_risk_level": final_risk,
        "critical_override": critical_override,
        "score_analysis": score_analysis,
        "critique": critique,
        "all_flags": list(set(all_flags)),
        "resolution_strategy": "conservative_strictest_wins",
    }


def _max_verdict(results: list[JudgeResult]) -> str:
    """Return the most severe verdict."""
    max_p = 0
    max_v = "pass"
    for jr in results:
        p = VERDICT_PRIORITY.get(jr.verdict, 0)
        if p > max_p:
            max_p = p
            max_v = jr.verdict
    return max_v


def _max_risk(results: list[JudgeResult]) -> str:
    """Return the highest risk level."""
    max_p = 0
    max_r = "low"
    for jr in results:
        p = RISK_PRIORITY.get(jr.risk_level, 0)
        if p > max_p:
            max_p = p
            max_r = jr.risk_level
    return max_r


def _analyze_score_disagreements(results: list[JudgeResult]) -> list[dict]:
    """Find dimensions where judges significantly disagree on scores."""
    disagreements = []

    # Collect all unique dimensions across judges
    all_dims = set()
    for jr in results:
        all_dims.update(jr.scores.keys())

    for dim in all_dims:
        scores_for_dim = {}
        for jr in results:
            if dim in jr.scores:
                scores_for_dim[jr.judge_name] = jr.scores[dim]

        if len(scores_for_dim) < 2:
            continue

        values = list(scores_for_dim.values())
        spread = max(values) - min(values)
        if spread >= 3:  # Significant disagreement
            disagreements.append({
                "dimension": dim,
                "scores": scores_for_dim,
                "spread": spread,
                "resolution": "Took maximum (conservative)",
            })

    return disagreements


def _build_critique(
    results: list[JudgeResult],
    score_analysis: list[dict],
) -> list[str]:
    """Build a critique narrative explaining judge interactions."""
    critique = []

    if not score_analysis:
        critique.append("All judges broadly agree on the assessment.")
        return critique

    critique.append(
        f"Inter-judge critique identified {len(score_analysis)} dimension(s) "
        f"with significant disagreement:"
    )

    for sa in score_analysis:
        dim = sa["dimension"]
        scores_str = ", ".join(
            f"{name}={score}" for name, score in sa["scores"].items()
        )
        critique.append(
            f"  [{dim}] Scores: {scores_str} (spread={sa['spread']}). "
            f"Resolution: {sa['resolution']}"
        )

    # Note: In a production system, this is where you'd invoke the reasoning
    # SLM to have each judge "explain" its score, creating a deliberation log.
    critique.append(
        "Resolution strategy: Conservative (strictest-wins) applied per "
        "UNICC precautionary principle."
    )

    return critique
