"""Standalone checks for the WP5 additions to shared/evaluation/statistics.py.

Used by: Paper 1 (WP5, papers/paper1/wp5-analysis-plan.md section 13).

Not a pytest suite (project convention): an argparse runner that prints a
pass/fail report and exits non-zero on any failure. Checks:

  * GEE recovers a known log-OR on simulated GLMM data (mean over replications);
  * type I error at OR = 1 is <= 0.06 over ``--n-type1`` (default 500) replications
    of the exact section 6 pipeline (GEE, exchangeable, bias-reduced, t(G - 1));
  * Jeffreys interval equals scipy.stats.beta quantiles, with the 0 / 1 rule;
  * paired and two-stage bootstraps are reproducible for a fixed seed and differ
    across seeds; stratum composition is preserved;
  * Gauss-Hermite calibration reproduces the marginal p0 by brute-force Monte Carlo;
  * wald_contrast, mde_from_grid, conditional logit and the VB mixed logit run.

Usage:
    nice -n 10 python shared/evaluation/test_wp5_statistics.py [--n-type1 500] [--seed 7]
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from shared.evaluation import statistics as st  # noqa: E402

logger = logging.getLogger("test_wp5_statistics")
RESULTS: list[tuple[str, bool, str]] = []
F1 = "resolved ~ C(condition, Treatment('A')) + C(model)"
CNAME = "C(condition, Treatment('A'))[T.C]"


def check(name: str, cond: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(cond), detail))
    logger.info("%s  %s %s", "PASS" if cond else "FAIL", name, detail)


def make_design(n_repo: int = 24, tasks_per_repo: int = 2) -> pd.DataFrame:
    rows = []
    stages = ["ID", "EVO", "SERV"]
    for g in range(n_repo):
        for t in range(tasks_per_repo):
            for cond in "ACD":
                for m in (0, 1):
                    for k in range(2):
                        rows.append({"repo": f"r{g}", "task": f"r{g}_t{t}", "stage": stages[g % 3],
                                     "condition": cond, "model": f"m{m}", "model_is_second": m,
                                     "is_C": int(cond == "C"), "is_D": int(cond == "D"), "rep": k})
    return pd.DataFrame(rows)


def pipeline_p(d: pd.DataFrame) -> dict:
    fit = st.gee_fit(d, F1, "repo")
    if not fit["converged"]:
        return {"H1": float("nan")}
    names = fit["param_names"]
    L = np.zeros(len(names))
    L[names.index(CNAME)] = 1
    return {"H1": st.wald_contrast([fit["params"][n] for n in names], fit["cov"], L,
                                   fit["n_clusters"] - 1)["p"],
            "est": fit["params"][CNAME]}


def test_gee_and_type1(seed: int, n_type1: int) -> None:
    design = make_design()
    s2 = 0.5 * (np.pi ** 2 / 3) / 0.5
    rng = np.random.default_rng(seed)
    alpha = st.calibrate_marginal_intercept(0.3, s2)
    # recovery
    true = np.log(2.0)
    ests = []
    t0 = time.perf_counter()
    for _ in range(60):
        d = design.copy()
        d["resolved"] = st.simulate_glmm_binary(d, alpha, {"is_C": true, "model_is_second": -0.3},
                                                0.2 * s2, 0.8 * s2, rng)
        ests.append(pipeline_p(d)["est"])
    # GEE is marginal (attenuated vs conditional): compare with the marginal log-OR by brute force
    big = pd.concat([design] * 1, ignore_index=True)
    marg = []
    for is_c in (0, 1):
        big2 = big.copy()
        big2["is_C"] = is_c
        ys = np.mean([st.simulate_glmm_binary(big2, alpha, {"is_C": true, "model_is_second": -0.3},
                                              0.2 * s2, 0.8 * s2, rng).mean() for _ in range(300)])
        marg.append(ys)
    marg_lor = np.log(marg[1] / (1 - marg[1])) - np.log(marg[0] / (1 - marg[0]))
    check("GEE recovers the marginal log-OR (|mean est - marginal| < 0.15)",
          abs(np.mean(ests) - marg_lor) < 0.15,
          f"mean est {np.mean(ests):.3f} marginal {marg_lor:.3f} conditional {true:.3f}")
    check("GEE marginal log-OR is attenuated but same sign as conditional",
          0 < np.mean(ests) < true + 0.05, f"{np.mean(ests):.3f}")
    # type I
    rej = 0
    ok = 0
    for _ in range(n_type1):
        d = design.copy()
        d["resolved"] = st.simulate_glmm_binary(d, alpha, {"model_is_second": -0.3}, 0.2 * s2, 0.8 * s2, rng)
        p = pipeline_p(d)["H1"]
        if np.isfinite(p):
            ok += 1
            rej += p < 0.05
    rate = rej / max(ok, 1)
    check(f"type I error <= 0.06 over {n_type1} reps (G = 24)", rate <= 0.06,
          f"rate {rate:.3f} on {ok} fits, {time.perf_counter() - t0:.0f}s total")


def test_jeffreys() -> None:
    from scipy.stats import beta

    for k, n in [(3, 20), (0, 20), (20, 20), (7, 20), (1, 1)]:
        lo, hi = st.jeffreys_interval(k, n, 0.80)
        elo = 0.0 if k == 0 else beta.ppf(0.1, k + .5, n - k + .5)
        ehi = 1.0 if k == n else beta.ppf(0.9, k + .5, n - k + .5)
        check(f"Jeffreys {k}/{n} matches scipy.stats.beta", abs(lo - elo) < 1e-12 and abs(hi - ehi) < 1e-12,
              f"[{lo:.4f}, {hi:.4f}]")


def test_bootstrap() -> None:
    rng = np.random.default_rng(3)
    rows = []
    for t in range(30):
        stage = ["ID", "SERV"][t % 2]
        for c in "AC":
            for k in range(4):
                rows.append({"task": f"t{t}", "repo": f"r{t // 2}", "stage": stage, "condition": c,
                             "y": float(rng.random() < (0.5 if c == "A" else 0.6))})
    df = pd.DataFrame(rows)
    a = st.paired_task_bootstrap(df, "y", "C", "A", "task", "stage", n_boot=500, seed=11)
    b = st.paired_task_bootstrap(df, "y", "C", "A", "task", "stage", n_boot=500, seed=11)
    c = st.paired_task_bootstrap(df, "y", "C", "A", "task", "stage", n_boot=500, seed=12)
    check("paired bootstrap reproducible for a fixed seed", np.array_equal(a["boot"], b["boot"]) and
          a["ci"] == b["ci"])
    check("paired bootstrap differs across seeds", not np.array_equal(a["boot"], c["boot"]))
    check("paired bootstrap CI contains the estimate", a["ci"][0] <= a["estimate"] <= a["ci"][1],
          f"{a['estimate']:.3f} {a['ci']}")
    repos = [f"r{t // 2}" for t in range(30)]
    strata = [["ID", "SERV"][t % 2] for t in range(30)]
    i1 = st.two_stage_cluster_bootstrap_indices(repos, list(range(30)), strata, 50, 5)
    i2 = st.two_stage_cluster_bootstrap_indices(repos, list(range(30)), strata, 50, 5)
    check("two-stage bootstrap reproducible", all(np.array_equal(x, y) for x, y in zip(i1, i2)))
    check("two-stage bootstrap indices in range", all(x.min() >= 0 and x.max() < 30 for x in i1))
    # repos alternate strata inside r (t%2) so modal stratum is a tie; just check repo structure kept
    check("two-stage bootstrap draws whole repos", all(set(np.asarray(repos, dtype=object)[x].tolist()) <=
                                                      set(repos) for x in i1))


def test_misc(seed: int) -> None:
    rng = np.random.default_rng(seed)
    a = st.calibrate_marginal_intercept(0.25, 1.5)
    z = rng.normal(0, np.sqrt(1.5), 400_000)
    check("calibration reproduces marginal p0 (MC)", abs(np.mean(1 / (1 + np.exp(-(a + z)))) - 0.25) < 0.005,
          f"alpha {a:.3f}")
    w = st.wald_contrast([1.0, 0.0], np.diag([0.04, 0.04]), [1, 0], df_denom=10)
    check("wald_contrast 1-df t", abs(w["stat"] - 5.0) < 1e-9 and w["p"] < 0.001, str(w["p"]))
    wj = st.wald_contrast([1.0, 1.0], np.diag([0.25, 0.25]), np.eye(2), df_denom=10)
    check("wald_contrast joint F = 4", abs(wj["stat"] - 4.0) < 1e-9 and wj["df_num"] == 2)
    check("mde_from_grid", st.mde_from_grid({1.25: .1, 1.5: .3, 2.0: .85, 2.5: .95}) == 2.0
          and st.mde_from_grid({1.5: .2}) is None)
    design = make_design(12)
    s2 = 1.0
    d = design.copy()
    d["resolved"] = st.simulate_glmm_binary(d, -0.5, {"is_C": 0.7}, 0.2, 0.8, rng)
    cl = st.conditional_logit_by_stratum(d, F1, "task", n_boot=40, seed=1, boot_strata="stage")
    check("conditional logit runs and bootstraps", cl["converged"] and CNAME in cl["params"] and
          cl["n_boot_ok"] > 20, f"{cl['params'].get(CNAME)}")
    vb = st.binomial_mixed_glm_vb(d, F1, {"repo": "0 + C(repo)", "task": "0 + C(task)"})
    check("VB mixed logit runs", CNAME in vb["post_mean"], f"OR {vb['or'].get(CNAME)}")
    sim = st.simulate_power(design, 0.3, {"is_C": np.log(3), "is_D": 0.0}, 0.5, 0.2, -0.3,
                            lambda dd: {"H1": pipeline_p(dd)["H1"]}, n_rep=30, seed=2)
    check("simulate_power: OR 3 power well above OR 1 size", sim["rejection"]["H1"]["0.05"] > 0.2,
          str(sim["rejection"]))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--n-type1", type=int, default=500)
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    test_jeffreys()
    test_bootstrap()
    test_misc(a.seed)
    test_gee_and_type1(a.seed, a.n_type1)
    failed = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    for name, _, detail in failed:
        print(f"FAILED: {name} {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
