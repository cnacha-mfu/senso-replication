"""WP2 step: assemble report.json with every metric of design section 6.4 (Paper 1, RQ2).

Reads the checkpointed artefacts (snapshots, agreement, measurements, verdicts, recheck, triangulation,
drift, sensitivity, explanations) and computes the flow table, prevalence, verdict distributions, the
contradiction rate per manifest and pooled (manifest-level bootstrap CIs, 10,000 resamples), breakdowns,
the foreign-manifest and mode-unanimity sensitivities, and the cue-word check. Nothing here decides a verdict.

Usage:
    python experiments/paper1_ontology_manifests/wp2_consistency.py report
"""

from __future__ import annotations

import logging
import re
import statistics
import time
from collections import Counter, defaultdict
from typing import Any, Optional

import numpy as np

from . import common as C

logger = logging.getLogger("wp2.report")
VERDICTS = ["SupportedClaim", "ContradictedClaim", "UnverifiableClaim", "IndeterminateClaim", "ConflictedClaim"]
FOREIGN_LEAVES = {"ScriptHostMissing", "PathNeverExisted"}
CUE = re.compile(r"create|add a new|will|should be|e\.g\.|example", re.I)


def q(x: list[float], p: float) -> Optional[float]:
    return float(np.percentile(x, p)) if x else None


def summarize(x: list[float]) -> dict[str, Any]:
    return {"n": len(x), "median": q(x, 50), "q1": q(x, 25), "q3": q(x, 75), "mean": float(np.mean(x)) if x else None}


def boot_ci(stat, n_items: int, B: int, seed: int) -> Optional[list[float]]:
    """Percentile 95% CI of ``stat(index array)`` over manifest-level resamples."""
    if n_items == 0:
        return None
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(B):
        idx = rng.integers(0, n_items, n_items)
        v = stat(idx)
        if v == v:
            vals.append(v)
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))] if vals else None


def rate_block(per: list[tuple[int, int, int]], B: int, seed: int) -> dict[str, Any]:
    """Pooled and mean-per-manifest contradiction rate from (S, C, K) triples, with bootstrap CIs."""
    arr = np.array(per) if per else np.zeros((0, 3))
    den = arr.sum(axis=1) if len(arr) else np.array([])
    ev = [i for i in range(len(arr)) if den[i] > 0]
    out: dict[str, Any] = {"n_manifests_evaluable": len(ev)}
    if not ev:
        return out
    a = arr[ev]
    d = a.sum(axis=1)
    pooled = a[:, 1].sum() / d.sum()
    per_rate = a[:, 1] / d
    out["pooled_rate"] = float(pooled)
    out["pooled_rate_ci95"] = boot_ci(lambda i: a[i, 1].sum() / max(1, a[i].sum()), len(a), B, seed)
    out["mean_manifest_rate"] = float(per_rate.mean())
    out["mean_manifest_rate_ci95"] = boot_ci(lambda i: float(per_rate[i].mean()), len(a), B, seed + 1)
    out["median_manifest_rate"] = float(np.median(per_rate))
    out["iqr_manifest_rate"] = [float(np.percentile(per_rate, 25)), float(np.percentile(per_rate, 75))]
    out["share_manifests_with_any_contradiction"] = float((a[:, 1] > 0).mean())
    out["share_ci95"] = boot_ci(lambda i: float((a[i, 1] > 0).mean()), len(a), B, seed + 2)
    out["totals"] = {"supported": int(a[:, 0].sum()), "contradicted": int(a[:, 1].sum()), "conflicted": int(a[:, 2].sum())}
    return out


