"""WP2b report: do manifest errors get fixed? Confirmatory A1/A2, robustness, exploratory (Paper 1, RQ2b).

Reads ``results/real_v2/wp2b/claims.jsonl`` and ``head_fetch.json`` (written by ``step_persist``) and the frozen RQ2
``recheck_rows.jsonl``; writes ``report.json`` and ``report.md`` next to them. Analyses follow
papers/paper1/wp2b-persistence-design.md section 5 (A1, A2, robustness a-f, pooled-RR check from section 9) and
section 6 (exploratory, labelled as such). The decision wording is applied mechanically from the CI. No model is called.

Usage:
    python experiments/paper1_ontology_manifests/wp2_consistency.py persist_report
"""

from __future__ import annotations

import logging
import math
import statistics
from collections import Counter
from typing import Any, Optional

import numpy as np

from . import common as C
from .step_persist import out_dir
from .step_recheck import cohen_kappa

logger = logging.getLogger("wp2.step_persist_report")
OUTCOMES = ["U", "G", "R", "P-C", "P-S", "P-O"]


def f(x: Any) -> Optional[float]:
    """JSON-safe float (None for NaN)."""
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(x) else x


# ---------------------------------------------------------------------------
# statistics
# ---------------------------------------------------------------------------
def wilson(k: int, n: int) -> list[Optional[float]]:
    from statsmodels.stats.proportion import proportion_confint

    if n == 0:
        return [None, None]
    lo, hi = proportion_confint(k, n, alpha=0.05, method="wilson")
    return [f(lo), f(hi)]


def pct(a: np.ndarray, lo: float = 2.5, hi: float = 97.5) -> list[Optional[float]]:
    a = np.asarray(a, dtype=float)
    a = a[~np.isnan(a)]
    return [f(np.percentile(a, lo)), f(np.percentile(a, hi))] if a.size else [None, None]


def a1_wording(ci: list[Optional[float]]) -> str:
    lo, hi = ci
    if lo is None:
        return "not estimable"
    if lo >= 0.75:
        return "almost all contradicted claims persist"
    if lo > 0.50:
        return "most persist"
    if hi is not None and hi < 0.50:
        return "most are resolved"
    return "about half persist; the data cannot say whether most do"


def a2_wording(ci: list[Optional[float]]) -> str:
    lo, hi = ci
    if lo is None or hi is None:
        return "not estimable"
    if lo > 1:
        return "contradicted claims are removed more often than other claims"
    if hi < 1:
        return "contradicted claims are removed less often than other claims"
    if lo >= 0.5 and hi <= 2:
        return "removed at about the same rate as other claims"
    bounds = [f"{b:.2f}" for b, out in ((lo, lo < 0.5), (hi, hi > 2)) if out]
    return f"no detectable difference; the study cannot exclude an RR of {' or '.join(bounds)}"


def a1(rows: list[dict[str, Any]], seed: int, B: int) -> dict[str, Any]:
    """Share of contradicted (non-U) claims that are P-C; Wilson and manifest-cluster bootstrap CIs."""
    cl: dict[str, list[int]] = {}
    for r in rows:
        if r["verdict_S"] == "ContradictedClaim" and r["outcome"] != "U":
            c = cl.setdefault(r["slug"], [0, 0])
            c[0] += 1
            c[1] += r["outcome"] == "P-C"
    n = sum(v[0] for v in cl.values())
    k = sum(v[1] for v in cl.values())
    out: dict[str, Any] = {"n_claims": n, "n_manifests": len(cl), "n_persisted": k}
    if n == 0:
        return {**out, "estimate": None, "wilson_ci": [None, None], "cluster_bootstrap_ci": [None, None], "wording": "not estimable"}
    arr = np.array(list(cl.values()), dtype=float)
    idx = np.random.default_rng(seed).integers(0, len(arr), size=(B, len(arr)))
    boot = arr[idx, 1].sum(axis=1) / arr[idx, 0].sum(axis=1)
    ci = pct(boot)
    return {**out, "estimate": k / n, "wilson_ci": wilson(k, n), "cluster_bootstrap_ci": ci, "wording": a1_wording(ci)}


def mh(a: np.ndarray, n1: np.ndarray, b: np.ndarray, n0: np.ndarray) -> tuple[float, float]:
    """Mantel-Haenszel risk ratio and risk difference (contradicted vs supported) over strata."""
    N = n1 + n0
    num, den = float((a * n0 / N).sum()), float((b * n1 / N).sum())
    rr = (num / den) if den > 0 else (float("inf") if num > 0 else float("nan"))
    w = float((n1 * n0 / N).sum())
    rd = float(((a * n0 - b * n1) / N).sum() / w) if w > 0 else float("nan")
    return rr, rd


