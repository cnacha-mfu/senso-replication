"""
Statistical Evaluation Module for SENSO Framework

Provides effect sizes, statistical tests, and analysis utilities
used consistently across all papers in the series.

Used by: All papers
"""

import numpy as np
from typing import Callable, Optional, Sequence


def cliffs_delta(x: list | np.ndarray, y: list | np.ndarray) -> tuple[float, str]:
    """Compute Cliff's delta effect size (non-parametric).

    Returns (delta, magnitude) where magnitude is negligible/small/medium/large.
    """
    x, y = np.asarray(x), np.asarray(y)
    n_x, n_y = len(x), len(y)
    if n_x == 0 or n_y == 0:
        return 0.0, "negligible"

    more = sum(1 for xi in x for yi in y if xi > yi)
    less = sum(1 for xi in x for yi in y if xi < yi)
    delta = (more - less) / (n_x * n_y)

    # Romano et al. (2006) thresholds
    abs_d = abs(delta)
    if abs_d < 0.147:
        magnitude = "negligible"
    elif abs_d < 0.33:
        magnitude = "small"
    elif abs_d < 0.474:
        magnitude = "medium"
    else:
        magnitude = "large"

    return delta, magnitude


def cohens_d(x: list | np.ndarray, y: list | np.ndarray) -> tuple[float, str]:
    """Compute Cohen's d effect size (parametric).

    Returns (d, magnitude) where magnitude is negligible/small/medium/large.
    """
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    nx, ny = len(x), len(y)
    if nx < 2 or ny < 2:
        return 0.0, "negligible"

    pooled_std = np.sqrt(((nx - 1) * np.var(x, ddof=1) + (ny - 1) * np.var(y, ddof=1)) / (nx + ny - 2))
    if pooled_std == 0:
        return 0.0, "negligible"

    d = (np.mean(x) - np.mean(y)) / pooled_std

    abs_d = abs(d)
    if abs_d < 0.2:
        magnitude = "negligible"
    elif abs_d < 0.5:
        magnitude = "small"
    elif abs_d < 0.8:
        magnitude = "medium"
    else:
        magnitude = "large"

    return d, magnitude


def holm_bonferroni(p_values: list[float], alpha: float = 0.05) -> list[bool]:
    """Apply Holm-Bonferroni correction for multiple testing.

    Returns list of booleans: True if the hypothesis is rejected (significant).
    """
    n = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    rejected = [False] * n

    for rank, (orig_idx, p) in enumerate(indexed):
        adjusted_alpha = alpha / (n - rank)
        if p <= adjusted_alpha:
            rejected[orig_idx] = True
        else:
            break  # All subsequent are not rejected

    return rejected


def bootstrap_ci(data: np.ndarray, statistic=np.mean,
                 n_boot: int = 10000, ci: float = 0.95,
                 seed: int = 42) -> tuple[float, float]:
    """Compute bootstrap confidence interval for a statistic."""
    rng = np.random.RandomState(seed)
    boot_stats = []
    for _ in range(n_boot):
        sample = rng.choice(data, size=len(data), replace=True)
        boot_stats.append(statistic(sample))
    boot_stats = np.sort(boot_stats)
    lower = np.percentile(boot_stats, (1 - ci) / 2 * 100)
    upper = np.percentile(boot_stats, (1 + ci) / 2 * 100)
    return lower, upper


def did_regression(panel_df, metric_col: str, post_col: str = "post",
                   treatment_col: str = "treatment",
                   controls: list[str] = None,
                   cluster_col: str = "repo_id"):
    """Run Difference-in-Differences regression.

    Model: Y = α + β₁·Post + β₂·Treatment + β₃·(Post×Treatment) + γ·X + ε

    Args:
        panel_df: Panel dataframe (repo × month)
        metric_col: Dependent variable column name
        post_col: Binary column (1 = post-adoption)
        treatment_col: Binary column (1 = treatment group)
        controls: List of control variable column names
        cluster_col: Column to cluster standard errors on

    Returns:
        statsmodels OLS results object. β₃ = params['post:treatment']
    """
    import statsmodels.formula.api as smf

    formula = f"{metric_col} ~ {post_col} * {treatment_col}"
    if controls:
        formula += " + " + " + ".join(controls)

    model = smf.ols(formula, data=panel_df).fit(
        cov_type="cluster",
        cov_kwds={"groups": panel_df[cluster_col]},
    )
    return model