def run(cfg: dict[str, Any], only: Optional[str] = None, force: bool = False) -> int:
    res = C.results_dir(cfg)
    B = cfg["bootstrap"]["report_resamples"]
    seed = cfg["seeds"]["bootstrap"]
    corpus = {e["slug"]: e for e in C.load_corpus(cfg)}
    snaps = {s: C.read_json(res / "snapshots" / f"{s}.json") for s in corpus if (res / "snapshots" / f"{s}.json").exists()}
    meas = {s: C.read_json(res / "measurements" / f"{s}.json") for s in corpus if (res / "measurements" / f"{s}.json").exists()}
    ver = {s: C.read_json(res / "verdicts" / f"{s}.json") for s in corpus if (res / "verdicts" / f"{s}.json").exists()}
    ag = C.read_json(res / "agreement.json") if (res / "agreement.json").exists() else {}
    rep: dict[str, Any] = {"generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    # ---------------- flow table ----------------
    from collections import Counter as Ct
    snap_status = Ct(s.get("snapshot_status") for s in snaps.values())
    resolved = [s for s, v in snaps.items() if v.get("snapshot_status") in ("exact_at_T_upper", "version_match")]
    min_votes = 2
    rows: list[dict[str, Any]] = []  # one per checked-or-not measured claim in analysed manifests
    for s in resolved:
        if s not in meas or s not in ver or not ver[s].get("consistent"):
            continue
        for c in meas[s]["claims"]:
            rec = ver[s]["claims"].get(c["key_str"], {})
            rows.append({"slug": s, "repo": meas[s]["repo"], "key": c["key_str"], "tcode": c["tcode"], "headline": c["headline"],
                         "votes": c["votes"], "verdict": (rec.get("verdicts") or [None])[0], "leaf": (rec.get("leaves") or [None])[0],
                         "mode_unanimous": c.get("mode_unanimous"), "quote": c["quote"], "attrs": c["attrs"],
                         "has_measure": bool(c["m"]["props"] or c["m"]["evidences"])})
    checked = [r for r in rows if r["votes"] >= min_votes and r["headline"]]
    flow = {
        "manifests": {"corpus": len(corpus), "cloneable": sum(1 for s in snaps.values() if s.get("cloneable")),
                      "snapshot_resolved": len(resolved), "snapshot_status": dict(snap_status),
                      "with_ge1_checked_claim": len({r["slug"] for r in checked}),
                      "with_ge1_verdict_claim": len({r["slug"] for r in checked if r["verdict"]}),
                      "inconsistent_aboxes": sum(1 for v in ver.values() if not v.get("consistent"))},
        "extraction": {m: {k: v.get(k) for k in ("responses", "parse_failures", "raw_claims", "schema_valid", "rejected_grounding",
                                                 "rejected_shape", "accepted_units_raw", "quote_repaired")}
                       for m, v in (ag.get("per_model") or {}).items()},
        "consensus": ag.get("flow", {}),
        "claims_in_analysed_manifests": {
            "consensus_asserting_votes_ge1": len(rows),
            "consensus_asserting_votes_ge2": sum(1 for r in rows if r["votes"] >= min_votes),
            "headline_eligible_votes_ge2": len(checked),
            "excluded_T7_or_protected": sum(1 for r in rows if r["votes"] >= min_votes and not r["headline"]),
            "measured": sum(1 for r in checked if r["has_measure"]),
            "with_verdict": sum(1 for r in checked if r["verdict"]),
            "unmeasured_no_verdict": sum(1 for r in checked if not r["verdict"]),
            "by_verdict": dict(Ct(r["verdict"] or "unmeasured" for r in checked)),
            "by_type": {t: dict(Ct(r["verdict"] or "unmeasured" for r in checked if r["tcode"] == t))
                        for t in sorted({r["tcode"] for r in checked})}}}
    rep["flow"] = flow

    # ---------------- prevalence ----------------
    types = sorted({r["tcode"] for r in checked})
    man = sorted({r["slug"] for r in checked} | set(resolved))
    prev = {}
    for t in types:
        counts = [sum(1 for r in checked if r["slug"] == s and r["tcode"] == t) for s in resolved if s in ver]
        prev[t] = {**summarize([float(x) for x in counts]), "pct_manifests_with_ge1": float(np.mean([x > 0 for x in counts])) if counts else None}
    rep["prevalence_checked_claims_per_manifest"] = prev
    rep["n_manifests_analysed"] = len([s for s in resolved if s in ver])

    # ---------------- verdict distribution ----------------
    vd: dict[str, Any] = {}
    for t in types:
        rt = [r for r in checked if r["tcode"] == t]
        vd[t] = {"n": len(rt), "verdicts": dict(Ct(r["verdict"] or "unmeasured" for r in rt)),
                 "leaves": dict(Ct(r["leaf"] or "unmeasured" for r in rt))}
    rep["verdict_distribution_by_type"] = vd
    rep["verdict_distribution_overall"] = dict(Ct(r["verdict"] or "unmeasured" for r in checked))

    # ---------------- contradiction rates ----------------
    def per_manifest(rs: list[dict[str, Any]]) -> tuple[list[str], list[tuple[int, int, int]]]:
        by = defaultdict(lambda: [0, 0, 0])
        for r in rs:
            if r["verdict"] == "SupportedClaim":
                by[r["slug"]][0] += 1
            elif r["verdict"] == "ContradictedClaim":
                by[r["slug"]][1] += 1
            elif r["verdict"] == "ConflictedClaim":
                by[r["slug"]][2] += 1
        slugs = [s for s in resolved if s in ver]
        return slugs, [tuple(by[s]) for s in slugs]  # type: ignore[misc]

    slugs, trip = per_manifest(checked)
    rep["contradiction_rate"] = {"all_types": rate_block(trip, B, seed)}
    doc_flag = {s: bool(ver[s].get("document")) for s in slugs if ver[s].get("consistent")}
    ev_slugs = [s for s, t in zip(slugs, trip) if sum(t) > 0]
    rep["pct_manifest_with_contradiction"] = {
        "reasoner_label_ManifestWithContradiction_among_analysed": float(np.mean([doc_flag.get(s, False) for s in slugs])) if slugs else None,
        "n_analysed": len(slugs),
        "among_manifests_with_ge1_S_C_K_claim": float(np.mean([doc_flag.get(s, False) for s in ev_slugs])) if ev_slugs else None,
        "n_with_ge1_S_C_K_claim": len(ev_slugs),
        "ci95_among_evaluable": boot_ci(lambda i: float(np.mean([doc_flag.get(ev_slugs[j], False) for j in i])), len(ev_slugs), B, seed + 7) if ev_slugs else None}
    for t in types:
        _, tr = per_manifest([r for r in checked if r["tcode"] == t])
        rep["contradiction_rate"][t] = rate_block(tr, B, seed + hash(t) % 1000)

    # breakdowns
    def breakdown(keyfn) -> dict[str, Any]:
        groups: dict[str, list[int]] = defaultdict(list)
        for i, s in enumerate(slugs):
            groups[keyfn(s)].append(i)
        return {g: {"n_manifests": len(ix), **{k: v for k, v in rate_block([trip[i] for i in ix], 2000, seed).items()
                                                if k in ("pooled_rate", "mean_manifest_rate", "n_manifests_evaluable", "totals")}}
                for g, ix in groups.items()}

    rep["contradiction_rate_by_manifest_type"] = breakdown(lambda s: (snaps[s].get("manifest_path") or "").rsplit("/", 1)[-1] or "?")
    rep["contradiction_rate_by_language"] = breakdown(lambda s: corpus[s].get("language") or "?")
    def cjk(s: str) -> str:
        t = corpus[s]["claude_md_content"]
        return "cjk_heavy" if sum(1 for ch in t if "一" <= ch <= "鿿" or "぀" <= ch <= "ヿ" or "가" <= ch <= "힯") / max(1, len(t)) > 0.05 else "latin"
    rep["manifest_text_script"] = dict(Ct(cjk(s) for s in slugs))
    ages, rates = [], []
    for s, t in zip(slugs, trip):
        sn = snaps[s]
        if sum(t) > 0 and sn.get("V_epoch") and sn.get("S_epoch"):
            ages.append((sn["S_epoch"] - sn["V_epoch"]) / 86400)
            rates.append(t[1] / sum(t))
    if len(ages) >= 5:
        from scipy.stats import spearmanr
        rho, p = spearmanr(ages, rates)
        rep["age_vs_contradiction_rate_spearman"] = {"n": len(ages), "rho": float(rho), "p": float(p), "exploratory": True,
                                                    "age_days_summary": summarize(ages)}
    # sensitivities on the claim set
    foreign = [r for r in checked if r["leaf"] not in FOREIGN_LEAVES]
    rep["sensitivity_exclude_foreign_manifest_leaves"] = {
        "excluded_leaves": sorted(FOREIGN_LEAVES), "n_excluded_claims": len(checked) - len(foreign),
        "n_foreign_contradicted": sum(1 for r in checked if r["leaf"] in FOREIGN_LEAVES and r["verdict"] == "ContradictedClaim"),
        "rate": rate_block(per_manifest(foreign)[1], B, seed + 11)}
    unan = [r for r in checked if r["mode_unanimous"]]
    rep["sensitivity_mode_unanimous_only"] = {"n_claims": len(unan), "rate": rate_block(per_manifest(unan)[1], B, seed + 12)}
    t1c = [r for r in checked if r["tcode"] == "T1" and r["verdict"] == "ContradictedClaim"]
    cue = [r for r in t1c if CUE.search(r["quote"])]
    rep["cue_word_check_T1_contradicted"] = {"n_contradicted_T1": len(t1c), "n_with_cue_word": len(cue),
                                             "share": (len(cue) / len(t1c)) if t1c else None,
                                             "meaning": "mechanical upper bound on mode errors among contradicted T1 claims"}
    sub = Ct(r["leaf"] for r in checked if r["verdict"] == "ContradictedClaim")
    rep["contradicted_subtypes"] = dict(sub)

    # ---------------- reasoner vs recheck, pellet ----------------
    if (res / "recheck.json").exists():
        rc = C.read_json(res / "recheck.json")
        rep["reasoner_vs_recheck"] = {k: rc[k] for k in ("n_claims", "agree_verdict", "agree_leaf", "kappa_verdict", "precision_contradicted",
                                                          "recall_contradicted", "n_reasoner_contradicted", "n_recheck_contradicted",
                                                          "confusion_matrix_rows_reasoner_cols_recheck", "by_type", "independence_check", "note")}
        rep["reasoner_vs_recheck"]["n_disagreements"] = len(rc["disagreements"])
        rep["reasoner_vs_recheck"]["n_leaf_only_disagreements"] = len(rc["leaf_only_disagreements"])
    pel = {s: C.read_json(res / "verdicts_pellet" / f"{s}.json") for s in corpus if (res / "verdicts_pellet" / f"{s}.json").exists()}
    if pel:
        agree = tot = 0
        n_inc = 0
        for s, pv in pel.items():
            if not pv.get("consistent"):
                n_inc += 1
                continue
            hv = ver.get(s)
            if not hv or not hv.get("consistent"):
                continue
            for k, h in hv["claims"].items():
                p = pv["claims"].get(k, {})
                tot += 1
                agree += (h["verdicts"] == p.get("verdicts", []))
        rep["hermit_vs_pellet"] = {"manifests_pellet_ran": len(pel), "manifests_pellet_crashed_or_inconsistent": n_inc,
                                   "note": "Pellet 2.3.1 throws InternalReasonerException ('Adding type to a pruned node') while classifying the "
                                           "claims TBox, as it did for the WP1 TBoxes; HermiT is therefore the only complete decision procedure here. "
                                           "Pellet's `explain` (instance check) still succeeds for most claims; see explanations.",
                                   "claims_compared": tot, "verdict_agreement": (agree / tot) if tot else None,
                                   "pellet_errors_sample": [pv.get("error", "")[:200] for pv in pel.values() if not pv.get("consistent")][:5]}
    for name, f in (("triangulation", "triangulation.json"), ("drift", "drift.json"), ("sensitivity", "sensitivity.json"),
                    ("explanations", "explanations_summary.json"), ("robustness_slow_models", "robustness.json")):
        if (res / f).exists():
            d = C.read_json(res / f)
            if name in ("triangulation",):
                d = {"summary": d["summary"], "notes": d["notes"]}
            if name == "drift":
                d = {"by_type": d["by_type"], "overall": d["overall"], "caveat": d["caveat"]}
            rep[name] = d
    rep["extraction_agreement"] = {k: ag.get(k) for k in ("panel", "pairwise_f1_overall", "pairwise_f1_mean", "pairwise_f1_by_type",
                                                          "alpha_presence", "alpha_line_level", "alpha_presence_by_type", "alpha_mode", "alpha_status_T2",
                                                          "alpha_qualifier_T6", "units_by_votes", "regex_recall", "caveat",
                                                          "strict_no_quote_repair")}
    # selftest, timings
    if (res / "selftest.json").exists():
        st = C.read_json(res / "selftest.json")
        rep["selftest"] = {k: st[k] for k in ("n_cases", "n_failures", "consistent", "verdicts_without_claims_module", "leaf_classes")}
    tm: dict[str, Any] = {}
    um = (ag.get("per_model") or {})
    tm["extraction_latency_s_sum_per_model"] = {m: round(v["usage"]["latency_s"], 1) for m, v in um.items()}
    tm["extraction_tokens"] = {m: v["usage"] for m, v in um.items()}
    raws = [p.stat().st_mtime for p in (res / "extraction" / "raw").glob("*/*.json")]
    tm["extraction_wall_s"] = round(max(raws) - min(raws), 1) if raws else None
    tm["measurement_s_total"] = round(sum(m_.get("seconds", 0) for m_ in meas.values()), 1)
    rs = [v["timings"].get("reason_s") for v in ver.values() if v.get("timings")]
    tm["hermit_reason_s_per_manifest"] = summarize([x for x in rs if x is not None])
    if (res / "explanations_summary.json").exists():
        tm["explain_mean_call_s"] = C.read_json(res / "explanations_summary.json").get("mean_call_s")
    rep["timings"] = tm
    # per-manifest table
    rep["per_manifest"] = [{"repo": corpus[s]["full_name"], "manifest": snaps[s].get("manifest_path"), "snapshot_status": snaps[s].get("snapshot_status"),
                            "S": snaps[s].get("S"), "S_C_K": list(t), "n_checked": sum(1 for r in checked if r["slug"] == s),
                            "ManifestWithContradiction": doc_flag.get(s)} for s, t in zip(slugs, trip)]
    C.write_json(res / "report.json", rep)
    logger.info("report written: %d manifests analysed, %d checked claims", rep["n_manifests_analysed"], len(checked))
    return 0