def a2(rows: list[dict[str, Any]], seed: int, B: int, removed: str = "removed") -> dict[str, Any]:
    """Within-manifest MH risk ratio of *removed*, contradicted vs supported, manifest-cluster bootstrap CI."""
    st: dict[str, list[int]] = {}
    for r in rows:
        if r["outcome"] == "U":
            continue
        c = st.setdefault(r["slug"], [0, 0, 0, 0])  # contra removed, contra n, supp removed, supp n
        i = 0 if r["verdict_S"] == "ContradictedClaim" else 2
        c[i] += int(r[removed])
        c[i + 1] += 1
    both = {s: v for s, v in st.items() if v[1] > 0 and v[3] > 0}
    out: dict[str, Any] = {"n_manifests_both_kinds": len(both),
                           "n_contradicted": sum(v[1] for v in both.values()), "n_supported": sum(v[3] for v in both.values()),
                           "removed_contradicted": sum(v[0] for v in both.values()), "removed_supported": sum(v[2] for v in both.values())}
    if not both:
        return {**out, "rr_mh": None, "rr_ci": [None, None], "rd_mh": None, "rd_ci": [None, None], "wording": "not estimable"}
    arr = np.array(list(both.values()), dtype=float)
    rr, rd = mh(arr[:, 0], arr[:, 1], arr[:, 2], arr[:, 3])
    idx = np.random.default_rng(seed).integers(0, len(arr), size=(B, len(arr)))
    br, bd = np.empty(B), np.empty(B)
    for i in range(B):
        s = arr[idx[i]]
        br[i], bd[i] = mh(s[:, 0], s[:, 1], s[:, 2], s[:, 3])
    ci = pct(br)
    return {**out, "rr_mh": f(rr) if math.isfinite(rr) else None, "rr_ci": ci, "rd_mh": f(rd), "rd_ci": pct(bd),
            "n_boot_rr_infinite": int(np.isinf(br).sum()), "wording": a2_wording(ci)}


def pooled_rr(rows: list[dict[str, Any]], seed: int, B: int) -> dict[str, Any]:
    """Crude (pooled) risk ratio of removed with a manifest-cluster bootstrap (design section 9: robustness)."""
    cl: dict[str, list[int]] = {}
    for r in rows:
        if r["outcome"] == "U":
            continue
        c = cl.setdefault(r["slug"], [0, 0, 0, 0])
        i = 0 if r["verdict_S"] == "ContradictedClaim" else 2
        c[i] += int(r["removed"])
        c[i + 1] += 1
    arr = np.array(list(cl.values()), dtype=float)
    if len(arr) == 0:
        return {}

    def rr(s: np.ndarray) -> float:
        t = s.sum(axis=0)
        return (t[0] / t[1]) / (t[2] / t[3]) if t[1] > 0 and t[3] > 0 and t[2] > 0 else float("nan")

    idx = np.random.default_rng(seed).integers(0, len(arr), size=(B, len(arr)))
    ci = pct(np.array([rr(arr[i]) for i in idx]))
    return {"rr": f(rr(arr)), "ci": ci, "wording": a2_wording(ci)}


