#!/usr/bin/env python3
"""Pure measurement functions for the ontology ABox (Paper 1, WP1).

Paper 1 - the measurement/inference boundary of WP1 (design 3.1). Everything
here counts, sums, averages, computes a statistic with no decision cut-off
(Mann-Kendall tau/S/p, Sen slope, CV, half-means, ratios) or extracts raw
strings. Nothing here compares a measurement with a constant, chooses a branch
because of a measured value, or emits a label. Thresholds and labels live in
``ontology/modules/thresholds.yaml`` and ``seo-inference.owl``.

Measurements that need NEW mining (not in the JSS-era pipeline) are marked
``NEW MINING`` in their docstrings and take their data as arguments:

  * real repository LOC per month (``count_loc_at_commit``, D9) - needs a git
    checkout and one commit per month end;
  * Conventional-Commit ``feat:`` counts (``is_feature_subject``, D9) - needs
    commit subjects, which the miner already has;
  * refactoring counts, dependency counts per snapshot, pull-request branch
    names - NOT mined (D9); the functions accept the data as input only.

Series layout. ``monthly_series`` returns one dict per calendar month of the
window, zero-filled (months without commits are present with zero counts).
Optional keys may be absent or None (``loc``, ``bug_fix_count``,
``feature_count``, ``refactoring_count``, ``dependency_count``,
``agent_commit_ratio``); ``project_measurements`` then simply omits the
dependent properties, which the ontology reads as "undetermined".

Usage:
    python ontology/population/measures.py --selftest
"""

from __future__ import annotations

import argparse
import logging
import math
import re
import statistics
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence

logger = logging.getLogger("senso.measures")

DECIMAL_PLACES = 6
"""Reals are rounded to this many places before assertion (design 3.2)."""

# Conventional Commits prefix (decision D9); the ontology has the same regex
# as the FeatureCommit rule. This is parsing a maintainer-declared type.
_FEATURE_RE = re.compile(r"^feat(\([^)]*\))?!?:", re.IGNORECASE)
_TRAILER_RE = re.compile(r"^\s*co-authored-by:.*$", re.IGNORECASE | re.MULTILINE)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def clean_real(x: Optional[float]) -> Optional[float]:
    """Round a real to 6 places; NaN, inf and None become None (not asserted)."""
    if x is None:
        return None
    try:
        if math.isnan(x) or math.isinf(x):
            return None
    except TypeError:
        return None
    return round(float(x), DECIMAL_PLACES)


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    return getattr(obj, key, default)


def month_key(d: datetime) -> str:
    """Return the ``YYYY-MM`` key of a datetime."""
    return d.strftime("%Y-%m")


def month_range(start: str, end: str) -> list[str]:
    """All ``YYYY-MM`` keys from start to end inclusive.

    Args:
        start: First month, ``YYYY-MM``.
        end: Last month, ``YYYY-MM``.

    Returns:
        Chronological list of month keys.
    """
    y, m = int(start[:4]), int(start[5:7])
    ey, em = int(end[:4]), int(end[5:7])
    out: list[str] = []
    while (y, m) <= (ey, em):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def is_feature_subject(subject: str) -> bool:
    """True if a commit subject has a Conventional-Commit ``feat`` prefix (D9)."""
    return bool(_FEATURE_RE.match((subject or "").strip()))


def is_feature_subject_of(commit: Any) -> bool:
    """Commit-level wrapper of ``is_feature_subject`` (message first line)."""
    msg = _get(commit, "message", "") or ""
    return is_feature_subject(msg.strip().split("\n", 1)[0])


# ---------------------------------------------------------------------------
# Commit evidence (replaces RepoMiner._detect_agent; extraction only)
# ---------------------------------------------------------------------------

def extract_commit_evidence(
    *,
    author_name: str,
    author_email: str,
    message: str,
    author_date: Optional[datetime] = None,
    branch_names: Optional[Iterable[str]] = None,
) -> dict[str, Any]:
    """Extract the raw strings the AgentCommit and BugFixCommit rules read.

    No classification happens here: trailers are copied verbatim, the subject is
    the first message line, branch names are passed through (NEW MINING: pull
    request head refs from the GitHub API are not mined, D9).

    Args:
        author_name: Commit author name.
        author_email: Commit author email.
        message: Full commit message.
        author_date: Author date.
        branch_names: Pull-request head branch names, if known.

    Returns:
        Dict keyed by ontology property name.
    """
    subject = (message or "").strip().split("\n", 1)[0]
    out: dict[str, Any] = {
        "authorName": author_name or "",
        "authorEmail": author_email or "",
        "commitSubject": subject,
        "coAuthorTrailer": [t.strip() for t in _TRAILER_RE.findall(message or "")],
        "branchName": list(branch_names or []),
    }
    if author_date is not None:
        out["authorDate"] = author_date
    return out