def parallel_trends_test(panel_df, metric_col: str,
                         time_col: str = "month_num",
                         treatment_col: str = "treatment",
                         pre_only: bool = True):
    """Test the parallel trends assumption for DiD.

    Fits: Y = α + β₁·Time + β₂·Treatment + β₃·(Time×Treatment) + ε
    on pre-adoption data only. If β₃ is not significant, parallel trends holds.
    """
    import statsmodels.formula.api as smf

    df = panel_df[panel_df["post"] == 0] if pre_only else panel_df
    formula = f"{metric_col} ~ {time_col} * {treatment_col}"
    model = smf.ols(formula, data=df).fit()

    interaction_term = f"{time_col}:{treatment_col}"
    p_value = model.pvalues.get(interaction_term, 1.0)

    return {
        "interaction_coef": model.params.get(interaction_term, 0),
        "p_value": p_value,
        "parallel_trends_holds": p_value > 0.05,
        "model_summary": model.summary2().as_text(),
    }


# =============================================================================
# RQ1 agreement statistics (Paper 1, papers/paper1/rq1-preregistration.md §12)
#
# Pure NumPy/SciPy, no file I/O. Random draws use np.random.default_rng(seed).
# The functions above (including the RandomState-based bootstrap_ci) are left
# untouched on purpose.
# =============================================================================

def confusion_table(y_true, y_pred, true_labels, pred_labels) -> np.ndarray:
    """Non-square contingency table: rows = true_labels, columns = pred_labels.

    Predicted-only categories (e.g. 'U' for undetermined) are supported by
    listing them in ``pred_labels`` only. Raises ValueError on a value that is
    not in the respective label list.
    """
    t_idx = {l: i for i, l in enumerate(true_labels)}
    p_idx = {l: i for i, l in enumerate(pred_labels)}
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred differ in length")
    table = np.zeros((len(true_labels), len(pred_labels)), dtype=float)
    for t, p in zip(y_true, y_pred):
        if t not in t_idx:
            raise ValueError(f"true label {t!r} not in true_labels")
        if p not in p_idx:
            raise ValueError(f"predicted label {p!r} not in pred_labels")
        table[t_idx[t], p_idx[p]] += 1
    return table


def _kappa_from_square(table: np.ndarray, weights: np.ndarray | None) -> float:
    n = table.sum()
    if n == 0:
        return float("nan")
    k = table.shape[0]
    w = (1.0 - np.eye(k)) if weights is None else np.asarray(weights, dtype=float)
    observed = table / n
    expected = np.outer(observed.sum(axis=1), observed.sum(axis=0))
    denom = float((w * expected).sum())
    if denom == 0.0:
        return float("nan")
    return float(1.0 - (w * observed).sum() / denom)


def cohen_kappa(y_true, y_pred, labels, weights: np.ndarray | None = None) -> float:
    """Cohen's kappa over the category union ``labels``.

    ``labels`` must include predicted-only categories: a category with no true
    cases adds 0 to p_e (its true marginal is 0) and counts as disagreement in
    p_o. ``weights`` is a *disagreement* matrix (k x k, zero diagonal);
    ``None`` means unweighted (0 on the diagonal, 1 elsewhere). Returns NaN if
    expected disagreement is 0 (kappa undefined).
    """
    table = confusion_table(y_true, y_pred, labels, labels)
    return _kappa_from_square(table, weights)


def ordinal_disagreement_weights(order, extra_max_disagreement=(),
                                 scheme: str = "linear") -> np.ndarray:
    """Disagreement weight matrix for ordered categories plus 'extra' ones.

    Ordered categories get |i-j|/(k-1) (linear) or its square (quadratic),
    k = len(order). Categories in ``extra_max_disagreement`` (e.g. 'U') get
    weight 1 against every other category and 0 against themselves. Row/column
    order is ``list(order) + list(extra_max_disagreement)``.
    """
    if scheme not in ("linear", "quadratic"):
        raise ValueError("scheme must be 'linear' or 'quadratic'")
    k = len(order)
    m = k + len(extra_max_disagreement)
    w = np.ones((m, m))
    np.fill_diagonal(w, 0.0)
    for i in range(k):
        for j in range(k):
            d = abs(i - j) / (k - 1) if k > 1 else 0.0
            w[i, j] = d if scheme == "linear" else d * d
    return w


def per_class_metrics(y_true, y_pred, classes) -> dict:
    """Precision/recall/F1/support per class, macro-F1 and balanced accuracy.

    ``classes`` are the true classes. A prediction outside ``classes`` (e.g.
    'U') is never correct and stays in the recall denominator of its true
    class. Precision is NaN when a class is never predicted; its F1 is then 0.
    Recall is NaN when a class has no true cases (such a class is left out of
    the macro averages).
    """
    yt = np.asarray(list(y_true), dtype=object)
    yp = np.asarray(list(y_pred), dtype=object)
    per: dict = {}
    f1s, recs = [], []
    for c in classes:
        tp = float(np.sum((yt == c) & (yp == c)))
        n_pred = float(np.sum(yp == c))
        n_true = float(np.sum(yt == c))
        prec = tp / n_pred if n_pred > 0 else float("nan")
        rec = tp / n_true if n_true > 0 else float("nan")
        if n_pred == 0:
            f1 = 0.0
        elif prec + rec > 0:
            f1 = 2 * prec * rec / (prec + rec)
        else:
            f1 = 0.0
        per[c] = {"precision": prec, "recall": rec, "f1": f1, "support": int(n_true),
                  "n_predicted": int(n_pred)}
        if n_true > 0:
            f1s.append(f1)
            recs.append(rec)
    return {
        "per_class": per,
        "macro_f1": float(np.mean(f1s)) if f1s else float("nan"),
        "balanced_accuracy": float(np.mean(recs)) if recs else float("nan"),
        "accuracy": float(np.mean(yt == yp)) if len(yt) else float("nan"),
    }