def regressions(rows: list[dict[str, Any]], seed: int, B: int) -> dict[str, Any]:
    import pandas as pd

    from shared.evaluation.statistics import conditional_logit_by_stratum, gee_fit

    df = pd.DataFrame([{"slug": r["slug"], "removed": int(r["removed"]), "contradicted": int(r["verdict_S"] == "ContradictedClaim"),
                        "tcode": r["tcode"]} for r in rows if r["outcome"] != "U"])
    out: dict[str, Any] = {"n_obs": len(df), "n_manifests": int(df["slug"].nunique())}

    def pack(res: dict[str, Any], term: str = "contradicted") -> dict[str, Any]:
        names = list(res.get("param_names", []))
        if not res.get("converged") or term not in names:
            return {"converged": False}
        i = names.index(term)
        b = float(np.asarray(list(res["params"].values()) if isinstance(res["params"], dict) else res["params"])[i])
        d: dict[str, Any] = {"converged": True, "log_odds": b, "odds_ratio": float(np.exp(b))}
        if "ci" in res and res["ci"]:
            ci = res["ci"][term] if isinstance(res["ci"], dict) else res["ci"][i]
            d["or_ci"] = [float(np.exp(ci[0])), float(np.exp(ci[1]))]
        elif res.get("cov") is not None and np.size(res["cov"]):
            se = float(np.sqrt(np.asarray(res["cov"])[i, i]))
            d["or_ci"] = [float(np.exp(b - 1.96 * se)), float(np.exp(b + 1.96 * se))]
        if "p" in res and isinstance(res["p"], dict) and term in res["p"]:
            d["p"] = float(res["p"][term])
        for k in ("fallback_used", "n_boot_ok", "n_clusters"):
            if k in res:
                d[k] = res[k]
        return d

    try:
        out["conditional_logit_by_manifest"] = pack(conditional_logit_by_stratum(df, "removed ~ contradicted", "slug", n_boot=2000, seed=seed))
    except Exception as exc:  # noqa: BLE001
        out["conditional_logit_by_manifest"] = {"converged": False, "error": f"{type(exc).__name__}: {exc}"[:200]}
    try:
        out["gee_exchangeable"] = pack(gee_fit(df, "removed ~ contradicted + C(tcode)", "slug"))
    except Exception as exc:  # noqa: BLE001
        out["gee_exchangeable"] = {"converged": False, "error": f"{type(exc).__name__}: {exc}"[:200]}
    return out


# ---------------------------------------------------------------------------
def med(x: list[float]) -> Optional[float]:
    return f(statistics.median(x)) if x else None


def rng(x: list[float]) -> list[Optional[float]]:
    return [f(min(x)), f(max(x))] if x else [None, None]