# ---------------------------------------------------------------------------
# Monthly series (zero-filled)
# ---------------------------------------------------------------------------

def monthly_series(
    commits: Iterable[Any],
    window_start: str,
    window_end: str,
    *,
    bug_fix_predicate: Optional[Callable[[Any], bool]] = None,
    feature_predicate: Optional[Callable[[Any], bool]] = is_feature_subject_of,
    loc_by_month: Optional[Mapping[str, int]] = None,
) -> list[dict[str, Any]]:
    """Aggregate commits into a zero-filled monthly series over a window.

    Fixes the JSS-era ``aggregate_monthly`` bias: months without commits are
    present (all counts zero), so Law I and the CVs see inactive months.

    Commits may be dicts or objects with ``author_date``, ``author_email``,
    ``merge``, ``insertions``, ``deletions``, ``files_changed``,
    ``modified_files`` (list of dicts with ``path``, ``complexity``, ``nloc``)
    and ``message`` / ``hash``.

    Args:
        commits: Commit records.
        window_start: First month of the window (``YYYY-MM``).
        window_end: Last month of the window.
        bug_fix_predicate: Optional commit -> bool taken from the INFERRED
            BugFixCommit class (D8: the keyword rule lives in the ontology).
            When None, bug-fix fields are None and Law VII stays undetermined.
        feature_predicate: Commit -> bool for ``feat:`` commits (D9). Default
            parses the subject.
        loc_by_month: NEW MINING. Real repository LOC at each month end
            (see ``count_loc_at_commit``). Absent months get None.

    Returns:
        One dict per month, chronological.
    """
    months = month_range(window_start, window_end)
    acc: dict[str, dict[str, Any]] = {
        m: {
            "commit_count": 0, "merge_count": 0, "authors": set(),
            "lines_added": 0, "lines_deleted": 0, "files_changed": 0,
            "bug_fix_count": 0, "feature_count": 0,
            "file_complexities": {}, "file_nlocs": {},
        }
        for m in months
    }
    for c in commits:
        key = month_key(_get(c, "author_date"))
        if key not in acc:
            continue
        a = acc[key]
        a["commit_count"] += 1
        if _get(c, "merge", False):
            a["merge_count"] += 1
        a["authors"].add(_get(c, "author_email"))
        a["lines_added"] += _get(c, "insertions", 0) or 0
        a["lines_deleted"] += _get(c, "deletions", 0) or 0
        a["files_changed"] += _get(c, "files_changed", 0) or 0
        if bug_fix_predicate is not None and bug_fix_predicate(c):
            a["bug_fix_count"] += 1
        if feature_predicate is not None and feature_predicate(c):
            a["feature_count"] += 1
        for mf in _get(c, "modified_files", []) or []:
            path = mf.get("path")
            if path and mf.get("complexity") is not None:
                a["file_complexities"][path] = mf["complexity"]
            if path and mf.get("nloc") is not None:
                a["file_nlocs"][path] = mf["nloc"]

    out: list[dict[str, Any]] = []
    for m in months:
        a = acc[m]
        cc = a["commit_count"]
        cx = list(a["file_complexities"].values())
        nl = list(a["file_nlocs"].values())
        row: dict[str, Any] = {
            "month": m,
            "commit_count": cc,
            "merge_count": a["merge_count"],
            "unique_authors": len(a["authors"]),
            "lines_added": a["lines_added"],
            "lines_deleted": a["lines_deleted"],
            "total_churn": a["lines_added"] + a["lines_deleted"],
            "files_changed": a["files_changed"],
            "complexity_mean": (sum(cx) / len(cx)) if cx else 0.0,
            "complexity_max": max(cx) if cx else 0,
            # NLOC of the files touched this month, NOT repository LOC.
            "nloc_touched": sum(nl),
            "loc": (loc_by_month or {}).get(m),
            "feature_count": a["feature_count"] if feature_predicate is not None else None,
            "bug_fix_count": a["bug_fix_count"] if bug_fix_predicate is not None else None,
        }
        row["bug_fix_ratio"] = (
            row["bug_fix_count"] / max(cc, 1) if row["bug_fix_count"] is not None else None
        )
        out.append(row)
    return out


# ---------------------------------------------------------------------------
# Statistics without decision cut-offs
# ---------------------------------------------------------------------------

def cv(values: Sequence[float], *, ddof: int = 0) -> Optional[float]:
    """Coefficient of variation SD / max(mean, 1).

    The max(mean, 1) floor is inherited from the JSS-era code. ``ddof=0`` is the
    population SD (pipeline variant); ``ddof=1`` the sample SD (paper-table
    variant). Which one the paper keeps is a pending decision, so both are
    asserted (``commitCountCV`` and ``commitCountCVSample``).

    Args:
        values: The monthly series.
        ddof: 0 population, 1 sample.

    Returns:
        The CV, or None if undefined (too few values).
    """
    n = len(values)
    if n < 1 + ddof:
        return None
    mean = sum(values) / n
    if ddof == 0:
        var = sum((v - mean) ** 2 for v in values) / n
        sd = var ** 0.5
    else:
        sd = statistics.stdev(values)
    return sd / max(mean, 1)


