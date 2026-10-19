"""WP6 power re-simulation with the realised dose (design section 5; written to wp6_power.json before the run freeze).

Used by Paper 1 (JSEP rebuild), WP6; deviation 13 (add mode) changed the dose, so the design's power figures are redone.

Data-generating process (80 tasks, their repositories and per-task numbers of false claims from the manifests index; 4 runs
per task and condition = 2 models x 2 replicates; latent ICC 0.3 split 0.2 repository / 0.8 task, as in WP5):
  H1 / H3  any-hit runs: P(hit) = 1 - (1 - q)^n_false for F_R (q = uptake per false claim; F_I uses rho * q); the T counterfactual rate
           is 0.01. Logit-scale random effects for repository and task.
  H2       wasted steps: Poisson with task mean 0.37 x gamma (shape 0.9, so the paired task-level SD is about 0.7 as in WP5);
           F_R adds delta4 * n_false / 4 per run (delta4 = the effect of a 4-claim manifest).
  H4       resolved: p0 = WP5 condition-A resolve rate, log OR = log(OR4) * n_false / 4.
Test: paired task-level difference (mean of the 4 runs), averaged within repository, one-sample t on the repository means with G-1 df
(a fast stand-in for the GEE with repository clusters; the GEE itself is too slow for 2,000 replicates x grid). Rejection at the
first Holm step (0.05 / 4) and at 0.05. Label: POWERED if H2 power at delta4 = 0.28 is at least 0.80, else UNDER-POWERED.

Usage:
    python experiments/paper1_ontology_manifests/run_wp6_analysis.py power --out experiments/paper1_ontology_manifests/results/real_v2/wp6/wp6_power.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats as sps
from scipy.special import expit, logit

SEED = 20261009
ICC, REPO_SHARE = 0.3, 0.2
ALPHAS = (0.05 / 4, 0.05)


def _cluster_p(diff: np.ndarray, repo: np.ndarray, n_repo: int) -> float:
    s = np.bincount(repo, weights=diff, minlength=n_repo)
    n = np.bincount(repo, minlength=n_repo)
    m = s[n > 0] / n[n > 0]
    if len(m) < 3 or m.std(ddof=1) == 0:
        return 1.0
    t = m.mean() / (m.std(ddof=1) / np.sqrt(len(m)))
    return float(2 * sps.t.sf(abs(t), len(m) - 1))


def simulate(tasks: list[dict[str, Any]], kind: str, n_rep: int, rng: np.random.Generator, **par: Any) -> dict[str, float]:
    repos = sorted({t["repo"] for t in tasks})
    repo = np.array([repos.index(t["repo"]) for t in tasks])
    nR = np.array([t["n_false_R"] for t in tasks], float)
    nI = np.array([t["n_false_I"] for t in tasks], float)
    n, G = len(tasks), len(repos)
    s2 = ICC * (np.pi ** 2 / 3) / (1 - ICC)
    sr, st_ = np.sqrt(REPO_SHARE * s2), np.sqrt((1 - REPO_SHARE) * s2)
    rej = {str(a): 0 for a in ALPHAS}
    runs = 4
    for _ in range(n_rep):
        if kind in ("hit", "resolved"):
            u = rng.normal(0, sr, G)[repo] + rng.normal(0, st_, n)
            if kind == "hit":
                q, rho, p_t = par["q"], par.get("rho", 0.0), 0.01
                pT = np.full(n, p_t)
                pR = 1 - (1 - q) ** nR
                pI = 1 - (1 - rho * q) ** nI
                pR, pI = np.maximum(pR, p_t), np.maximum(pI, p_t)
            else:
                p0, or4 = par["p0"], par["or4"]
                pT = np.full(n, p0)
                pR = expit(logit(p0) + np.log(or4) * nR / 4)
                pI = np.full(n, p0)
            draw = lambda p: (rng.random((n, runs)) < expit(logit(p)[:, None] + u[:, None])).astype(float)   # noqa: E731
            yT, yR, yI = draw(pT), draw(pR), draw(pI)
        else:   # wasted steps
            lam = 0.37 * rng.gamma(0.9, 1 / 0.9, n)
            d4 = par["delta4"]
            yT = rng.poisson(np.repeat(lam[:, None], runs, 1)).astype(float)
            yR = rng.poisson(np.repeat((lam + d4 * nR / 4)[:, None], runs, 1)).astype(float)
            yI = rng.poisson(np.repeat(lam[:, None], runs, 1)).astype(float)
        if par.get("contrast", "R_vs_T") == "R_vs_T":
            diff = yR.mean(1) - yT.mean(1)
        else:
            diff = yR.mean(1) - yI.mean(1)
        p = _cluster_p(diff, repo, G)
        for a in ALPHAS:
            rej[str(a)] += int(p < a)
    return {a: v / n_rep for a, v in rej.items()}


def run_power(idx: dict[str, dict], tasks_meta: dict[str, dict], p0: float, n_rep: int = 2000) -> dict[str, Any]:
    rows = []
    for tid, m in sorted(idx.items()):
        fc = m.get("false_claims", [])
        rows.append({"task": tid, "repo": tasks_meta.get(tid, {}).get("repo", tid.split("__")[0]),
                     "n_false_R": sum(1 for c in fc if c["cond"] == "F_R"), "n_false_I": sum(1 for c in fc if c["cond"] == "F_I")})
    rng = np.random.default_rng(SEED)
    mean_n = float(np.mean([r["n_false_R"] for r in rows]))
    out: dict[str, Any] = {"n_tasks": len(rows), "n_rep": n_rep, "alphas": list(ALPHAS), "seed": SEED, "p0_resolve_A": p0,
                           "dose_mean_n_false_F_R": mean_n,
                           "dose_distribution_F_R": {str(k): int(sum(1 for r in rows if r["n_false_R"] == k)) for k in range(5)}}
    def grid(kind: str, key: str, vals: list[float], **fixed: Any) -> dict[str, Any]:
        return {str(v): simulate(rows, kind, n_rep, rng, **{key: v}, **fixed) for v in vals}
    qs = [0.01, 0.02, 0.04, 0.06, 0.08, 0.12]
    out["H1_any_hit_F_R_vs_T"] = {"by_q_per_false_claim": grid("hit", "q", qs, rho=0.0),
                                  "mean_F_R_hit_rate_at_q": {str(q): float(np.mean([1 - (1 - q) ** r["n_false_R"] for r in rows])) for q in qs}}
    out["H2_wasted_steps_F_R_vs_T"] = {"by_delta4": grid("steps", "delta4", [0.0, 0.1, 0.2, 0.28, 0.4, 0.6])}
    out["H3_relevance_F_R_vs_F_I"] = {f"q={q},rho={r}": simulate(rows, "hit", n_rep, rng, q=q, rho=r, contrast="R_vs_I")
                                      for q in (0.04, 0.08, 0.12) for r in (0.25, 0.5)}
    out["H4_resolve_F_R_vs_T"] = {"by_or4": grid("resolved", "or4", [1.0, 0.6, 0.5, 0.4, 0.3], p0=p0)}
    h2 = out["H2_wasted_steps_F_R_vs_T"]["by_delta4"]["0.28"][str(ALPHAS[0])]
    out["label_H2_at_0.28"] = "POWERED" if h2 >= 0.8 else "UNDER-POWERED"
    def mde(g: dict[str, dict], fn=min) -> Any:
        ok = [float(k) for k, v in g.items() if v[str(ALPHAS[0])] >= 0.8]
        return fn(ok) if ok else None
    out["MDE_at_first_holm_step"] = {"H1_q": mde(out["H1_any_hit_F_R_vs_T"]["by_q_per_false_claim"]),
                                     "H2_delta4": mde(out["H2_wasted_steps_F_R_vs_T"]["by_delta4"]),
                                     "H4_or4": mde(out["H4_resolve_F_R_vs_T"]["by_or4"], max)}
    if out["MDE_at_first_holm_step"]["H1_q"] is not None:
        q = out["MDE_at_first_holm_step"]["H1_q"]
        out["MDE_at_first_holm_step"]["H1_mean_F_R_hit_rate"] = out["H1_any_hit_F_R_vs_T"]["mean_F_R_hit_rate_at_q"][str(q)]
    out["design_comparison"] = {"design_H2_MDE_delta": 0.28, "design_H1_MDE_hit_rate": 0.08, "design_H4_MDE_or": 0.4}
    return out