def run(cfg: dict[str, Any], only: Optional[str] = None, force: bool = False) -> int:
    od = out_dir(cfg)
    res = C.results_dir(cfg)
    seed, B = int(cfg["seeds"]["bootstrap"]), int(cfg["bootstrap"]["report_resamples"])
    rows = C.read_jsonl(od / "claims.jsonl")
    hf = C.read_json(od / "head_fetch.json")
    rc = {(r["repo"], r["key"]): r for r in C.read_jsonl(res / "recheck_rows.jsonl")}
    for r in rows:
        r["removed"] = r["outcome"] in ("G", "R")
        r["removed_quote"] = r["outcome"] == "G" or (r["outcome"] not in ("U",) and not r.get("quote_verbatim", True))
        r["recheck_S_agrees"] = rc[(r["repo"], r["key"])]["agree_verdict"]
    contra = [r for r in rows if r["verdict_S"] == "ContradictedClaim"]
    supp = [r for r in rows if r["verdict_S"] == "SupportedClaim"]

    def oc(rs: list[dict[str, Any]]) -> dict[str, int]:
        c = Counter(r["outcome"] for r in rs)
        return {k: c.get(k, 0) for k in OUTCOMES}

    out: dict[str, Any] = {
        "design": "papers/paper1/wp2b-persistence-design.md (tag wp2b-prereg)",
        "head_fetch": {k: hf[k] for k in ("fetch_date", "fetch_started", "fetch_finished", "n_repos", "n_unavailable", "n_archived",
                                          "n_S_not_ancestor")},
        "population": {"n_claims": len(rows), "n_contradicted": len(contra), "n_supported": len(supp),
                       "n_manifests": len({r["slug"] for r in rows}),
                       "n_manifests_with_contradicted": len({r["slug"] for r in contra}),
                       "outcomes_contradicted": oc(contra), "outcomes_supported": oc(supp)},
    }
    # --- confirmatory
    out["A1"] = a1(rows, seed, B)
    out["A2"] = a2(rows, seed + 1, B)

    # --- robustness
    edited = [r for r in rows if (r.get("n_manifest_commits_S_H") or 0) >= 1]
    clean = [r for r in rows if not r.get("archived") and r.get("S_is_ancestor_of_H") is not False]
    agree = [r for r in rows if r["verdict_S"] != "ContradictedClaim" or r["recheck_S_agrees"]]
    rob: dict[str, Any] = {
        "a_conditional_logit_and_b_gee": regressions(rows, seed, B),
        "pooled_rr": pooled_rr(rows, seed + 2, B),
        "c_edited_manifests": {"n_manifests": len({r["slug"] for r in edited}), "A1": a1(edited, seed, B), "A2": a2(edited, seed + 1, B)},
        "d_excl_archived_and_non_ancestor": {"n_manifests": len({r["slug"] for r in clean}), "A1": a1(clean, seed, B),
                                             "A2": a2(clean, seed + 1, B)},
        "e_reasoner_recheck_agree": {"n_contradicted_dropped": sum(1 for r in contra if not r["recheck_S_agrees"]),
                                     "A1": a1(agree, seed, B), "A2": a2(agree, seed + 1, B)},
        "f_removed_by_quote_disappearance": a2(rows, seed + 1, B, removed="removed_quote"),
    }
    out["robustness"] = rob

    # --- exploratory
    ex: dict[str, Any] = {}
    by_t = {t: {"contradicted": oc([r for r in contra if r["tcode"] == t]), "supported": oc([r for r in supp if r["tcode"] == t])}
            for t in sorted({r["tcode"] for r in rows})}
    ex["outcomes_by_type"] = by_t
    ex["outcomes_contradicted_by_origin"] = {"drifted": oc([r for r in contra if r.get("drifted")]),
                                             "born_wrong": oc([r for r in contra if r.get("born_wrong")])}
    mans = {r["slug"]: r for r in rows}
    days = [(r["H_epoch"] - r["S_epoch"]) / 86400 for r in mans.values() if r.get("H_epoch")]
    ex["days_S_to_H_per_manifest"] = {"median": med(days), "range": rng(days), "n_manifests": len(days)}
    ex["commits_S_to_H_per_manifest"] = {"median": med([r["n_commits_S_H"] for r in mans.values() if r.get("n_commits_S_H") is not None]),
                                         "n_manifests_zero_commits": sum(1 for r in mans.values() if r.get("n_commits_S_H") == 0),
                                         "n_manifests_manifest_edited": sum(1 for r in mans.values() if (r.get("n_manifest_commits_S_H") or 0) >= 1),
                                         "n_manifests_gone": sum(1 for r in mans.values() if r["manifest_status"] == "gone")}
    sret = [r for r in supp if r["outcome"] in ("P-C", "P-S", "P-O")]
    yrs = sum((r["H_epoch"] - r["S_epoch"]) / 86400 / 365.25 for r in sret if r.get("H_epoch"))
    nfd = sum(1 for r in sret if r["outcome"] == "P-C")
    ex["forward_drift"] = {"n_retained_supported": len(sret), "n_now_contradicted": nfd,
                           "share": f(nfd / len(sret)) if sret else None, "wilson_ci": wilson(nfd, len(sret)),
                           "claim_years": f(yrs), "per_claim_year": f(nfd / yrs) if yrs else None}
    pc = [r for r in contra if r["outcome"] == "P-C"]
    age = [(r["H_epoch"] - r["intro_commit_epoch"]) / 86400 for r in pc if r.get("intro_commit_epoch")]
    flip = [(r["H_epoch"] - r["flip_commit_epoch"]) / 86400 for r in pc if r.get("flip_commit_epoch")]
    ex["minimum_age_of_uncorrected_error_days"] = {"n": len(age), "median": med(age), "range": rng(age)}
    ex["days_since_flip_for_persisting_drifted_days"] = {"n": len(flip), "median": med(flip), "range": rng(flip)}
    rem = [r for r in rows if r["outcome"] == "R"]
    found = [r for r in rem if (r.get("removal") or {}).get("commit")]
    tr = [(r["removal"]["epoch"] - r["S_epoch"]) / 86400 for r in found]
    ex["removal"] = {"n_R": len(rem), "n_removal_commit_found": len(found), "median_days_S_to_removal": med(tr), "range": rng(tr),
                     "hunk_shape": dict(Counter(r["removal"]["shape"] for r in found)),
                     "agent_signal": dict(Counter(str(r["removal"].get("agent_signal")) for r in found)),
                     "method": dict(Counter(r["removal"]["method"] for r in found)),
                     "by_verdict": {"contradicted": sum(1 for r in rem if r["verdict_S"] == "ContradictedClaim"),
                                    "supported": sum(1 for r in rem if r["verdict_S"] == "SupportedClaim")}}
    ret = [r for r in rows if r["outcome"] in ("P-C", "P-S", "P-O") and r.get("recheck_verdict_H")]
    pairs = [(r["verdict_H"], r["recheck_verdict_H"]) for r in ret]
    ex["recheck_agreement_at_H"] = {"n": len(pairs), "agree": sum(1 for a, b in pairs if a == b),
                                    "kappa": f(cohen_kappa(pairs)) if pairs else None,
                                    "n_disagree_contradicted": sum(1 for a, b in pairs if a != b and "ContradictedClaim" in (a, b))}
    ex["retained_contradicted_quote_edited"] = {
        "P-C_quote_verbatim": sum(1 for r in pc if r.get("quote_verbatim")), "P-C_quote_edited": sum(1 for r in pc if not r.get("quote_verbatim"))}
    ex["P-S_from_contradicted_leaves"] = dict(Counter(f"{r.get('leaf_S')}->{r.get('leaf_H')}" for r in contra if r["outcome"] == "P-S"))
    out["exploratory"] = ex
    C.write_json(od / "report.json", out)
    write_md(od, out)
    logger.info("A1 %s | A2 %s", {k: out["A1"][k] for k in ("estimate", "cluster_bootstrap_ci", "wording")},
                {k: out["A2"][k] for k in ("rr_mh", "rr_ci", "wording")})
    return 0