def half_means(values: Sequence[float]) -> Optional[tuple[float, float]]:
    """Means of the first ``n//2`` and the remaining values.

    Returns:
        (first_half_mean, second_half_mean) or None if the first half is empty.
    """
    n = len(values)
    if n // 2 < 1:
        return None
    first, second = values[: n // 2], values[n // 2:]
    return sum(first) / len(first), sum(second) / len(second)


MK_VARIANTS = ("original", "hamed_rao")


def mann_kendall(values: Sequence[float], variant: str = "original") -> Optional[dict[str, Any]]:
    """Mann-Kendall statistics of a series (pymannkendall).

    Returns the raw statistics only; the trend label is NOT taken from the
    library (``seo:GrowthStage`` etc. are inferred from p and tau).

    Args:
        values: Monthly series (LOC, or commit counts for the comparator).
        variant: ``original`` (``original_test``, decision D6) or ``hamed_rao``
            (``hamed_rao_modification_test``, autocorrelation-corrected; RQ1
            sensitivity S5). The Sen slope is the same in both.

    Returns:
        Dict with n, tau (= S / (n(n-1)/2)), s, p, slope; None if the test fails.
    """
    if len(values) < 2:
        return None
    if variant not in MK_VARIANTS:
        raise ValueError(f"unknown Mann-Kendall variant {variant!r}")
    import warnings

    import pymannkendall as mk

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)  # constant series: 0/0 in the ACF
            test = mk.original_test if variant == "original" else mk.hamed_rao_modification_test
            r = test(list(values))
    except Exception as exc:  # pragma: no cover - library edge cases
        logger.warning("Mann-Kendall failed: %s", exc)
        return None
    if any(isinstance(x, float) and math.isnan(x) for x in (r.Tau, r.p, r.slope)):
        return None
    return {"n": len(values), "tau": float(r.Tau), "s": int(r.s), "p": float(r.p),
            "slope": float(r.slope)}


def months_since_last_commit(snapshot_month: str, last_commit_month: str) -> int:
    """Whole calendar months from the last commit's month to the snapshot month (RQ1 C2).

    ``12 * (year(M_S) - year(M_last)) + (month(M_S) - month(M_last))``; 0 when
    the last commit falls in the snapshot month. Computed over the FULL history
    (author date of the latest commit up to the snapshot), not the window.

    Args:
        snapshot_month: ``YYYY-MM`` of the snapshot.
        last_commit_month: ``YYYY-MM`` of the latest commit author date <= snapshot.

    Returns:
        The integer difference (never negative for commits up to the snapshot).
    """
    return (12 * (int(snapshot_month[:4]) - int(last_commit_month[:4]))
            + (int(snapshot_month[5:7]) - int(last_commit_month[5:7])))


def rel_sen_slope_annual(sen_slope: float, locs: Sequence[float]) -> float:
    """12 * Sen slope / max(median monthly LOC, 1): net growth as a fraction of size per year (RQ1 C2)."""
    return 12.0 * sen_slope / max(statistics.median(locs), 1)


def distinct_authors(commits: Iterable[Any]) -> int:
    """Number of distinct author e-mails over the given commits (descriptive count)."""
    return len({_get(c, "author_email") for c in commits})


def truncated_window(snapshot_month: str, length: int, first_commit_month: Optional[str]) -> list[str]:
    """Months ``max(M_S - length + 1, M_0)`` .. ``M_S`` (RQ1 3): LEFT-truncated, never zero-filled before the first commit.

    Args:
        snapshot_month: ``YYYY-MM`` of the snapshot (M_S).
        length: Lookback length L in months.
        first_commit_month: ``YYYY-MM`` of the first commit (M_0); None = no truncation.

    Returns:
        Chronological month keys.
    """
    y, m = int(snapshot_month[:4]), int(snapshot_month[5:7]) - (length - 1)
    while m < 1:
        y, m = y - 1, m + 12
    start = f"{y:04d}-{m:02d}"
    if first_commit_month and first_commit_month > start:
        start = first_commit_month
    return month_range(start, snapshot_month)


def recent_ratio(monthly_ratios: Sequence[float], window: int = 3) -> float:
    """Sum of the last ``window`` ratios divided by ``window``.

    Mirrors the legacy ``recent_agent_ratio`` (divides by the window length even
    when fewer months exist). Post stage A aggregate: the monthly ratios come
    from the INFERRED AgentCommit class.

    Args:
        monthly_ratios: Monthly agent-commit ratios.
        window: Window length.

    Returns:
        The recent ratio.
    """
    return sum(monthly_ratios[-window:]) / window