def stratified_bootstrap_indices(strata, n_boot: int, seed: int) -> np.ndarray:
    """(n_boot, N) resampling indices, with replacement within each stratum.

    Column j of every row holds an index from the same stratum as original
    position j, so the stratum composition of each resample equals the
    original and strata can be read off by original position.
    """
    strata = np.asarray(list(strata), dtype=object)
    n = len(strata)
    rng = np.random.default_rng(seed)
    out = np.empty((n_boot, n), dtype=np.int64)
    for s in sorted(set(strata.tolist()), key=str):
        pos = np.flatnonzero(strata == s)
        draws = rng.integers(0, len(pos), size=(n_boot, len(pos)))
        out[:, pos] = pos[draws]
    return out


def percentile_ci(samples, level: float) -> tuple[float, float]:
    """Two-sided percentile interval at ``level`` (e.g. 0.975); NaNs ignored."""
    a = np.asarray(samples, dtype=float)
    a = a[~np.isnan(a)]
    if a.size == 0:
        return float("nan"), float("nan")
    lo = (1.0 - level) / 2.0 * 100.0
    return float(np.percentile(a, lo)), float(np.percentile(a, 100.0 - lo))


def bootstrap_agreement(y_true, preds: dict, strata, metric_fns: dict,
                        n_boot: int = 10_000, seed: int = 20261006,
                        levels=(0.95, 0.975),
                        pairwise_diff: Sequence[tuple[str, str]] = ()) -> dict:
    """Stratified paired bootstrap of agreement metrics for several classifiers.

    ``metric_fns``: name -> f(y_true_array, y_pred_array) -> float. One set of
    index draws is shared by all classifiers and metrics (paired). For each
    (a, b) in ``pairwise_diff`` the difference metric(a) - metric(b) is
    bootstrapped on the same draws.

    Returns {"n", "n_boot", "seed", "point": {clf: {metric: v}},
    "ci": {clf: {metric: {str(level): [lo, hi]}}},
    "diff": {"a-b": {metric: {"point", "ci": {str(level): [lo, hi]}}}}}.
    """
    yt = np.asarray(list(y_true))
    arrs = {k: np.asarray(list(v)) for k, v in preds.items()}
    idx = stratified_bootstrap_indices(strata, n_boot, seed)
    point: dict = {}
    boots: dict = {}
    for name, yp in arrs.items():
        point[name] = {m: float(f(yt, yp)) for m, f in metric_fns.items()}
        boots[name] = {m: np.empty(n_boot) for m in metric_fns}
        for b in range(n_boot):
            ib = idx[b]
            ytb, ypb = yt[ib], yp[ib]
            for m, f in metric_fns.items():
                boots[name][m][b] = f(ytb, ypb)
    ci = {name: {m: {str(l): list(percentile_ci(boots[name][m], l)) for l in levels}
                 for m in metric_fns} for name in arrs}
    diff: dict = {}
    for a, b in pairwise_diff:
        key = f"{a}-{b}"
        diff[key] = {}
        for m in metric_fns:
            d = boots[a][m] - boots[b][m]
            diff[key][m] = {"point": point[a][m] - point[b][m],
                            "ci": {str(l): list(percentile_ci(d, l)) for l in levels}}
    return {"n": int(len(yt)), "n_boot": int(n_boot), "seed": int(seed),
            "point": point, "ci": ci, "diff": diff}


def agreement_verdict(kappa: float, kappa_lb: float, recalls: dict,
                      undetermined_rate: float, kappa_pass: float = 0.60,
                      lb_pass: float = 0.40, recall_pass: float = 0.50,
                      max_undetermined: float = 0.10) -> str:
    """Pre-registered verdict: 'PASS' | 'WEAK' | 'FAIL' (prereg §6.4).

    PASS: kappa >= kappa_pass, kappa_lb > lb_pass, every recall >= recall_pass
    and undetermined_rate <= max_undetermined. FAIL: kappa_lb <= 0 (or kappa
    undefined). WEAK otherwise (so an undetermined rate above the cap, or a
    failed gate, caps a would-be PASS at WEAK, never at FAIL).
    """
    if kappa_lb is None or np.isnan(kappa_lb) or kappa is None or np.isnan(kappa):
        return "FAIL"
    if kappa_lb <= 0:
        return "FAIL"
    recall_ok = all((r is not None) and (not np.isnan(r)) and r >= recall_pass
                    for r in recalls.values())
    if (kappa >= kappa_pass and kappa_lb > lb_pass and recall_ok
            and undetermined_rate <= max_undetermined):
        return "PASS"
    return "WEAK"


