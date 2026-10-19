"""WP6 analysis: confirmatory H1-H4 (GEE clustered by repository, Holm), companion Wilcoxon, effect sizes, secondary and sensitivity.

Used by Paper 1 (JSEP rebuild), WP6; design papers/paper1/wp6-harm-design.md section 4 and 6. Run only after `wp6-runs-complete`.

Data: `wp6_runs.jsonl` and `wp6_outcomes.jsonl` (written by `run_wp6.py outcomes`) from `--results-dir`, the manifests index and the
WP5 task list (repository and stage per task).

Scoring. Every run is scored against both false-token sets of its task (F_R and F_I). A run of condition F_R is scored with
its own set (F_R), a run of F_I with its own set (F_I), and the counterfactual runs A and T with the set that the contrast
needs: model "R" (A, T scored with the F_R tokens) answers F_R vs T, F_R vs A, T vs A and F_R vs F_I; model "I" (A, T scored with the
F_I tokens) answers F_I vs T. This is the design's "same token set applied to the T and A runs as a counterfactual baseline".

Confirmatory family (Holm, familywise 0.05, `holm_adjusted_p`):  H1 Y1 F_R vs T;  H2 Y2 F_R vs T;  H3 Y1 F_R vs F_I;  H4 resolved F_R vs T.
Estimator: `statistics.gee_fit` (exchangeable, bias-reduced sandwich, t(G - 1)), formula
`y ~ C(condition, Treatment('T')) + C(model)` on all four conditions; Poisson (rate ratio) for counts, binomial (OR) for binary.
Companion: paired Wilcoxon (Pratt zeros) on task-level means; "estimator-sensitive" if its sign differs or it falls on the other
side of the Holm threshold. Effect sizes: ratio with 95 % CI and `paired_task_bootstrap` (B = 10,000, seed 20261009).
Nothing here is run on real data before the runs are complete; `--synthetic` makes planted-effect data for the tests.

Usage:
    python experiments/paper1_ontology_manifests/run_wp6_analysis.py analyze \\
        --results-dir experiments/paper1_ontology_manifests/results/real_v2/wp6/runs --out-dir <dir>
    python experiments/paper1_ontology_manifests/test_wp6_analysis_synthetic.py
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import sys
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from shared.evaluation import statistics as st  # noqa: E402

logger = logging.getLogger("wp6.analysis")
SEED = 20261009
N_BOOT = 10_000
FORMULA = "y ~ C(condition, Treatment('T')) + C(model)"
TERMS = {"F_R": "C(condition, Treatment('T'))[T.F_R]", "F_I": "C(condition, Treatment('T'))[T.F_I]",
         "A": "C(condition, Treatment('T'))[T.A]"}
HOLM_ALPHA = 0.05


# ----------------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------------
def load_frame(results_dir: Path, tasks: list[dict], variant: str = "sets") -> pd.DataFrame:
    """One row per run: meta, resolved, Y9, and Y1..Y8 against both token sets."""
    runs = [json.loads(ln) for ln in (results_dir / "wp6_runs.jsonl").read_text().splitlines() if ln.strip()]
    outs = {r["run_id"]: r for r in (json.loads(ln) for ln in (results_dir / "wp6_outcomes.jsonl").read_text().splitlines() if ln.strip())}
    tinfo = {t["instance_id"]: t for t in tasks}
    rows = []
    for r in runs:
        o = outs.get(r["run_id"], {})
        t = tinfo.get(r["instance_id"], {})
        row: dict[str, Any] = {"run_id": r["run_id"], "task": r["instance_id"], "repo": t.get("repo", r["instance_id"].split("__")[0]),
                               "stage": t.get("stage", "NA"), "condition": r["condition"], "model": r["model"].split("/")[-1],
                               "rep": r["rep"], "infra_failure": bool(r["infra_failure"]), "state": r["state"],
                               "resolved": int(o.get("resolved", 0)), "steps": r.get("steps"), "wall_s": r.get("wall_s"),
                               "prompt_tokens": r.get("prompt_tokens"), "completion_tokens": r.get("completion_tokens"),
                               "hit_step_limit": o.get("hit_step_limit"), "Y7": o.get("Y7")}
        for s in ("R", "I"):
            sc = (o.get(variant) or {}).get("F_" + s)
            for key in ("Y1", "Y2", "Y3", "Y5", "Y8"):
                row[f"{key}_{s}"] = sc.get(key, np.nan) if sc else np.nan  # SA6/SA7 token sets carry no Y8
            for k in (1, 2, 3, 4):
                row[f"Y4k{k}_{s}"] = (sc["Y4_by_kind"].get(str(k), 0) if sc else np.nan)
            y6 = (o.get("Y6_sets") or {}).get("F_" + s)
            row[f"Y6_{s}"] = y6["Y6"] if y6 else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def add_covariates(df: pd.DataFrame, idx: dict[str, dict]) -> pd.DataFrame:
    """Recorded covariates from the manifests index: n_false (dose), mode (replace / add) and the per-kind modes, per token set.

    `n_false_R`, `n_false_I`: false claims in the task's F_R / F_I manifest; `n_replace_R/I`: how many of them replace a T line;
    `mode_k{1..4}_R/I`: "replace", "add" or "none"; `dose`: the run's own dose (0 for A and T runs).
    """
    d = df.copy()
    for s in ("R", "I"):
        cond = "F_" + s
        d[f"n_false_{s}"] = d["task"].map(lambda t: sum(1 for c in idx.get(t, {}).get("false_claims", []) if c["cond"] == cond))
        d[f"n_replace_{s}"] = d["task"].map(lambda t: sum(1 for c in idx.get(t, {}).get("false_claims", [])
                                                           if c["cond"] == cond and c["mode"] == "replace"))
        for k in (1, 2, 3, 4):
            d[f"mode_k{k}_{s}"] = d["task"].map(lambda t: (idx.get(t, {}).get("modes", {}).get(cond, {}).get(str(k), "none")))
    d["dose"] = np.where(d["condition"] == "F_R", d["n_false_R"], np.where(d["condition"] == "F_I", d["n_false_I"], 0))
    return d


def scored(df: pd.DataFrame, key: str, model_set: str) -> pd.Series:
    """The outcome `key` under own tokens for F_R / F_I runs and under `model_set` tokens for A and T runs."""
    own = np.where(df["condition"] == "F_R", df[f"{key}_R"], np.where(df["condition"] == "F_I", df[f"{key}_I"], df[f"{key}_{model_set}"]))
    return pd.Series(own, index=df.index, dtype=float)


def with_y(df: pd.DataFrame, key: str, model_set: str = "R", plain: bool = False) -> pd.DataFrame:
    d = df.copy()
    d["y"] = d[key].astype(float) if plain else scored(d, key, model_set)
    return d.dropna(subset=["y"])


# ----------------------------------------------------------------------------
# Estimation
# ----------------------------------------------------------------------------
def _Lvec(names: list[str], coefs: dict[str, float]) -> Optional[np.ndarray]:
    if any(k not in names for k in coefs):
        return None
    v = np.zeros(len(names))
    for k, c in coefs.items():
        v[names.index(k)] = c
    return v


def contrast(fit: dict[str, Any], coefs: dict[str, float], ratio: bool) -> dict[str, Any]:
    from scipy import stats as sps
    nan = {"est": float("nan"), "se": float("nan"), "p": float("nan"), "ci": [float("nan")] * 2}
    if not fit.get("converged"):
        return {**nan, "note": "not converged"}
    L = _Lvec(fit["param_names"], coefs)
    if L is None:
        return {**nan, "note": "term not estimable"}
    dfd = max(fit["n_clusters"] - 1, 1)
    w = st.wald_contrast([fit["params"][n] for n in fit["param_names"]], fit["cov"], L, dfd)
    tcrit = sps.t.ppf(0.975, dfd)
    ci = [w["est"] - tcrit * w["se"], w["est"] + tcrit * w["se"]]
    out = {"est": w["est"], "se": w["se"], "p": w["p"], "ci": ci, "df": dfd, "fallback": fit.get("fallback_used")}
    if ratio:
        ex = lambda x: math.exp(max(min(x, 700.0), -700.0))  # noqa: E731
        out.update({"ratio": ex(w["est"]), "ratio_ci": [ex(ci[0]), ex(ci[1])]})
    return out


def fit(d: pd.DataFrame, family: str, groups: str = "repo", formula: str = FORMULA) -> dict[str, Any]:
    if family == "negbin":
        return _fit_negbin(d, groups, formula)
    return st.gee_fit(d, formula, groups, family)


def _fit_negbin(d: pd.DataFrame, groups: str, formula: str) -> dict[str, Any]:
    """SA8: GEE with a negative-binomial family (alpha estimated by the method of moments from a Poisson fit)."""
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    try:
        pois = smf.glm(formula, d, family=sm.families.Poisson()).fit()
        mu = pois.mu
        alpha = max(float(np.sum(((d["y"] - mu) ** 2 - mu)) / np.sum(mu ** 2)), 1e-3)
        res = smf.gee(formula, groups=groups, data=d, family=sm.families.NegativeBinomial(alpha=alpha),
                      cov_struct=sm.cov_struct.Exchangeable()).fit(cov_type="bias_reduced")
        cov = np.asarray(res.cov_params())
        return {"params": {k: float(v) for k, v in res.params.items()}, "param_names": list(res.params.index), "cov": cov,
                "converged": bool(np.all(np.isfinite(cov))), "n_clusters": int(d[groups].nunique()), "n_obs": len(d),
                "fallback_used": None, "alpha": alpha}
    except Exception as exc:  # noqa: BLE001
        return {"params": {}, "param_names": [], "cov": np.empty((0, 0)), "converged": False, "n_clusters": int(d[groups].nunique()),
                "n_obs": len(d), "fallback_used": "failed", "error": repr(exc)[:120]}


CONTRASTS = {   # name -> (coefficients, model set)
    "F_R_vs_T": ({TERMS["F_R"]: 1.0}, "R"),
    "F_I_vs_T": ({TERMS["F_I"]: 1.0}, "I"),
    "F_R_vs_A": ({TERMS["F_R"]: 1.0, TERMS["A"]: -1.0}, "R"),
    "T_vs_A": ({TERMS["A"]: -1.0}, "R"),
    "F_R_vs_F_I": ({TERMS["F_R"]: 1.0, TERMS["F_I"]: -1.0}, "R"),
}
FAMILY_OF = {"Y1": "poisson", "Y2": "poisson", "resolved": "binomial", "Y3": "binomial", "Y6": "binomial", "Y7": "binomial",
             "Y8": "poisson", "steps": "gaussian", "wall_s": "gaussian", "prompt_tokens": "gaussian"}
PLAIN = {"resolved", "steps", "wall_s", "prompt_tokens", "Y7"}


def estimate(df: pd.DataFrame, outcome: str, contrast_name: str, family: Optional[str] = None, groups: str = "repo",
             formula: str = FORMULA, key_suffix: str = "") -> dict[str, Any]:
    coefs, mset = CONTRASTS[contrast_name]
    d = with_y(df, outcome, mset, plain=outcome in PLAIN)
    fam = family or FAMILY_OF[outcome]
    f = fit(d, fam, groups, formula)
    ratio = fam in ("poisson", "binomial", "negbin")
    c = contrast(f, coefs, ratio)
    c.update(n_obs=f["n_obs"], n_clusters=f["n_clusters"], family=fam, outcome=outcome, contrast=contrast_name)
    return c


def task_level(df: pd.DataFrame, outcome: str, x: str, ref: str, mset: str, plain: bool) -> pd.DataFrame:
    d = with_y(df, outcome, mset, plain=plain)
    m = d.groupby(["task", "condition"])["y"].mean().unstack("condition")
    return m[[x, ref]].dropna() if {x, ref} <= set(m.columns) else pd.DataFrame(columns=[x, ref])


def wilcoxon_pratt(df: pd.DataFrame, outcome: str, x: str, ref: str, mset: str, plain: bool) -> dict[str, Any]:
    from scipy import stats as sps
    m = task_level(df, outcome, x, ref, mset, plain)
    diff = (m[x] - m[ref]).to_numpy()
    if len(diff) == 0 or not np.any(diff != 0):
        return {"p": 1.0 if len(diff) else float("nan"), "n_tasks": len(diff), "median_diff": 0.0 if len(diff) else float("nan"),
                "mean_diff": float(np.mean(diff)) if len(diff) else float("nan")}
    r = sps.wilcoxon(m[x], m[ref], zero_method="pratt", alternative="two-sided")
    return {"p": float(r.pvalue), "stat": float(r.statistic), "n_tasks": len(diff), "median_diff": float(np.median(diff)),
            "mean_diff": float(np.mean(diff))}


def boot_diff(df: pd.DataFrame, outcome: str, x: str, ref: str, mset: str, plain: bool, n_boot: int) -> dict[str, Any]:
    d = with_y(df, outcome, mset, plain=plain)
    b = st.paired_task_bootstrap(d, "y", x, ref, "task", "stage", n_boot=n_boot, seed=SEED)
    return {"estimate": b["estimate"], "ci": b["ci"], "n_tasks": b["n_tasks"]}


# ----------------------------------------------------------------------------
# Confirmatory family
# ----------------------------------------------------------------------------
HYP = [   # id, outcome, contrast, x, ref, model set, plain
    ("H1", "Y1", "F_R_vs_T", "F_R", "T", "R", False),
    ("H2", "Y2", "F_R_vs_T", "F_R", "T", "R", False),
    ("H3", "Y1", "F_R_vs_F_I", "F_R", "F_I", "R", False),
    ("H4", "resolved", "F_R_vs_T", "F_R", "T", "R", True),
]


def confirmatory(df: pd.DataFrame, n_boot: int = N_BOOT, groups: str = "repo", family_override: Optional[dict[str, str]] = None
                 ) -> dict[str, Any]:
    rows = []
    for hid, outcome, cname, x, ref, mset, plain in HYP:
        fam = (family_override or {}).get(hid)
        e = estimate(df, outcome, cname, fam, groups)
        w = wilcoxon_pratt(df, outcome, x, ref, mset, plain)
        e["wilcoxon"] = w
        e["bootstrap_task_diff"] = boot_diff(df, outcome, x, ref, mset, plain, n_boot) if n_boot else None
        e["id"] = hid
        rows.append(e)
    holm = st.holm_adjusted_p([r["p"] if not math.isnan(r["p"]) else 1.0 for r in rows])
    holm_w = st.holm_adjusted_p([r["wilcoxon"]["p"] if not math.isnan(r["wilcoxon"]["p"]) else 1.0 for r in rows])
    for r, p_adj, pw_adj in zip(rows, holm, holm_w):
        r["p_holm"], r["wilcoxon"]["p_holm"] = p_adj, pw_adj
        r["reject"] = bool(p_adj < HOLM_ALPHA)
        sign_g = np.sign(r["est"]) if not math.isnan(r["est"]) else 0
        sign_w = np.sign(r["wilcoxon"]["mean_diff"]) if not math.isnan(r["wilcoxon"]["mean_diff"]) else 0
        r["estimator_sensitive"] = bool(sign_g != sign_w or (pw_adj < HOLM_ALPHA) != r["reject"])
    return {"family": "Holm across H1..H4, familywise alpha 0.05 (holm_adjusted_p)", "hypotheses": rows}


# ----------------------------------------------------------------------------
# Secondary, exploratory and sensitivity
# ----------------------------------------------------------------------------
def secondary(df: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {"contrasts": []}
    for cname in ("F_I_vs_T", "F_R_vs_A"):
        for oc in ("Y1", "Y2", "resolved", "steps", "wall_s", "prompt_tokens"):
            out["contrasts"].append(estimate(df, oc, cname))
    for oc in ("Y1", "Y2", "resolved", "steps", "wall_s", "prompt_tokens"):
        out["contrasts"].append(estimate(df, oc, "T_vs_A"))
    ps = [c["p"] if not math.isnan(c["p"]) else 1.0 for c in out["contrasts"]]
    for c, pa in zip(out["contrasts"], st.holm_adjusted_p(ps)):
        c["p_holm_descriptive"] = pa
    out["y3_to_y8"] = []
    for cname in ("F_R_vs_T", "F_R_vs_F_I"):
        for oc in ("Y3", "Y6", "Y7", "Y8"):
            out["y3_to_y8"].append(estimate(df, oc, cname))
        for k in (1, 2, 3, 4):
            e = estimate(df.assign(**{f"Y4_{k}_R": df[f"Y4k{k}_R"], f"Y4_{k}_I": df[f"Y4k{k}_I"]}), f"Y4_{k}", cname, "poisson")
            e["outcome"] = f"Y4_kind{k}"
            out["y3_to_y8"].append(e)
    hit = df[(df["condition"] == "F_R") & (df["Y5_R"].notna())]
    out["Y5_first_hit_step_F_R"] = {"n": int(len(hit)), "median": float(hit["Y5_R"].median()) if len(hit) else None}
    return out


def sensitivity(df: pd.DataFrame, df_sa6: pd.DataFrame, df_sa7: pd.DataFrame, tasks_meta: dict[str, dict], drift_fail: set[str],
                n_boot: int) -> dict[str, Any]:
    def conf(d: pd.DataFrame, **kw: Any) -> list[dict[str, Any]]:
        res = confirmatory(d, n_boot=0, **kw)["hypotheses"]
        return [{k: r[k] for k in ("id", "est", "p", "p_holm", "reject", "ratio", "ratio_ci", "n_obs") if k in r} for r in res]
    fall = {t for t, m in tasks_meta.items() if any(m.get("fallbacks", {}).values())}
    lenv = {t for t, m in tasks_meta.items() if any(f.startswith("length_violation") for f in m.get("flags", []))}
    out: dict[str, Any] = {
        "SA1_exclude_final_infra_failures": conf(df[~df["infra_failure"]]),
        "SA3_exclude_tasks_with_fallback": conf(df[~df["task"].isin(fall)]),
        "SA4_exclude_length_violation_tasks": conf(df[~df["task"].isin(lenv)]),
        "SA5_cluster_by_task": conf(df, groups="task"),
        "SA6_full_path_hits_only": conf(df_sa6),
        "SA7_narrow_NF": conf(df_sa7),
        "SA8_negative_binomial_instead_of_Poisson": conf(df, family_override={"H1": "negbin", "H2": "negbin", "H3": "negbin"}),
        "SA9_exclude_gold_drift_failures": conf(df[~df["task"].isin(drift_fail)]),
    }
    for m in sorted(df["model"].unique()):
        out[f"SA2_{m}_alone"] = conf(df[df["model"] == m])
    if "n_replace_R" in df.columns and tasks_meta:
        out["SA10_replace_mode_claims_only"] = replace_only(df, conf)
    return out


def replace_only(df: pd.DataFrame, conf: Any) -> dict[str, Any]:
    """Deviation 13 sensitivity: only claims that replace a T line. H1 and H3 count hits on replace-mode kinds only (Y1 from the
    per-kind hit counts); H2 and H4 use the tasks whose F_R false claims are all replace-mode (Y2 cannot be split by kind)."""
    d = df.copy()
    for s in ("R", "I"):
        d[f"Y1_{s}"] = sum(d[f"Y4k{k}_{s}"] * (d[f"mode_k{k}_{s}"] == "replace") for k in (1, 2, 3, 4))
    all_rep = d[(d["n_false_R"] > 0) & (d["n_false_R"] == d["n_replace_R"]) & (d["n_false_I"] == d["n_replace_I"])]
    a, b = conf(d), conf(all_rep)
    return {"H1_H3_Y1_on_replace_kinds_only": [r for r in a if r["id"] in ("H1", "H3")],
            "H2_H4_on_tasks_with_only_replace_claims": [r for r in b if r["id"] in ("H2", "H4")],
            "n_tasks_all_replace": int(all_rep["task"].nunique())}


def exploratory(df: pd.DataFrame, wp5_dir: Optional[Path]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    by = df.groupby(["condition", "model"]).agg(n=("run_id", "count"), resolved=("resolved", "mean"), steps=("steps", "mean"))
    out["per_condition_model"] = {f"{c}|{m}": {k: float(v) for k, v in r.items()} for (c, m), r in by.iterrows()}
    if "dose" in df.columns:
        sub = df[df["condition"].isin(["A", "T", "F_R"])].copy()
        sub["y"] = sub["Y1_R"]
        sub = sub.dropna(subset=["y"])
        if len(sub) and sub["dose"].max() > 0:
            f = st.gee_fit(sub, "y ~ dose + C(model)", "repo", "poisson")
            out["dose_response_Y1_per_false_claim_rate_ratio"] = (
                {"ratio": math.exp(f["params"]["dose"]), "n_obs": f["n_obs"]} if f["converged"] and "dose" in f["params"] else "not converged")
        fr = df[df["condition"] == "F_R"]
        out["Y1_by_kind_and_mode_F_R"] = {f"kind{k}_{m}": {"n_runs": int((fr[f"mode_k{k}_R"] == m).sum()),
                                                            "mean_hits": float(fr.loc[fr[f"mode_k{k}_R"] == m, f"Y4k{k}_R"].mean())
                                                            if (fr[f"mode_k{k}_R"] == m).any() else None}
                                          for k in (1, 2, 3, 4) for m in ("replace", "add")}
    if wp5_dir and (wp5_dir / "wp5_outcomes.jsonl").exists() and (wp5_dir / "wp5_runs.jsonl").exists():
        w5 = {r["run_id"]: r for r in map(json.loads, (wp5_dir / "wp5_runs.jsonl").read_text().splitlines())}
        a5 = [json.loads(ln) for ln in (wp5_dir / "wp5_outcomes.jsonl").read_text().splitlines()]
        a5 = [o["resolved"] for o in a5 if w5.get(o["run_id"], {}).get("condition") == "A"]
        a6 = df[df["condition"] == "A"]["resolved"]
        out["endpoint_drift_A_resolve_rate"] = {"wp5_A": float(np.mean(a5)) if a5 else None, "wp6_A": float(a6.mean()) if len(a6) else None,
                                                "n_wp5": len(a5), "n_wp6": int(len(a6))}
    return out


# ----------------------------------------------------------------------------
# Driver
# ----------------------------------------------------------------------------
def analyze(results_dir: Path, tasks_file: Path, index_file: Path, out_dir: Path, drift_file: Optional[Path], wp5_dir: Optional[Path],
            n_boot: int = N_BOOT, synthetic: bool = False) -> dict[str, Any]:
    tasks_doc = json.loads(tasks_file.read_text())
    tasks = [t for t in tasks_doc["tasks"] if not t.get("excluded") and not t.get("dev")]
    idx = json.loads(index_file.read_text())["tasks"] if index_file.exists() else {}
    df = add_covariates(load_frame(results_dir, tasks, "sets"), idx)
    df6 = add_covariates(load_frame(results_dir, tasks, "sets_sa6"), idx)
    df7 = add_covariates(load_frame(results_dir, tasks, "sets_sa7"), idx)
    drift = set(json.loads(drift_file.read_text()).get("gold_drift_fail", [])) if drift_file and drift_file.exists() else set()
    res = {"synthetic": synthetic, "n_runs": int(len(df)), "n_tasks": int(df["task"].nunique()),
           "n_repos": int(df["repo"].nunique()), "counts_by_condition": df["condition"].value_counts().to_dict(),
           "confirmatory": confirmatory(df, n_boot), "secondary": secondary(df),
           "sensitivity": sensitivity(df, df6, df7, idx, drift, n_boot), "exploratory": exploratory(df, wp5_dir),
           "scope": "Two NIM models, mini-SWE-agent in text mode, 40 steps, a manifest injected into the prompt (not read from a "
                    "file), short synthetic manifests, Python SWE-rebench tasks."}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "wp6_primary.json").write_text(json.dumps(res["confirmatory"], indent=1, default=float))
    (out_dir / "wp6_secondary.json").write_text(json.dumps(res["secondary"], indent=1, default=float))
    (out_dir / "wp6_sensitivity.json").write_text(json.dumps(res["sensitivity"], indent=1, default=float))
    (out_dir / "wp6_exploratory.json").write_text(json.dumps(res["exploratory"], indent=1, default=float))
    return res


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("power", help="power re-simulation with the realised dose -> wp6_power.json (design section 5)")
    q.add_argument("--out", required=True)
    q.add_argument("--config", default=str(PROJECT_ROOT / "experiments/paper1_ontology_manifests/configs/wp6.yaml"))
    q.add_argument("--n-rep", type=int, default=2000)
    p = sub.add_parser("analyze")
    p.add_argument("--results-dir", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--config", default=str(PROJECT_ROOT / "experiments/paper1_ontology_manifests/configs/wp6.yaml"))
    p.add_argument("--tasks", default=None)
    p.add_argument("--index", default=None)
    p.add_argument("--n-boot", type=int, default=N_BOOT)
    p.add_argument("--synthetic", action="store_true", help="tests only: stamps the outputs, refuses real_v2 output")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    cfg = yaml.safe_load(Path(a.config).read_text())
    rel = lambda s: (Path(s) if Path(s).is_absolute() else PROJECT_ROOT / s)  # noqa: E731
    if a.cmd == "power":
        from experiments.paper1_ontology_manifests.wp6 import power
        idx = json.loads((rel(cfg["output_dir"]) / "wp6_manifests_index.json").read_text())["tasks"]
        tasks = {t["instance_id"]: t for t in json.loads(rel(cfg["wp5_tasks"]).read_text())["tasks"]}
        w5 = rel(cfg["wp5_output_dir"])
        runs = {r["run_id"]: r for r in map(json.loads, (w5 / "wp5_runs.jsonl").read_text().splitlines())}
        a_res = [json.loads(ln)["resolved"] for ln in (w5 / "wp5_outcomes.jsonl").read_text().splitlines()
                 if runs.get(json.loads(ln)["run_id"], {}).get("condition") == "A"]
        res = power.run_power(idx, tasks, float(np.mean(a_res)), a.n_rep)
        Path(a.out).write_text(json.dumps(res, indent=1))
        logger.info("power: label %s, MDE %s", res["label_H2_at_0.28"], res["MDE_at_first_holm_step"])
        return 0
    res_dir, out_dir = Path(a.results_dir), Path(a.out_dir)
    if a.synthetic and "real_v2" in str(out_dir):
        raise SystemExit("--synthetic output must not go under real_v2")
    wp6_out = rel(cfg["output_dir"])
    analyze(res_dir, Path(a.tasks) if a.tasks else rel(cfg["wp5_tasks"]), Path(a.index) if a.index else wp6_out / "wp6_manifests_index.json",
            out_dir, rel(cfg["wp5_output_dir"]) / "wp5_gold_drift.json", rel(cfg["wp5_output_dir"]), a.n_boot, a.synthetic)
    return 0


if __name__ == "__main__":
    sys.exit(main())
