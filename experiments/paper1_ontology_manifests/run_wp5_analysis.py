#!/usr/bin/env python3
"""WP5 analysis runner: confirmatory, secondary, sensitivity, exploratory, power (Paper 1, RQ3/RQ4).

Implements papers/paper1/wp5-analysis-plan.md sections 0, 5-10, 12 (outputs) and 7.2
(``power`` subcommand). Pure analysis: no LLM, no network. Statistical machinery is in
``shared/evaluation/statistics.py`` (section 13).

Subcommands
-----------
``analyze`` (default)
    Reads the inputs below, runs the section 0 refusal checks, and writes
    ``wp5_primary.json``, ``wp5_secondary.json``, ``wp5_sensitivity.json``,
    ``wp5_exploratory.json`` and ``wp5_deviations.json`` into ``--out-dir``.
``power``
    Plan 7.2 simulation from the pilot summary and the frozen task design;
    writes ``wp5_power.json``.

Input schema (results directory; all readers are tolerant of extra keys)
-----------------------------------------------------------------------
``wp5_tasks.json``: ``{"tasks": [task, ...]}`` (or a bare list). Per task:
``instance_id``, ``repo``, ``declared_stage`` in {ID, EVO, SERV, PO} (alias ``stage``),
optional ``b_available`` (bool), ``agent_manifest_in_tree`` (bool),
``gold_drift_fail`` (bool; gold patch failed at the drift check),
``inferred_stage`` (C's C2 stage, any of A/S/P / RBActive.. / active|servicing|phase_out),
``excluded`` / ``dev`` (bool; such tasks are ignored).

``wp5_runs.jsonl`` (ledger, one JSON object per line; the LAST line per run wins):
``run_id`` (or the tuple ``instance_id, condition, model, rep``), ``state`` (terminal
states in the config; anything else is non-terminal and makes the analysis refuse),
optional ``infra_failure`` (bool; also implied by an infra state).

``wp5_outcomes.jsonl``: per run, joined to the ledger by ``run_id`` (or the tuple).
``resolved`` (0/1), ``Y0`` (alias ``patch_produced``), ``Y1`` (``delta_ccn``), ``Y2``
(``new_edges``), ``Y3`` (``stable_share``), ``Y3_gold``, ``Y3_excess``, ``Y3w``, ``Y4``,
``Y5``, ``Y6`` (``steps``), ``hit_step_limit``, ``uptake`` = {``repo_context``,
``label_term``, ``d1_name``}. Missing / null outcomes are NaN (undefined). A final infra
failure counts as ``resolved = 0`` (intention-to-treat) and has no secondary outcomes.

``wp5_manifests_index.json``: ``{"tasks": {instance_id: {"length_violation": bool,
"explanation_fallback": int, "C": {"chars": int}, "D": {"chars": int}, "B": {"chars": int}}}}``
(also accepted: top-level ``{instance_id: {...}}`` and flat keys ``L_C``/``L_D``/``L_B``).

``wp5_run_manifest.json``: ``hashes`` = {``tasks``, ``manifests_index``, ``analysis_config``}
(sha256 hex of the files byte-for-byte), plus optional ``plan_commit``.

Optional: ``wp5_deviations.json`` (carried over, auto entries appended),
``wp5_outcomes_sa9.jsonl`` (``run_id, variant, Y3``: Y3 recomputed under the SA9 module
thresholds, produced outside this script because it needs a TBox rebuild).

Refusal checks (plan 0; exit code 2, nothing written): the tag ``wp5-run-freeze`` is not an
ancestor of HEAD (``git merge-base --is-ancestor`` in ``--repo-root``); the sha256 of the
task list, the manifest index or ``configs/wp5_analysis.yaml`` differs from the one in
``wp5_run_manifest.json``; any scheduled run is not in a terminal state. ``--synthetic``
(tests only) skips the git and hash checks, stamps every output with ``"synthetic": true``,
allows ``--n-boot*`` overrides, and is refused when ``--out-dir`` lies under ``real_v2``.

Usage:
    python experiments/paper1_ontology_manifests/run_wp5_analysis.py analyze \\
        --results-dir experiments/paper1_ontology_manifests/results/real_v2/wp5
    python experiments/paper1_ontology_manifests/run_wp5_analysis.py analyze --synthetic \\
        --results-dir /tmp/wp5_synth --out-dir /tmp/wp5_synth/out --n-boot 300 --n-boot-clogit 20
    python experiments/paper1_ontology_manifests/run_wp5_analysis.py power \\
        --pilot-summary results/real_v2/wp5/wp5_pilot_summary.json --tasks results/real_v2/wp5/wp5_tasks.json \\
        --out results/real_v2/wp5/wp5_power.json [--n-rep 1000]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.evaluation import statistics as st  # noqa: E402

logger = logging.getLogger("senso.wp5_analysis")

HERE = Path(__file__).resolve().parent
DEFAULT_CONFIG = HERE / "configs" / "wp5_analysis.yaml"
DEFAULT_RESULTS = HERE / "results" / "real_v2" / "wp5"
CC = "C(condition, Treatment('A'))"
ALIASES = {
    "Y0": ["Y0", "patch_produced"], "Y1": ["Y1", "delta_ccn"], "Y2": ["Y2", "new_edges"],
    "Y3": ["Y3", "stable_share"], "Y3_gold": ["Y3_gold"], "Y3_excess": ["Y3_excess"], "Y3w": ["Y3w"],
    "Y4": ["Y4", "log2_size_ratio"], "Y5": ["Y5", "files_touched"], "Y6": ["Y6", "steps"],
    "hit_step_limit": ["hit_step_limit"], "resolved": ["resolved"],
}
SECONDARY = {  # outcome -> family (plan 8.1)
    "Y0": "binomial", "Y1": "gaussian", "Y2": "poisson", "Y3": "binomial", "Y4": "gaussian",
    "Y5": "poisson", "Y6": "poisson", "Y3_excess": "gaussian", "Y3w": "binomial",
    "hit_step_limit": "binomial", "any_new_edge": "binomial"}
HOLM_OUTCOMES = ["Y0", "Y1", "Y2", "Y3", "Y4", "Y5", "Y6"]
STAGE_ALIAS = {"A": "ACTIVE", "ACTIVE": "ACTIVE", "RBACTIVEDEVELOPMENTSTAGE": "ACTIVE",
               "S": "SERVICING", "SERVICING": "SERVICING", "RBSERVICINGSTAGE": "SERVICING",
               "P": "PO", "PHASE_OUT": "PO", "PHASEOUT": "PO", "RBPHASEOUTSTAGE": "PO"}


# ---------------------------------------------------------------------------
# generic helpers
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    """SHA-256 of a file's bytes."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def jsonable(o: Any) -> Any:
    """Recursively convert numpy / pandas / Path objects; NaN and inf become None."""
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, set)):
        return [jsonable(v) for v in o]
    if isinstance(o, np.ndarray):
        return jsonable(o.tolist())
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if not math.isfinite(float(o)) else float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, Path):
        return str(o)
    return o


def write_json(path: Path, obj: Any) -> None:
    """Write sorted-key JSON (deterministic)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jsonable(obj), indent=1, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read a JSON-lines file (blank lines skipped)."""
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]


def load_config(path: Path) -> dict[str, Any]:
    """Load the analysis YAML."""
    return yaml.safe_load(Path(path).read_text())