def stratum_weighted_metrics(y_true, y_pred, strata, stratum_weights: dict,
                             classes, labels) -> dict:
    """Inverse-sampling-weighted accuracy, recall and kappa (exploratory).

    Each repository in stratum h gets weight stratum_weights[h] / n_h, so
    stratum h contributes stratum_weights[h] in total (population counts).
    ``classes``: true classes; ``labels``: union incl. predicted-only ones.
    """
    yt = np.asarray(list(y_true), dtype=object)
    yp = np.asarray(list(y_pred), dtype=object)
    st = np.asarray(list(strata), dtype=object)
    w = np.zeros(len(yt))
    for h in set(st.tolist()):
        m = st == h
        w[m] = stratum_weights[h] / m.sum()
    l_idx = {l: i for i, l in enumerate(labels)}
    table = np.zeros((len(labels), len(labels)))
    for t, p, wi in zip(yt, yp, w):
        table[l_idx[t], l_idx[p]] += wi
    total = table.sum()
    recalls = {}
    for c in classes:
        row = table[l_idx[c]].sum()
        recalls[c] = float(table[l_idx[c], l_idx[c]] / row) if row > 0 else float("nan")
    valid = [r for r in recalls.values() if not np.isnan(r)]
    return {
        "accuracy": float(np.trace(table) / total) if total > 0 else float("nan"),
        "kappa": _kappa_from_square(table, None),
        "recall": recalls,
        "balanced_accuracy": float(np.mean(valid)) if valid else float("nan"),
        "weighted_confusion": table.tolist(),
        "labels": list(labels),
    }


def mann_whitney_one_sided(x, y, alternative: str) -> tuple[float, float]:
    """Mann-Whitney U test; ``alternative`` in {'greater','less','two-sided'}.

    'greater' tests x stochastically greater than y. Returns (U, p).
    """
    from scipy.stats import mannwhitneyu
    if alternative not in ("greater", "less", "two-sided"):
        raise ValueError("alternative must be 'greater', 'less' or 'two-sided'")
    res = mannwhitneyu(np.asarray(x, dtype=float), np.asarray(y, dtype=float),
                       alternative=alternative)
    return float(res.statistic), float(res.pvalue)


def cliffs_delta_ci(x, y, n_boot: int = 10_000, seed: int = 20261006,
                    level: float = 0.95) -> tuple[float, float, float]:
    """Cliff's delta (x vs y) with a percentile bootstrap CI.

    x and y are resampled independently with replacement. Returns
    (delta, lo, hi). Empty input gives NaNs.
    """
    xa = np.asarray(x, dtype=float)
    ya = np.asarray(y, dtype=float)
    if xa.size == 0 or ya.size == 0:
        return float("nan"), float("nan"), float("nan")
    delta = float(np.mean(np.sign(xa[:, None] - ya[None, :])))
    rng = np.random.default_rng(seed)
    out = np.empty(n_boot)
    chunk = 500
    for s in range(0, n_boot, chunk):
        e = min(n_boot, s + chunk)
        xb = xa[rng.integers(0, xa.size, size=(e - s, xa.size))]
        yb = ya[rng.integers(0, ya.size, size=(e - s, ya.size))]
        out[s:e] = np.sign(xb[:, :, None] - yb[:, None, :]).mean(axis=(1, 2))
    lo, hi = percentile_ci(out, level)
    return delta, lo, hi


def holm_adjusted_p(p_values) -> list[float]:
    """Holm step-down adjusted p-values (monotone, capped at 1).

    Companion to the unchanged boolean ``holm_bonferroni``.
    """
    p = np.asarray(list(p_values), dtype=float)
    m = len(p)
    order = np.argsort(p, kind="stable")
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * p[i])
        adj[i] = min(1.0, running)
    return adj.tolist()


# ---------------------------------------------------------------------------
# WP5 additions (papers/paper1/wp5-analysis-plan.md section 13)
#
# Pure functions: no file I/O, ``np.random.default_rng(seed)`` only. Used by
# experiments/paper1_ontology_manifests/run_wp5_analysis.py. Tested by
# shared/evaluation/test_wp5_statistics.py.
# ---------------------------------------------------------------------------

