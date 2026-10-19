#!/usr/bin/env python3
"""Differential test: Pellet inferences vs the frozen legacy oracle (Paper 1, WP1).

Paper 1 - proves that the ontology encodings reproduce the old Python
judgements, so that moving every label into ``seo-inference.owl`` /
``seo-legacy.owl`` changes no result unintentionally. For the 20 scenarios in
``scenarios.yaml`` plus N randomized synthetic monthly series (random walks,
small-integer grids that hit ties, and hand-built cases exactly at threshold
values) it:

  1. computes measurements with ``ontology/population/measures.py``;
  2. writes an ABox, reasons with Pellet (two passes: the second adds the
     counts of inferred months that the paper-table Law VIII needs);
  3. compares every label against the oracle:

     =====================  ==========================================  ========
     ontology encoding      oracle                                      module
     =====================  ==========================================  ========
     Legacy*Stage           legacy_oracle.determine_phase_from_snapshot seo-legacy
     PaperLaw*              legacy_oracle.check_law_conformance         seo-legacy
     Exhibits* patterns     legacy_oracle.detect_patterns               seo-inference
     GrowthStage etc. (MK)  populate.PhaseDetector.detect               seo-inference
     Law*Conformant         populate.LawConformanceChecker              seo-inference
     =====================  ==========================================  ========

Outcomes per label: ``agree``; ``undetermined_vs_default`` (the old code
returned a default or an insufficient-data False where the ontology correctly
gives no label; counted separately, not a mismatch); ``mismatch_boundary``
(a measurement lies within 2e-6 of a threshold, i.e. float-versus-decimal
rounding at a boundary); ``mismatch`` (anything else: an encoding bug).

Also checked, without a 100% target (differences are the intended WP1
decisions): AgentCommit / BugFixCommit rules against the old ``_detect_agent``
and keyword substring test.

Usage:
    python ontology/scenario_bank/differential_test.py --n-random 150 --n-grid 150 \\
        --out experiments/paper1_ontology_manifests/results/real_v2/wp1/differential_report.json
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import re
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ontology.modules.build_ontology import load_thresholds  # noqa: E402
from ontology.population import measures as M  # noqa: E402
from ontology.reasoning.abox import AboxWriter  # noqa: E402
from ontology.reasoning.reasoner import HermitReasoner, PelletReasoner, count_month_labels  # noqa: E402
from ontology.scenario_bank import legacy_oracle as oracle  # noqa: E402
from ontology.scenario_bank.test_scenarios import SCENARIOS_FILE, load_scenarios  # noqa: E402

logger = logging.getLogger("senso.differential")

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
DEFAULT_OUT = (PROJECT_ROOT / "experiments" / "paper1_ontology_manifests" / "results"
               / "real_v2" / "wp1" / "differential_report.json")
PATTERNS = {
    "ShadowTechDebt": "ExhibitsAgentAssociatedComplexityGrowth",
    "DependencySprawl": "ExhibitsDependencySprawl",
    "RefactoringAvoidance": "ExhibitsRefactoringAvoidance",
    "CopyPasteOverReuse": "ExhibitsCopyPasteOverReuse",
}
RB = {"active": "RBActiveDevelopmentStage", "servicing": "RBServicingStage", "phase_out": "RBPhaseOutStage"}
GAPS = [0, 0, 1, 3, 6, 11, 12, 12, 13, 18, 24, 40]
ENSEMBLE = {"growth": "LegacyGrowthStage", "decline": "LegacyDeclineStage",
            "stabilization": "LegacyStabilizationStage"}
MK = {"growth": "GrowthStage", "decline": "DeclineStage", "stabilization": "StabilizationStage"}
EPS = 2e-6
"""Distance to a threshold below which a mismatch is classed as rounding at a boundary."""


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------

@dataclass
class Case:
    """One monthly series. ``months`` use the scenario layout plus optional pipeline keys."""

    cid: str
    kind: str
    months: list[dict[str, Any]]
    has_pipeline: bool = False
    meas: dict[str, Any] = field(default_factory=dict)
    snaps: list[dict[str, Any]] = field(default_factory=list)
    gap: int = 0
    """Months between the snapshot month and the last commit (RQ1 C2 input)."""

    def series(self) -> list[dict[str, Any]]:
        """Monthly series in the ``measures`` layout."""
        out = []
        for m in self.months:
            row = {
                "month": m["month"], "commit_count": m["commits"], "loc": m["loc"],
                "complexity_mean": m["complexity_avg"], "feature_count": m.get("new_features", 0),
                "refactoring_count": m.get("refactorings", 0), "bug_fix_count": m.get("bug_fixes", 0),
                "dependency_count": m.get("dependency_count"),
                "agent_commit_ratio": m.get("agent_commit_ratio", 0),
            }
            if self.has_pipeline:
                row.update({
                    "total_churn": m["total_churn"], "lines_added": m["lines_added"],
                    "merge_count": m["merge_count"], "unique_authors": m["unique_authors"],
                    "bug_fix_ratio": m["bug_fixes"] / max(m["commits"], 1),
                })
            out.append(row)
        return out

    def pipeline_metrics(self) -> list[dict[str, Any]]:
        """Series in populate.py's ``aggregate_monthly`` layout."""
        return [{
            "month": m["month"], "commit_count": m["commits"], "total_churn": m["total_churn"],
            "lines_added": m["lines_added"], "complexity_mean": m["complexity_avg"],
            "bug_fix_ratio": m["bug_fixes"] / max(m["commits"], 1),
            "merge_ratio": m["merge_count"] / max(m["commits"], 1),
            "unique_authors": m["unique_authors"],
        } for m in self.months]