def count_ratio(numerator: int, denominator: int) -> Optional[float]:
    """numerator / denominator, or None when the denominator is not positive.

    Used for the stratified counts of inferred months (``correctiveToRisingRatio``).
    """
    return numerator / denominator if denominator > 0 else None


def half_bug_fix_ratios(series: Sequence[Mapping[str, Any]]) -> Optional[tuple[float, float]]:
    """First/second half mean bug-fix ratio over ACTIVE months.

    Needs ``bug_fix_ratio`` (from the inferred BugFixCommit, post stage A).

    Returns:
        (first, second) or None if bug-fix data is absent or too few active months.
    """
    ratios = [m.get("bug_fix_ratio") for m in series if m.get("commit_count", 0) > 0]
    if any(r is None for r in ratios):
        return None
    return half_means(ratios)


# ---------------------------------------------------------------------------
# Per-month snapshots
# ---------------------------------------------------------------------------

def month_snapshots(series: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Per-month measurements (design 3.2, MonthSnapshot).

    ``commitDeltaFromPrev``, ``locDeltaFromPrev``, ``locChangeRatio`` and
    ``complexityDelta`` are absent for the first month. ``correctiveCount`` needs
    ``refactoring_count`` (NEW MINING, not mined) and ``bug_fix_count``.

    Args:
        series: Monthly series.

    Returns:
        One dict per month keyed by ontology property name.
    """
    n = len(series)
    out: list[dict[str, Any]] = []
    for i, m in enumerate(series):
        s: dict[str, Any] = {
            "month": m["month"], "monthIndex": i, "monthIndexFromEnd": n - 1 - i,
            "commitCount": int(m["commit_count"]),
        }
        if m.get("refactoring_count") is not None and m.get("bug_fix_count") is not None:
            s["correctiveCount"] = int(m["refactoring_count"] + m["bug_fix_count"])
        if i > 0:
            p = series[i - 1]
            s["commitDeltaFromPrev"] = int(m["commit_count"] - p["commit_count"])
            if m.get("loc") is not None and p.get("loc") is not None:
                s["locDeltaFromPrev"] = int(m["loc"] - p["loc"])
                s["locChangeRatio"] = clean_real(abs(m["loc"] - p["loc"]) / max(p["loc"], 1))
            if m.get("complexity_mean") is not None and p.get("complexity_mean") is not None:
                s["complexityDelta"] = clean_real(m["complexity_mean"] - p["complexity_mean"])
        out.append(s)
    return out


# ---------------------------------------------------------------------------
# Project-level measurements
# ---------------------------------------------------------------------------

def project_measurements(
    series: Sequence[Mapping[str, Any]],
    *,
    mk_variant: str = "original",
    snapshot_month: Optional[str] = None,
    last_commit_month: Optional[str] = None,
    distinct_authors_in_window: Optional[int] = None,
) -> dict[str, Any]:
    """All project-level measured properties computable from a monthly series.

    Missing inputs omit the dependent properties. Values are ints or reals
    rounded to 6 places; no comparison with any constant is made.

    Args:
        series: Output of ``monthly_series`` (or a scenario in the same layout:
            ``commit_count``, ``loc``, ``complexity_mean``, ``feature_count``,
            ``refactoring_count``, ``bug_fix_count``, ``dependency_count``).
        mk_variant: ``original`` or ``hamed_rao`` (see ``mann_kendall``).
        snapshot_month: With ``last_commit_month``, asserts ``monthsSinceLastCommit``.
        last_commit_month: Month of the latest commit in the full history.
        distinct_authors_in_window: Asserted as ``distinctAuthorsInWindow``.

    Returns:
        Dict keyed by ontology property name.
    """
    n = len(series)
    out: dict[str, Any] = {"monthsObserved": n}
    if n == 0:
        return out

    def col(key: str) -> Optional[list[float]]:
        vals = [m.get(key) for m in series]
        return None if any(v is None for v in vals) else vals

    def put(name: str, v: Any) -> None:
        if isinstance(v, bool):
            raise TypeError(name)
        if isinstance(v, float):
            v = clean_real(v)
        if v is not None:
            out[name] = v

    if snapshot_month is not None and last_commit_month is not None:
        put("monthsSinceLastCommit", months_since_last_commit(snapshot_month, last_commit_month))
    if distinct_authors_in_window is not None:
        put("distinctAuthorsInWindow", int(distinct_authors_in_window))

    commits = col("commit_count")
    if commits is not None:
        cmk = mann_kendall(commits, mk_variant)
        if cmk:
            put("commitMKTau", cmk["tau"])
            put("commitMKpValue", cmk["p"])
        active = sum(1 for c in commits if c > 0)
        put("activeMonthCount", active)
        put("activeMonthRatio", active / n)
        put("meanMonthlyCommits", sum(commits) / n)
        put("commitsLast3Months", int(sum(commits[-3:])))
        put("commitCountCV", cv(commits, ddof=0))
        put("commitCountCVSample", cv(commits, ddof=1))
        hc = half_means_commit_stats(commits)
        if hc:
            put("commitHalfRatio", hc[0])
            put("commitSecondHalfMean", hc[1])
    churn = col("total_churn")
    if churn is not None:
        put("churnCV", cv(churn))
    added = col("lines_added")
    if added is not None:
        put("linesAddedCV", cv(added))
    merge = col("merge_count")
    if merge is not None:
        put("mergeMonthRatio", sum(1 for x in merge if x > 0) / n)
    authors = col("unique_authors")
    if authors is not None:
        put("multiAuthorMonthRatio", sum(1 for x in authors if x > 1) / n)

    cx_all = col("complexity_mean")
    if cx_all is not None:
        cx_pos = [c for c in cx_all if c > 0]
        put("complexityMonthCount", len(cx_pos))
        hm = half_means(cx_pos)
        if hm:
            put("complexityHalfMeanFirst", hm[0])
            put("complexityHalfMeanSecond", hm[1])
            put("complexityHalfMeanChange", hm[1] - hm[0])
            put("complexityHalfMeanChange", hm[1] - hm[0])
        first, last = cx_all[0], cx_all[-1]
        put("complexityFirst", first)
        put("complexityLast", last)
        put("complexityChange", last - first)
        put("complexityGrowthRate", (last - first) / max(first, 1))
        put("monthlyComplexityGrowth", (last - first) / max(n - 1, 1) / max(first, 1))

    bf = half_bug_fix_ratios(series)
    if bf:
        put("bugFixRatioFirstHalf", bf[0])
        put("bugFixRatioSecondHalf", bf[1])
        if bf[0] > 0:
            put("bugFixHalfRatio", bf[1] / bf[0])

    locs = col("loc")
    if locs is not None:
        put("locSeriesLength", n)
        mk_r = mann_kendall(locs, mk_variant)
        if mk_r:
            put("locRelSenSlopeAnnual", rel_sen_slope_annual(mk_r["slope"], locs))
            put("locMKTau", mk_r["tau"])
            put("locMKS", mk_r["s"])
            put("locMKpValue", mk_r["p"])
            put("locSenSlope", mk_r["slope"])
        put("locStart", int(locs[0]))
        put("locEnd", int(locs[-1]))
        put("locDelta", int(locs[-1] - locs[0]))
        put("locGrowthRate", (locs[-1] - locs[0]) / max(locs[0], 1))
        put("locChangePct", (locs[-1] - locs[0]) / max(locs[0], 1) * 100)
        if locs[0] > 0:
            put("locEndToStartRatio", locs[-1] / locs[0])
        if cx_all is not None:
            lg = (locs[-1] - locs[0]) / max(locs[0], 1)
            cg = (cx_all[-1] - cx_all[0]) / max(cx_all[0], 1)
            if lg != 0:
                put("complexityToLocGrowthRatio", cg / lg)
            if cg != 0:
                put("locToComplexityGrowthRatio", lg / cg)
        if n >= 3:
            l3 = locs[-3:]
            put("locGrowthLast3", (l3[-1] - l3[0]) / max(l3[0], 1))

    feats = col("feature_count")
    if feats is not None:
        mid = n // 2
        f1, f2 = int(sum(feats[:mid])), int(sum(feats[mid:]))
        put("featureCommitsFirstHalf", f1)
        put("featureCommitsSecondHalf", f2)
        put("featureCommitsTotal", f1 + f2)
        if f1 > 0:
            put("featureSecondToFirstRatio", f2 / f1)
        if locs is not None:
            put("locDeltaPerFeature", (locs[-1] - locs[0]) / max(f1 + f2, 1))

    refs = col("refactoring_count")
    if refs is not None and commits is not None:
        put("refactoringCommits", int(sum(refs)))
        put("refactoringRatio", sum(refs) / max(sum(commits), 1))
    deps = col("dependency_count")
    if deps is not None:
        put("dependencyCountStart", int(deps[0]))
        put("dependencyCountEnd", int(deps[-1]))
        put("dependencyGrowthRate", (deps[-1] - deps[0]) / max(deps[0], 1))
    ag = col("agent_commit_ratio")
    if ag is not None:
        put("recentAgentCommitRatio", recent_ratio(ag))

    snaps = month_snapshots(series)
    if all("correctiveCount" in s for s in snaps) and n >= 3:
        put("correctiveLast2Months", sum(s["correctiveCount"] for s in snaps[-2:]))
    return out


def half_means_commit_stats(commits: Sequence[float]) -> Optional[tuple[float, float]]:
    """Commit-vote statistics of the legacy ensemble.

    ``mid = n // 2``; first-half mean = sum(c[:mid]) / max(mid, 1); second-half
    mean = sum(c[mid:]) / max(n - mid, 1); ratio = second / max(first, 1).

    Returns:
        (ratio, second_half_mean) or None for n < 2.
    """
    n = len(commits)
    if n < 2:
        return None
    mid = n // 2
    first = sum(commits[:mid]) / max(mid, 1)
    second = sum(commits[mid:]) / max(n - mid, 1)
    return second / max(first, 1), second


# ---------------------------------------------------------------------------
# NEW MINING: real repository LOC per month (decision D9)
# ---------------------------------------------------------------------------

def month_end_commits(
    repo_path: str | Path, months: Sequence[str], ref: str = "HEAD", *, first_parent: bool = False,
) -> dict[str, Optional[str]]:
    """Last commit reachable from ``ref`` with committer date <= each month end.

    NEW MINING. Months before the first commit map to None. The cut-off is the
    last second of the month (UTC when the process runs with TZ=UTC), so a
    commit stamped exactly at the next month's first second belongs to the next.

    Args:
        repo_path: Path to a git checkout or bare clone.
        months: ``YYYY-MM`` keys.
        ref: Branch or ref to walk.
        first_parent: Follow only first parents (the default-branch spine; RQ1 3).

    Returns:
        Mapping month -> commit sha (or None).
    """
    import calendar

    out: dict[str, Optional[str]] = {}
    for m in months:
        y, mo = int(m[:4]), int(m[5:7])
        last_day = calendar.monthrange(y, mo)[1]
        until = f"{y:04d}-{mo:02d}-{last_day:02d}T23:59:59"
        cmd = ["git", "-C", str(repo_path), "rev-list", "-1", f"--before={until}"]
        if first_parent:
            cmd.append("--first-parent")
        r = subprocess.run(cmd + [ref], capture_output=True, text=True, check=False)
        sha = r.stdout.strip()
        out[m] = sha or None
    return out


def count_loc_at_commit(
    repo_path: str | Path,
    commit: str,
    *,
    extensions: Optional[Sequence[str]] = None,
    work_dir: Optional[str | Path] = None,
) -> int:
    """Repository LOC (non-comment, non-blank) at a commit, via lizard.

    NEW MINING (D9). Exports the commit with ``git archive`` into a temporary
    directory and sums lizard's per-file NLOC. Falls back to counting non-blank
    lines when lizard is unavailable. No threshold is applied.

    Args:
        repo_path: Path to a git checkout.
        commit: Commit sha.
        extensions: Optional file-extension whitelist (``[".py", ".js"]``);
            default lets lizard decide by extension.
        work_dir: Parent directory for the temporary export.

    Returns:
        Total NLOC.
    """
    with tempfile.TemporaryDirectory(dir=work_dir) as tmp:
        arch = subprocess.Popen(
            ["git", "-C", str(repo_path), "archive", commit], stdout=subprocess.PIPE)
        subprocess.run(["tar", "-x", "-C", tmp], stdin=arch.stdout, check=True)
        arch.wait()
        files = [str(p) for p in Path(tmp).rglob("*") if p.is_file()
                 and (extensions is None or p.suffix in extensions)]
        try:
            import lizard

            total = 0
            for info in lizard.analyze_files(files):
                total += info.nloc
            return total
        except ImportError:  # pragma: no cover
            total = 0
            for f in files:
                try:
                    total += sum(1 for line in open(f, errors="ignore") if line.strip())
                except OSError:
                    pass
            return total


def loc_by_month_from_checkout(
    repo_path: str | Path, months: Sequence[str], *, ref: str = "HEAD",
    extensions: Optional[Sequence[str]] = None,
) -> dict[str, Optional[int]]:
    """NEW MINING (D9): LOC at every month end of a window.

    Args:
        repo_path: Git checkout.
        months: Window months.
        ref: Ref to walk.
        extensions: Optional extension whitelist.

    Returns:
        Mapping month -> LOC (None before the first commit).
    """
    shas = month_end_commits(repo_path, months, ref)
    cache: dict[str, int] = {}
    out: dict[str, Optional[int]] = {}
    for m in months:
        sha = shas[m]
        if sha is None:
            out[m] = None
            continue
        if sha not in cache:
            cache[sha] = count_loc_at_commit(repo_path, sha, extensions=extensions)
        out[m] = cache[sha]
    return out


# ---------------------------------------------------------------------------
# WP5: module partition and module-level measurements (wp5-analysis-plan.md 3.2)
# ---------------------------------------------------------------------------

MODULE_TEST_RE = re.compile(r"(^|/)(tests?|testing)/|(^|/)test_[^/]*\.py$|_test\.py$|(^|/)conftest\.py$")
"""Test files of the module partition (WP5 3.2 item 1); the task's test patch adds more."""
MODULE_ROOT_EXCLUDED = frozenset(
    "tests test testing docs doc examples example benchmarks benchmark scripts tools build dist".split())
"""Directory names that never become package roots."""
MODULE_EXCLUDED_ROOT_FILES = frozenset({"setup.py", "noxfile.py", "tasks.py", "conf.py"})
"""Root-level files that belong to no module."""


def is_test_path(path: str, test_patch_files: Iterable[str] = ()) -> bool:
    """True if a path is a test file (regex of WP5 3.2 or touched by the task's test patch)."""
    return bool(MODULE_TEST_RE.search(path)) or path in set(test_patch_files)


def module_source_paths(
    paths: Iterable[str], is_source: Callable[[str], bool], test_patch_files: Iterable[str] = (),
) -> list[str]:
    """Sorted non-test Python source paths: ``is_source(path)``, ``.py``, not a test file (WP5 3.2).

    Args:
        paths: Repository paths (e.g. ``ls-tree -r``).
        is_source: The LOC instrument's ``is_source_path`` (extension whitelist, vendored dirs).
        test_patch_files: Paths touched by the task's test patch.
    """
    tp = set(test_patch_files)
    return sorted(p for p in set(paths)
                  if p.endswith(".py") and is_source(p) and not is_test_path(p, tp))


def package_roots(source_paths: Iterable[str]) -> frozenset[str]:
    """Package roots of the base tree (WP5 3.2 item 2).

    Every top-level directory with an ``__init__.py`` and every immediate subdirectory
    of ``src/`` (with or without ``__init__.py``), minus ``MODULE_ROOT_EXCLUDED``.
    When ``src/__init__.py`` exists, ``src`` is an ordinary root and its subdirectories
    are not roots of their own.

    Args:
        source_paths: Output of ``module_source_paths`` for the base tree.
    """
    paths = set(source_paths)
    roots: set[str] = set()
    for p in paths:
        parts = p.split("/")
        if len(parts) >= 2 and parts[0] not in MODULE_ROOT_EXCLUDED and f"{parts[0]}/__init__.py" in paths:
            roots.add(parts[0])
    if "src/__init__.py" not in paths:
        for p in paths:
            parts = p.split("/")
            if len(parts) >= 3 and parts[0] == "src" and parts[1] not in MODULE_ROOT_EXCLUDED:
                roots.add(f"src/{parts[1]}")
    return frozenset(roots)


def module_of(path: str, roots: frozenset[str], test_patch_files: Iterable[str] = ()) -> Optional[str]:
    """Module id of a Python source path under the partition (WP5 3.2 items 1, 3, 4).

    ``R/sub`` for a subpackage and ``R/name.py`` for a module file directly under the
    package root R; otherwise the top-level directory, or the file itself at the root.
    Test files and the excluded root files map to None. The same mapping applies to
    historical paths.
    """
    if is_test_path(path, test_patch_files):
        return None
    parts = path.split("/")
    root = None
    if len(parts) >= 2 and parts[0] in roots:
        root = parts[0]
    elif len(parts) >= 3 and parts[0] == "src" and f"src/{parts[1]}" in roots:
        root = f"src/{parts[1]}"
    if root is not None:
        rest = parts[len(root.split("/")):]
        return f"{root}/{rest[0]}"
    if len(parts) == 1:
        return None if path in MODULE_EXCLUDED_ROOT_FILES else path
    return parts[0]


def add_months(dt: datetime, k: int) -> datetime:
    """``dt`` shifted by ``k`` calendar months (day clamped to the target month's length)."""
    import calendar

    y, m = divmod(dt.year * 12 + (dt.month - 1) + k, 12)
    day = min(dt.day, calendar.monthrange(y, m + 1)[1])
    return dt.replace(year=y, month=m + 1, day=day)


def module_measurements(
    commits: Iterable[Mapping[str, Any]],
    module_loc: Mapping[str, int],
    S: datetime,
    window_months: int,
    module_fn: Callable[[str], Optional[str]],
    last_change_month: Optional[Mapping[str, str]] = None,
) -> dict[str, dict[str, Any]]:
    """Module-level measurements anchored at S (WP5 3.2); no thresholds, no labels.

    Window: non-merge ancestor commits with author date in (S - W months, S].
    A commit touches a module when one of its Python source files maps to it; its lines
    changed are the numstat insertions plus deletions of those files.

    Args:
        commits: Dicts with ``author_date`` (aware), ``merge`` and ``files``
            (list of ``(path, insertions, deletions)``).
        module_loc: Non-blank LOC at the base tree per module; defines the module set
            (paths mapping to another module are ignored).
        S: Committer date of the base commit (UTC).
        window_months: W.
        module_fn: Path -> module id or None.
        last_change_month: Module -> ``YYYY-MM`` of its last commit over the full history.

    Returns:
        ``{module: {property: value}}`` keyed by ontology property name; ``moduleRelChurnInWindow``
        only where LOC > 0; ``moduleMonthsSinceLastChange`` only where a last change is known.
    """
    lo = add_months(S, -window_months)
    acc: dict[str, dict[str, Any]] = {m: {"c": 0, "months": set(), "lines": 0} for m in module_loc}
    for c in commits:
        d = c["author_date"]
        if c.get("merge") or not (lo < d <= S):
            continue
        per: dict[str, int] = {}
        for path, ins, dele in c["files"]:
            m = module_fn(path)
            if m in acc:
                per[m] = per.get(m, 0) + int(ins) + int(dele)
        for m, lines in per.items():
            a = acc[m]
            a["c"] += 1
            a["months"].add(month_key(d))
            a["lines"] += lines
    out: dict[str, dict[str, Any]] = {}
    sm = month_key(S)
    for m in sorted(module_loc):
        a, loc = acc[m], int(module_loc[m])
        row: dict[str, Any] = {
            "modulePath": m, "moduleLoc": loc, "moduleCommitsInWindow": a["c"],
            "moduleChangeMonthsInWindow": len(a["months"]), "moduleLinesChangedInWindow": a["lines"]}
        if loc > 0:
            row["moduleRelChurnInWindow"] = clean_real(a["lines"] / loc)
        if last_change_month and last_change_month.get(m):
            row["moduleMonthsSinceLastChange"] = months_since_last_commit(sm, last_change_month[m])
        out[m] = row
    return out


MODULE_RULE_INPUTS = ("moduleChangeMonthsInWindow", "moduleRelChurnInWindow")


def module_abox_properties(row: Mapping[str, Any]) -> dict[str, Any]:
    """The properties of a module row that are asserted in the ABox.

    A module with LOC 0 has no ``moduleRelChurnInWindow``; its other rule input
    (``moduleChangeMonthsInWindow``) is withheld too, so that the module is
    undetermined instead of ActiveModule through the change-months branch alone.
    """
    if row.get("moduleLoc", 0) > 0:
        return dict(row)
    return {k: v for k, v in row.items() if k not in MODULE_RULE_INPUTS}


# ---------------------------------------------------------------------------
# Scenario adapter (YAML scenario months -> series layout)
# ---------------------------------------------------------------------------

def series_from_scenario_months(months: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Convert a scenarios.yaml month list to the monthly-series layout."""
    out = []
    for m in months:
        out.append({
            "month": str(m.get("month", "")),
            "commit_count": m["commits"],
            "loc": m["loc"],
            "complexity_mean": m["complexity_avg"],
            "feature_count": m.get("new_features", 0),
            "refactoring_count": m.get("refactorings", 0),
            "bug_fix_count": m.get("bug_fixes", 0),
            "dependency_count": m.get("dependency_count"),
            "agent_commit_ratio": m.get("agent_commit_ratio", 0),
        })
    return out


def _selftest() -> int:
    """Tiny sanity checks of the pure functions."""
    series = [
        {"month": f"2025-{i + 1:02d}", "commit_count": c, "loc": l, "complexity_mean": 2.0 + i * 0.1,
         "feature_count": 1, "refactoring_count": 0, "bug_fix_count": 1, "total_churn": 10 * c,
         "lines_added": 5 * c, "merge_count": i % 2, "unique_authors": 1 + i % 3, "bug_fix_ratio": 0.1}
        for i, (c, l) in enumerate([(5, 100), (0, 100), (7, 130), (9, 160), (4, 170), (6, 190)])
    ]
    m = project_measurements(series)
    assert m["monthsObserved"] == 6 and m["activeMonthCount"] == 5, m
    assert abs(m["locMKTau"] - 0.9333) < 1e-3, m
    assert month_range("2024-11", "2025-02") == ["2024-11", "2024-12", "2025-01", "2025-02"]
    ev = extract_commit_evidence(author_name="a", author_email="b",
                                 message="feat: x\n\nCo-authored-by: Claude <n@anthropic.com>")
    assert ev["coAuthorTrailer"] == ["Co-authored-by: Claude <n@anthropic.com>"], ev
    assert is_feature_subject("feat(core)!: x") and not is_feature_subject("prefix: x")
    assert months_since_last_commit("2025-06", "2025-06") == 0
    assert months_since_last_commit("2025-06", "2024-05") == 13
    assert truncated_window("2025-06", 3, None) == ["2025-04", "2025-05", "2025-06"]
    assert truncated_window("2025-06", 36, "2025-02") == ["2025-02", "2025-03", "2025-04", "2025-05", "2025-06"]
    assert abs(rel_sen_slope_annual(10, [2380, 2390, 2400, 2410, 2420]) - 0.05) < 1e-12
    assert mann_kendall([1, 2, 3, 4, 5, 7, 6, 9], "hamed_rao")["tau"] > 0.9
    print("selftest ok")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Measurement functions (Paper 1, WP1)")
    ap.add_argument("--selftest", action="store_true")
    if ap.parse_args().selftest:
        sys.exit(_selftest())
    ap.print_help()
