"""Standalone checks for the RQ1 additions to shared/evaluation/statistics.py.

Used by: Paper 1 (RQ1, papers/paper1/rq1-preregistration.md §12).

Not a pytest suite (project convention): an argparse runner that prints a
pass/fail report and exits non-zero on any failure. Validates cohen_kappa against
sklearn.metrics.cohen_kappa_score on square cases, against hand-computed
non-square cases with the predicted-only category 'U', weighted kappa,
per-class metrics, stratified bootstrap shape/strata preservation, verdict
edge cases, Holm adjustment and Cliff's delta.

Usage:
    python shared/evaluation/test_rq1_statistics.py [--seed 7] [--n-random 200]
"""

from __future__ import annotations

import argparse
import logging
import math
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from shared.evaluation import statistics as st  # noqa: E402

logger = logging.getLogger("test_rq1_statistics")
RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(cond), detail))
    logger.info("%s  %s %s", "PASS" if cond else "FAIL", name, detail)


def close(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol


def test_kappa_vs_sklearn(rng: np.random.Generator, n_random: int) -> None:
    from sklearn.metrics import cohen_kappa_score
    worst, worst_w = 0.0, 0.0
    labels = ["A", "S", "P"]
    for _ in range(n_random):
        n = int(rng.integers(10, 150))
        yt = rng.choice(labels, size=n).tolist()
        yp = [t if rng.random() < 0.6 else rng.choice(labels) for t in yt]
        if len(set(yt)) < 2 and len(set(yp)) < 2:
            continue
        k_ref = cohen_kappa_score(yt, yp, labels=labels)
        k = st.cohen_kappa(yt, yp, labels)
        worst = max(worst, abs(k - k_ref))
        w = st.ordinal_disagreement_weights(labels)
        kw_ref = cohen_kappa_score(yt, yp, labels=labels, weights="linear")
        kw = st.cohen_kappa(yt, yp, labels, weights=w)
        worst_w = max(worst_w, abs(kw - kw_ref))
    check("kappa == sklearn (square, unweighted)", worst < 1e-12, f"max|diff|={worst:.2e}")
    check("kappa == sklearn (square, linear weighted)", worst_w < 1e-12,
          f"max|diff|={worst_w:.2e}")
    # quadratic
    yt = ["A", "S", "P", "A", "P", "S", "S", "A"]
    yp = ["A", "P", "P", "S", "S", "S", "A", "A"]
    kq = st.cohen_kappa(yt, yp, labels, st.ordinal_disagreement_weights(labels, scheme="quadratic"))
    check("kappa == sklearn (quadratic weights)",
          close(kq, cohen_kappa_score(yt, yp, labels=labels, weights="quadratic")))


def test_non_square_with_u() -> None:
    yt = ["A", "A", "S", "S", "P", "P"]
    yp = ["A", "U", "S", "A", "P", "P"]
    labels = ["A", "S", "P", "U"]
    # hand: p_o = 4/6, p_e = (2*2 + 2*1 + 2*2 + 0*1)/36 = 10/36, kappa = 7/13
    k = st.cohen_kappa(yt, yp, labels)
    check("non-square kappa with U (hand: 7/13)", close(k, 7 / 13), f"{k:.6f}")
    tab = st.confusion_table(yt, yp, ["A", "S", "P"], labels)
    check("confusion_table shape 3x4 and counts",
          tab.shape == (3, 4) and tab.sum() == 6 and tab[0, 3] == 1 and tab[1, 0] == 1
          and tab[2, 2] == 2)
    w = st.ordinal_disagreement_weights(["A", "S", "P"], ["U"])
    check("ordinal weights: linear |i-j|/2, U row/col = 1, U-U = 0",
          w.shape == (4, 4) and w[0, 2] == 1.0 and w[0, 1] == 0.5 and w[1, 2] == 0.5
          and w[0, 3] == 1 and w[3, 1] == 1 and w[3, 3] == 0 and np.all(np.diag(w) == 0))
    kw = st.cohen_kappa(yt, yp, labels, w)
    check("weighted non-square kappa with U (hand: 0.55)", close(kw, 0.55), f"{kw:.6f}")
    # U never in truth: kappa must not change if U is replaced by a wrong true-class label? (not
    # equal in general) so instead check p_e excludes U: all-U predictions give kappa 0
    k0 = st.cohen_kappa(yt, ["U"] * 6, labels)
    check("all-U prediction gives kappa 0 (U adds 0 to p_e)", close(k0, 0.0), f"{k0}")
    # degenerate: both constant -> NaN
    check("kappa NaN when expected disagreement is 0",
          math.isnan(st.cohen_kappa(["A"] * 4, ["A"] * 4, ["A", "S"])))
    try:
        st.confusion_table(["A", "X"], ["A", "A"], ["A"], ["A"])
        check("confusion_table rejects unknown label", False)
    except ValueError:
        check("confusion_table rejects unknown label", True)


def test_per_class() -> None:
    yt = ["A", "A", "S", "S", "P", "P"]
    yp = ["A", "U", "S", "A", "P", "P"]
    r = st.per_class_metrics(yt, yp, ["A", "S", "P"])
    pc = r["per_class"]
    ok = (close(pc["A"]["precision"], 0.5) and close(pc["A"]["recall"], 0.5)
          and close(pc["S"]["precision"], 1.0) and close(pc["S"]["recall"], 0.5)
          and close(pc["S"]["f1"], 2 / 3) and close(pc["P"]["f1"], 1.0))
    check("per-class P/R/F1 (hand)", ok)
    check("macro-F1 and balanced accuracy (hand)",
          close(r["macro_f1"], (0.5 + 2 / 3 + 1.0) / 3) and close(r["balanced_accuracy"], 2 / 3))
    r2 = st.per_class_metrics(["A", "S", "P", "P"], ["A", "A", "A", "U"], ["A", "S", "P"])
    check("never-predicted class: F1 = 0, precision NaN, U counts against recall",
          r2["per_class"]["S"]["f1"] == 0.0 and math.isnan(r2["per_class"]["S"]["precision"])
          and r2["per_class"]["P"]["recall"] == 0.0)


def test_bootstrap(rng: np.random.Generator) -> None:
    strata = ["ID"] * 30 + ["EVO"] * 30 + ["SERV"] * 30 + ["PO"] * 30
    idx = st.stratified_bootstrap_indices(strata, 200, 123)
    check("bootstrap indices shape (B, N)", idx.shape == (200, 120))
    arr = np.asarray(strata, dtype=object)
    preserved = all(np.all(arr[idx[b]] == arr) for b in range(200))
    check("bootstrap preserves strata per column", preserved)
    # with replacement: some duplicates somewhere
    check("bootstrap resamples with replacement",
          any(len(set(idx[b, :30])) < 30 for b in range(200)))
    idx2 = st.stratified_bootstrap_indices(strata, 200, 123)
    idx3 = st.stratified_bootstrap_indices(strata, 200, 124)
    check("bootstrap deterministic per seed, differs across seeds",
          np.array_equal(idx, idx2) and not np.array_equal(idx, idx3))
    # unequal strata
    s2 = ["a"] * 5 + ["b"] * 1 + ["c"] * 9
    i2 = st.stratified_bootstrap_indices(s2, 50, 1)
    check("unequal strata: single-member stratum always resamples itself",
          np.all(i2[:, 5] == 5) and np.all(i2[:, :5] < 5) and np.all(i2[:, 6:] >= 6))
    # bootstrap_agreement structure & pairing
    truth = rng.choice(["A", "S", "P"], size=120, p=[.5, .25, .25]).tolist()
    # make strata consistent with an order
    p1 = [t if rng.random() < .7 else "U" for t in truth]
    p2 = [t if rng.random() < .8 else rng.choice(["A", "S", "P"]) for t in truth]
    labels = ["A", "S", "P", "U"]
    fns = {"kappa": lambda a, b: st.cohen_kappa(a, b, labels),
           "acc": lambda a, b: float(np.mean(a == b))}
    res = st.bootstrap_agreement(truth, {"X": p1, "Y": p2}, strata, fns, n_boot=300, seed=5,
                                 pairwise_diff=[("Y", "X")])
    lo, hi = res["ci"]["X"]["kappa"]["0.95"]
    lo2, hi2 = res["ci"]["X"]["kappa"]["0.975"]
    check("bootstrap_agreement: point inside 95% CI, 97.5% CI wider",
          lo <= res["point"]["X"]["kappa"] <= hi and lo2 <= lo and hi2 >= hi)
    d = res["diff"]["Y-X"]["acc"]
    check("paired diff point == difference of points",
          close(d["point"], res["point"]["Y"]["acc"] - res["point"]["X"]["acc"]))
    res_b = st.bootstrap_agreement(truth, {"X": p1, "Y": p2}, strata, fns, n_boot=300, seed=5,
                                   pairwise_diff=[("Y", "X")])
    check("bootstrap_agreement reproducible", res == res_b)
    lo_, hi_ = st.percentile_ci(np.arange(1001), 0.95)
    check("percentile_ci", close(lo_, 25.0) and close(hi_, 975.0))
    check("percentile_ci ignores NaN", st.percentile_ci([1.0, float("nan"), 3.0], 0.5) == (1.5, 2.5))


def test_verdict() -> None:
    v = st.agreement_verdict
    rec = {"A": 0.9, "S": 0.5, "P": 0.6}
    check("verdict PASS at exact thresholds (kappa .60, recall .50, undet .10)",
          v(0.60, 0.4001, rec, 0.10) == "PASS")
    check("verdict lb == 0.40 is not PASS (strict >)", v(0.70, 0.40, rec, 0.0) == "WEAK")
    check("verdict kappa .5999 -> WEAK", v(0.5999, 0.5, rec, 0.0) == "WEAK")
    check("verdict recall .49 -> WEAK", v(0.8, 0.6, {**rec, "S": 0.49}, 0.0) == "WEAK")
    check("verdict undetermined 10.01% caps at WEAK", v(0.8, 0.6, rec, 0.1001) == "WEAK")
    check("verdict lb == 0 -> FAIL", v(0.3, 0.0, rec, 0.0) == "FAIL")
    check("verdict lb < 0 -> FAIL even if undet high", v(0.3, -0.1, rec, 0.5) == "FAIL")
    check("verdict lb tiny positive -> WEAK", v(0.3, 1e-6, rec, 0.0) == "WEAK")
    check("verdict NaN kappa -> FAIL", v(float("nan"), float("nan"), rec, 0.0) == "FAIL")
    check("verdict NaN recall blocks PASS",
          v(0.8, 0.6, {**rec, "S": float("nan")}, 0.0) == "WEAK")


def test_holm_and_tests(rng: np.random.Generator) -> None:
    adj = st.holm_adjusted_p([0.01, 0.04, 0.03])
    check("Holm adjusted (hand: .03,.06,.06)", all(close(a, b) for a, b in zip(adj, [0.03, 0.06, 0.06])),
          str(adj))
    check("Holm cap at 1 and monotone", st.holm_adjusted_p([0.5, 0.9]) == [1.0, 1.0])
    check("Holm single p unchanged", st.holm_adjusted_p([0.2]) == [0.2])
    p = rng.random(10).tolist()
    adj = st.holm_adjusted_p(p)
    rej_adj = [a <= 0.05 for a in adj]
    check("Holm adjusted agrees with boolean holm_bonferroni", rej_adj == st.holm_bonferroni(p, 0.05))
    try:
        from statsmodels.stats.multitest import multipletests
        ref = multipletests(p, method="holm")[1].tolist()
        check("Holm == statsmodels", all(close(a, b) for a, b in zip(adj, ref)))
    except ImportError:
        logger.info("statsmodels not installed: skipping cross-check")
    x = rng.normal(1.0, 1.0, 40)
    y = rng.normal(0.0, 1.0, 40)
    _, pg = st.mann_whitney_one_sided(x, y, "greater")
    _, pl = st.mann_whitney_one_sided(x, y, "less")
    _, p2 = st.mann_whitney_one_sided(x, y, "two-sided")
    check("Mann-Whitney one-sided direction", pg < 0.01 and pl > 0.99 and close(p2, 2 * min(pg, pl), 1e-6))
    d, lo, hi = st.cliffs_delta_ci(x, y, n_boot=1000, seed=1)
    d_ref, _ = st.cliffs_delta(x, y)
    check("cliffs_delta_ci point == existing cliffs_delta", close(d, d_ref))
    check("cliffs_delta_ci CI brackets point and in [-1,1]", lo <= d <= hi and -1 <= lo and hi <= 1)
    d, lo, hi = st.cliffs_delta_ci([5, 6, 7], [1, 2, 3], n_boot=200, seed=1)
    check("cliffs_delta_ci perfectly separated = (1,1,1)", (d, lo, hi) == (1.0, 1.0, 1.0))
    d, lo, hi = st.cliffs_delta_ci([1, 2], [1, 2], n_boot=200, seed=1)
    check("cliffs_delta_ci with ties: delta 0", d == 0.0)
    check("cliffs_delta_ci reproducible", st.cliffs_delta_ci(x, y, 300, 9) == st.cliffs_delta_ci(x, y, 300, 9))
    check("cliffs_delta_ci empty -> NaN", math.isnan(st.cliffs_delta_ci([], [1])[0]))


def test_stratum_weighted() -> None:
    yt = ["A", "A", "S", "S"]
    yp = ["A", "A", "S", "A"]
    strata = ["x", "x", "y", "y"]
    labels = ["A", "S", "P", "U"]
    eq = st.stratum_weighted_metrics(yt, yp, strata, {"x": 10, "y": 10}, ["A", "S"], labels)
    check("stratum-weighted equal weights: accuracy = unweighted", close(eq["accuracy"], 0.75))
    wt = st.stratum_weighted_metrics(yt, yp, strata, {"x": 90, "y": 10}, ["A", "S"], labels)
    # weights per repo: x 45, y 5. correct: 45+45+5 = 95 of 100
    check("stratum-weighted accuracy (hand: 0.95)", close(wt["accuracy"], 0.95), f"{wt['accuracy']}")
    check("stratum-weighted recall S (hand: 0.5)", close(wt["recall"]["S"], 0.5))
    check("stratum-weighted confusion total = sum of weights", close(sum(map(sum, wt["weighted_confusion"])), 100.0))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--n-random", type=int, default=200)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    rng = np.random.default_rng(args.seed)
    test_kappa_vs_sklearn(rng, args.n_random)
    test_non_square_with_u()
    test_per_class()
    test_bootstrap(rng)
    test_verdict()
    test_holm_and_tests(rng)
    test_stratum_weighted()
    failed = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    for name, _, detail in failed:
        print(f"FAILED: {name} {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