def _wp5_imports():
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    return sm, smf


_FAMILIES = {"binomial": "Binomial", "gaussian": "Gaussian", "poisson": "Poisson"}


def gee_fit(df, formula: str, groups: str, family: str = "binomial",
            cov_struct: str = "exchangeable", cov_type: str = "bias_reduced") -> dict:
    """GEE with a (bias-reduced) sandwich covariance (plan 6.2).

    Fallback chain on failure (non-convergence, singular or non-finite
    covariance, exception): the same model with an independence working
    correlation; if that fails too, ``converged`` is False and ``params`` is
    empty. ``fallback_used`` is None, ``"independence"`` or ``"failed"``.

    Returns:
        Dict with ``params`` (name -> estimate), ``param_names``, ``cov``
        (ndarray, robust), ``converged``, ``n_clusters``, ``n_obs``,
        ``fallback_used``, ``cov_struct_used``, ``cov_type``.
    """
    import warnings

    sm, smf = _wp5_imports()
    fam = getattr(sm.families, _FAMILIES[family])()
    structs = {"exchangeable": sm.cov_struct.Exchangeable, "independence": sm.cov_struct.Independence}
    order = [cov_struct] + ([] if cov_struct == "independence" else ["independence"])
    n_clusters = int(df[groups].nunique())
    for i, cs in enumerate(order):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                mod = smf.gee(formula, groups=groups, data=df, family=fam, cov_struct=structs[cs]())
                res = mod.fit(cov_type=cov_type)
            cov = np.asarray(res.cov_params())
            ok = (bool(getattr(res, "converged", True)) and np.all(np.isfinite(cov))
                  and np.all(np.isfinite(np.asarray(res.params))) and np.all(np.diag(cov) > 0))
            if ok:
                return {"params": {k: float(v) for k, v in res.params.items()},
                        "param_names": list(res.params.index), "cov": cov, "converged": True,
                        "n_clusters": n_clusters, "n_obs": int(len(df)),
                        "fallback_used": None if i == 0 else "independence",
                        "cov_struct_used": cs, "cov_type": cov_type}
        except Exception:  # noqa: BLE001 - any numerical failure triggers the fallback chain
            continue
    return {"params": {}, "param_names": [], "cov": np.empty((0, 0)), "converged": False,
            "n_clusters": n_clusters, "n_obs": int(len(df)), "fallback_used": "failed",
            "cov_struct_used": None, "cov_type": cov_type}


def wald_contrast(params, cov, L, df_denom: Optional[float] = None) -> dict:
    """Wald test of ``L @ beta`` (plan 6.3).

    Args:
        params: Parameter vector (array-like).
        cov: Robust covariance matrix.
        L: A vector (one contrast) or a (q, p) matrix (joint test).
        df_denom: ``G - 1`` for t / F reference distributions; None uses the
            normal / chi-square distributions.

    Returns:
        One contrast: ``est, se, stat, df, p, kind`` (t or z). Joint test:
        ``est`` (list), ``stat`` (F or chi2), ``df_num, df_denom, p, kind``.
    """
    from scipy import stats as sps

    b = np.asarray(params, dtype=float)
    V = np.asarray(cov, dtype=float)
    Lm = np.atleast_2d(np.asarray(L, dtype=float))
    q = Lm.shape[0]
    est = Lm @ b
    Vc = Lm @ V @ Lm.T
    if np.ndim(L) == 1 or q == 1:
        se = float(np.sqrt(max(Vc[0, 0], 0.0)))
        kind = "t" if df_denom else "z"
        if not se > 0:
            return {"est": float(est[0]), "se": se, "stat": float("nan"), "df": df_denom,
                    "p": float("nan"), "kind": kind}
        t = float(est[0]) / se
        p = 2 * sps.t.sf(abs(t), df_denom) if df_denom else 2 * sps.norm.sf(abs(t))
        return {"est": float(est[0]), "se": se, "stat": t, "df": df_denom, "p": float(p), "kind": kind}
    try:
        w = float(est @ np.linalg.solve(Vc, est))
    except np.linalg.LinAlgError:
        return {"est": est.tolist(), "stat": float("nan"), "df_num": q, "df_denom": df_denom,
                "p": float("nan"), "kind": "F" if df_denom else "chi2"}
    if df_denom:
        F = w / q
        return {"est": est.tolist(), "stat": float(F), "df_num": q, "df_denom": df_denom,
                "p": float(sps.f.sf(F, q, df_denom)), "kind": "F"}
    return {"est": est.tolist(), "stat": w, "df_num": q, "df_denom": None,
            "p": float(sps.chi2.sf(w, q)), "kind": "chi2"}


