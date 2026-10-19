#!/usr/bin/env python3
"""Frozen legacy oracle for the SEO ontology (Paper 1, WP1).

Paper 1 - the three Python functions that used to *decide* labels in
``test_scenarios.py`` (RQ1's 95% / kappa = 0.68 were measured against them),
moved here verbatim. They are an ORACLE: the differential test
(``differential_test.py``) compares the ontology's inferences against them,
and nothing may use them to label data any more (WP1: the ontology makes every
judgement; WP3: a single classifier). Do not edit the logic; a change would
silently change what "agreement with the legacy encoding" means.

The pipeline oracle wrappers at the bottom call ``populate.py``'s own
``PhaseDetector`` and ``LawConformanceChecker`` unchanged.

Usage:
    python ontology/scenario_bank/legacy_oracle.py   # prints nothing; import only
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def determine_phase_from_snapshot(months: list[dict[str, Any]]) -> str:
    """Determine evolution phase using a multi-signal voting ensemble.

    Paper 1 — Uses three independent signals (LOC trend, commit trend,
    complexity trend) and determines phase by 2/3 majority vote.
    This aligns with the Mann-Kendall trend test used for convergent
    validity, improving Cohen's kappa between the two methods.

    Signals:
    - LOC trend (Mann-Kendall-like slope): growth/decline/stable
    - Commit activity trend: growth/decline/stable
    - Feature-to-maintenance ratio: growth/decline/stable

    Args:
        months: List of monthly snapshot dicts with 'loc' and 'commits' keys.

    Returns:
        One of 'growth', 'stabilization', 'decline'.
    """
    if len(months) < 2:
        return "stabilization"

    mid = len(months) // 2

    # --- Signal 1: LOC trend (primary, aligns with Mann-Kendall) ---
    locs = [m["loc"] for m in months]
    # Mann-Kendall-style: count concordant vs discordant pairs
    n = len(locs)
    s = 0
    for i in range(n):
        for j in range(i + 1, n):
            s += (1 if locs[j] > locs[i] else (-1 if locs[j] < locs[i] else 0))
    # Normalize S by max possible (n*(n-1)/2)
    max_s = n * (n - 1) / 2
    tau = s / max_s if max_s > 0 else 0

    # Combine trend direction (tau) with magnitude (% change)
    loc_change_pct = (locs[-1] - locs[0]) / max(locs[0], 1) * 100

    if tau > 0.3 and loc_change_pct > 5.0:
        loc_vote = "growth"
    elif tau < -0.3 and loc_change_pct < -1.5:
        loc_vote = "decline"
    else:
        loc_vote = "stabilization"

    # --- Signal 2: Commit activity trend ---
    commits = [m["commits"] for m in months]
    first_half_commits = sum(commits[:mid]) / max(mid, 1)
    second_half_commits = sum(commits[mid:]) / max(len(months) - mid, 1)
    commit_ratio = second_half_commits / max(first_half_commits, 1)

    if commit_ratio < 0.5:
        commit_vote = "decline"
    elif commit_ratio > 1.15 and second_half_commits > 20:
        commit_vote = "growth"
    elif commit_ratio < 0.70:
        # Significant commit decline — indicates winding down
        commit_vote = "decline" if second_half_commits < 15 else "stabilization"
    else:
        commit_vote = "stabilization"

    # --- Signal 3: Feature activity trend ---
    first_half_features = sum(m.get("new_features", 0) for m in months[:mid])
    second_half_features = sum(m.get("new_features", 0) for m in months[mid:])
    total_features = first_half_features + second_half_features

    if total_features > 50 and second_half_features > first_half_features * 0.7:
        feature_vote = "growth"
    elif total_features < 15 or second_half_features < 5:
        # Very low feature activity
        if second_half_commits < 15 and commit_ratio < 0.7:
            feature_vote = "decline"
        else:
            feature_vote = "stabilization"
    else:
        # Moderate features — check trajectory
        if second_half_features < first_half_features * 0.4:
            feature_vote = "stabilization"
        else:
            feature_vote = "growth"

    # --- Override: strong decline signal (commits collapsing monotonically) ---
    if len(commits) >= 4:
        monotonic_decline = all(commits[i] >= commits[i + 1] for i in range(len(commits) - 1))
        if monotonic_decline and commit_ratio < 0.65 and second_half_features < first_half_features * 0.5:
            return "decline"

    # --- Override: recovery growth (LOC dipped but last 3 months rising) ---
    if len(locs) >= 4:
        recent_locs = locs[-3:]
        recent_rising = all(recent_locs[i] < recent_locs[i + 1] for i in range(len(recent_locs) - 1))
        recent_loc_growth = (recent_locs[-1] - recent_locs[0]) / max(recent_locs[0], 1)
        if recent_rising and recent_loc_growth > 0.05 and second_half_features > 30:
            return "growth"

    # --- Majority vote (2/3 wins) ---
    votes = [loc_vote, commit_vote, feature_vote]
    for phase in ["growth", "decline", "stabilization"]:
        if votes.count(phase) >= 2:
            return phase

    # No majority — use LOC trend as tiebreaker (aligns with MK)
    return loc_vote


def check_law_conformance(months: list[dict[str, Any]]) -> dict[str, bool]:
    """Check conformance to Lehman's 8 laws from snapshot data.

    Paper 1 — Operationalizes Lehman's laws as computable checks over
    time-series repository metrics. These mirror the SWRL rules in the
    SEO Evolution Law Module.

    Law I   (Continuing Change): System must change or become less useful.
            Check: total commits > threshold (>= 3/month average).
    Law II  (Increasing Complexity): Complexity increases unless actively reduced.
            Check: complexity trend is non-decreasing (last >= first).
    Law III (Self Regulation): Evolution is self-regulating.
            Check: commit rate variance is bounded (CV < 0.6) AND
            complexity growth rate proportional to LOC growth rate.
    Law IV  (Conservation of Organisational Stability): Work rate roughly constant.
            Check: commit rate coefficient of variation < 0.5.
    Law V   (Conservation of Familiarity): Incremental changes stay familiar.
            Check: max month-over-month LOC change < 40% of total LOC.
    Law VI  (Continuing Growth): Functional content must grow to maintain satisfaction.
            Check: new_features sum > 0 in recent months and LOC trending up.
    Law VII (Declining Quality): Quality declines unless actively maintained.
            Check: complexity increasing OR no refactoring activity.
    Law VIII(Feedback System): Evolution is a multi-feedback process.
            Check: bug fixes and refactorings respond to complexity increases
            (positive correlation between complexity delta and corrective activity).

    Args:
        months: List of monthly snapshot dicts.

    Returns:
        Dict mapping law number (roman numeral string) to boolean conformance.
    """
    import statistics

    if len(months) < 2:
        return {k: True for k in ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]}

    commits = [m["commits"] for m in months]
    complexities = [m["complexity_avg"] for m in months]
    locs = [m["loc"] for m in months]
    new_features_list = [m.get("new_features", 0) for m in months]
    refactorings_list = [m.get("refactorings", 0) for m in months]
    bug_fixes_list = [m.get("bug_fixes", 0) for m in months]

    avg_commits = statistics.mean(commits)
    mid = len(months) // 2

    # Law I: Continuing Change — average commits >= 3/month
    law_i = avg_commits >= 3.0 and sum(commits[-3:]) > 5

    # Law II: Increasing Complexity — complexity non-decreasing overall
    law_ii = complexities[-1] >= complexities[0] - 0.1  # small tolerance

    # Law III: Self Regulation — complexity growth proportional to LOC growth
    loc_growth_rate = (locs[-1] - locs[0]) / max(locs[0], 1)
    complexity_growth_rate = (complexities[-1] - complexities[0]) / max(complexities[0], 1)

    commit_cv = statistics.stdev(commits) / max(avg_commits, 1) if len(commits) > 1 else 0
    if loc_growth_rate > 0.1:
        # If LOC is growing, complexity should grow proportionally (not runaway)
        law_iii = complexity_growth_rate <= loc_growth_rate * 1.2 and commit_cv < 0.6
    elif loc_growth_rate < -0.05:
        # If LOC shrinking (refactoring), complexity should also decrease
        law_iii = complexity_growth_rate <= 0.02 and commit_cv < 0.6
    else:
        # Stable LOC — complexity should be stable
        law_iii = abs(complexity_growth_rate) < 0.10 and commit_cv < 0.5

    # Law IV: Conservation of Organisational Stability — commit rate CV < 0.45
    law_iv = commit_cv < 0.45

    # Law V: Conservation of Familiarity — no single month changes > 40% LOC
    max_loc_change_pct = 0.0
    for i in range(1, len(locs)):
        change_pct = abs(locs[i] - locs[i - 1]) / max(locs[i - 1], 1)
        max_loc_change_pct = max(max_loc_change_pct, change_pct)
    # Also check complexity: if complexity grows faster than 15% per month avg, familiarity lost
    monthly_complexity_growth = (complexities[-1] - complexities[0]) / max(len(months) - 1, 1) / max(complexities[0], 1)
    law_v = max_loc_change_pct < 0.40 and monthly_complexity_growth < 0.04

    # Law VI: Continuing Growth — LOC increasing and new features present
    recent_features = sum(new_features_list[mid:])
    loc_increasing = locs[-1] > locs[0] * 1.03
    law_vi = loc_increasing and recent_features > 5

    # Law VII: Declining Quality — complexity increasing or insufficient refactoring
    total_refactoring = sum(refactorings_list)
    total_commits_sum = sum(commits)
    refactoring_ratio = total_refactoring / max(total_commits_sum, 1)
    law_vii = complexities[-1] >= complexities[0] or refactoring_ratio < 0.15

    # Law VIII: Feedback System — corrective actions correlate with problems
    # Check if there's responsive behavior: when complexity rises, refactoring/bugfixes follow
    if len(months) >= 4:
        complexity_deltas = [complexities[i] - complexities[i - 1] for i in range(1, len(months))]
        corrective = [refactorings_list[i] + bug_fixes_list[i] for i in range(1, len(months))]

        # Check: are there corrective actions when complexity increases?
        rising_months = sum(1 for d in complexity_deltas if d > 0.1)
        corrective_months = sum(1 for c in corrective if c > 5)

        # Correlation: after a rising month, does the next month have corrective action?
        responsive = 0
        for i in range(len(complexity_deltas) - 1):
            if complexity_deltas[i] > 0.1 and corrective[i + 1] > 3:
                responsive += 1

        recent_corrective = sum(corrective[-2:])
        law_viii = (
            corrective_months >= rising_months * 0.5
            and recent_corrective > 8
            and (responsive > 0 or rising_months == 0)
        )
    else:
        law_viii = True

    return {
        "I": law_i,
        "II": law_ii,
        "III": law_iii,
        "IV": law_iv,
        "V": law_v,
        "VI": law_vi,
        "VII": law_vii,
        "VIII": law_viii,
    }


def detect_patterns(months: list[dict[str, Any]]) -> list[str]:
    """Detect evolution anti-patterns from snapshot data.

    Paper 1 — Implements pattern detection heuristics that mirror the
    SEO Pattern Module's class definitions.

    Patterns detected:
    - ShadowTechDebt: High agent ratio + complexity growing faster than LOC
    - DependencySprawl: Dependency count growing > 30% over the window
    - RefactoringAvoidance: High agent ratio + very low refactoring ratio
    - CopyPasteOverReuse: LOC growth >> functional growth with high agent ratio

    Args:
        months: List of monthly snapshot dicts.

    Returns:
        List of detected pattern names.
    """
    if len(months) < 2:
        return []

    patterns: list[str] = []

    avg_agent_ratio = sum(m.get("agent_commit_ratio", 0) for m in months) / len(months)
    recent_agent_ratio = sum(m.get("agent_commit_ratio", 0) for m in months[-3:]) / 3

    loc_growth = (months[-1]["loc"] - months[0]["loc"]) / max(months[0]["loc"], 1)
    complexity_growth = (months[-1]["complexity_avg"] - months[0]["complexity_avg"]) / max(months[0]["complexity_avg"], 1)
    dep_growth = (months[-1]["dependency_count"] - months[0]["dependency_count"]) / max(months[0]["dependency_count"], 1)

    total_commits = sum(m["commits"] for m in months)
    total_refactorings = sum(m.get("refactorings", 0) for m in months)
    refactoring_ratio = total_refactorings / max(total_commits, 1)

    total_new_features = sum(m.get("new_features", 0) for m in months)
    loc_per_feature = (months[-1]["loc"] - months[0]["loc"]) / max(total_new_features, 1)

    # ShadowTechDebt: agents present + complexity outpacing LOC growth
    if recent_agent_ratio > 0.25 and complexity_growth > loc_growth * 0.5 and complexity_growth > 0.15:
        patterns.append("ShadowTechDebt")

    # DependencySprawl: rapid dependency growth
    if dep_growth > 0.30 and recent_agent_ratio > 0.05:
        patterns.append("DependencySprawl")

    # RefactoringAvoidance: high agent ratio but very low refactoring
    if recent_agent_ratio > 0.30 and refactoring_ratio < 0.12 and complexity_growth > 0.10:
        patterns.append("RefactoringAvoidance")

    # CopyPasteOverReuse: LOC bloat relative to complexity growth (code duplication)
    # High agent ratio + LOC growing much faster than complexity = copy-paste code
    if recent_agent_ratio > 0.30 and loc_growth > 0.5:
        if loc_per_feature > 800 or (loc_growth > complexity_growth * 3 and loc_growth > 1.0):
            patterns.append("CopyPasteOverReuse")

    return patterns


# ---------------------------------------------------------------------------
# Pipeline oracles: populate.py's own logic, called unchanged
# ---------------------------------------------------------------------------

def pipeline_phase(monthly_loc: list[tuple[str, float]]) -> Optional[str]:
    """Phase from ``PhaseDetector.detect`` (Mann-Kendall), or None if < 4 months."""
    from ontology.population.populate import PhaseDetector

    label = PhaseDetector().detect(monthly_loc)
    return None if label is None else label.phase


def pipeline_laws(monthly_metrics: list[dict], phase: Optional[str]) -> dict[str, tuple[bool, str]]:
    """All eight laws from ``LawConformanceChecker`` as ``{roman: (conforms, evidence)}``.

    Args:
        monthly_metrics: Series in populate.py's ``aggregate_monthly`` layout
            (``commit_count``, ``total_churn``, ``lines_added``,
            ``complexity_mean``, ``bug_fix_ratio``, ``merge_ratio``,
            ``unique_authors``).
        phase: Phase string (growth/stabilization/decline) or None.

    Returns:
        Roman numeral -> (conforms, evidence text). Evidence starting with
        "Insufficient" / "No phase" marks the old code's insufficient-data False.
    """
    from ontology.population.populate import LawConformanceChecker, PhaseLabel

    label = None
    if phase is not None:
        label = PhaseLabel(phase=phase, trend="", p_value=0.0, tau=0.0, slope=0.0,
                           start_month="", end_month="")
    out = {}
    roman = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
    for r, res in zip(roman, LawConformanceChecker().check_all(monthly_metrics, label)):
        out[r] = (res.conforms, res.evidence)
    return out


def rb_stage(
    monthly_loc: list[tuple[str, float]], months_since_last_commit: int,
    dormancy_months: int, min_rel_growth: float,
) -> Optional[str]:
    """RQ1 C2 (Rajlich-Bennett rule set) as plain Python, independent of measures.py (pre-registration 2.2).

    The oracle for the ``RB*Stage`` classes. It recomputes the Sen slope (median of
    pairwise slopes) and the median LOC with NumPy, rounds the ratio to 6 decimals
    (the measurement protocol's rounding), and takes the Mann-Kendall phase from
    ``pipeline_phase`` (the JSS-era PhaseDetector, same test, alpha and minimum length).

    Returns:
        ``phase_out`` | ``active`` | ``servicing`` | None (no class can be inferred).
    """
    if months_since_last_commit >= dormancy_months:
        return "phase_out"
    import numpy as np

    y = [float(v) for _, v in monthly_loc]
    rel: Optional[float] = None
    if len(y) >= 2:
        slopes = [(y[j] - y[i]) / (j - i) for i in range(len(y)) for j in range(i + 1, len(y))]
        rel = round(12.0 * float(np.median(slopes)) / max(float(np.median(y)), 1.0), 6)
    if rel is not None and rel < min_rel_growth:
        return "servicing"  # MinorLocGrowth is a NonSubstantialChange (needs no MK)
    phase = pipeline_phase(monthly_loc)
    if phase in ("stabilization", "decline"):
        return "servicing"
    if phase == "growth" and rel is not None and rel >= min_rel_growth:
        return "active"
    return None