def write_md(od: Any, o: dict[str, Any]) -> None:
    def ci(x: list[Optional[float]]) -> str:
        return "[" + ", ".join("n/a" if v is None else f"{v:.2f}" for v in x) + "]"

    a1_, a2_, p = o["A1"], o["A2"], o["population"]
    rb = o["robustness"]
    L = [
        "# WP2b report: do manifest errors get fixed?", "",
        f"Head fetched {o['head_fetch']['fetch_date']} (single run). {p['n_claims']} claims in {p['n_manifests']} manifests "
        f"({p['n_contradicted']} contradicted in {p['n_manifests_with_contradicted']}, {p['n_supported']} supported). "
        "All values are in `report.json`; this file only restates them.", "",
        "## Outcomes", "", "| verdict at S | " + " | ".join(OUTCOMES) + " |", "|---|" + "---|" * len(OUTCOMES),
        "| contradicted | " + " | ".join(str(p["outcomes_contradicted"][k]) for k in OUTCOMES) + " |",
        "| supported | " + " | ".join(str(p["outcomes_supported"][k]) for k in OUTCOMES) + " |", "",
        "## A1 persistence of errors", "",
        f"{a1_['n_persisted']}/{a1_['n_claims']} contradicted claims persist (P-C): "
        f"{a1_['estimate']:.3f}, Wilson 95% CI {ci(a1_['wilson_ci'])}, cluster-bootstrap CI {ci(a1_['cluster_bootstrap_ci'])}. "
        f"Wording: \"{a1_['wording']}\".", "",
        "## A2 noticing (within manifest)", "",
        f"{a2_['n_manifests_both_kinds']} manifests have both kinds; removed: contradicted {a2_['removed_contradicted']}/{a2_['n_contradicted']}, "
        f"supported {a2_['removed_supported']}/{a2_['n_supported']}. MH RR {a2_['rr_mh']} CI {ci(a2_['rr_ci'])}; "
        f"MH RD {a2_['rd_mh']} CI {ci(a2_['rd_ci'])}. Wording: \"{a2_['wording']}\".", "",
        "## Robustness (decision unchanged)", "",
        f"- Pooled RR: {rb['pooled_rr']}", f"- Regressions: {rb['a_conditional_logit_and_b_gee']}",
        f"- (c) edited manifests: A1 {rb['c_edited_manifests']['A1']['estimate']} {ci(rb['c_edited_manifests']['A1']['cluster_bootstrap_ci'])}; "
        f"A2 RR {rb['c_edited_manifests']['A2']['rr_mh']} {ci(rb['c_edited_manifests']['A2']['rr_ci'])}",
        f"- (d) excl. archived/non-ancestor: A1 {rb['d_excl_archived_and_non_ancestor']['A1']['estimate']}; A2 RR {rb['d_excl_archived_and_non_ancestor']['A2']['rr_mh']} {ci(rb['d_excl_archived_and_non_ancestor']['A2']['rr_ci'])}",
        f"- (e) reasoner/re-check agree: A1 {rb['e_reasoner_recheck_agree']['A1']['estimate']}; A2 RR {rb['e_reasoner_recheck_agree']['A2']['rr_mh']} {ci(rb['e_reasoner_recheck_agree']['A2']['rr_ci'])}",
        f"- (f) removed = quote gone: RR {rb['f_removed_by_quote_disappearance']['rr_mh']} {ci(rb['f_removed_by_quote_disappearance']['rr_ci'])}", "",
        "## Exploratory (labelled as such in report.json)", "",
        f"- Forward drift: {o['exploratory']['forward_drift']}", f"- Removal: {o['exploratory']['removal']}",
        f"- Re-check agreement at H: {o['exploratory']['recheck_agreement_at_H']}", ""]
    (od / "report.md").write_text("\n".join(L), encoding="utf-8")