def _clogit_design(df, formula: str, strata: str):
    """(endog, exog without intercept and without within-stratum-constant columns, names)."""
    import patsy

    y, X = patsy.dmatrices(formula, df, return_type="dataframe")
    X = X.drop(columns=[c for c in X.columns if c == "Intercept"])
    g = df[strata].to_numpy()
    keep = [c for c in X.columns if X[c].groupby(g).std(ddof=0).fillna(0).max() > 0]
    return y.iloc[:, 0].to_numpy(), X[keep], keep


def conditional_logit_by_stratum(df, formula: str, strata: str, n_boot: int = 10_000,
                                 seed: int = 20261006, boot_strata: Optional[str] = None) -> dict:
    """Conditional logistic regression stratified by ``strata`` (plan 6.2 fallback 2).

    The formula's intercept and every column that is constant within a stratum
    are dropped (not identified). P-values come from a task-level cluster
    bootstrap: strata (tasks) are resampled with replacement within the levels
    of ``boot_strata`` (a task-constant column; None = unstratified), the model
    is refitted, and ``p = 2 * min(P(b <= 0), P(b >= 0))`` (+1 corrected,
    capped at 1). Resamples that fail to fit are discarded and counted.

    Returns:
        Dict ``params``, ``param_names``, ``cov`` (bootstrap), ``ci`` (percentile
        95 %), ``p`` (bootstrap), ``n_boot_ok``, ``converged``.
    """
    import warnings

    import pandas as pd
    from statsmodels.discrete.conditional_models import ConditionalLogit

    def fit(d):
        y, X, names = _clogit_design(d, formula, strata)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = ConditionalLogit(y, X.to_numpy(), groups=d[strata].to_numpy()).fit(disp=False)
        return np.asarray(r.params), names

    empty = {"params": {}, "param_names": [], "cov": np.empty((0, 0)), "ci": {}, "p": {},
             "n_boot_ok": 0, "converged": False}
    try:
        b0, names = fit(df)
    except Exception:  # noqa: BLE001
        return empty
    if not np.all(np.isfinite(b0)):
        return empty
    rng = np.random.default_rng(seed)
    tasks = df[[strata] + ([boot_strata] if boot_strata else [])].drop_duplicates(strata).reset_index(drop=True)
    groups = {t: g for t, g in df.groupby(strata)}
    labels = tasks[boot_strata].to_numpy() if boot_strata else np.zeros(len(tasks))
    tid = tasks[strata].to_numpy()
    pos_by = {s: np.flatnonzero(labels == s) for s in sorted(set(labels.tolist()), key=str)}
    boots = []
    for _ in range(n_boot):
        parts = []
        k = 0
        for pos in pos_by.values():
            for j in pos[rng.integers(0, len(pos), len(pos))]:
                part = groups[tid[j]].copy()
                part[strata] = f"{tid[j]}__b{k}"
                k += 1
                parts.append(part)
        try:
            bb, nm = fit(pd.concat(parts, ignore_index=True))
            if nm == names and np.all(np.isfinite(bb)):
                boots.append(bb)
        except Exception:  # noqa: BLE001
            continue
    B = np.asarray(boots)
    out = {"params": dict(zip(names, map(float, b0))), "param_names": names, "n_boot_ok": int(len(B)),
           "converged": True, "cov": np.cov(B.T) if len(B) > 2 else np.full((len(names),) * 2, np.nan),
           "ci": {}, "p": {}}
    for i, nme in enumerate(names):
        if len(B) > 2:
            out["ci"][nme] = list(percentile_ci(B[:, i], 0.95))
            lo = (np.sum(B[:, i] <= 0) + 1) / (len(B) + 1)
            hi = (np.sum(B[:, i] >= 0) + 1) / (len(B) + 1)
            out["p"][nme] = float(min(1.0, 2 * min(lo, hi)))
        else:
            out["ci"][nme], out["p"][nme] = [float("nan")] * 2, float("nan")
    return out


def binomial_mixed_glm_vb(df, fixed_formula: str, vc_formulas: dict) -> dict:
    """Variational-Bayes mixed logit (plan 6.2 secondary estimator (i)).

    Posterior means, SDs, 95 % credible intervals (mean +- 1.96 SD of the
    Gaussian variational posterior) and conditional odds ratios of the fixed
    effects. Never decisive: posterior summaries, not frequentist SEs.
    """
    import warnings

    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = BinomialBayesMixedGLM.from_formula(fixed_formula, vc_formulas, df).fit_vb()
    names = list(res.model.exog_names)
    mean, sd = np.asarray(res.fe_mean), np.asarray(res.fe_sd)
    return {"param_names": names, "post_mean": dict(zip(names, map(float, mean))),
            "post_sd": dict(zip(names, map(float, sd))),
            "cri95": {n: [float(m - 1.96 * s), float(m + 1.96 * s)] for n, m, s in zip(names, mean, sd)},
            "or": {n: float(np.exp(m)) for n, m in zip(names, mean)},
            "or_cri95": {n: [float(np.exp(m - 1.96 * s)), float(np.exp(m + 1.96 * s))]
                         for n, m, s in zip(names, mean, sd)},
            "vc_names": list(res.model.vcp_names),
            "vc_sd_post_mean": [float(np.exp(v)) for v in res.vcp_mean]}