def _month_name(i: int) -> str:
    return f"{2023 + i // 12}-{i % 12 + 1:02d}"


def _finish(months: list[dict[str, Any]], rng: random.Random) -> list[dict[str, Any]]:
    """Add the pipeline-only fields to scenario-layout months."""
    for i, m in enumerate(months):
        c = m["commits"]
        m["month"] = _month_name(i)
        m["total_churn"] = c * rng.randint(20, 400) if c else 0
        m["lines_added"] = int(m["total_churn"] * rng.choice([0.4, 0.5, 0.6, 0.8]))
        m["merge_count"] = rng.randint(0, c // 2) if c and rng.random() < 0.8 else 0
        m["unique_authors"] = rng.randint(1, min(c, 6)) if c else 0
    return months


def gen_random(rng: random.Random, idx: int) -> Case:
    """Random-walk series in the style of the scenario bank."""
    n = rng.randint(2, 14)
    style = rng.choice(["growth", "decline", "stable", "noisy"])
    step = {"growth": (0.0, 0.2), "decline": (-0.1, 0.0), "stable": (-0.02, 0.02), "noisy": (-0.3, 0.4)}[style]
    loc = rng.choice([500, 2000, 10000, 50000])
    base = rng.choice([2, 8, 20, 60, 120])
    cx = round(rng.uniform(1.5, 8.0), 1)
    dep = rng.randint(5, 100)
    agent = round(rng.uniform(0, 0.4), 2)
    months = []
    for i in range(n):
        loc = max(int(round(loc * (1 + rng.uniform(*step)))), 0)
        c = max(int(base * (1 + (0.1 if style == "growth" else -0.1 if style == "decline" else 0) * i
                            + rng.uniform(-0.4, 0.4))), 0)
        cx = max(round(cx + rng.choice([-0.2, -0.1, 0.0, 0.1, 0.2, 0.3]), 1), 0.0)
        if rng.random() < 0.04:
            cx = 0.0
        dep = max(int(dep * (1 + rng.uniform(-0.02, 0.1))), 0)
        agent = min(max(round(agent + rng.uniform(-0.05, 0.1), 2), 0.0), 1.0)
        bug = min(int(c * rng.uniform(0, 0.6)), c)
        months.append({
            "loc": loc, "commits": c, "complexity_avg": cx, "dependency_count": dep,
            "agent_commit_ratio": agent, "new_features": int(c * rng.uniform(0, 0.7)),
            "bug_fixes": bug, "refactorings": int(c * rng.uniform(0, 0.3)),
        })
    return Case(f"random_{idx:04d}", "random", _finish(months, rng), True)


def gen_grid(rng: random.Random, idx: int) -> Case:
    """Small-integer grids that produce ties and values exactly at thresholds."""
    n = rng.randint(2, 8)
    loc0 = rng.choice([100, 200, 1000])
    unit = rng.choice([1, 5, 10, loc0 // 20, loc0 // 10])
    loc, months = loc0, []
    for i in range(n):
        loc = max(loc + rng.choice([-2, -1, 0, 0, 1, 2, 3]) * unit, 0)
        c = rng.choice([0, 2, 3, 5, 6, 10, 14, 15, 20, 21, 23, 40])
        months.append({
            "loc": loc, "commits": c,
            "complexity_avg": rng.choice([0.0, 2.0, 2.1, 2.2, 2.3, 2.4, 3.0, 4.0]),
            "dependency_count": rng.choice([10, 13, 20, 100]),
            "agent_commit_ratio": rng.choice([0.0, 0.05, 0.25, 0.3, 0.5]),
            "new_features": rng.choice([0, 1, 5, 6, 10, 15, 30, 31, 50]),
            "bug_fixes": min(rng.choice([0, 1, 2, 3, 4, 5, 6]), c),
            "refactorings": rng.choice([0, 1, 2, 3, 4]),
        })
    return Case(f"grid_{idx:04d}", "grid", _finish(months, rng), True)


def boundary_cases(rng: random.Random) -> list[Case]:
    """Hand-built series sitting exactly on thresholds."""
    def mk(cid: str, locs: list[int], commits: list[int], feats: Optional[list[int]] = None,
           cx: Optional[list[float]] = None) -> Case:
        n = len(locs)
        months = [{
            "loc": locs[i], "commits": commits[i], "complexity_avg": (cx or [2.0] * n)[i],
            "dependency_count": 10, "agent_commit_ratio": 0.0,
            "new_features": (feats or [0] * n)[i], "bug_fixes": min(1, commits[i]), "refactorings": 0,
        } for i in range(n)]
        return Case(cid, "boundary", _finish(months, rng), True)

    return [
        mk("b_loc_pct_exactly_5", [100, 101, 102, 103, 105], [10] * 5),
        mk("b_loc_pct_above_5", [100, 101, 102, 103, 106], [10] * 5),
        mk("b_loc_tau_exactly_0.3", [100, 105, 100, 103, 120], [10] * 5),
        mk("b_commit_ratio_0.5", [100] * 4, [10, 10, 5, 5]),
        mk("b_commit_ratio_0.7_low_mean", [100] * 4, [10, 10, 7, 7]),
        mk("b_commit_ratio_1.15_mean_23", [100] * 4, [20, 20, 23, 23]),
        mk("b_commit_ratio_1.15_mean_20", [100] * 4, [20, 20, 23, 17]),
        mk("b_active_ratio_exactly_half", [100] * 4, [3, 0, 2, 0]),
        mk("b_feature_total_50", [100] * 6, [20] * 6, [10, 10, 5, 5, 10, 10]),
        mk("b_feature_second_vs_first", [100] * 4, [20] * 4, [10, 10, 7, 7]),
        mk("b_complexity_tolerance_0.1", [100] * 4, [10] * 4, cx=[2.2, 2.2, 2.1, 2.1]),
        mk("b_complexity_equal", [100] * 4, [10] * 4, cx=[2.0, 2.0, 2.0, 2.0]),
        mk("b_loc_flat_all_ties", [100] * 5, [10] * 5),
        mk("b_single_month", [100], [10]),
        mk("b_two_months", [100, 120], [10, 12]),
        mk("b_three_months_up", [100, 150, 220], [10, 12, 14]),
        mk("b_zero_commits", [100] * 6, [0] * 6),
        mk("b_loc_zero_start", [0, 0, 10, 20, 40], [1, 2, 3, 4, 5]),
    ]


def rb_boundary_cases(rng: random.Random) -> list[Case]:
    """Hand-built C2 cases on the dormancy and growth thresholds (gap is set per case)."""
    def lin(cid: str, start: int, step: int, n: int, gap: int, commits: int = 10) -> Case:
        months = [{
            "loc": start + i * step, "commits": commits, "complexity_avg": 2.0, "dependency_count": 10,
            "agent_commit_ratio": 0.0, "new_features": 0, "bug_fixes": 1, "refactorings": 0,
        } for i in range(n)]
        c = Case(cid, "rb_boundary", _finish(months, rng), True)
        c.gap = gap
        return c

    return [
        lin("rb_gap_11_growth", 2380, 10, 5, 11), lin("rb_gap_12_growth", 2380, 10, 5, 12),
        lin("rb_gap_13_growth", 2380, 10, 5, 13),
        lin("rb_rel_exactly_0.05", 2380, 10, 5, 0), lin("rb_rel_just_below", 2381, 10, 5, 0),
        lin("rb_rel_just_above", 2379, 10, 5, 0), lin("rb_rel_zero_flat", 1000, 0, 6, 3),
        lin("rb_decline", 5000, -30, 8, 2), lin("rb_two_months_up", 100, 50, 2, 1),
        lin("rb_three_months_up", 100, 50, 3, 1), lin("rb_two_months_gap_12", 100, 50, 2, 12),
        lin("rb_big_growth", 1000, 100, 12, 0), lin("rb_tiny_growth_sig", 100000, 50, 12, 0),
        lin("rb_gap_0_flat_short", 100, 0, 3, 0),
    ]


def scenario_cases() -> list[Case]:
    """The 20 scenarios of scenarios.yaml."""
    out = []
    for sc in load_scenarios(SCENARIOS_FILE):
        months = [dict(m) for m in sc["repo_snapshot"]["months"]]
        out.append(Case(sc["id"], "scenario", months, False))
    return out


# ---------------------------------------------------------------------------
# Near-boundary detection (classifies float/decimal rounding mismatches)
# ---------------------------------------------------------------------------

def near_entries(case: Case, T: dict[str, Any]) -> dict[str, list[tuple[str, float, float]]]:
    """Per label group, (name, lhs, rhs) comparisons the label depends on."""
    m, v = case.meas, (lambda i: T[i]["value"])
    g: dict[str, list[tuple[str, float, float]]] = defaultdict(list)

    def add(group: str, name: str, lhs: Optional[float], rhs: Optional[float]) -> None:
        if lhs is not None and rhs is not None:
            g[group].append((name, float(lhs), float(rhs)))

    for grp in ("phase_ensemble",):
        add(grp, "tau>+e_tau", m.get("locMKTau"), v("e_tau"))
        add(grp, "tau<-e_tau", m.get("locMKTau"), -v("e_tau"))
        add(grp, "pct_growth", m.get("locChangePct"), v("e_loc_growth_pct"))
        add(grp, "pct_decline", m.get("locChangePct"), v("e_loc_decline_pct"))
        for tid in ("e_commit_collapse", "e_commit_growth", "e_commit_wind_down", "e_feat_low_ratio", "e_decl_ratio"):
            add(grp, tid, m.get("commitHalfRatio"), v(tid))
        for tid in ("e_commit_growth_min_mean", "e_commit_low_mean", "e_feat_low_mean"):
            add(grp, tid, m.get("commitSecondHalfMean"), v(tid))
        f1, f2 = m.get("featureCommitsFirstHalf"), m.get("featureCommitsSecondHalf")
        if f1 is not None:
            for tid in ("e_feat_second_vs_first", "e_feat_stab_factor", "e_decl_feat_factor"):
                add(grp, tid, f2, f1 * v(tid))
        add(grp, "grow3", m.get("locGrowthLast3"), v("e_grow_recent_growth"))
    add("phase_mk", "p<alpha", m.get("locMKpValue"), v("mk_alpha"))
    add("phase_mk", "tau0", m.get("locMKTau"), 0)
    add("rb_stage", "rel_growth", m.get("locRelSenSlopeAnnual"), v("rb_min_rel_loc_growth_per_year"))
    pg = "paper_law_"
    add(pg + "I", "mean", m.get("meanMonthlyCommits"), v("t_law1_mean_commits"))
    add(pg + "II", "cx", (m.get("complexityLast") or 0) + v("t_law2_tolerance"), m.get("complexityFirst"))
    lg, cg = m.get("locGrowthRate"), m.get("complexityGrowthRate")
    for tid in ("t_law3_loc_up", "t_law3_loc_down"):
        add(pg + "III", tid, lg, v(tid))
    if lg is not None:
        add(pg + "III", "cx_factor", cg, lg * v("t_law3_cx_factor"))
    add(pg + "III", "cx_shrink", cg, v("t_law3_cx_shrink_max"))
    add(pg + "III", "cx_stable+", cg, v("t_law3_cx_stable_abs"))
    add(pg + "III", "cx_stable-", cg, -v("t_law3_cx_stable_abs"))
    for tid in ("t_law3_cv_up", "t_law3_cv_down", "t_law3_cv_stable"):
        add(pg + "III", tid, m.get("commitCountCVSample"), v(tid))
    add(pg + "IV", "cv", m.get("commitCountCVSample"), v("t_law4_cv"))
    add(pg + "V", "cx_growth", m.get("monthlyComplexityGrowth"), v("t_law5_cx_growth"))
    for s in case.snaps:
        add(pg + "V", "month_loc_change", s.get("locChangeRatio"), v("t_law5_max_loc_change"))
        add(pg + "VIII", "rising_delta", s.get("complexityDelta"), v("t_law8_rising_delta"))
    if m.get("locStart") is not None:
        add(pg + "VI", "loc_factor", m.get("locEnd"), m["locStart"] * v("t_law6_loc_factor"))
    add(pg + "VII", "refactor", m.get("refactoringRatio"), v("t_law7_refactor_ratio"))
    add(pg + "VII", "cx_dir", m.get("complexityLast"), m.get("complexityFirst"))
    if m.get("risingMonthCount") is not None:
        add(pg + "VIII", "corr_vs_rising", m.get("correctiveMonthCount"), m["risingMonthCount"] * v("t_law8_factor"))
    pl = "pipeline_law_"
    add(pl + "I", "active", m.get("activeMonthRatio"), v("p_law1_active_ratio"))
    add(pl + "II", "halves", m.get("complexityHalfMeanSecond"), m.get("complexityHalfMeanFirst"))
    add(pl + "III", "churn_cv", m.get("churnCV"), v("p_law3_churn_cv"))
    add(pl + "IV", "commit_cv", m.get("commitCountCV"), v("p_law4_commit_cv"))
    add(pl + "V", "added_cv", m.get("linesAddedCV"), v("p_law5_additions_cv"))
    if m.get("bugFixRatioFirstHalf") is not None:
        add(pl + "VII", "bugfix", m.get("bugFixRatioSecondHalf"), m["bugFixRatioFirstHalf"] * v("p_law7_tolerance"))
    add(pl + "VIII", "merge", m.get("mergeMonthRatio"), v("p_law8_merge_ratio"))
    add(pl + "VIII", "authors", m.get("multiAuthorMonthRatio"), v("p_law8_multiauthor_ratio"))
    add(pl + "VI", "p<alpha", m.get("locMKpValue"), v("mk_alpha"))
    # anti-patterns
    ar = m.get("recentAgentCommitRatio")
    pat = "pattern_"
    for name, tids in (("ShadowTechDebt", ["a_agent_shadow"]), ("DependencySprawl", ["a_agent_dep"]),
                       ("RefactoringAvoidance", ["a_agent_refactor"]), ("CopyPasteOverReuse", ["a_agent_copy"])):
        for tid in tids:
            add(pat + name, tid, ar, v(tid))
    cg2, lg2 = m.get("complexityGrowthRate"), m.get("locGrowthRate")
    add(pat + "ShadowTechDebt", "cg", cg2, v("a_cx_growth_shadow"))
    if lg2 is not None:
        add(pat + "ShadowTechDebt", "cg_vs_lg", cg2, lg2 * v("a_cx_vs_loc_factor"))
    add(pat + "DependencySprawl", "dep", m.get("dependencyGrowthRate"), v("a_dep_growth"))
    add(pat + "RefactoringAvoidance", "ratio", m.get("refactoringRatio"), v("a_refactor_ratio"))
    add(pat + "RefactoringAvoidance", "cg", cg2, v("a_cx_growth_refactor"))
    add(pat + "CopyPasteOverReuse", "lg", lg2, v("a_loc_growth_copy"))
    add(pat + "CopyPasteOverReuse", "lg2", lg2, v("a_loc_growth_copy2"))
    if cg2 is not None:
        add(pat + "CopyPasteOverReuse", "lg_vs_cg", lg2, cg2 * v("a_loc_vs_cx_factor"))
    if m.get("locDelta") is not None and m.get("featureCommitsTotal") is not None:
        add(pat + "CopyPasteOverReuse", "per_feature", m["locDelta"] / max(m["featureCommitsTotal"], 1), v("a_loc_per_feature"))
    return g


def is_near(entries: list[tuple[str, float, float]]) -> bool:
    """True if any comparison lies within EPS (relative to scale) of its threshold."""
    return any(abs(a - b) <= EPS * max(1.0, abs(b)) for _, a, b in entries)


# ---------------------------------------------------------------------------
# Running the reasoner on a batch
# ---------------------------------------------------------------------------

def write_batch(cases: list[Case], counts: Optional[dict[str, dict[str, int]]] = None,
                months: bool = True) -> tuple[AboxWriter, dict[str, str]]:
    """ABox for a batch; ``counts`` adds the stratified month-class counts (pass 2).

    ``months=False`` omits the month individuals and their closure axioms: the
    canonical module does not use them.
    """
    w = AboxWriter()
    iris: dict[str, str] = {}
    for c in cases:
        meas = dict(c.meas)
        if counts is not None:
            meas.update({k: v for k, v in counts.get(c.cid, {}).items()})
        iris[c.cid] = w.project(c.cid, meas, c.snaps if months else None)
    return w, iris


MONTH_COUNT_MAP = {"RisingMonth": "risingMonthCount", "CorrectiveMonth5": "correctiveMonthCount",
                   "ResponsiveRisingMonth": "responsiveMonthCount"}


def run_batch(reasoner: PelletReasoner, cases: list[Case], legacy: bool = False) -> dict[str, Any]:
    """Pellet passes over a batch; labels per case and timings.

    Canonical TBox: one pass. With seo-legacy: pass 1 classifies the month
    individuals, the counts of inferred months are asserted (counting is
    measurement) and pass 2, only for cases with at least 4 months, takes the
    final labels (paper-table Law VIII compares those counts in SWRL).
    """
    w1, iris1 = write_batch(cases, months=legacy)
    r1 = reasoner.infer(w1.ntriples())
    timings: dict[str, Any] = {"pass1": r1.timings, "pass2": {}}
    fail = {"error": r1.error, "timings": timings, "labels": {}, "consistent": False,
            "cids": [c.cid for c in cases]}
    if not r1.consistent:
        return fail
    labels = {c.cid: set(r1.labels.get(iris1[c.cid], ())) for c in cases}
    out: dict[str, Any] = {"labels": labels, "counts": {}, "timings": timings, "consistent": True,
                           "abox_triples": w1.n_triples, "abox_individuals": w1.individuals,
                           "cids": [c.cid for c in cases]}
    if not legacy:
        return out
    mc = count_month_labels(r1.labels, w1.month_owner, list(MONTH_COUNT_MAP))
    iri_to_cid = {i: c for c, i in iris1.items()}
    counts = {iri_to_cid[p]: {MONTH_COUNT_MAP[k]: v for k, v in d.items()} for p, d in mc.items()
              if p in iri_to_cid}
    for d in counts.values():
        ratio = M.count_ratio(d["correctiveMonthCount"], d["risingMonthCount"])
        if ratio is not None:
            d["correctiveToRisingRatio"] = ratio
    need2 = [c for c in cases if len(c.months) >= 4]
    if need2:
        w2, iris2 = write_batch(need2, counts)
        r2 = reasoner.infer(w2.ntriples())
        timings["pass2"] = r2.timings
        if not r2.consistent:
            return {**fail, "error": r2.error}
        for c in need2:
            labels[c.cid] = set(r2.labels.get(iris2[c.cid], ()))
    out["counts"] = counts
    return out


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

class Tally:
    """Per-label agreement counters and the list of mismatches."""

    def __init__(self) -> None:
        self.counts: dict[str, Counter] = defaultdict(Counter)
        self.mismatches: list[dict[str, Any]] = []

    def add(self, group: str, outcome: str, case: Case, oracle_v: Any, onto_v: Any,
            near: bool = False, note: str = "") -> None:
        if outcome == "mismatch" and near:
            outcome = "mismatch_boundary"
        self.counts[group][outcome] += 1
        if outcome.startswith("mismatch"):
            self.mismatches.append({
                "label": group, "case": case.cid, "kind": case.kind, "outcome": outcome,
                "oracle": oracle_v, "ontology": onto_v, "note": note,
                "measurements": case.meas,
                "months": case.months if len(case.months) <= 14 else case.months[:14],
            })


def compare_case(case: Case, labels: set[str], T: dict[str, Any], tally: Tally,
                 canonical: bool = True, legacy: bool = True) -> None:
    """Compare the labels of one case against the oracles (canonical and/or legacy groups)."""
    near = near_entries(case, T)
    months = case.months
    n = len(months)

    # --- A. legacy ensemble phase
    if legacy:
        o = oracle.determine_phase_from_snapshot(months)
        got = [p for p, cls in ENSEMBLE.items() if cls in labels]
        if n < 2:
            tally.add("ensemble_phase", "undetermined_vs_default" if not got else "mismatch", case, o, got)
        else:
            tally.add("ensemble_phase", "agree" if got == [o] else "mismatch", case, o, got,
                      is_near(near["phase_ensemble"]))

    # --- B. Mann-Kendall phase vs PhaseDetector
    loc_series = [(m["month"], m["loc"]) for m in months]
    if canonical:
        o_mk = oracle.pipeline_phase(loc_series)
        got = [p for p, cls in MK.items() if cls in labels]
        if o_mk is None:
            tally.add("mk_phase", "agree" if not got else "mismatch", case, o_mk, got)
        else:
            tally.add("mk_phase", "agree" if got == [o_mk] else "mismatch", case, o_mk, got,
                      is_near(near["phase_mk"]))

    # --- B2. RQ1 C2 rule set vs the Python oracle
    if canonical:
        o_rb = oracle.rb_stage(loc_series, case.gap, T["rb_dormancy_months"]["value"],
                               T["rb_min_rel_loc_growth_per_year"]["value"])
        got = [k for k, cls in RB.items() if cls in labels]
        want = [o_rb] if o_rb else []
        tally.add("rb_stage", "agree" if got == want else "mismatch", case, o_rb, got,
                  is_near(near["rb_stage"] + near["phase_mk"]))

    # --- C. paper-table laws
    laws = oracle.check_law_conformance(months)
    for r in (ROMAN if legacy else []):
        c_, nc = f"PaperLaw{r}Conformant" in labels, f"PaperLaw{r}NonConformant" in labels
        grp = f"paper_law_{r}"
        if c_ and nc:
            tally.add(grp, "mismatch", case, laws[r], "both (inconsistent)")
        elif n < 2 or (r == "VIII" and n < 4):
            # the old code returns True for everything below the minimum history
            tally.add(grp, "undetermined_vs_default" if not (c_ or nc) else "mismatch", case, laws[r],
                      "conformant" if c_ else "nonconformant" if nc else "undetermined")
        elif not (c_ or nc):
            tally.add(grp, "mismatch", case, laws[r], "undetermined", False, "no label although history suffices")
        else:
            tally.add(grp, "agree" if c_ == laws[r] else "mismatch", case, laws[r],
                      "conformant" if c_ else "nonconformant", is_near(near[grp]))

    # --- D. pipeline laws vs LawConformanceChecker
    if canonical and case.has_pipeline:
        phase = oracle.pipeline_phase(loc_series)
        pl = oracle.pipeline_laws(case.pipeline_metrics(), phase)
        for r in ROMAN:
            ok, evidence = pl[r]
            c_, nc = f"Law{r}Conformant" in labels, f"Law{r}NonConformant" in labels
            grp = f"pipeline_law_{r}"
            insufficient = evidence.startswith("Insufficient") or evidence.startswith("No phase")
            shown = "conformant" if c_ else "nonconformant" if nc else "undetermined"
            if c_ and nc:
                tally.add(grp, "mismatch", case, ok, "both (inconsistent)")
            elif insufficient:
                # old code: insufficient data published as a violation; new: no label
                tally.add(grp, "undetermined_vs_default" if not (c_ or nc) else "mismatch", case,
                          f"{ok} ({evidence})", shown)
            elif not (c_ or nc):
                tally.add(grp, "mismatch", case, ok, "undetermined", False, "no label although history suffices")
            else:
                tally.add(grp, "agree" if c_ == ok else "mismatch", case, ok, shown, is_near(near[grp]))

    # --- E. anti-patterns
    o_pat = set(oracle.detect_patterns(months))
    for old, new in (PATTERNS.items() if canonical else []):
        want, have = old in o_pat, new in labels
        tally.add(f"pattern_{old}", "agree" if want == have else "mismatch", case, want, have,
                  is_near(near[f"pattern_{old}"]))


# ---------------------------------------------------------------------------
# Commit-rule comparison (documented differences, no 100% target)
# ---------------------------------------------------------------------------

def commit_rule_check(reasoner: PelletReasoner) -> dict[str, Any]:
    """AgentCommit/BugFixCommit rules versus the old Python detection."""
    from ontology.population.populate import BUG_FIX_KEYWORDS, RepoMiner

    class _A:
        def __init__(self, name: str) -> None:
            self.name = name

    class _C:
        def __init__(self, msg: str, author: str) -> None:
            self.msg, self.author = msg, _A(author)

    samples: list[tuple[str, str, str, list[str]]] = [  # (subject+body, author, desc, branches)
        ("Add parser", "Alice", "plain", []),
        ("Fix crash\n\nCo-authored-by: Claude <noreply@anthropic.com>", "Alice", "claude trailer", []),
        ("Update\n\nCo-Authored-By: Claude Opus <noreply@anthropic.com>", "Bob", "claude trailer mixed case", []),
        ("Tweak\n\nCo-authored-by: Copilot <copilot@github.com>", "Bob", "copilot trailer", []),
        ("Tweak\n\nCo-authored-by: github-copilot[bot] <x@y>", "Bob", "github-copilot trailer", []),
        ("Tweak\n\nCo-authored-by: Codex <codex@openai.com>", "Bob", "codex trailer", []),
        ("Bump deps", "dependabot[bot]", "bot author", []),
        ("Release", "codex-runner", "codex name substring only", []),
        ("Release", "devin-ai", "devin name substring only", []),
        ("Generated by AI: add docs", "Carol", "message marker only", []),
        ("Regenerate\n\nauto-generated by protoc", "Carol", "message marker (protoc)", []),
        ("Add feature", "Dana", "agent branch (new evidence)", ["codex/add-feature"]),
        ("Add feature", "Dana", "claude branch", ["claude-fix-123"]),
        ("Add feature", "Dana", "copilot-fix branch", ["copilot-fix-9"]),
        ("Add feature", "Dana", "human branch", ["feature/x"]),
        ("Edit CLAUDE.md", "Erin", "touches CLAUDE.md (no signal)", []),
    ]
    subjects = ["Fix typo", "fixes #12", "Prefix handling", "Bugfix: crash", "Hot-fix release", "correct spelling",
                "Add feature", "Refactor module", "Merge pull request #3", "issue 42 resolved", "Prepatch notes",
                "Crashing on start", "catch exception", "failures in CI", "Postfix config", "workaround for X",
                "regression test", "Bug-fix: x", "debugging output", "Unfixable", "fix", "FIX: caps"]
    commits = []
    for i, (msg, author, desc, br) in enumerate(samples):
        commits.append({"id": f"a{i}", "desc": desc, "msg": msg, "author": author, "branches": br})
    for i, s in enumerate(subjects):
        commits.append({"id": f"s{i}", "desc": f"subject: {s}", "msg": s, "author": "Zed", "branches": []})
    evid = []
    for c in commits:
        e = M.extract_commit_evidence(author_name=c["author"], author_email="x@y", message=c["msg"],
                                      branch_names=c["branches"])
        evid.append({"id": c["id"], **e})
    res = reasoner.stage_a(evid)
    rows, diff_agent, diff_bug = [], [], []
    for c in commits:
        iri = AboxWriter().base + "commit/" + c["id"]
        lab = res.labels.get(iri, [])
        old_agent = RepoMiner._detect_agent(_C(c["msg"], c["author"])) is not None
        new_agent = "AgentCommit" in lab
        old_bug = any(k in c["msg"].lower() for k in BUG_FIX_KEYWORDS)
        new_bug = "BugFixCommit" in lab
        rows.append({"desc": c["desc"], "old_agent": old_agent, "new_agent": new_agent,
                     "old_bugfix_keyword_substring": old_bug, "new_bugfix_rule": new_bug,
                     "labels": sorted(lab)})
        if old_agent != new_agent:
            diff_agent.append(c["desc"])
        if old_bug != new_bug:
            diff_bug.append(c["desc"])
    return {
        "n_commits": len(commits), "agent_differences": diff_agent, "bugfix_differences": diff_bug,
        "note": ("Agent differences are the intended WP1 changes: message markers and codex/devin "
                 "author substrings dropped, branch evidence added. Bug-fix differences come from "
                 "word-boundary matching on the subject only (D8)."),
        "stage_a_chunk_timings": res.chunk_timings, "rows": rows,
    }


# ---------------------------------------------------------------------------
# Mechanical check: label-deciding axioms only in the rule modules
# ---------------------------------------------------------------------------

def structure_check() -> dict[str, Any]:
    """Count rules, datatype restrictions and defined classes per module file.

    WP1 "done" test (design 3.1): the five base modules must contain no SWRL
    rule, no datatype restriction and no equivalent-class axiom, so loading the
    TBox without seo-inference / seo-evidence / seo-legacy yields no label at all.
    """
    mod_dir = PROJECT_ROOT / "ontology" / "modules"
    base = ["seo-entities", "seo-processes", "seo-metrics", "seo-laws", "seo-patterns"]
    out: dict[str, Any] = {}
    for name in base + ["seo-inference", "seo-evidence", "seo-legacy"]:
        text = (mod_dir / f"{name}.owl").read_text(encoding="utf-8")
        out[name] = {"swrl_rules": text.count("<swrl:Imp>"),
                     "datatype_restrictions": text.count("owl:withRestrictions"),
                     "equivalent_class_axioms": text.count("<owl:equivalentClass")}
    clean = all(out[n]["swrl_rules"] == 0 and out[n]["datatype_restrictions"] == 0
                and out[n]["equivalent_class_axioms"] == 0 for n in base)
    return {"modules": out, "label_axioms_only_in_rule_modules": clean,
            "inference_module_is_swrl_free": out["seo-inference"]["swrl_rules"] == 0,
            "legacy_module_is_swrl_free": out["seo-legacy"]["swrl_rules"] == 0}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Differential test: ontology vs legacy oracle (Paper 1, WP1)")
    ap.add_argument("--n-random", type=int, default=150)
    ap.add_argument("--n-grid", type=int, default=150)
    ap.add_argument("--legacy-cases", type=int, default=70,
                    help="how many of the cases (scenarios and boundary cases first, then random/grid "
                         "alternating) also go through the slow seo-legacy reasoning")
    ap.add_argument("--seed", type=int, default=20261006)
    ap.add_argument("--batch", type=int, default=30, help="projects per canonical Pellet call")
    ap.add_argument("--legacy-batch", type=int, default=3, help="projects per legacy Pellet call")
    ap.add_argument("--workers", type=int, default=3, help="concurrent Pellet JVMs (max 3)")
    ap.add_argument("--temp-dir", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--skip-commit-check", action="store_true")
    ap.add_argument("--canonical-only", action="store_true",
                    help="skip the seo-legacy phase (MK stages, pipeline laws, patterns only)")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    logging.getLogger("senso.population").setLevel(logging.ERROR)
    workers = max(1, min(args.workers, 3))
    T = load_thresholds()
    rng = random.Random(args.seed)

    fixed = scenario_cases() + boundary_cases(rng) + rb_boundary_cases(rng)
    rand = [gen_random(rng, i) for i in range(args.n_random)]
    grid = [gen_grid(rng, i) for i in range(args.n_grid)]
    mixed: list[Case] = []
    for i in range(max(len(rand), len(grid))):
        mixed += [x[i] for x in (rand, grid) if i < len(x)]
    cases = fixed + mixed
    for c in cases:
        s = c.series()
        if c.kind != "rb_boundary":
            c.gap = random.Random(c.cid).choice(GAPS)
        snap_m = s[-1]["month"] if re.fullmatch(r"\d{4}-\d{2}", str(s[-1]["month"])) else "2025-06"
        last_m = M.month_range("1990-01", snap_m)[-1 - c.gap]
        c.meas = M.project_measurements(s, snapshot_month=snap_m, last_commit_month=last_m)
        c.snaps = M.month_snapshots(s)
    legacy_cases = [] if args.canonical_only else cases[: args.legacy_cases]
    logger.info("%d cases (%s), %d through seo-legacy", len(cases),
                dict(Counter(c.kind for c in cases)), len(legacy_cases))

    t0 = time.perf_counter()
    canon = HermitReasoner(temp_dir=args.temp_dir)
    baseline = canon.jvm_baseline()
    logger.info("HermiT baseline, stage-B TBox, empty ABox: %.2f s", baseline)
    leg = HermitReasoner(legacy=True, temp_dir=args.temp_dir)
    baseline_legacy = None if args.canonical_only else leg.jvm_baseline()
    if baseline_legacy:
        logger.info("HermiT baseline, legacy TBox, empty ABox: %.2f s", baseline_legacy)

    def work(job: tuple[PelletReasoner, list[Case], bool]) -> dict[str, Any]:
        reasoner, b, is_legacy = job
        t = time.perf_counter()
        r = run_batch(reasoner, b, is_legacy)
        r["wall_s"] = time.perf_counter() - t
        logger.info("%s batch of %d: %.1f s (consistent=%s)", "legacy" if is_legacy else "canonical",
                    len(b), r["wall_s"], r["consistent"])
        return r

    jobs = [(canon, cases[i: i + args.batch], False) for i in range(0, len(cases), args.batch)]
    jobs += [(leg, legacy_cases[i: i + args.legacy_batch], True)
             for i in range(0, len(legacy_cases), args.legacy_batch)]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(work, jobs))

    tally = Tally()
    inconsistent = []
    boundary_hits: Counter = Counter()
    canon_labels: dict[str, set[str]] = {}
    legacy_labels: dict[str, set[str]] = {}
    for (reasoner, b, is_legacy), r in zip(jobs, results):
        if not r["consistent"]:
            inconsistent.append({"legacy": is_legacy, "cases": [c.cid for c in b], "error": r["error"]})
            continue
        (legacy_labels if is_legacy else canon_labels).update(r["labels"])
        if is_legacy:
            for c in b:
                c.meas.update(r.get("counts", {}).get(c.cid, {}))
    for c in cases:
        if c.cid in canon_labels:
            compare_case(c, canon_labels[c.cid], T, tally, canonical=True, legacy=False)
        if c.cid in legacy_labels:
            compare_case(c, legacy_labels[c.cid], T, tally, canonical=False, legacy=True)
        for grp, ent in near_entries(c, T).items():
            if is_near(ent):
                boundary_hits[grp] += 1

    agreement: dict[str, dict[str, Any]] = {}
    for grp in sorted(tally.counts):
        cnt = tally.counts[grp]
        decided = cnt["agree"] + cnt["mismatch"] + cnt["mismatch_boundary"]
        agreement[grp] = {
            "n": sum(cnt.values()), "agree": cnt["agree"], "mismatch": cnt["mismatch"],
            "mismatch_boundary": cnt["mismatch_boundary"],
            "undetermined_vs_default": cnt["undetermined_vs_default"],
            "agreement_pct_strict": round(100 * cnt["agree"] / decided, 2) if decided else None,
            "agreement_pct_excluding_boundary": (
                round(100 * cnt["agree"] / (cnt["agree"] + cnt["mismatch"]), 2)
                if cnt["agree"] + cnt["mismatch"] else None),
        }
    total_agree = sum(a["agree"] for a in agreement.values())
    total_hard = sum(a["mismatch"] for a in agreement.values())
    total_bnd = sum(a["mismatch_boundary"] for a in agreement.values())
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "args": {k: str(v) for k, v in vars(args).items()},
        "tbox_sha256": canon.tbox_sha256(),
        "tbox_sha256_with_legacy": leg.tbox_sha256(),
        "n_cases": dict(Counter(c.kind for c in cases)),
        "n_cases_through_legacy": len(legacy_cases),
        "summary": {
            "comparisons_agree": total_agree, "hard_mismatches": total_hard,
            "boundary_mismatches": total_bnd,
            "undetermined_vs_default": sum(a["undetermined_vs_default"] for a in agreement.values()),
            "agreement_pct_strict": round(100 * total_agree / max(total_agree + total_hard + total_bnd, 1), 3),
            "agreement_pct_excluding_boundary": round(100 * total_agree / max(total_agree + total_hard, 1), 3),
        },
        "agreement": agreement,
        "mismatch_classes": dict(Counter(f"{m['label']}:{m['outcome']}" for m in tally.mismatches)),
        "mismatches": tally.mismatches,
        "inconsistent_batches": inconsistent,
        "cases_near_a_threshold_per_group": dict(boundary_hits),
        "timings": {
            "jvm_baseline_canonical_s": baseline, "jvm_baseline_with_legacy_s": baseline_legacy,
            "workers": workers, "batch_size": args.batch, "legacy_batch_size": args.legacy_batch,
            "wall_total_s": time.perf_counter() - t0,
            "batches": [{"legacy": is_legacy, "n_cases": len(b), "wall_s": r["wall_s"], **r["timings"],
                         "abox_triples": r.get("abox_triples"), "abox_individuals": r.get("abox_individuals")}
                        for (_, b, is_legacy), r in zip(jobs, results)],
        },
    }
    report["structure_check"] = structure_check()
    if not args.skip_commit_check:
        report["commit_rules"] = commit_rule_check(PelletReasoner(temp_dir=args.temp_dir))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=1, default=str))
    logger.info("report written to %s", args.out)

    print(f"{'label group':34s} {'n':>5s} {'agree':>6s} {'mism':>5s} {'bound':>5s} {'undet':>5s}  strict%")
    for grp, a in agreement.items():
        print(f"{grp:34s} {a['n']:5d} {a['agree']:6d} {a['mismatch']:5d} {a['mismatch_boundary']:5d} "
              f"{a['undetermined_vs_default']:5d}  {a['agreement_pct_strict']}")
    print(json.dumps(report["summary"], indent=1))
    return 0 if total_hard == 0 and not inconsistent else 1


if __name__ == "__main__":
    sys.exit(main())