def run_key(r: dict[str, Any]) -> str:
    """Stable key of a run record: ``run_id`` or ``instance_id|condition|model|rep``."""
    if r.get("run_id") is not None:
        return str(r["run_id"])
    return "|".join(str(r.get(k, r.get("k") if k == "rep" else "")) for k in
                    ("instance_id", "condition", "model", "rep"))


def collapse_stage(s: Any) -> Optional[str]:
    """Declared stage ID/EVO -> ACTIVE, SERV -> SERVICING, PO -> PO."""
    s = str(s).upper()
    if s in ("ID", "EVO", "ACTIVE"):
        return "ACTIVE"
    if s in ("SERV", "SERVICING"):
        return "SERVICING"
    if s == "PO":
        return "PO"
    return None


# ---------------------------------------------------------------------------
# section 0: refusal checks
# ---------------------------------------------------------------------------

def git_is_ancestor(repo_root: Path, tag: str) -> tuple[bool, str]:
    """True if ``tag`` exists and is an ancestor of HEAD in ``repo_root``."""
    env_git = ["git", "-C", str(repo_root)]
    r = subprocess.run([*env_git, "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}^{{commit}}"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return False, f"tag {tag} does not exist in {repo_root}"
    r = subprocess.run([*env_git, "merge-base", "--is-ancestor", tag, "HEAD"], capture_output=True, text=True)
    return (r.returncode == 0), ("" if r.returncode == 0 else f"tag {tag} is not an ancestor of HEAD")


def check_refusals(res_dir: Path, cfg_path: Path, cfg: dict[str, Any], repo_root: Path,
                   synthetic: bool, ledger: list[dict[str, Any]]) -> list[str]:
    """Return the list of section 0 violations (empty when the analysis may run)."""
    problems: list[str] = []
    manifest_path = res_dir / "wp5_run_manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    hashes = manifest.get("hashes", {})
    if not synthetic:
        ok, why = git_is_ancestor(repo_root, cfg.get("freeze_tag", "wp5-run-freeze"))
        if not ok:
            problems.append(why)
        if not manifest:
            problems.append(f"{manifest_path.name} is missing")
        for label, file, key in (("task list", res_dir / "wp5_tasks.json", "tasks"),
                                 ("manifest index", res_dir / "wp5_manifests_index.json", "manifests_index"),
                                 ("analysis config", cfg_path, "analysis_config")):
            want = hashes.get(key)
            if not file.exists():
                problems.append(f"{label} {file} is missing")
            elif not want:
                problems.append(f"{manifest_path.name} has no hashes.{key}")
            elif sha256_file(file) != want:
                problems.append(f"sha256 of the {label} differs from {manifest_path.name} hashes.{key}")
    terminal = set(cfg["terminal_states"])
    bad = [run_key(r) for r in ledger if r.get("state") not in terminal]
    if bad:
        problems.append(f"{len(bad)} scheduled run(s) not in a terminal state, e.g. {bad[:3]}")
    return problems


# ---------------------------------------------------------------------------
# data assembly
# ---------------------------------------------------------------------------

def _num(x: Any) -> float:
    try:
        return float("nan") if x is None else float(x)
    except (TypeError, ValueError):
        return float("nan")


def load_tasks(path: Path) -> list[dict[str, Any]]:
    """Task records (excluded and dev-set tasks removed)."""
    doc = json.loads(path.read_text())
    tasks = doc["tasks"] if isinstance(doc, dict) else doc
    out = []
    for t in tasks:
        if t.get("excluded") or t.get("dev"):
            continue
        t = dict(t)
        t["declared_stage"] = str(t.get("declared_stage", t.get("stage", ""))).upper()
        out.append(t)
    return out


def load_index(path: Path) -> dict[str, dict[str, Any]]:
    """Manifest index per task (tolerant of the shapes in the module docstring)."""
    if not path.exists():
        return {}
    doc = json.loads(path.read_text())
    idx = doc.get("tasks", doc) if isinstance(doc, dict) else {}
    out = {}
    for k, v in idx.items():
        if not isinstance(v, dict):
            continue
        row = {"length_violation": bool(v.get("length_violation", False)),
               "explanation_fallback": int(v.get("explanation_fallback", 0) or 0)}
        for c in "BCD":
            ch = (v.get(c) or {}).get("chars") if isinstance(v.get(c), dict) else v.get(f"L_{c}")
            row[f"L_{c}"] = _num(ch)
        out[k] = row
    return out


def build_dataset(res_dir: Path, cfg: dict[str, Any], ledger: list[dict[str, Any]],
                  tasks: list[dict[str, Any]], index: dict[str, dict[str, Any]]) -> pd.DataFrame:
    """One row per scheduled run with outcomes, task attributes and covariates."""
    outs: dict[str, dict[str, Any]] = {}
    p = res_dir / "wp5_outcomes.jsonl"
    if p.exists():
        for r in read_jsonl(p):
            outs[run_key(r)] = r
    tmap = {t["instance_id"]: t for t in tasks}
    infra = set(cfg["infra_states"])
    rows = []
    for r in ledger:
        tid = r.get("instance_id")
        if tid not in tmap:
            continue  # dev / excluded / unknown tasks never enter the analysis
        o = outs.get(run_key(r), {})
        t = tmap[tid]
        ix = index.get(tid, {})
        is_infra = bool(r.get("infra_failure")) or r.get("state") in infra
        row: dict[str, Any] = {
            "run_id": run_key(r), "task": tid, "repo": t["repo"], "condition": r["condition"],
            "model": r["model"], "rep": r.get("rep", r.get("k")), "state": r.get("state"),
            "infra_failure": is_infra, "stage": t["declared_stage"],
            "stage_H3": collapse_stage(t["declared_stage"]),
            "b_available": bool(t.get("b_available", False)),
            "agent_manifest_in_tree": bool(t.get("agent_manifest_in_tree", False)),
            "gold_drift_fail": bool(t.get("gold_drift_fail", False)),
            "inferred_stage": STAGE_ALIAS.get(str(t.get("inferred_stage", "")).upper()),
            "length_violation": bool(ix.get("length_violation", False)),
            "explanation_fallback": int(ix.get("explanation_fallback", 0)),
            "log_lc_ld": (math.log(ix["L_C"] / ix["L_D"]) if ix.get("L_C") and ix.get("L_D")
                          and ix["L_C"] > 0 and ix["L_D"] > 0 else 0.0),
            "L_B": ix.get("L_B", float("nan")),
        }
        for name, keys in ALIASES.items():
            v = next((o[k] for k in keys if k in o), None)
            row[name] = _num(v)
        up = o.get("uptake") or {}
        for k in ("repo_context", "label_term", "d1_name"):
            row[f"uptake_{k}"] = _num(up.get(k)) if up.get(k) is not None else float("nan")
        row["resolved"] = 0.0 if (is_infra or math.isnan(row["resolved"])) else row["resolved"]  # ITT
        if is_infra:
            for k in list(ALIASES):
                if k != "resolved":
                    row[k] = float("nan")
        row["any_new_edge"] = float(row["Y2"] > 0) if not math.isnan(row["Y2"]) else float("nan")
        rows.append(row)
    df = pd.DataFrame(rows)
    df["model_idx"] = df["model"].map({m: i for i, m in enumerate(cfg["models"])})
    return df


def complete_tasks(df: pd.DataFrame, cfg: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Tasks with every A, C, D run for every configured model; and the models with no runs."""
    models = [m for m in cfg["models"]]
    present = set(df["model"].unique())
    missing_models = [m for m in models if m not in present]
    need = cfg["replicates"]
    keep = []
    for t, g in df[df["condition"].isin(cfg["conditions_confirmatory"])].groupby("task"):
        cnt = g.groupby(["condition", "model"]).size()
        if all(cnt.get((c, m), 0) >= need for c in cfg["conditions_confirmatory"] for m in models):
            keep.append(t)
    return sorted(keep), missing_models


# ---------------------------------------------------------------------------
# models
# ---------------------------------------------------------------------------

def pname(c: str) -> str:
    """patsy name of the condition coefficient."""
    return f"{CC}[T.{c}]"


def ixname(c: str, s: str) -> str:
    """patsy name of the condition x stage interaction coefficient."""
    return f"{pname(c)}:C(stage_H3)[T.{s}]"


def build_formula(d: pd.DataFrame, y: str, *, interaction: bool = False, stage: bool = True,
                  model: bool = True, extra: tuple[str, ...] = ()) -> str:
    """Model formula; terms with fewer than two levels are dropped (e.g. each model alone)."""
    terms = [CC]
    if stage and d["stage_H3"].nunique() >= 2:
        terms = [f"{CC} * C(stage_H3)"] if interaction else [CC, "C(stage_H3)"]
    if model and d["model"].nunique() >= 2:
        terms.append("C(model)")
    terms += list(extra)
    return f"{y} ~ " + " + ".join(terms)


def _Lvec(names: list[str], coefs: dict[str, float]) -> Optional[np.ndarray]:
    if any(k not in names for k in coefs):
        return None
    v = np.zeros(len(names))
    for k, c in coefs.items():
        v[names.index(k)] = c
    return v


def contrast(fit: dict[str, Any], coefs: dict[str, float], *, log_link: bool = True) -> dict[str, Any]:
    """Wald contrast with t(G - 1) p and 95 % CI; ratio scale added for logit / log links."""
    nan = {"est": float("nan"), "se": float("nan"), "p": float("nan"), "ci": [float("nan")] * 2}
    if not fit.get("converged"):
        return {**nan, "note": "not converged"}
    L = _Lvec(fit["param_names"], coefs)
    if L is None:
        return {**nan, "note": "term not estimable"}
    dfd = max(fit["n_clusters"] - 1, 1)
    w = st.wald_contrast([fit["params"][n] for n in fit["param_names"]], fit["cov"], L, dfd)
    from scipy import stats as sps
    tcrit = sps.t.ppf(0.975, dfd)
    ci = [w["est"] - tcrit * w["se"], w["est"] + tcrit * w["se"]]
    out = {"est": w["est"], "se": w["se"], "stat": w["stat"], "df": dfd, "p": w["p"], "ci": ci}
    if log_link:
        def _exp(x: float) -> float:  # a quasi-separated simulated fit can give |est| > 700
            return math.exp(max(min(x, 700.0), -700.0))
        out.update({"ratio": _exp(w["est"]), "ratio_ci": [_exp(ci[0]), _exp(ci[1])]})
    return out


def fit_gee(d: pd.DataFrame, formula: str, groups: str = "repo", family: str = "binomial") -> dict[str, Any]:
    """GEE per plan 6.2 (exchangeable, bias-reduced)."""
    return st.gee_fit(d, formula, groups, family)


def fit_estimator(d: pd.DataFrame, formula: str, estimator: str, cfg: dict[str, Any],
                  n_boot_clogit: int) -> dict[str, Any]:
    """GEE (default) or the conditional-logit fallback in the same fit-dict shape."""
    if estimator == "gee":
        return fit_gee(d, formula, "repo")
    if estimator == "gee_task":
        return fit_gee(d, formula, "task")
    cl = st.conditional_logit_by_stratum(d, formula, "task", n_boot=n_boot_clogit,
                                         seed=cfg["seed"], boot_strata="stage")
    cl["n_clusters"] = int(d["task"].nunique())
    cl["cov_type"] = "bootstrap"
    return cl


def confirmatory(d: pd.DataFrame, cfg: dict[str, Any], *, estimator: str = "gee", extra: tuple[str, ...] = (),
                 model: bool = True, n_boot_clogit: int = 100, po_h3: bool = False) -> dict[str, Any]:
    """H1, H2 (M1) and H3 (M2) with raw p-values; Holm is applied by the caller."""
    d = d[d["condition"].isin(cfg["conditions_confirmatory"])]
    f1 = build_formula(d, "resolved", model=model, extra=extra)
    fit1 = fit_estimator(d, f1, estimator, cfg, n_boot_clogit)
    h1 = contrast(fit1, {pname("C"): 1})
    h2 = contrast(fit1, {pname("C"): 1, pname("D"): -1})
    d2 = d if po_h3 else d[d["stage_H3"] != "PO"]
    f2 = build_formula(d2, "resolved", interaction=True, model=model, extra=extra)
    fit2 = fit_estimator(d2, f2, estimator, cfg, n_boot_clogit)
    levels = sorted(d2["stage_H3"].unique())
    inter = [ixname("C", s) for s in levels[1:]]
    h3: dict[str, Any] = {"p": float("nan"), "levels": levels, "formula": f2}
    if fit2.get("converged") and levels[1:] and all(k in fit2["param_names"] for k in inter):
        L = np.array([_Lvec(fit2["param_names"], {k: 1}) for k in inter])
        w = st.wald_contrast([fit2["params"][n] for n in fit2["param_names"]], fit2["cov"], L,
                             max(fit2["n_clusters"] - 1, 1) if estimator != "clogit" else None)
        h3.update({"stat": w["stat"], "kind": w["kind"], "df_num": w.get("df_num"),
                   "df_denom": w.get("df_denom"), "p": w["p"]})
    stage_specific = {}
    for s in levels:
        ca = {pname("C"): 1}
        cd = {pname("C"): 1, pname("D"): -1}
        if s != levels[0]:
            ca[ixname("C", s)] = 1
            cd[ixname("C", s)] = 1
            if ixname("D", s) in fit2.get("param_names", []):
                cd[ixname("D", s)] = -1
        stage_specific[s] = {"C-A": contrast(fit2, ca), "C-D": contrast(fit2, cd),
                             "n_tasks": int(d2[d2["stage_H3"] == s]["task"].nunique()),
                             "n_repos": int(d2[d2["stage_H3"] == s]["repo"].nunique())}
    return {"formula_M1": f1, "formula_M2": f2, "H1": h1, "H2": h2, "H3": h3, "stage_specific": stage_specific,
            "n_runs": int(len(d)), "n_tasks": int(d["task"].nunique()), "n_clusters": fit1.get("n_clusters"),
            "converged": bool(fit1.get("converged")), "fallback_used": fit1.get("fallback_used"),
            "cov_struct_used": fit1.get("cov_struct_used"), "M2_converged": bool(fit2.get("converged")),
            "M2_fallback_used": fit2.get("fallback_used"), "_fit1": fit1}


def compact(c: dict[str, Any]) -> dict[str, Any]:
    """A confirmatory result without the fit object."""
    return {k: v for k, v in c.items() if not k.startswith("_")}


def holm3(c: dict[str, Any], alpha: float) -> dict[str, Any]:
    """Holm over (p_H1, p_H2, p_H3); verdicts at the familywise alpha."""
    ps = [c["H1"]["p"], c["H2"]["p"], c["H3"]["p"]]
    ok = [p for p in ps if p is not None and math.isfinite(p)]
    adj = [float("nan")] * 3
    if ok:
        a = st.holm_adjusted_p([p if math.isfinite(p) else 1.0 for p in ps])
        adj = [a[i] if math.isfinite(ps[i]) else float("nan") for i in range(3)]
    return {"raw_p": dict(zip(["H1", "H2", "H3"], ps)), "holm_p": dict(zip(["H1", "H2", "H3"], adj)),
            "reject": {h: bool(math.isfinite(a) and a < alpha) for h, a in zip(["H1", "H2", "H3"], adj)}}


# ---------------------------------------------------------------------------
# primary analysis (plan 6)
# ---------------------------------------------------------------------------

def po_is_h3_level(tasks_df: pd.DataFrame, cfg: dict[str, Any]) -> bool:
    """PO is a third H3 level only with >= 10 tasks from >= 4 repositories (plan 2.2)."""
    po = tasks_df[tasks_df["stage"] == "PO"]
    return bool(po["task"].nunique() >= cfg["stage"]["po_h3_min_tasks"]
                and po["repo"].nunique() >= cfg["stage"]["po_h3_min_repos"])


def vb_and_clogit(d: pd.DataFrame, cfg: dict[str, Any], gee_res: dict[str, Any], n_boot_clogit: int) -> dict[str, Any]:
    """Secondary estimators (plan 6.2) and the estimator-agreement flag."""
    out: dict[str, Any] = {}
    f1 = gee_res["formula_M1"]
    signs = {"gee": {"H1": np.sign(gee_res["H1"]["est"]), "H2": np.sign(gee_res["H2"]["est"])}}
    try:
        vb = st.binomial_mixed_glm_vb(d, f1, {"repo": "0 + C(repo)", "task": "0 + C(task)"})
        pm = vb["post_mean"]
        # rounded to 3 places: the VB optimiser is not bit-reproducible (differences ~1e-7)
        out["vb"] = {"conditional_or_C": round(vb["or"].get(pname("C"), float("nan")), 3),
                     "or_cri95_C": [round(v, 3) for v in vb["or_cri95"].get(pname("C"), [float("nan")] * 2)],
                     "H2_log_or": round(pm.get(pname("C"), float("nan")) - pm.get(pname("D"), float("nan")), 3),
                     "vc_sd_post_mean": {k: round(v, 3) for k, v in zip(vb["vc_names"], vb["vc_sd_post_mean"])},
                     "note": "variational posterior; not a calibrated frequentist SE"}
        signs["vb"] = {"H1": np.sign(pm.get(pname("C"), float("nan"))),
                       "H2": np.sign(out["vb"]["H2_log_or"])}
    except Exception as exc:  # noqa: BLE001
        out["vb"] = {"error": str(exc)[:300]}
    try:
        cl = fit_estimator(d, f1, "clogit", cfg, n_boot_clogit)
        c1, c2 = contrast(cl, {pname("C"): 1}), contrast(cl, {pname("C"): 1, pname("D"): -1})
        out["clogit"] = {"H1": c1, "H2": c2, "n_boot_ok": cl.get("n_boot_ok")}
        signs["clogit"] = {"H1": np.sign(c1["est"]), "H2": np.sign(c2["est"])}
    except Exception as exc:  # noqa: BLE001
        out["clogit"] = {"error": str(exc)[:300]}
    sens = {}
    for h in ("H1", "H2"):
        base = signs["gee"][h]
        others = [s[h] for k, s in signs.items() if k != "gee" and np.isfinite(s[h])]
        sens[h] = bool(any(o != base for o in others)) if np.isfinite(base) else None
    out["estimator_sensitive"] = sens
    out["signs"] = jsonable(signs)
    return out


def paired_boot_summary(d: pd.DataFrame, outcome: str, x: str, ref: str, n_boot: int, seed: int,
                        stat: str = "mean") -> dict[str, Any]:
    """Compact task-level paired bootstrap (plan 8.2)."""
    sub = d[d["condition"].isin([x, ref])]
    r = st.paired_task_bootstrap(sub, outcome, x, ref, "task", "stage", n_boot=n_boot, seed=seed, stat=stat)
    return {"estimate": r["estimate"], "ci": r["ci"], "n_tasks": r["n_tasks"], "stat": stat}


def primary(df: pd.DataFrame, cfg: dict[str, Any], tasks_df: pd.DataFrame, n_boot: int, n_boot_clogit: int,
            deviations: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Confirmatory analysis; returns (primary JSON, intermediate objects for later sections)."""
    keep, missing_models = complete_tasks(df, cfg)
    withdrawn = bool(missing_models)
    if withdrawn:
        deviations.append({"what": "model withdrawn / no runs", "models": missing_models, "when": "analysis",
                           "before_wp5_runs_complete": False,
                           "why": "plan 5: confirmatory analysis requires complete A, C, D runs for both models"})
    d = df[df["task"].isin(keep) & df["condition"].isin(cfg["conditions_confirmatory"])].copy()
    n_tasks = int(d["task"].nunique())
    exploratory_only = n_tasks < cfg["min_tasks_confirmatory"]
    out: dict[str, Any] = {"n_tasks_complete": n_tasks, "n_tasks_scheduled": int(df["task"].nunique()),
                           "n_runs": int(len(d)), "model_withdrawn": withdrawn,
                           "exploratory_only": exploratory_only, "scope": (
                               "two NIM models, mini-SWE-agent text mode, 40-step limit, manifests injected "
                               "into the prompt, Python SWE-rebench tasks; inference conditional on these models")}
    inter: dict[str, Any] = {"d": d}
    if d.empty or withdrawn:
        out["confirmatory"] = None
        return out, inter
    tdf = d.drop_duplicates("task")
    po3 = po_is_h3_level(tdf, cfg)
    res = confirmatory(d, cfg, po_h3=po3)
    out.update({"po_is_h3_level": po3, "h3_df": len(res["H3"]["levels"]) - 1 + (1 if po3 and "PO" not in res["H3"]["levels"] else 0),
                "G_repos": res["n_clusters"], "M1_M2": compact(res)})
    hm = holm3(res, cfg["alpha_familywise"])
    if exploratory_only:
        out["verdicts"] = None
        out["note"] = (f"only {n_tasks} tasks (< {cfg['min_tasks_confirmatory']}): WP5 is exploratory as a "
                       "whole (plan 7.4 rule 4); estimates with CIs only, no confirmatory family")
        out["holm"] = {"raw_p": hm["raw_p"]}
    else:
        out["holm"] = hm
        out["verdicts"] = {h: ("rejected" if hm["reject"][h] else "not rejected") for h in ("H1", "H2", "H3")}
    out["marginal_or"] = {"C_vs_A": {k: res["H1"].get(k) for k in ("ratio", "ratio_ci")},
                          "C_vs_D": {k: res["H2"].get(k) for k in ("ratio", "ratio_ci")}}
    seed = cfg["seed"]
    out["risk_difference"] = {
        "C-A": paired_boot_summary(d, "resolved", "C", "A", n_boot, seed),
        "C-D": paired_boot_summary(d, "resolved", "C", "D", n_boot, seed)}
    out["secondary_estimators"] = vb_and_clogit(d, cfg, res, n_boot_clogit)
    out["estimator_sensitive"] = out["secondary_estimators"]["estimator_sensitive"]
    inter.update({"res": res, "po3": po3})
    return out, inter


# ---------------------------------------------------------------------------
# secondary (plan 8)
# ---------------------------------------------------------------------------

def secondary(df: pd.DataFrame, cfg: dict[str, Any], d_conf: pd.DataFrame, po3: bool, n_boot: int) -> dict[str, Any]:
    """Outcome models (8.1), paired bootstraps (8.2), within-stage (8.3), condition B (8.4)."""
    out: dict[str, Any] = {"outcome_models": {}, "bootstrap": {}, "within_stage": {}, "condition_B": {}}
    acd = d_conf[d_conf["condition"].isin(["A", "C", "D"])] if not d_conf.empty else d_conf
    holm_keys: list[tuple[str, str]] = []
    holm_p: list[float] = []

    def one(d: pd.DataFrame, y: str, fam: str) -> dict[str, Any]:
        d = d[d[y].notna()]
        if d.empty or d["condition"].nunique() < 3 or d["repo"].nunique() < 3:
            return {"n_runs": int(len(d)), "note": "too little data"}
        fit = fit_gee(d, build_formula(d, y), "repo", fam)
        link = fam != "gaussian"
        return {"n_runs": int(len(d)), "n_clusters": fit["n_clusters"], "converged": fit["converged"],
                "family": fam, "C-A": contrast(fit, {pname("C"): 1}, log_link=link),
                "C-D": contrast(fit, {pname("C"): 1, pname("D"): -1}, log_link=link),
                "D-A": contrast(fit, {pname("D"): 1}, log_link=link)}

    for y, fam in SECONDARY.items():
        out["outcome_models"][y] = one(acd, y, fam)
        if y in HOLM_OUTCOMES:
            for c in ("C-A", "C-D"):
                holm_keys.append((y, c))
                holm_p.append(out["outcome_models"][y].get(c, {}).get("p", float("nan")))
        if y in ("Y1", "Y2", "Y4"):
            out["outcome_models"][f"{y}_among_resolved"] = one(acd[acd["resolved"] == 1], y, fam)
    adj = st.holm_adjusted_p([p if p is not None and math.isfinite(p) else 1.0 for p in holm_p]) if holm_p else []
    out["holm_descriptive_guard"] = {f"{y}:{c}": (a if math.isfinite(p) else None)
                                     for (y, c), a, p in zip(holm_keys, adj, holm_p)}
    for y in ["resolved"] + [f"Y{i}" for i in range(7)]:
        out["bootstrap"][y] = {}
        for x, ref in (("C", "A"), ("D", "A"), ("C", "D")):
            if acd.empty:
                continue
            out["bootstrap"][y][f"{x}-{ref}"] = paired_boot_summary(acd, y, x, ref, n_boot, cfg["seed"])
            if y in ("Y1", "Y4"):
                out["bootstrap"][y][f"{x}-{ref}_median"] = paired_boot_summary(acd, y, x, ref, n_boot,
                                                                                cfg["seed"], "median")
    # 8.3 within-stage, four-level strata, descriptive
    for s in sorted(acd["stage"].unique()) if not acd.empty else []:
        sub = acd[acd["stage"] == s]
        n_t, n_r = int(sub["task"].nunique()), int(sub["repo"].nunique())
        entry: dict[str, Any] = {"n_tasks": n_t, "n_repos": n_r,
                                 "claims_allowed": bool(n_t >= cfg["stage"]["within_stage_min_tasks"]
                                                        and n_r >= cfg["stage"]["within_stage_min_repos"]),
                                 "resolved_rate": sub.groupby("condition")["resolved"].mean().to_dict()}
        if n_r >= 3:
            fit = fit_gee(sub, build_formula(sub, "resolved", stage=False), "repo")
            entry.update({"C-A": contrast(fit, {pname("C"): 1}), "C-D": contrast(fit, {pname("C"): 1, pname("D"): -1})})
        out["within_stage"][s] = entry
    # 8.4 condition B
    tb = df[df["b_available"]]
    if not tb.empty and (tb["condition"] == "B").any():
        tb = tb.copy()
        full = [t for t, g in tb.groupby("task") if set(g["condition"]) >= {"A", "B", "C", "D"}]
        tb = tb[tb["task"].isin(full)]
        if tb["repo"].nunique() >= 3:
            fit = fit_gee(tb, build_formula(tb, "resolved"), "repo")
            out["condition_B"] = {
                "n_tasks": len(full), "B-A": contrast(fit, {pname("B"): 1}),
                "C-B": contrast(fit, {pname("C"): 1, pname("B"): -1}),
                "composition_by_stratum": tb.drop_duplicates("task")["stage"].value_counts().to_dict(),
                "B_length_chars": {k: float(v) for k, v in tb.drop_duplicates("task")["L_B"].describe().items()},
                "note": "exploratory; B is in no confirmatory hypothesis"}
    return out


# ---------------------------------------------------------------------------
# sensitivity (plan 9) and exploratory (plan 10)
# ---------------------------------------------------------------------------

def sensitivity(df: pd.DataFrame, cfg: dict[str, Any], d_conf: pd.DataFrame, po3: bool, n_boot: int,
                n_boot_clogit: int, res_dir: Path) -> dict[str, Any]:
    """SA1-SA9: reported in full, never changes a confirmatory verdict."""
    out: dict[str, Any] = {"note": "sensitivity analyses never change a confirmatory verdict"}
    if d_conf.empty:
        return {**out, "skipped": "no confirmatory population"}
    full_acd = df[df["condition"].isin(cfg["conditions_confirmatory"])]

    def run(name: str, d: pd.DataFrame, **kw: Any) -> dict[str, Any]:
        if d["repo"].nunique() < 3 or d["task"].nunique() < 6:
            out[name] = {"skipped": "too few clusters"}
            return out[name]
        c = confirmatory(d, cfg, n_boot_clogit=n_boot_clogit, po_h3=po3, **kw)
        r = {k: c[k] for k in ("n_runs", "n_tasks", "n_clusters", "converged", "fallback_used")}
        r.update({"H1": c["H1"], "H2": c["H2"], "H3_p": c["H3"]["p"]})
        out[name] = r
        return r

    run("SA1_exclude_infra_failures", full_acd[~full_acd["infra_failure"]])
    for m in cfg["models"]:
        run(f"SA2_model_{m}", d_conf[d_conf["model"] == m], model=False)
    run("SA3_exclude_agent_manifest_in_tree", d_conf[~d_conf["agent_manifest_in_tree"]])
    sa4 = d_conf[~d_conf["length_violation"]]
    run("SA4_exclude_length_violation_with_covariate", sa4, extra=("log_lc_ld",))
    run("SA5_exclude_gold_drift_fail", d_conf[~d_conf["gold_drift_fail"]])
    r6 = run("SA6_gee_grouped_by_task", d_conf, estimator="gee_task")
    # two-stage cluster bootstrap of the C-A and C-D risk differences
    for x, ref in (("C", "A"), ("C", "D")):
        b = st.paired_task_bootstrap(d_conf[d_conf["condition"].isin([x, ref])], "resolved", x, ref, "task",
                                     "stage", n_boot=10, seed=cfg["seed"])
        if b["n_tasks"]:
            t2r = d_conf.drop_duplicates("task").set_index("task")["repo"]
            idx = st.two_stage_cluster_bootstrap_indices([t2r[t] for t in b["task_ids"]], b["task_ids"],
                                                         b["strata"], n_boot, cfg["seed"])
            boot = np.array([b["d"][i].mean() for i in idx])
            out.setdefault("SA6_two_stage_bootstrap", {})[f"{x}-{ref}"] = {
                "estimate": b["estimate"], "ci": list(st.percentile_ci(boot, 0.95)), "n_tasks": b["n_tasks"]}
    run("SA7_conditional_logit", d_conf, estimator="clogit")
    run("SA8_exclude_explanation_fallback", d_conf[d_conf["explanation_fallback"] == 0])
    sa9 = res_dir / "wp5_outcomes_sa9.jsonl"
    if sa9.exists():
        rows = pd.DataFrame(read_jsonl(sa9))
        out["SA9_Y3_thresholds"] = {}
        base = d_conf.set_index("run_id")
        for var, g in rows.groupby("variant"):
            d = base.join(g.set_index("run_id")[["Y3"]].rename(columns={"Y3": "Y3_var"}), how="inner").reset_index()
            d = d[d["Y3_var"].notna()]
            if d["repo"].nunique() < 3:
                out["SA9_Y3_thresholds"][var] = {"skipped": "too few clusters"}
                continue
            fit = fit_gee(d, build_formula(d, "Y3_var"), "repo", "binomial")
            out["SA9_Y3_thresholds"][var] = {"C-A": contrast(fit, {pname("C"): 1}),
                                             "C-D": contrast(fit, {pname("C"): 1, pname("D"): -1}),
                                             "n_runs": int(len(d))}
    else:
        out["SA9_Y3_thresholds"] = {"status": "not provided",
                                    "reason": "needs a TBox rebuild and re-reasoning (and W re-measurement); "
                                              "supply wp5_outcomes_sa9.jsonl (run_id, variant, Y3)"}
    return out


def exploratory(df: pd.DataFrame, cfg: dict[str, Any], d_conf: pd.DataFrame, po3: bool,
                n_boot_clogit: int) -> dict[str, Any]:
    """Plan 10 items, all labelled exploratory."""
    out: dict[str, Any] = {"label": "exploratory; no multiplicity claims"}
    if d_conf.empty:
        return {**out, "skipped": "no confirmatory population"}
    d = d_conf
    # condition x model (joint Wald) and per-model contrasts
    if d["model"].nunique() >= 2 and d["repo"].nunique() >= 3:
        f = f"resolved ~ {CC} * C(model) + C(stage_H3)" if d["stage_H3"].nunique() >= 2 else \
            f"resolved ~ {CC} * C(model)"
        fit = fit_gee(d, f, "repo")
        inter = [n for n in fit["param_names"] if ":C(model)" in n] if fit["converged"] else []
        j = {}
        if inter:
            L = np.array([_Lvec(fit["param_names"], {k: 1}) for k in inter])
            w = st.wald_contrast([fit["params"][n] for n in fit["param_names"]], fit["cov"], L,
                                 max(fit["n_clusters"] - 1, 1))
            j = {"stat": w["stat"], "df_num": w["df_num"], "p": w["p"]}
        out["condition_x_model"] = {"joint_wald": j,
                                    "per_model": {m: compact(confirmatory(d[d["model"] == m], cfg, model=False,
                                                                          po_h3=po3)) for m in cfg["models"]
                                                  if d[d["model"] == m]["repo"].nunique() >= 3}}
    out["D_vs_A"] = None
    f1 = build_formula(d, "resolved")
    fit1 = fit_gee(d, f1, "repo")
    out["D_vs_A"] = contrast(fit1, {pname("D"): 1})
    # four-level declared stage interaction
    d4 = d.copy()
    d4["stage_H3"] = d4["stage"]
    if d4["stage"].nunique() >= 2:
        f4 = build_formula(d4, "resolved", interaction=True)
        fit4 = fit_gee(d4, f4, "repo")
        names = fit4["param_names"]
        inter = [n for n in names if n.startswith(pname("C") + ":")]
        if fit4["converged"] and inter:
            L = np.array([_Lvec(names, {k: 1}) for k in inter])
            w = st.wald_contrast([fit4["params"][n] for n in names], fit4["cov"], L, max(fit4["n_clusters"] - 1, 1))
            out["four_level_stage_interaction"] = {"stat": w["stat"], "df_num": w["df_num"], "p": w["p"]}
    # inferred stage replaces declared stage (only RQ1 = GO)
    if str(cfg.get("rq1_verdict", "")).upper() == "GO" and d["inferred_stage"].notna().any():
        di = d[d["inferred_stage"].notna()].copy()
        di["stage_H3"] = di["inferred_stage"]
        out["inferred_stage_replaces_declared"] = compact(confirmatory(di, cfg, po_h3=True))
    else:
        out["inferred_stage_replaces_declared"] = {"status": "not run",
                                                   "reason": "only if RQ1 verdict is GO and inferred stage is available"}
    # tables
    out["rates_by_model_stage_condition"] = jsonable(
        d.groupby(["model", "stage", "condition"])["resolved"].agg(["mean", "count"]).reset_index()
        .to_dict(orient="records"))
    up = df.groupby(["condition", "model"])[["uptake_repo_context", "uptake_label_term", "uptake_d1_name"]].mean()
    out["uptake_by_condition_model"] = jsonable(up.reset_index().to_dict(orient="records"))
    steps = {}
    for c in cfg["conditions_confirmatory"]:
        sub = d[d["condition"] == c]
        steps[c] = {str(s): float(((sub["resolved"] == 1) & (sub["Y6"] <= s)).mean()) if len(sub) else None
                    for s in cfg["step_grid"]}
    out["step_efficiency_curves"] = {"definition": "share of runs resolved within <= s steps", "curves": steps}
    ci = d[(d["condition"].isin(["A", "C"])) & d["inferred_stage"].notna()]
    rows = []
    for (s, inf), g in ci.groupby(["stage", "inferred_stage"]):
        ra = g[g["condition"] == "A"]["resolved"].mean()
        rc = g[g["condition"] == "C"]["resolved"].mean()
        rows.append({"declared": s, "inferred": inf, "n_tasks": int(g["task"].nunique()),
                     "resolved_A": ra, "resolved_C": rc, "risk_diff_C_minus_A": rc - ra})
    out["outcome_by_inferred_stage_within_declared"] = rows
    return out


# ---------------------------------------------------------------------------
# analyze driver
# ---------------------------------------------------------------------------

def cmd_analyze(a: argparse.Namespace) -> int:
    """Run all analyses; returns the process exit code (2 = refused)."""
    res_dir = Path(a.results_dir).resolve()
    out_dir = Path(a.out_dir).resolve() if a.out_dir else res_dir
    cfg_path = Path(a.config).resolve()
    cfg = load_config(cfg_path)
    if a.synthetic and "real_v2" in out_dir.parts:
        logger.error("refusing: --synthetic output directory %s is inside real_v2", out_dir)
        return 2
    if not a.synthetic and (a.n_boot or a.n_boot_clogit):
        logger.error("refusing: --n-boot overrides are only honoured with --synthetic (frozen config)")
        return 2
    n_boot = a.n_boot or cfg["bootstrap"]["n_boot"]
    n_boot_cl = a.n_boot_clogit or cfg["bootstrap"]["n_boot_clogit"]
    ledger_path = res_dir / "wp5_runs.jsonl"
    ledger: dict[str, dict[str, Any]] = {}
    if ledger_path.exists():
        for r in read_jsonl(ledger_path):
            ledger[run_key(r)] = r
    problems = check_refusals(res_dir, cfg_path, cfg, Path(a.repo_root).resolve(), a.synthetic, list(ledger.values()))
    if not ledger_path.exists():
        problems.append("wp5_runs.jsonl is missing")
    if problems:
        for p in problems:
            logger.error("REFUSED: %s", p)
        return 2
    t0 = time.perf_counter()
    tasks = load_tasks(res_dir / "wp5_tasks.json")
    drift_p = res_dir / "wp5_gold_drift.json"  # plan 5 drift check (run_wp5.py drift); wp5_tasks.json stays frozen
    if drift_p.exists():
        drift_fail = set(json.loads(drift_p.read_text()).get("gold_drift_fail", []))
        for t in tasks:
            if t["instance_id"] in drift_fail:
                t["gold_drift_fail"] = True
    index = load_index(res_dir / "wp5_manifests_index.json")
    df = build_dataset(res_dir, cfg, list(ledger.values()), tasks, index)
    deviations: list[dict[str, Any]] = []
    dev_path = res_dir / "wp5_deviations.json"
    if dev_path.exists():
        prev = json.loads(dev_path.read_text())
        deviations = list(prev.get("deviations", prev) if isinstance(prev, dict) else prev)
    stamp = {"synthetic": bool(a.synthetic), "config_sha256": sha256_file(cfg_path), "seed": cfg["seed"]}
    prim, inter = primary(df, cfg, df.drop_duplicates("task"), n_boot, n_boot_cl, deviations)
    d_conf, po3 = inter["d"], inter.get("po3", False)
    write_json(out_dir / "wp5_primary.json", {**stamp, **prim})
    logger.info("primary done (%.0fs): verdicts %s", time.perf_counter() - t0, prim.get("verdicts"))
    write_json(out_dir / "wp5_secondary.json", {**stamp, **secondary(df, cfg, d_conf, po3, n_boot)})
    write_json(out_dir / "wp5_sensitivity.json", {**stamp, **sensitivity(df, cfg, d_conf, po3, n_boot, n_boot_cl,
                                                                         res_dir)})
    expl = exploratory(df, cfg, d_conf, po3, n_boot_cl)
    if prim.get("model_withdrawn"):
        expl["surviving_model_analyses"] = {
            m: compact(confirmatory(df[df["model"] == m], cfg, model=False, po_h3=po3))
            for m in df["model"].unique() if df[df["model"] == m]["repo"].nunique() >= 3}
    write_json(out_dir / "wp5_exploratory.json", {**stamp, **expl})
    write_json(out_dir / "wp5_deviations.json", {**stamp, "deviations": deviations})
    logger.info("wrote outputs to %s (%.0fs)", out_dir, time.perf_counter() - t0)
    return 0


# ---------------------------------------------------------------------------
# power (plan 7)
# ---------------------------------------------------------------------------

def select_design(tasks: list[dict[str, Any]], cap: int, seed: int) -> list[dict[str, Any]]:
    """N = min(supply, cap); over the cap keep all PO, then equal allocation over ID/EVO/SERV in seeded order."""
    if len(tasks) <= cap:
        return sorted(tasks, key=lambda t: t["instance_id"])
    rng = np.random.default_rng(seed)
    by: dict[str, list[dict[str, Any]]] = {}
    for t in sorted(tasks, key=lambda t: t["instance_id"]):
        by.setdefault(t["declared_stage"], []).append(t)
    chosen = list(by.get("PO", []))
    rest = cap - len(chosen)
    orders = {s: [by[s][i] for i in rng.permutation(len(by[s]))] for s in ("ID", "EVO", "SERV") if s in by}
    take = {s: 0 for s in orders}
    while rest > 0 and any(take[s] < len(orders[s]) for s in orders):
        for s in sorted(orders):
            if rest > 0 and take[s] < len(orders[s]):
                take[s] += 1
                rest -= 1
    for s in orders:
        chosen += orders[s][:take[s]]
    return sorted(chosen, key=lambda t: t["instance_id"])


def design_frame(tasks: list[dict[str, Any]], replicates: int, h3_servicing_or: Optional[float] = None) -> pd.DataFrame:
    """Row-per-run design for A, C, D x 2 models x replicates with indicator columns."""
    rows = []
    for t in tasks:
        sh = collapse_stage(t["declared_stage"])
        for cond in "ACD":
            for m in (0, 1):
                for k in range(replicates):
                    rows.append({"repo": t["repo"], "task": t["instance_id"], "stage": t["declared_stage"],
                                 "stage_H3": sh, "condition": cond, "model": f"m{m}", "model_is_second": m,
                                 "is_A": int(cond == "A"), "is_C": int(cond == "C"), "is_D": int(cond == "D"),
                                 "is_C_ACTIVE": int(cond == "C" and sh == "ACTIVE"),
                                 "is_C_SERV": int(cond == "C" and sh == "SERVICING")})
    return pd.DataFrame(rows)


def power_test_fn(cfg: dict[str, Any], po3: bool, part: str):
    """test_fn for simulate_power: ``part`` = "M1" (H1, H2) or "M2" (H3), the section 6 pipeline."""
    def fn(d: pd.DataFrame) -> dict[str, float]:
        d = d[d["condition"].isin(cfg["conditions_confirmatory"])]
        if part == "M1":
            fit = fit_gee(d, build_formula(d, "resolved"))
            return {"H1": contrast(fit, {pname("C"): 1})["p"],
                    "H2": contrast(fit, {pname("C"): 1, pname("D"): -1})["p"]}
        d2 = d if po3 else d[d["stage_H3"] != "PO"]
        fit = fit_gee(d2, build_formula(d2, "resolved", interaction=True))
        levels = sorted(d2["stage_H3"].unique())
        inter = [ixname("C", s) for s in levels[1:]]
        if not fit["converged"] or not inter or not all(k in fit["param_names"] for k in inter):
            return {"H3": float("nan")}
        L = np.array([_Lvec(fit["param_names"], {k: 1}) for k in inter])
        return {"H3": st.wald_contrast([fit["params"][n] for n in fit["param_names"]], fit["cov"], L,
                                       max(fit["n_clusters"] - 1, 1))["p"]}
    return fn


def cmd_power(a: argparse.Namespace) -> int:
    """Plan 7.2 power simulation; writes wp5_power.json."""
    cfg = load_config(Path(a.config))
    pw = cfg["power"]
    seed = cfg["seed"]
    if a.workers > 1:
        logger.warning("--workers %d capped at 1 (resource limits)", a.workers)
    pilot = json.loads(Path(a.pilot_summary).read_text())
    k = pilot.get("k_A_resolved", pilot.get("A_resolved"))
    n = pilot.get("n_A_runs", pilot.get("A_total"))
    if n is None:
        n = 20  # plan 7.1: the pilot has 20 condition-A runs (10 tasks x 2 models)
    p0 = float(pilot["p0_hat"]) if "p0_hat" in pilot else float(k) / float(n)
    if k is None:
        k = round(p0 * n)
    jl = pilot.get("p0_jeffreys_80") or pilot.get("p0_jeffreys80")
    lo, hi = (jl if jl else st.jeffreys_interval(int(k), int(n), pw["jeffreys_level"]))
    raw_ml = float(pilot.get("model_logor", pilot.get("model_log_or", 0.0)))
    ml = float(np.clip(raw_ml / 2.0, -pw["model_logor_clip"], pw["model_logor_clip"]))
    tasks = load_tasks(Path(a.tasks))
    supply = {s: sum(1 for t in tasks if t["declared_stage"] == s) for s in ("ID", "EVO", "SERV", "PO")}
    chosen = select_design(tasks, a.cap or pw["cap_tasks"], seed)
    n_tasks = len(chosen)
    design = design_frame(chosen, cfg["replicates"])
    tdf = design.drop_duplicates("task")
    po3 = po_is_h3_level(tdf, cfg)
    n_rep = a.n_rep or pw["n_rep"]
    icc_grid = [float(x) for x in a.icc_grid.split(",")] if a.icc_grid else pw["icc_grid"]
    or_grid = [float(x) for x in a.or_grid.split(",")] if a.or_grid else pw["or_grid"]
    p0s = {"p0_hat": p0, "p0_lo": float(lo), "p0_hi": float(hi)}
    if a.p0_only:
        p0s = {"p0_hat": p0}
    fn1, fn3 = power_test_fn(cfg, po3, "M1"), power_test_fn(cfg, po3, "M2")
    cells: list[dict[str, Any]] = []
    t0 = time.perf_counter()
    # per-cell checkpoint (a crash must not lose hours): <out>.cells*.jsonl are read, <out>.cells.<tag>.jsonl is appended to
    cache: dict[str, dict[str, Any]] = {}
    outp = Path(a.out)
    for cf in sorted(outp.parent.glob(outp.name + ".cells*.jsonl")):
        for line in cf.read_text().splitlines():
            rec = json.loads(line)
            if rec["n_rep"] == n_rep:
                cache[rec["key"]] = rec["cell"]
    ckpt = outp.parent / (outp.name + ".cells." + (a.p0_subset or "all") + ".jsonl")

    def cached(key: str, make: Any) -> dict[str, Any]:
        if key not in cache:
            cache[key] = make()
            with open(ckpt, "a") as fh:
                fh.write(json.dumps({"key": key, "n_rep": n_rep, "cell": cache[key]}) + "\n")
        return cache[key]

    subset = set(a.p0_subset.split(",")) if a.p0_subset else None
    for pn, pv in p0s.items():
        if subset and pn not in subset:
            continue
        for icc in icc_grid:
            for orc in or_grid:
                for ord_name, ord_ in (("1", 1.0), ("sqrt(OR_C)", math.sqrt(orc))):
                    def mk1() -> dict[str, Any]:
                        r = st.simulate_power(design, pv, {"is_C": math.log(orc), "is_D": math.log(ord_)}, icc,
                                              pw["repo_share"], ml, fn1, n_rep=n_rep, seed=seed)
                        return {"test": "H1_H2", "p0_name": pn, "p0": pv, "icc": icc, "or_c": orc,
                                "or_d": ord_, "or_d_rule": ord_name, "power": r["rejection"],
                                "n_failed": r["n_failed"]}
                    c = cached(f"H12|{pn}|{icc}|{orc}|{ord_name}", mk1)
                    cells.append(c)
                    logger.info("cell %s icc=%.1f OR_C=%.2f OR_D=%s: H1 %s (%.0fs)", pn, icc, orc, ord_name,
                                c["power"].get("H1"), time.perf_counter() - t0)

            def mk3() -> dict[str, Any]:
                r = st.simulate_power(design, pv, {"is_C_ACTIVE": 0.0, "is_C_SERV": math.log(pw["h3_servicing_or"])},
                                      icc, pw["repo_share"], ml, fn3, n_rep=n_rep, seed=seed)
                return {"test": "H3", "p0_name": pn, "p0": pv, "icc": icc, "log_or_C_active": 0.0,
                        "or_C_servicing": pw["h3_servicing_or"], "power": r["rejection"], "n_failed": r["n_failed"]}
            cells.append(cached(f"H3|{pn}|{icc}", mk3))
    if subset:
        logger.info("subset %s done; run without --p0-subset to merge", sorted(subset))
        return 0
    a3 = str(0.05 / 3)
    grid = {c["or_c"]: c["power"]["H1"][a3] for c in cells
            if c["test"] == "H1_H2" and c["p0_name"] == "p0_hat" and c["icc"] == pw["icc_primary"]
            and c["or_d"] == 1.0}
    mde = st.mde_from_grid(grid, pw["powered_min"])
    label_p = next((c["power"]["H1"][a3] for c in cells if c["test"] == "H1_H2" and c["p0_name"] == "p0_hat"
                    and c["icc"] == pw["icc_primary"] and c["or_c"] == pw["label_or"] and c["or_d"] == 1.0), None)
    if label_p is None:
        label = "UNKNOWN (grid does not contain the labelling cell)"
    elif p0 < pw["p0_uninformative_below"] or p0 > pw["p0_uninformative_above"] or label_p < pw["underpowered_min"]:
        label = "UNINFORMATIVE"
    elif label_p >= pw["powered_min"]:
        label = "POWERED"
    else:
        label = "UNDER-POWERED"
    out = {"synthetic": False, "plan": cfg["plan"], "seed": seed, "n_rep": n_rep, "icc_grid": icc_grid,
           "or_grid": or_grid, "p0": {**p0s, "jeffreys80": [float(lo), float(hi)]}, "model_logor_raw": raw_ml,
           "model_logor_used": ml, "alpha_levels": [0.05 / 3, 0.05],
           "design": {"supply_by_stage": supply, "n_tasks_designed": n_tasks, "cap": a.cap or pw["cap_tasks"],
                      "n_repos": int(tdf["repo"].nunique()), "po_is_h3_level": po3,
                      "runs_per_task": 3 * 2 * cfg["replicates"]},
           "cells": cells, "power_H1_by_or_c_at_p0hat_icc_primary_alpha3": grid, "mde_or_c": mde,
           "label": label, "label_power": label_p,
           "n_decision": {"N": n_tasks, "confirmatory": bool(sum(supply.values()) >= pw["min_tasks_confirmatory"]),
                          "rule": "N = min(sum S_s, cap); exploratory as a whole if sum S_s < 40"},
           "label_cell": {"p0": "p0_hat", "or_c": pw["label_or"], "or_d": 1.0, "icc": pw["icc_primary"],
                          "alpha": "0.05/3", "test": "H1"}}
    write_json(Path(a.out), out)
    logger.info("wrote %s: label %s, MDE %s (%.0fs)", a.out, label, mde, time.perf_counter() - t0)
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description="WP5 analysis runner (Paper 1)")
    sub = ap.add_subparsers(dest="cmd")
    pa = sub.add_parser("analyze", help="sections 5-10 and 12 outputs")
    pa.add_argument("--results-dir", default=str(DEFAULT_RESULTS))
    pa.add_argument("--out-dir", default=None)
    pa.add_argument("--config", default=str(DEFAULT_CONFIG))
    pa.add_argument("--repo-root", default=str(PROJECT_ROOT))
    pa.add_argument("--synthetic", action="store_true", help="tests only: skip git/hash checks, stamp outputs")
    pa.add_argument("--n-boot", type=int, default=0, help="override (synthetic only)")
    pa.add_argument("--n-boot-clogit", type=int, default=0, help="override (synthetic only)")
    pp = sub.add_parser("power", help="plan 7.2 simulation -> wp5_power.json")
    pp.add_argument("--pilot-summary", required=True)
    pp.add_argument("--tasks", required=True)
    pp.add_argument("--out", default=str(DEFAULT_RESULTS / "wp5_power.json"))
    pp.add_argument("--config", default=str(DEFAULT_CONFIG))
    pp.add_argument("--n-rep", type=int, default=0)
    pp.add_argument("--workers", type=int, default=1)
    pp.add_argument("--cap", type=int, default=0)
    pp.add_argument("--icc-grid", default="")
    pp.add_argument("--or-grid", default="")
    pp.add_argument("--p0-subset", default=None, help="comma list of p0_hat,p0_lo,p0_hi: compute only these cells "
                    "(checkpointed); a final run without it merges all checkpoints into wp5_power.json")
    pp.add_argument("--p0-only", action="store_true", help="only p0_hat (test speed-up; not the plan grid)")
    ap.set_defaults(cmd="analyze")
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in ("analyze", "power", "-h", "--help"):
        argv = ["analyze", *argv]
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    return cmd_power(a) if a.cmd == "power" else cmd_analyze(a)


if __name__ == "__main__":
    sys.exit(main())