def calibrate_marginal_intercept(p0: float, sigma2: float, n_quad: int = 40, offsets=None) -> float:
    """alpha with E[expit(alpha + offset + sqrt(sigma2) Z)] = p0, by Gauss-Hermite quadrature.

    ``offsets`` (optional array) are fixed linear-predictor shifts of the
    reference rows (e.g. the model effect); the expectation then also averages
    over them.
    """
    from scipy.optimize import brentq
    from scipy.special import expit

    x, w = np.polynomial.hermite_e.hermegauss(n_quad)
    w = w / w.sum()
    off = np.zeros(1) if offsets is None else np.unique(np.asarray(offsets, dtype=float))
    cnt = (np.ones(1) if offsets is None else
           np.array([np.sum(np.asarray(offsets, dtype=float) == o) for o in off], dtype=float))
    cnt = cnt / cnt.sum()
    z = np.sqrt(sigma2) * x

    def f(a: float) -> float:
        return float(sum(c * np.sum(w * expit(a + o + z)) for o, c in zip(off, cnt)) - p0)

    return float(brentq(f, -30.0, 30.0, xtol=1e-12))


def simulate_glmm_binary(design_df, alpha: float, betas: dict, sigma2_repo: float, sigma2_task: float,
                         rng) -> np.ndarray:
    """One draw of binary outcomes: logit p = alpha + sum betas[col]*df[col] + u_repo + v_task.

    ``design_df`` needs ``repo`` and ``task`` columns plus the numeric columns
    named in ``betas``. Returns an int array aligned with the rows.
    """
    from scipy.special import expit

    eta = np.full(len(design_df), float(alpha))
    for col, b in betas.items():
        eta += float(b) * design_df[col].to_numpy(dtype=float)
    for col, s2 in (("repo", sigma2_repo), ("task", sigma2_task)):
        _, codes = np.unique(design_df[col].to_numpy().astype(str), return_inverse=True)
        k = int(codes.max()) + 1
        eta += (rng.normal(0.0, np.sqrt(s2), k) if s2 > 0 else np.zeros(k))[codes]
    return (rng.random(len(design_df)) < expit(eta)).astype(int)


def simulate_power(design_df, p0: float, effects: dict, icc: float, repo_share: float, model_logor: float,
                   test_fn: Callable, n_rep: int = 1000, seed: int = 20261006,
                   alphas=(0.05 / 3, 0.05), model_col: str = "model_is_second") -> dict:
    """Monte-Carlo power of ``test_fn`` under the plan 7.2 data-generating process.

    sigma2 = icc * (pi^2 / 3) / (1 - icc) is the total latent variance, split
    ``repo_share`` (0.2) to repositories and ``1 - repo_share`` to tasks. The
    intercept is calibrated so the marginal P(resolved | reference rows) = p0
    (reference rows: ``is_A == 1`` if that column exists, else rows whose
    ``effects`` columns are all zero).

    Args:
        design_df: Rows with ``repo``, ``task``, the effect columns and ``model_col`` (0/1).
        effects: Column -> conditional log-OR (e.g. ``{"is_C": log 2, "is_D": 0}``).
        test_fn: ``df_with_resolved -> {name: p}``; NaN counts as no rejection.
        alphas: Rejection levels.

    Returns:
        ``{"rejection": {name: {str(alpha): rate}}, "n_rep", "n_failed": {name: n}, "alpha_intercept", "sigma2"}``.
    """
    s2 = icc * (np.pi ** 2 / 3.0) / (1.0 - icc)
    s2r, s2t = repo_share * s2, (1.0 - repo_share) * s2
    betas = dict(effects)
    gam = np.asarray(design_df[model_col], dtype=float) * model_logor
    if "is_A" in design_df.columns:  # explicit reference rows (condition A)
        ref = np.asarray(design_df["is_A"]) == 1
    else:
        ref = np.ones(len(design_df), dtype=bool)
        for c in effects:
            ref &= np.asarray(design_df[c]) == 0
    alpha = calibrate_marginal_intercept(p0, s2, offsets=gam[ref] if ref.any() else gam)
    betas[model_col] = model_logor
    rng = np.random.default_rng(seed)
    d = design_df.copy()
    rej: dict = {}
    failed: dict = {}
    for _ in range(n_rep):
        d["resolved"] = simulate_glmm_binary(design_df, alpha, betas, s2r, s2t, rng)
        for k, p in test_fn(d).items():
            r = rej.setdefault(k, {str(a): 0 for a in alphas})
            failed.setdefault(k, 0)
            if p is None or not np.isfinite(p):
                failed[k] += 1
                continue
            for a in alphas:
                r[str(a)] += int(p < a)
    return {"rejection": {k: {a: v / n_rep for a, v in r.items()} for k, r in rej.items()},
            "n_rep": n_rep, "n_failed": failed, "alpha_intercept": alpha, "sigma2": s2}


def mde_from_grid(power_grid: dict, target: float = 0.80) -> Optional[float]:
    """Smallest effect (grid key) with power >= target; None if none reaches it."""
    ok = [float(k) for k, v in power_grid.items() if v is not None and v >= target]
    return min(ok) if ok else None


def jeffreys_interval(k: int, n: int, level: float = 0.80) -> tuple[float, float]:
    """Jeffreys interval: Beta(k + 1/2, n - k + 1/2) quantiles, with the usual 0 / 1 end-point rule."""
    from scipy.stats import beta

    a = (1.0 - level) / 2.0
    lo = 0.0 if k == 0 else float(beta.ppf(a, k + 0.5, n - k + 0.5))
    hi = 1.0 if k == n else float(beta.ppf(1.0 - a, k + 0.5, n - k + 0.5))
    return lo, hi


def paired_task_bootstrap(df, outcome: str, cond_x: str, cond_ref: str, task_col: str, strata_col: str,
                          n_boot: int = 10_000, seed: int = 20261006, stat: str = "mean",
                          condition_col: str = "condition") -> dict:
    """Task-level paired bootstrap of the difference X - ref (plan 8.2).

    d_t = mean outcome in ``cond_x`` minus mean in ``cond_ref`` over task t's
    runs (NaN outcomes ignored; tasks lacking either side are dropped). Tasks
    are resampled with replacement within ``strata_col``
    (``stratified_bootstrap_indices``); ``stat`` is mean or median of d_t.

    Returns:
        Dict ``estimate``, ``ci`` (percentile 95 %), ``n_tasks``, ``task_ids``,
        ``d`` (array of d_t), ``strata`` (array), ``boot`` (replicates).
    """
    fn = np.mean if stat == "mean" else np.median
    x = df[df[condition_col] == cond_x].groupby(task_col)[outcome].mean()
    r = df[df[condition_col] == cond_ref].groupby(task_col)[outcome].mean()
    common = sorted(set(x.dropna().index) & set(r.dropna().index), key=str)
    if not common:
        return {"estimate": float("nan"), "ci": [float("nan")] * 2, "n_tasks": 0, "task_ids": [],
                "d": np.empty(0), "strata": np.empty(0), "boot": np.empty(0)}
    d = np.array([x[t] - r[t] for t in common])
    st_of = df.drop_duplicates(task_col).set_index(task_col)[strata_col]
    strata = np.array([st_of[t] for t in common], dtype=object)
    idx = stratified_bootstrap_indices(strata, n_boot, seed)
    boot = fn(d[idx], axis=1)
    return {"estimate": float(fn(d)), "ci": list(percentile_ci(boot, 0.95)), "n_tasks": len(common),
            "task_ids": common, "d": d, "strata": strata, "boot": boot}


def two_stage_cluster_bootstrap_indices(repos, tasks, strata, n_boot: int, seed: int) -> list:
    """Two-stage cluster bootstrap over tasks (plan SA6).

    Stage 1 resamples repositories with replacement within the stratum they
    mostly belong to (modal stratum of their tasks); stage 2 resamples the
    tasks of each drawn repository with replacement. Positions index the
    input arrays.

    Returns:
        ``n_boot`` integer arrays of positions into the task arrays (variable length).
    """
    repos = np.asarray(list(repos), dtype=object)
    strata = np.asarray(list(strata), dtype=object)
    if not len(tasks) == len(repos) == len(strata):
        raise ValueError("repos, tasks and strata must have the same length")
    rng = np.random.default_rng(seed)
    by_repo = {r: np.flatnonzero(repos == r) for r in sorted(set(repos.tolist()), key=str)}
    modal = {}
    for r, pos in by_repo.items():
        vals, cnt = np.unique(strata[pos].astype(str), return_counts=True)
        modal[r] = vals[np.argmax(cnt)]
    groups: dict = {}
    for r, s in modal.items():
        groups.setdefault(s, []).append(r)
    out = []
    for _ in range(n_boot):
        parts = []
        for s in sorted(groups):
            rs = groups[s]
            for j in rng.integers(0, len(rs), len(rs)):
                pos = by_repo[rs[j]]
                parts.append(pos[rng.integers(0, len(pos), len(pos))])
        out.append(np.concatenate(parts))
    return out
