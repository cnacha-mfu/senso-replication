"""RQ1 analysis for the Paper 1 rebuild, implemented exactly as pre-registered.

Used by: Paper 1 (RQ1). Spec: papers/paper1/rq1-preregistration.md (sections
4-8, 11). Configuration: configs/rq1_analysis.yaml. Statistics:
shared/evaluation/statistics.py (section 12 functions).

Compares reasoner-inferred lifecycle stages (C1 canonical Mann-Kendall stages,
C2 Rajlich & Bennett rule set) and the LOC-free comparator CF with the
maintainer-declared ground truth (WP3), collapsed to ACTIVE (A) / SERVICING (S)
/ PHASE_OUT (P); undetermined or inconsistent output is the predicted-only
category U (intention-to-classify).

Order of operations (prereg section 9, items 1-5):
  1. refuse unless the ground-truth sha256 matches and git is clean under
     ontology/ and experiments/paper1_ontology_manifests/;
  2. read population JSONs, take the reasoner labels from them (never
     recompute C1/C2 here), compute CF in Python;
  3. differential check: Python oracle vs reasoner labels on every config
     present in the input; a mismatch aborts BEFORE any ground-truth join;
  4. write rq1_labels.json and its sha256, THEN compute any agreement;
  5. primary, secondary, convergent, sensitivity, grid, noise, descriptive.

Expected input (adapter ``adapt_population_json``): one JSON per repository in
--input-dir (files starting with '_' are ignored, except '_run_meta.json'):

  {"repo": "owner/name",
   "unmineable": false, "unmineable_reason": null,
   "replaces": null,                      # GT repo this one replaces (prereg section 4)
   "measures": {                          # primary configuration, asserted values
       "locMKTau", "locMKpValue", "locSenSlope", "locRelSenSlopeAnnual",
       "monthsSinceLastCommit", "commitMKTau", "commitMKpValue",
       "meanMonthlyCommits", "activeMonthRatio", "distinctAuthorsInWindow",
       "multiAuthorMonthRatio", "featCommitCount", "bugFixCommitCount", "commitCount",
       "monthly_series": {"months": ["YYYY-MM", ...48, left-truncated, ending 2025-06],
                          "commits": [int, ...], "loc": [int, ...] | null}},
   "inferred": {                          # reasoner output keyed by config id
       "a0.05_L36_D12_G0.05_orig": {
           "classes": ["GrowthStage", "RBServicingStage", ...],  # inferred named classes
           "inconsistent": false, "inconsistency_explanation": null,
           "undetermined_reason": null,
           "explanation_graph": "<iri>" | {"C1": "<iri>", "C2": "<iri>"}}}}

Config id: ``cfg_id(alpha, L, D, G, mk)`` = f"a{alpha:g}_L{L}_D{D}_G{G:g}_{mk}",
mk in {orig, hr}. Measure keys are matched case- and underscore-insensitively.
The one-at-a-time sensitivity runs (S1-S5) need their config ids in
``inferred``; missing ones are reported as missing, never filled by Python.

Usage:
    python experiments/paper1_ontology_manifests/run_rq1_v2.py \\
        --input-dir experiments/paper1_ontology_manifests/results/real_v2/population
    # holdout, only if rq1_primary.json says REVISE:
    python experiments/paper1_ontology_manifests/run_rq1_v2.py --holdout \\
        --holdout-dir <holdout population dir> --holdout-ground-truth <holdout gt json>
    # synthetic pipeline test (never writes to the real output directory):
    python experiments/paper1_ontology_manifests/run_rq1_v2.py --synthetic --allow-dirty \\
        --input-dir <dir> --ground-truth <synthetic gt> --output-dir <dir> --n-boot 300
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import logging
import math
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from shared.evaluation import statistics as st  # noqa: E402

logger = logging.getLogger("rq1")

CLASSES = ["A", "S", "P"]
LABELS = ["A", "S", "P", "U"]
CODE = {"A": 0, "S": 1, "P": 2, "U": 3}
CLF_NAMES = ["C1", "C2", "CF"]
C1_CLASSES = ("GrowthStage", "StabilizationStage", "DeclineStage")
C2_CLASSES = ("RBActiveDevelopmentStage", "RBServicingStage", "RBPhaseOutStage")
C1_SHORT = {"GrowthStage": "Growth", "StabilizationStage": "Stabilization",
            "DeclineStage": "Decline"}
MK_VARIANTS = {"orig": "original_test", "hr": "hamed_rao_modification_test"}
CONFIG_PATH = Path(__file__).resolve().parent / "configs" / "rq1_analysis.yaml"


# =============================================================================
# Generic helpers
# =============================================================================
def cfg_id(alpha: float, L: int, D: int, G: float, mk: str) -> str:
    """Config id used as the key of ``inferred`` in the population JSONs."""
    return f"a{alpha:g}_L{int(L)}_D{int(D)}_G{G:g}_{mk}"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def clean(o: Any) -> Any:
    """Make an object JSON-safe: numpy -> python, NaN/inf -> None."""
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, np.ndarray):
        return clean(o.tolist())
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        f = float(o)
        return None if (math.isnan(f) or math.isinf(f)) else f
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(clean(obj), f, indent=2, sort_keys=False)
        f.write("\n")


def norm_key(k: str) -> str:
    return re.sub(r"[^a-z0-9]", "", k.lower())


def local_name(x: str) -> str:
    return re.split(r"[#/:]", str(x))[-1]


def parse_time(s: str) -> datetime:
    s = s.replace("Z", "+00:00")
    t = datetime.fromisoformat(s)
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return t


def git(args: list[str]) -> str:
    return subprocess.run(["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True,
                          check=False).stdout.strip()


# =============================================================================
# Input adapter (adjust here once the real population format is known)
# =============================================================================
@dataclass
class RepoRecord:
    repo: str
    unmineable: bool = False
    unmineable_reason: Optional[str] = None
    replaces: Optional[str] = None
    measures: dict = field(default_factory=dict)       # normalised key -> raw value
    months: Optional[list[str]] = None
    commits: Optional[list[float]] = None
    loc: Optional[list[float]] = None
    inferred: dict = field(default_factory=dict)       # cfg id -> entry dict
    source_file: str = ""
    _cache: dict = field(default_factory=dict, repr=False)

    def mk(self, kind: str, L: int, variant: str) -> Optional[dict]:
        """Cached Mann-Kendall measures of the last L months of the 'loc' or 'commits' series."""
        key = (kind, L, variant)
        if key not in self._cache:
            series = self.loc if kind == "loc" else self.commits
            self._cache[key] = _mk(_tail(series, L), variant)
        return self._cache[key]

    def m(self, name: str) -> Optional[float]:
        """Measured value by (case/underscore-insensitive) name; None if absent/NaN."""
        v = self.measures.get(norm_key(name))
        if v is None or isinstance(v, (dict, list)):
            return None
        try:
            f = float(v)
        except (TypeError, ValueError):
            return None
        return None if math.isnan(f) else f


def adapt_population_json(obj: dict, source: str = "") -> RepoRecord:
    """Convert one per-repository population JSON to a RepoRecord (schema in the module docstring)."""
    meas_raw = dict(obj.get("measures") or {})
    series = meas_raw.pop("monthly_series", None) or obj.get("monthly_series") or {}
    rec = RepoRecord(
        repo=obj["repo"],
        unmineable=bool(obj.get("unmineable", False)),
        unmineable_reason=obj.get("unmineable_reason"),
        replaces=obj.get("replaces"),
        measures={norm_key(k): v for k, v in meas_raw.items()},
        months=series.get("months"),
        commits=series.get("commits"),
        loc=series.get("loc"),
        inferred=dict(obj.get("inferred") or {}),
        source_file=source,
    )
    return rec


def load_population(input_dir: Path) -> tuple[list[RepoRecord], dict]:
    recs: list[RepoRecord] = []
    meta: dict = {}
    for p in sorted(input_dir.glob("*.json")):
        if p.name == "_run_meta.json":
            meta = json.load(open(p))
            continue
        if p.name.startswith("_"):
            continue
        recs.append(adapt_population_json(json.load(open(p)), p.name))
    return recs, meta


# =============================================================================
# Labels from reasoner output (C1, C2) and Python (CF)
# =============================================================================
def reasoner_label(entry: Optional[dict], family: str, mapping: dict) -> dict:
    """Collapsed label from the inferred classes of one configuration.

    Never recomputed: read from ``classes``. Returns {label, raw, reason, explanation}.
    label in A/S/P/U. Inconsistent ABox, no stage class, or several stage classes
    (impossible under AllDisjoint) all give U with a reason.
    """
    if entry is None:
        return {"label": None, "raw": None, "reason": "CONFIG_MISSING", "explanation": None}
    group = C1_CLASSES if family == "C1" else C2_CLASSES
    expl = entry.get("explanation_graph")
    if isinstance(expl, dict):
        expl = expl.get(family)
    if entry.get("inconsistent"):
        return {"label": "U", "raw": "U", "reason": "REASONER_INCONSISTENT", "explanation": expl,
                "detail": entry.get("inconsistency_explanation")}
    found = [c for c in (local_name(x) for x in entry.get("classes", [])) if c in group]
    if len(found) == 1:
        raw = found[0]
        return {"label": mapping[raw], "raw": raw, "reason": None, "explanation": expl}
    reason = entry.get("undetermined_reason") or (
        "NO_STAGE_CLASS_INFERRED" if not found else "MULTIPLE_STAGE_CLASSES")
    return {"label": "U", "raw": "U", "reason": reason, "explanation": expl}


def _mk(series: list[float], variant: str) -> Optional[dict]:
    """Mann-Kendall measures as asserted (6 dp); None if not applicable / NaN."""
    import warnings
    import pymannkendall as pmk
    if series is None or len(series) < 4 or any(v is None for v in series):
        return None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = getattr(pmk, MK_VARIANTS[variant])(list(map(float, series)))
    vals = (r.Tau, r.p, r.slope)
    if any(v is None or (isinstance(v, float) and math.isnan(v)) for v in vals):
        return None
    slope = round(float(r.slope), 6)
    med = float(np.median(series))
    return {"tau": round(float(r.Tau), 6), "p": round(float(r.p), 6), "slope": slope,
            "rel": round(12.0 * slope / max(med, 1.0), 6), "n": len(series)}


def _tail(xs: Optional[list], L: int) -> Optional[list]:
    return None if xs is None else list(xs)[-L:]


def oracle_c1(rec: RepoRecord, alpha: float, L: int, mk: str) -> str:
    """Python oracle for C1 (raw: Growth/Stabilization/Decline/U). Differential-test only."""
    r = rec.mk("loc", L, mk)
    if r is None:
        return "U"
    if r["p"] < alpha:
        return "Growth" if r["tau"] > 0 else ("Decline" if r["tau"] < 0 else "U")
    return "Stabilization"


def oracle_c2(rec: RepoRecord, alpha: float, L: int, D: int, G: float, mk: str) -> str:
    """Python oracle for C2 (collapsed A/S/P/U). Differential-test and grid only."""
    msl = rec.m("monthsSinceLastCommit")
    if msl is not None and msl >= D:
        return "P"
    if msl is None:
        return "U"
    r = rec.mk("loc", L, mk)
    if r is None:
        return "U"
    growth = r["p"] < alpha and r["tau"] > 0
    return "A" if (growth and r["rel"] >= G) else "S"


def cf_label(rec: RepoRecord, alpha: float, L: int, D: int) -> dict:
    """CF (prereg 2.3): commit-count series only, no LOC. Independent of the reasoner.

    1. P if monthsSinceLastCommit >= D; 2. U if fewer than 4 months; 3. S if
    commit-MK p < alpha and tau < 0; 4. otherwise A. Missing recency -> U.
    Original MK always (CF is not part of S5). Falls back to the asserted
    commit-MK measures when no commit series is in the input (primary L only).
    """
    msl = rec.m("monthsSinceLastCommit")
    if msl is None:
        return {"label": "U", "reason": "MISSING_RECENCY"}
    if msl >= D:
        return {"label": "P", "reason": None}
    if rec.commits is not None:
        r = rec.mk("commits", L, "orig")
        if r is None:
            return {"label": "U", "reason": "COMMIT_SERIES_TOO_SHORT"}
        tau, p = r["tau"], r["p"]
    else:
        tau, p = rec.m("commitMKTau"), rec.m("commitMKpValue")
        if tau is None or p is None:
            return {"label": "U", "reason": "NO_COMMIT_SERIES"}
    return {"label": "S" if (p < alpha and tau < 0) else "A", "reason": None}


# =============================================================================
# Ground truth, noise subsets
# =============================================================================
def load_gt_records(path: Path) -> list[dict]:
    d = json.load(open(path))
    return d["records"] if isinstance(d, dict) else d


def noise_memberships(gt: dict, cfg: dict) -> dict:
    """Membership of one GT record in each noise subset (prereg 8.1)."""
    smap = cfg["classifier_stage_map"]
    w0 = parse_time(cfg["noise"]["window_start"] + "T23:59:59+00:00")
    snap = parse_time(cfg_snapshot_end(cfg))
    is_clf = gt["mapping"]["mapped_basis"] == "classifier"
    stratum = gt["stratum"]
    h = gt["history"]
    rels = [(parse_time(r["time"]), r) for r in h.get("releases", []) if r.get("time")]
    rels.sort(key=lambda x: x[0])

    def stage_of(r: dict) -> Optional[str]:
        v = r.get("dev_status")
        if isinstance(v, dict):
            v = v.get("value")
        return None if v is None else smap.get(str(v))

    in_window = [r for t, r in rels if w0 < t <= snap]
    before = [r for t, r in rels if t <= w0]
    in_effect = before[-1] if before else None
    n1_lenient, n1_strict = True, True
    if is_clf:
        for r in in_window + ([in_effect] if in_effect else []):
            s = stage_of(r)
            if s is not None and s != stratum:
                n1_lenient = n1_strict = False
        unverifiable = False
        for r in in_window:
            if (not r.get("fetched", False)) or (not r.get("has_classifier_field", False)) \
                    or r.get("dev_status") is None:
                unverifiable = True
        if h.get("truncated") and h.get("n_releases_total", 0) > h.get("n_releases_fetched", 0):
            unverifiable = True
        if unverifiable:
            n1_strict = False
    n2 = not bool(gt["signals"].get("classifier_stale_vs_latest", False))
    n3 = gt["mapping"]["mapped_basis"] != "readme"
    return {"N1-lenient": n1_lenient, "N1-strict": n1_strict, "N2": n2, "N3": n3,
            "N-clean": n1_strict and n2 and n3}


def cfg_snapshot_end(cfg: dict) -> str:
    return cfg["snapshot_date"] + "T23:59:59+00:00"


# =============================================================================
# Metrics on integer codes (truth 0..2, predicted 0..3)
# =============================================================================
W_LINEAR = st.ordinal_disagreement_weights(CLASSES, ("U",), "linear")


def _conf(t: np.ndarray, p: np.ndarray) -> np.ndarray:
    return np.bincount((t * 4 + p).astype(np.int64), minlength=12).reshape(3, 4).astype(float)


def _sq(t: np.ndarray, p: np.ndarray) -> np.ndarray:
    tab = np.zeros((4, 4))
    tab[:3] = _conf(t, p)
    return tab


def m_kappa(t, p) -> float:
    return st._kappa_from_square(_sq(t, p), None)


def m_kappa_w(t, p) -> float:
    return st._kappa_from_square(_sq(t, p), W_LINEAR)


def m_accuracy(t, p) -> float:
    return float(np.mean(t == p))


def m_undet(t, p) -> float:
    return float(np.mean(p == 3))


def _prf(c: np.ndarray, k: int) -> tuple[float, float, float]:
    tp = c[k, k]
    n_pred = c[:, k].sum()
    n_true = c[k].sum()
    prec = tp / n_pred if n_pred > 0 else float("nan")
    rec = tp / n_true if n_true > 0 else float("nan")
    f1 = 0.0 if n_pred == 0 else (2 * tp / (n_pred + n_true) if (n_pred + n_true) > 0 else 0.0)
    return prec, rec, f1


def _macro_f1(c: np.ndarray) -> float:
    f = [_prf(c, k)[2] for k in range(3) if c[k].sum() > 0]
    return float(np.mean(f)) if f else float("nan")


def m_macro_f1(t, p) -> float:
    return _macro_f1(_conf(t, p))


def m_bal_acc(t, p) -> float:
    c = _conf(t, p)
    r = [_prf(c, k)[1] for k in range(3) if c[k].sum() > 0]
    return float(np.mean(r)) if r else float("nan")


def m_kappa_cc(t, p) -> float:
    m = p != 3
    return m_kappa(t[m], p[m]) if m.any() else float("nan")


def m_macro_f1_cc(t, p) -> float:
    m = p != 3
    return m_macro_f1(t[m], p[m]) if m.any() else float("nan")


def _mk_class_fn(k: int, which: int):
    return lambda t, p: _prf(_conf(t, p), k)[which]


FULL_METRICS: dict = {"kappa": m_kappa, "kappa_linear_weighted": m_kappa_w,
                      "macro_f1": m_macro_f1, "balanced_accuracy": m_bal_acc,
                      "accuracy": m_accuracy, "undetermined_rate": m_undet,
                      "kappa_complete_case": m_kappa_cc, "macro_f1_complete_case": m_macro_f1_cc}
for _k, _c in enumerate(CLASSES):
    for _w, _n in enumerate(("precision", "recall", "f1")):
        FULL_METRICS[f"{_n}_{_c}"] = _mk_class_fn(_k, _w)
SLIM_METRICS = {m: FULL_METRICS[m] for m in
                ["kappa", "undetermined_rate", "recall_A", "recall_S", "recall_P"]}


def m_pair_kappa(a, b) -> float:
    tab = np.bincount((a * 4 + b).astype(np.int64), minlength=16).reshape(4, 4).astype(float)
    return st._kappa_from_square(tab, None)


def enc(labels: list[str]) -> np.ndarray:
    return np.array([CODE[x] for x in labels], dtype=np.int64)


def metric_block(res: dict, name: str, metric: str) -> dict:
    return {"point": res["point"][name][metric], "ci95": res["ci"][name][metric]["0.95"],
            "ci975": res["ci"][name][metric]["0.975"]}


def verdict_for(res: dict, name: str, vcfg: dict, level: str = "0.975") -> dict:
    p = res["point"][name]
    lb = res["ci"][name]["kappa"][level][0]
    recalls = {c: p[f"recall_{c}"] for c in CLASSES}
    v = st.agreement_verdict(p["kappa"], lb, recalls, p["undetermined_rate"],
                             vcfg["kappa_pass"], vcfg["lb_pass"], vcfg["recall_pass"],
                             vcfg["max_undetermined"])
    return {"verdict": v, "kappa": p["kappa"], "kappa_lower_bound": lb, "ci_level": float(level),
            "recalls": recalls, "undetermined_rate": p["undetermined_rate"]}


def agreement(truth: np.ndarray, preds: dict, strata: list[str], metrics: dict, bcfg: dict,
              pairs: tuple = ()) -> dict:
    return st.bootstrap_agreement(truth, preds, strata, metrics, n_boot=bcfg["n_boot"],
                                  seed=bcfg["seed"], levels=tuple(bcfg["levels"]),
                                  pairwise_diff=pairs)


# =============================================================================
# Pre-flight
# =============================================================================
class Refusal(RuntimeError):
    pass


def preflight(cfg: dict, args: argparse.Namespace, deviations: list[dict]) -> dict:
    info: dict = {}
    gt_path = Path(args.ground_truth) if args.ground_truth else PROJECT_ROOT / cfg["ground_truth"]["path"]
    if args.ground_truth and not args.synthetic:
        raise Refusal("--ground-truth override is only allowed with --synthetic")
    gt_sha = sha256_file(gt_path)
    info["ground_truth_path"] = str(gt_path)
    info["ground_truth_sha256"] = gt_sha
    if not args.synthetic:
        if gt_sha != cfg["ground_truth"]["sha256"]:
            raise Refusal(f"ground-truth sha256 mismatch: {gt_sha} != {cfg['ground_truth']['sha256']}")
    else:
        info["ground_truth_sha_check"] = "SKIPPED (--synthetic)"
        deviations.append({"what": "ground-truth sha256 check skipped and ground truth overridden",
                           "why": "--synthetic pipeline test", "when": now_iso(),
                           "before_unblinding": True})
    if args.n_boot is not None and not args.synthetic:
        raise Refusal("--n-boot override is only allowed with --synthetic")
    out_dir = Path(args.output_dir) if args.output_dir else PROJECT_ROOT / cfg["output_dir"]
    if args.synthetic and out_dir.resolve() == (PROJECT_ROOT / cfg["output_dir"]).resolve():
        raise Refusal("--synthetic must not write into the real RQ1 output directory")
    if args.output_dir and not args.synthetic and out_dir.resolve() != (PROJECT_ROOT / cfg["output_dir"]).resolve():
        logger.warning("non-default output directory %s", out_dir)
    excl = f":(exclude){cfg['output_dir']}"
    dirty = git(["status", "--porcelain", "--untracked-files=all", "--",
                 *cfg["clean_tree_paths"], excl])
    info["dirty_tree_paths"] = dirty.splitlines()
    if dirty:
        if args.allow_dirty:
            if not args.synthetic:
                raise Refusal("--allow-dirty is only allowed together with --synthetic")
            deviations.append({"what": "ran with a dirty git tree under ontology/ or "
                               "experiments/paper1_ontology_manifests/",
                               "why": "--allow-dirty, synthetic test only", "when": now_iso(),
                               "before_unblinding": True})
        else:
            raise Refusal("uncommitted changes under ontology/ or experiments/paper1_ontology_manifests/:\n"
                          + dirty)
    info["allow_dirty"] = bool(args.allow_dirty)
    info["output_dir"] = str(out_dir)
    return info


def build_manifest(cfg: dict, args: argparse.Namespace, pre: dict, meta: dict) -> dict:
    import scipy
    try:
        import pymannkendall
        pmk_v = getattr(pymannkendall, "__version__", None)
    except ImportError:  # pragma: no cover
        pmk_v = None
    tbox = {}
    for p in sorted((PROJECT_ROOT / "ontology" / "modules").glob("*.owl")):
        tbox[p.name] = sha256_file(p)
    freeze = git(["rev-parse", "--verify", "--quiet", f"{cfg['freeze_tag']}^{{commit}}"]) or None
    return {
        "prereg_file": cfg["prereg"],
        "prereg_commit": git(["log", "-1", "--format=%H", "--", cfg["prereg"]]) or None,
        "git_head": git(["rev-parse", "HEAD"]),
        "freeze_tag": cfg["freeze_tag"], "freeze_tag_commit": freeze,
        "ground_truth": {"path": pre["ground_truth_path"], "sha256": pre["ground_truth_sha256"],
                         "expected_sha256": cfg["ground_truth"]["sha256"],
                         "sha_check": pre.get("ground_truth_sha_check", "PASSED")},
        "analysis_config_sha256": sha256_file(CONFIG_PATH),
        "tbox_sha256": tbox,
        "reasoner_run_meta": meta,        # jar hashes, LOC tool version, if provided by the population run
        "libraries": {"numpy": np.__version__, "scipy": scipy.__version__,
                      "pymannkendall": pmk_v, "python": sys.version.split()[0]},
        "seed": cfg["bootstrap"]["seed"],
        "n_boot": args.n_boot or cfg["bootstrap"]["n_boot"],
        "synthetic": bool(args.synthetic), "allow_dirty": pre["allow_dirty"],
        "dirty_tree_paths": pre["dirty_tree_paths"],
        "command": sys.argv, "started_at": now_iso(),
    }


# =============================================================================
# Differential check (prereg 9.4): Python oracle vs reasoner labels
# =============================================================================
def differential_check(recs: list[RepoRecord], cfg: dict) -> dict:
    """Compare oracle and reasoner labels on every config present in the input.

    Covers C1 (raw phase) and C2 (collapsed) for every config id found in
    ``inferred``. Needs the monthly series; without them the check cannot run
    and the grid stays unavailable.
    """
    missing_series = [r.repo for r in recs if r.loc is None or r.months is None]
    parsed = {}
    for r in recs:
        for cid in r.inferred:
            m = re.fullmatch(r"a([0-9.]+)_L(\d+)_D(\d+)_G([0-9.]+)_(orig|hr)", cid)
            if m:
                parsed[cid] = (float(m[1]), int(m[2]), int(m[3]), float(m[4]), m[5])
    out: dict = {"n_repos": len(recs), "configs_checked": sorted(parsed),
                 "n_comparisons": 0, "mismatches": [], "measure_mismatches": [],
                 "repos_without_series": missing_series}
    # Repositories whose LOC series is absent (prereg §3 LOC-instrument failure path) are
    # checked separately: C1 must be undetermined, C2 undetermined or PHASE_OUT (Dormant
    # needs no LOC). All other repositories go through the full oracle comparison.
    for r in recs:
        if r.repo not in missing_series:
            continue
        for cid in parsed:
            if cid not in r.inferred:
                continue
            e = r.inferred[cid]
            l1 = reasoner_label(e, "C1", {c: "A" for c in C1_CLASSES})
            l2 = reasoner_label(e, "C2", {c: dict(zip(C2_CLASSES, CLASSES))[c] for c in C2_CLASSES})
            r1 = C1_SHORT.get(l1["raw"], "U")
            for fam, rv, ok in (("C1", r1, r1 == "U"), ("C2", l2["label"], l2["label"] in ("U", "P"))):
                out["n_comparisons"] += 1
                if not ok:
                    out["mismatches"].append({"repo": r.repo, "config": cid, "family": fam,
                                              "reasoner": rv, "oracle": "U (no LOC series)"})
    for r in recs:
        if r.repo in missing_series:
            continue
        for cid, (a, L, D, G, mk) in parsed.items():
            if cid not in r.inferred:
                continue
            e = r.inferred[cid]
            l1 = reasoner_label(e, "C1", {c: "A" for c in C1_CLASSES})
            l2 = reasoner_label(e, "C2", {c: dict(zip(C2_CLASSES, CLASSES))[c] for c in C2_CLASSES})
            o1 = oracle_c1(r, a, L, mk)
            o2 = oracle_c2(r, a, L, D, G, mk)
            r1 = C1_SHORT.get(l1["raw"], "U")
            for fam, rv, ov in (("C1", r1, o1), ("C2", l2["label"], o2)):
                out["n_comparisons"] += 1
                if rv != ov:
                    out["mismatches"].append({"repo": r.repo, "config": cid, "family": fam,
                                              "reasoner": rv, "oracle": ov})
        # informational: asserted primary measures vs recomputed
        pm = r.mk("loc", 36, "orig")
        if pm is not None and r.m("locMKTau") is not None:
            for key, mine in (("locMKTau", pm["tau"]), ("locMKpValue", pm["p"]),
                              ("locSenSlope", pm["slope"]), ("locRelSenSlopeAnnual", pm["rel"])):
                v = r.m(key)
                if v is not None and abs(v - mine) > 1e-5:
                    out["measure_mismatches"].append({"repo": r.repo, "measure": key,
                                                      "input": v, "recomputed": mine})
    out["status"] = "PASSED" if (out["n_comparisons"] > 0 and not out["mismatches"]) else (
        "FAILED" if out["mismatches"] else "NOT_RUN")
    if out["status"] == "NOT_RUN":
        out["reason"] = "no reasoner configurations in the input"
    out["agreement"] = (1.0 - len(out["mismatches"]) / out["n_comparisons"]) if out["n_comparisons"] else None
    return out


# =============================================================================
# Labels
# =============================================================================
def primary_cfg_id(cfg: dict) -> str:
    p = cfg["primary"]
    return cfg_id(p["alpha"], p["lookback_months"], p["dormancy_months"],
                  p["min_rel_loc_growth_per_year"], "orig")


def classify_primary(rec: RepoRecord, cfg: dict) -> dict:
    p = cfg["primary"]
    cid = primary_cfg_id(cfg)
    entry = rec.inferred.get(cid)
    if entry is None:
        raise Refusal(f"{rec.repo}: reasoner output for the primary configuration {cid} is missing")
    l1 = reasoner_label(entry, "C1", cfg["c1_mapping"])
    l2 = reasoner_label(entry, "C2", cfg["c2_mapping"])
    cf = cf_label(rec, p["alpha"], p["lookback_months"], p["dormancy_months"])
    return {"C1": l1, "C2": l2, "CF": cf}


def build_label_records(recs_in_slots: list[tuple[RepoRecord, dict]], cfg: dict) -> list[dict]:
    """Per-repository label record (prereg 11, rq1_labels.json)."""
    out = []
    cids = sorted({c for r, _ in recs_in_slots for c in r.inferred})
    pm = ["locMKTau", "locMKpValue", "locSenSlope", "locRelSenSlopeAnnual", "monthsSinceLastCommit",
          "commitMKTau", "commitMKpValue"]
    for rec, gt in recs_in_slots:
        lab = classify_primary(rec, cfg)
        cl = {}
        for cid in cids:
            e = rec.inferred.get(cid)
            if e is None:
                continue
            cl[cid] = {"C1": reasoner_label(e, "C1", cfg["c1_mapping"])["label"],
                       "C1_raw": reasoner_label(e, "C1", cfg["c1_mapping"])["raw"],
                       "C2": reasoner_label(e, "C2", cfg["c2_mapping"])["label"]}
        nm = noise_memberships(gt, cfg)
        out.append({
            "repo": rec.repo, "replaces": rec.replaces, "gt_repo": gt["repo"],
            "stratum": gt["stratum"], "collapsed_truth": cfg["collapse"][gt["stratum"]],
            "label_source": gt["mapping"]["mapped_basis"],
            "close_down_candidate": bool(gt["signals"].get("close_down_candidate", False)),
            "noise_subsets": [k for k, v in nm.items() if v],
            "inputs": {k: rec.m(k) for k in pm},
            "C1_raw": lab["C1"]["raw"], "C1": lab["C1"]["label"], "C2": lab["C2"]["label"],
            "CF": lab["CF"]["label"],
            "undetermined_reason": {"C1": lab["C1"]["reason"], "C2": lab["C2"]["reason"],
                                    "CF": lab["CF"]["reason"]},
            "inconsistency_detail": {"C1": lab["C1"].get("detail"), "C2": lab["C2"].get("detail")},
            "explanation_graph": {"C1": lab["C1"]["explanation"], "C2": lab["C2"]["explanation"]},
            "config_labels": cl,
        })
    return out


def assemble_slots(recs: list[RepoRecord], gt_records: list[dict], extra_gt: list[dict],
                   manifest: dict) -> list[tuple[RepoRecord, dict]]:
    """Match population JSONs to the ground-truth sample, handling replacements (prereg 4)."""
    by_name = {r.repo.lower(): r for r in recs}
    extra = {g["repo"].lower(): g for g in extra_gt}
    replacement_of = {r.replaces.lower(): r for r in recs if r.replaces and not r.unmineable}
    slots, unmineable, replacements, errors = [], [], [], []
    for g in gt_records:
        key = g["repo"].lower()
        r = by_name.get(key)
        if r is not None and not r.unmineable:
            slots.append((r, g))
            continue
        if r is not None and r.unmineable:
            unmineable.append({"repo": g["repo"], "reason": r.unmineable_reason})
        else:
            errors.append(f"{g['repo']}: no population JSON")
            continue
        rep = replacement_of.get(key)
        if rep is None:
            errors.append(f"{g['repo']}: unmineable and no replacement provided")
            continue
        eg = extra.get(rep.repo.lower())
        if eg is None:
            errors.append(f"{rep.repo}: replacement has no ground-truth record (--extra-ground-truth)")
            continue
        if eg["stratum"] != g["stratum"]:
            errors.append(f"{rep.repo}: replacement stratum {eg['stratum']} != {g['stratum']}")
            continue
        replacements.append({"replaced": g["repo"], "replacement": rep.repo, "stratum": g["stratum"]})
        slots.append((rep, eg))
    if errors:
        raise Refusal("cannot assemble the analysis population:\n  " + "\n  ".join(errors))
    manifest["unmineable"] = unmineable
    manifest["replacements"] = replacements
    return slots


# =============================================================================
# Analyses
# =============================================================================
def counts_by(items: list[tuple[str, str]]) -> dict:
    out: dict = {}
    for a, b in items:
        out.setdefault(a, {}).setdefault(b, 0)
        out[a][b] += 1
    return out


def confusion_json(truth: list[str], pred: list[str]) -> dict:
    t = st.confusion_table(truth, pred, CLASSES, LABELS)
    return {"rows_true": CLASSES, "cols_pred": LABELS, "counts": t.astype(int).tolist()}


def analyse_primary(L: list[dict], cfg: dict, bcfg: dict, level_key: str = "0.975") -> dict:
    """Primary (confirmatory) analysis and secondary metrics (prereg 6)."""
    truth_l = [r["collapsed_truth"] for r in L]
    strata = [r["stratum"] for r in L]
    truth = enc(truth_l)
    preds_l = {c: [r[c] for r in L] for c in CLF_NAMES}
    preds = {c: enc(v) for c, v in preds_l.items()}
    pairs = (("C2", "C1"), ("C1", "CF"), ("C2", "CF"))
    res = agreement(truth, preds, strata, FULL_METRICS, bcfg, pairs)
    vcfg = cfg["verdict"]
    out: dict = {"n": len(L), "bootstrap": {k: bcfg[k] for k in ("n_boot", "seed", "levels")},
                 "classifiers": {}}
    for c in CLF_NAMES:
        reasons = [(strata[i], L[i]["undetermined_reason"][c] or "?")
                   for i in range(len(L)) if preds_l[c][i] == "U"]
        cc_mask = [p != "U" for p in preds_l[c]]
        pc = st.per_class_metrics(truth_l, preds_l[c], CLASSES)
        block = {
            "metrics": {m: metric_block(res, c, m) for m in FULL_METRICS},
            "per_class_check": pc,
            "undetermined": {"n": int(sum(1 for p in preds_l[c] if p == "U")),
                             "rate": res["point"][c]["undetermined_rate"],
                             "by_reason": {k: sum(1 for _, v in reasons if v == k)
                                           for k in {v for _, v in reasons}},
                             "by_stratum": counts_by([(s, r) for s, r in reasons])},
            "complete_case": {"n_dropped": int(len(L) - sum(cc_mask)),
                              "kappa": metric_block(res, c, "kappa_complete_case"),
                              "macro_f1": metric_block(res, c, "macro_f1_complete_case")},
            "confusion_collapsed_truth_x_pred": confusion_json(truth_l, preds_l[c]),
            "confusion_strata_x_pred": {
                "rows_true": cfg["strata"], "cols_pred": LABELS,
                "counts": st.confusion_table(strata, preds_l[c], cfg["strata"], LABELS).astype(int).tolist()},
            "per_class_claimable": {k: (res["ci"][c][f"recall_{k}"]["0.95"][0]
                                        >= vcfg["per_class_claim_recall_lb"]) for k in CLASSES},
        }
        if c in ("C1", "C2"):
            block["verdict"] = verdict_for(res, c, vcfg, level_key)
            block["verdict_95ci_for_reference"] = verdict_for(res, c, vcfg, "0.95")["verdict"]
        else:
            block["verdict"] = {"verdict": "NOT_APPLICABLE",
                                "note": "CF is an evaluation comparator, not a stage model"}
        out["classifiers"][c] = block
    # (iii) C1 unmapped table
    raw_cols = ["Growth", "Stabilization", "Decline", "U"]
    raw_pred = [C1_SHORT.get(r["C1_raw"], "U") for r in L]
    out["classifiers"]["C1"]["confusion_strata_x_unmapped_phase"] = {
        "rows_true": cfg["strata"], "cols_pred": raw_cols,
        "counts": st.confusion_table(strata, raw_pred, cfg["strata"], raw_cols).astype(int).tolist()}
    v1 = out["classifiers"]["C1"]["verdict"]["verdict"]
    v2 = out["classifiers"]["C2"]["verdict"]["verdict"]
    if v1 == "PASS":
        action = "GO"
        note = "MK (D6) stays canonical; C2 reported as a secondary result."
    elif v2 == "PASS":
        action = "REVISE"
        note = ("C2 becomes the candidate canonical model; confirm on the holdout (positions 30-59 of "
                "each stratum's clean seeded order) with run_rq1_v2.py --holdout; GO with C2 only if "
                "the holdout verdict is PASS (95% CI, single test), otherwise NO-GO.")
    else:
        action = "NO-GO"
        note = "No stage model is claimed valid."
    rank = {"PASS": 3, "WEAK": 2, "FAIL": 1}
    best = max((v1, v2), key=lambda v: rank.get(v, 0))
    out["decision"] = {"C1": v1, "C2": v2, "action": action, "note": note,
                       "no_go_category": (best if action == "NO-GO" else None),
                       "per_class_claim_rule": ("per-class claims only for classes whose recall 95% "
                                                "lower bound >= 0.50 (see per_class_claimable)")}
    out["paired_differences"] = res["diff"]
    out["_res"] = res                 # stripped before writing
    out["_preds"] = (truth, preds, strata)
    return out


def analyse_secondary(L: list[dict], prim: dict, cfg: dict, bcfg: dict) -> dict:
    truth = enc([r["collapsed_truth"] for r in L])
    strata = [r["stratum"] for r in L]
    out: dict = {"paired_delta_kappa": {k: v["kappa"] for k, v in prim["paired_differences"].items()}}
    # ablation ladder
    p = cfg["primary"]
    g0 = cfg_id(p["alpha"], p["lookback_months"], p["dormancy_months"], 0.0, "orig")
    ladder_preds = {"C1": [r["C1"] for r in L], "C2": [r["C2"] for r in L]}
    miss = [r["repo"] for r in L if g0 not in r["config_labels"]]
    if miss:
        out["ablation_ladder"] = {"status": "UNAVAILABLE",
                                  "reason": f"config {g0} missing in the input for {len(miss)} repositories"}
    else:
        ladder_preds["C2_G0"] = [r["config_labels"][g0]["C2"] for r in L]
        res = agreement(truth, {k: enc(v) for k, v in ladder_preds.items()}, strata, SLIM_METRICS,
                        bcfg, (("C2_G0", "C1"), ("C2", "C2_G0")))
        out["ablation_ladder"] = {
            "steps": ["C1 (MK only)", "C2_G0 (MK + dormancy)", "C2 (adds magnitude)"],
            "metrics": {c: {m: metric_block(res, c, m) for m in SLIM_METRICS} for c in ladder_preds},
            "delta": res["diff"]}
    # 4-class tables + ID vs EVO ACTIVE difference
    four: dict = {}
    idx = st.stratified_bootstrap_indices(strata, bcfg["n_boot"], bcfg["seed"])
    st_arr = np.asarray(strata, dtype=object)
    for c in CLF_NAMES:
        pc = enc([r[c] for r in L])
        tab = st.confusion_table(strata, [r[c] for r in L], cfg["strata"], LABELS)
        fr = {}
        for s in ("initial_development", "evolution"):
            pos = np.flatnonzero(st_arr == s)
            fr[s] = (pc[pos] == 0).mean() if len(pos) else float("nan")
        diffs = np.full(len(idx), np.nan)
        pi, pe = np.flatnonzero(st_arr == "initial_development"), np.flatnonzero(st_arr == "evolution")
        if len(pi) and len(pe):
            diffs = (pc[idx[:, pi]] == 0).mean(axis=1) - (pc[idx[:, pe]] == 0).mean(axis=1)
        four[c] = {"rows_true": cfg["strata"], "cols_pred": LABELS, "counts": tab.astype(int).tolist(),
                   "proportion_predicted_ACTIVE": fr,
                   "ID_minus_EVO_ACTIVE": {"point": fr["initial_development"] - fr["evolution"],
                                           "ci95": list(st.percentile_ci(diffs, 0.95))}}
    out["four_class_reporting"] = four
    out["four_class_note"] = "No 4-class kappa is computed: no classifier outputs four classes."
    # population-weighted
    pw = {}
    for c in CLF_NAMES:
        pw[c] = st.stratum_weighted_metrics([r["collapsed_truth"] for r in L], [r[c] for r in L],
                                            strata, cfg["population_counts"], CLASSES, LABELS)
        pw[c].pop("weighted_confusion")
    out["population_weighted_exploratory"] = {
        "weights": cfg["population_counts"], "metrics": pw,
        "note": "Exploratory. The stratified kappa describes the balanced design, not the PyPI population."}
    return out


def analyse_convergent(L: list[dict], bcfg: dict) -> dict:
    strata = [r["stratum"] for r in L]
    out: dict = {"note": "Kappa between classifiers over {A,S,P,U}; pre-stated expectation "
                         "kappa(C1,CF) > 0 (not a decision criterion)."}
    labs = {c: enc([r[c] for r in L]) for c in CLF_NAMES}
    for a, b in (("C1", "CF"), ("C2", "CF"), ("C1", "C2")):
        res = agreement(labs[a], {b: labs[b]}, strata, {"kappa": m_pair_kappa}, bcfg)
        out[f"{a}_vs_{b}_all"] = {"n": len(L), "kappa": metric_block(res, b, "kappa")}
    keep = [i for i in range(len(L)) if L[i]["C2"] != "P" and L[i]["CF"] != "P"]
    if keep:
        res = agreement(labs["C2"][keep], {"CF": labs["CF"][keep]}, [strata[i] for i in keep],
                        {"kappa": m_pair_kappa}, bcfg)
        out["C2_vs_CF_both_non_PHASE_OUT"] = {"n": len(keep), "kappa": metric_block(res, "CF", "kappa")}
    return out


def analyse_noise(L: list[dict], cfg: dict, bcfg: dict) -> dict:
    out: dict = {"definitions": "prereg 8.1", "subsets": {}}
    min_n = cfg["noise"]["min_stratum_n"]
    contrib = {"A": ["initial_development", "evolution"], "S": ["servicing"], "P": ["phase_out"]}
    for sid in ("N1-lenient", "N1-strict", "N2", "N3", "N-clean"):
        sub = [r for r in L if sid in r["noise_subsets"]]
        counts = {s: sum(1 for r in sub if r["stratum"] == s) for s in cfg["strata"]}
        entry: dict = {"n": len(sub), "stratum_counts": counts, "n_dropped": len(L) - len(sub)}
        small = [s for s, n in counts.items() if n < min_n]
        entry["strata_below_min_n"] = small
        if len(sub) < 3 or len({r["collapsed_truth"] for r in sub}) < 2:
            entry["status"] = "NOT_ANALYSED (too few repositories or classes)"
            out["subsets"][sid] = entry
            continue
        out["subsets"][sid] = entry
        truth = enc([r["collapsed_truth"] for r in sub])
        strata = [r["stratum"] for r in sub]
        preds = {c: enc([r[c] for r in sub]) for c in CLF_NAMES}
        res = agreement(truth, preds, strata, FULL_METRICS, bcfg,
                        (("C2", "C1"), ("C1", "CF"), ("C2", "CF")))
        entry["classifiers"] = {}
        for c in CLF_NAMES:
            e = {"metrics": {m: metric_block(res, c, m) for m in FULL_METRICS},
                 "per_class_flag": {k: ("n < 10, not interpreted"
                                        if any(counts[s] < min_n for s in contrib[k]) else None)
                                    for k in CLASSES}}
            if c != "CF":
                e["verdict"] = verdict_for(res, c, cfg["verdict"])
            entry["classifiers"][c] = e
        entry["paired_differences"] = res["diff"]
    # close-down split (PO, descriptive)
    po = [r for r in L if r["stratum"] == "phase_out"]
    split = {}
    for name, flag in (("close_down_candidate", True), ("other_phase_out", False)):
        g = [r for r in po if r["close_down_candidate"] == flag]
        split[name] = {"n": len(g), **{c: {"recall_PHASE_OUT": (sum(1 for r in g if r[c] == "P") / len(g)
                                                               if g else None),
                                           "predicted": {l: sum(1 for r in g if r[c] == l) for l in LABELS}}
                                       for c in CLF_NAMES}}
    out["close_down_split_descriptive"] = split
    return out


def sens_variants(cfg: dict) -> list[dict]:
    p = cfg["primary"]
    base = dict(alpha=p["alpha"], L=p["lookback_months"], D=p["dormancy_months"],
                G=p["min_rel_loc_growth_per_year"], mk="orig")
    sens = cfg["sensitivity"]
    out = []
    key = {"alpha": "alpha", "lookback_months": "L", "dormancy_months": "D",
           "min_rel_loc_growth_per_year": "G"}
    for sid in ("S1", "S2", "S3", "S4"):
        f = sens[sid]
        for v in f["values"]:
            c = dict(base)
            c[key[f["factor"]]] = v
            out.append({"id": sid, "factor": f["factor"], "value": v, "applies_to": f["applies_to"],
                        "params": c, "mapping": "primary"})
    c = dict(base)
    c["mk"] = "hr"
    out.append({"id": "S5", "factor": "mk_variant", "value": "hamed_rao",
                "applies_to": sens["S5"]["applies_to"], "params": c, "mapping": "primary"})
    out.append({"id": "S6", "factor": "c1_mapping", "value": "decline_to_servicing",
                "applies_to": sens["S6"]["applies_to"], "params": dict(base), "mapping": "s6"})
    return out


def variant_labels(recs_slots: list[tuple[RepoRecord, dict]], var: dict, cfg: dict,
                   clf: str) -> tuple[Optional[list[str]], Optional[str]]:
    prm = var["params"]
    cid = cfg_id(prm["alpha"], prm["L"], prm["D"], prm["G"], prm["mk"])
    if clf == "CF":
        return [cf_label(r, prm["alpha"], prm["L"], prm["D"])["label"] for r, _ in recs_slots], "python"
    mapping = cfg["c1_mapping_s6"] if (clf == "C1" and var["mapping"] == "s6") else (
        cfg["c1_mapping"] if clf == "C1" else cfg["c2_mapping"])
    labs = []
    for r, _ in recs_slots:
        e = r.inferred.get(cid)
        if e is None:
            return None, f"config {cid} missing in the input"
        labs.append(reasoner_label(e, clf, mapping)["label"])
    return labs, "reasoner"


def analyse_sensitivity(slots: list[tuple[RepoRecord, dict]], L: list[dict], prim: dict,
                        cfg: dict, bcfg: dict, canonical: str) -> dict:
    truth = enc([r["collapsed_truth"] for r in L])
    strata = [r["stratum"] for r in L]
    variants = []
    for var in sens_variants(cfg):
        entry = {"id": var["id"], "factor": var["factor"], "value": var["value"],
                 "config": cfg_id(**{"alpha": var["params"]["alpha"], "L": var["params"]["L"],
                                     "D": var["params"]["D"], "G": var["params"]["G"],
                                     "mk": var["params"]["mk"]}), "classifiers": {}}
        if var["id"] == "S2":
            Lm = var["params"]["L"]
            tr = [r.months is not None and len(r.months) < Lm for r, _ in slots]
            entry["left_truncated_repositories"] = (int(sum(tr))
                                                    if all(r.months is not None for r, _ in slots) else None)
        preds = {}
        for clf in var["applies_to"]:
            labs, src = variant_labels(slots, var, cfg, clf)
            if labs is None:
                entry["classifiers"][clf] = {"status": "MISSING", "reason": src}
            else:
                preds[clf] = (enc(labs), src)
        if preds:
            res = agreement(truth, {k: v[0] for k, v in preds.items()}, strata, SLIM_METRICS, bcfg)
            for clf, (_, src) in preds.items():
                v = verdict_for(res, clf, cfg["verdict"]) if clf != "CF" else None
                entry["classifiers"][clf] = {
                    "label_source": src,
                    "metrics": {m: metric_block(res, clf, m) for m in SLIM_METRICS},
                    "verdict": (v["verdict"] if v else "NOT_APPLICABLE"),
                    "verdict_detail": v}
        variants.append(entry)
    nid = cfg["sensitivity"]["not_independent_value"]
    robustness = {}
    for clf in ("C1", "C2"):
        base = prim["classifiers"][clf]["verdict"]["verdict"]
        changed, unavailable = [], []
        for e in variants:
            c = e["classifiers"].get(clf)
            if c is None:
                continue
            if c.get("status") == "MISSING":
                unavailable.append(f"{e['id']}={e['value']}")
                continue
            if e["factor"] == nid["factor"] and e["value"] == nid["value"]:
                continue
            if c["verdict"] != base:
                changed.append({"variant": f"{e['id']} {e['factor']}={e['value']}",
                                "verdict": c["verdict"]})
        robustness[clf] = {
            "primary_category": base, "category_changes": changed,
            "unavailable_variants": unavailable,
            "statement": ("ROBUST" if not changed and not unavailable else
                          ("FRAGILE" if changed else "INCOMPLETE")),
            "fragile_factors": sorted({c["variant"].split()[1].split("=")[0] for c in changed})}
    return {"variants": variants, "robustness": robustness, "canonical_model": canonical,
            "robustness_rule": "robust iff the category equals the primary one in every one-at-a-time "
                               "variant except D = 24; otherwise fragile (factor named)",
            "D24_flag": ("D = 24 is not independent evidence: sampling kept only conflict-free repositories, "
                         "so every ID/EVO/SERV repository was pushed to within 24 months of the snapshot; "
                         "agreement on non-PO classes at D = 24 is partly guaranteed by sample construction. "
                         "pushed_at is not the last default-branch commit date, so the guarantee is incomplete.")}


def analyse_grid(slots: list[tuple[RepoRecord, dict]], L: list[dict], diff: dict, cfg: dict) -> dict:
    """288-configuration factorial via the Python oracle (only after the differential check passed)."""
    out: dict = {"differential_test": diff}
    if diff.get("status") != "PASSED":
        out["status"] = "NOT_COMPUTED"
        out["reason"] = ("oracle not validated: differential check status = "
                         f"{diff.get('status')} ({diff.get('reason', 'see differential_test')})")
        return out
    primary_ok = primary_cfg_id(cfg) in diff["configs_checked"]
    if not primary_ok:
        out["status"] = "NOT_COMPUTED"
        out["reason"] = "differential check did not cover the primary configuration"
        return out
    g = cfg["grid"]
    truth = enc([r["collapsed_truth"] for r in L])
    recs = [r for r, _ in slots]
    vc = cfg["verdict"]

    def row(preds: np.ndarray) -> dict:
        pm = {m: float(FULL_METRICS[m](truth, preds)) for m in
              ("kappa", "macro_f1", "undetermined_rate", "recall_A", "recall_S", "recall_P")}
        pm["point_gate_passed"] = bool(
            pm["kappa"] >= vc["kappa_pass"] and pm["undetermined_rate"] <= vc["max_undetermined"]
            and all(pm[f"recall_{c}"] >= vc["recall_pass"] for c in CLASSES))
        return pm

    mk_short = {"original": "orig", "hamed_rao": "hr"}
    c2_rows, c1_rows, cf_rows = [], [], []
    for a, Lm, D, G, mk in itertools.product(g["alpha"], g["lookback_months"], g["dormancy_months"],
                                             g["min_rel_loc_growth_per_year"], g["mk_variant"]):
        k = mk_short[mk]
        pr = enc([oracle_c2(r, a, Lm, D, G, k) for r in recs])
        c2_rows.append({"alpha": a, "L": Lm, "D": D, "G": G, "mk": mk, **row(pr)})
    for a, Lm, mk in itertools.product(g["alpha"], g["lookback_months"], g["mk_variant"]):
        k = mk_short[mk]
        labs = []
        for r in recs:
            raw = oracle_c1(r, a, Lm, k)
            labs.append({"Growth": "A", "Stabilization": "S", "Decline": "P", "U": "U"}[raw])
        c1_rows.append({"alpha": a, "L": Lm, "mk": mk, **row(enc(labs))})
    for a, Lm, D in itertools.product(g["alpha"], g["lookback_months"], g["dormancy_months"]):
        cf_rows.append({"alpha": a, "L": Lm, "D": D,
                        **row(enc([cf_label(r, a, Lm, D)["label"] for r in recs]))})
    k2 = [r["kappa"] for r in c2_rows if r["kappa"] == r["kappa"]]
    out.update({"status": "COMPUTED", "n_configs": {"C2": len(c2_rows), "C1": len(c1_rows),
                                                    "CF": len(cf_rows)},
                "C2": c2_rows, "C1": c1_rows, "CF": cf_rows,
                "summary": {"C2_kappa_min": min(k2), "C2_kappa_max": max(k2),
                            "C2_configs_passing_point_gate": sum(r["point_gate_passed"] for r in c2_rows),
                            "note": "descriptive heatmap; point estimates only, no verdicts"}})
    return out


def _vals(L_by_repo: dict, slots, name: str, repos: list[str]) -> list[float]:
    out = []
    for r, _ in slots:
        if r.repo in repos:
            v = derived_measure(r, name)
            if v is not None:
                out.append(v)
    return out


def derived_measure(r: RepoRecord, name: str) -> Optional[float]:
    if name == "featureCommitShare":
        v = r.m("featureCommitShare")
        if v is not None:
            return v
        n, c = r.m("featCommitCount"), r.m("commitCount")
        return n / c if (n and c) else None        # only repositories with >= 1 feat: commit
    if name == "bugFixRatio":
        v = r.m("bugFixRatio")
        if v is not None:
            return v
        n, c = r.m("bugFixCommitCount"), r.m("commitCount")
        return n / c if (n is not None and c) else None
    return r.m(name)


def analyse_descriptive(slots: list[tuple[RepoRecord, dict]], L: list[dict], cfg: dict,
                        bcfg: dict) -> dict:
    d = cfg["descriptive"]
    stratum_of = {r["repo"]: r["stratum"] for r in L}
    truth_of = {r["repo"]: r["collapsed_truth"] for r in L}
    out: dict = {"by_stratum": {}, "feature_commit_repositories": {}}
    for name in d["measures"]:
        out["by_stratum"][name] = {}
        for s in cfg["strata"]:
            v = np.array([x for x in (derived_measure(r, name) for r, _ in slots
                                      if stratum_of[r.repo] == s) if x is not None], dtype=float)
            out["by_stratum"][name][s] = (
                {"n": int(len(v)), "median": float(np.median(v)), "q1": float(np.percentile(v, 25)),
                 "q3": float(np.percentile(v, 75))} if len(v) else {"n": 0})
    for s in cfg["strata"]:
        rs = [r for r, _ in slots if stratum_of[r.repo] == s]
        have = [r for r in rs if (r.m("featCommitCount") or 0) > 0 or (r.m("featureCommitShare") or 0) > 0]
        out["feature_commit_repositories"][s] = {"n_with_feat_commit": len(have), "n": len(rs),
                                                 "share": (len(have) / len(rs)) if rs else None}
    tests, raw_p = {}, []
    for eid, spec in d["directional"].items():
        gx = [x for x in (derived_measure(r, spec["measure"]) for r, _ in slots
                          if truth_of[r.repo] == spec["greater"]) if x is not None]
        gy = [x for x in (derived_measure(r, spec["measure"]) for r, _ in slots
                          if truth_of[r.repo] == spec["than"]) if x is not None]
        if len(gx) >= 2 and len(gy) >= 2:
            u, p = st.mann_whitney_one_sided(gx, gy, "greater")
            delta, lo, hi = st.cliffs_delta_ci(gx, gy, bcfg["n_boot"], bcfg["seed"], 0.95)
        else:
            u = p = delta = lo = hi = float("nan")
        tests[eid] = {"contrast": f"{spec['measure']} {spec['greater']} > {spec['than']}",
                      "n_x": len(gx), "n_y": len(gy), "U": u, "p_raw": p,
                      "cliffs_delta": delta, "delta_ci95": [lo, hi]}
        raw_p.append(1.0 if p != p else p)
    adj = st.holm_adjusted_p(raw_p)
    for (eid, t), a in zip(tests.items(), adj):
        t["p_holm"] = a
        t["significant_holm_0.05"] = bool(a < d["holm_alpha"]) if t["p_raw"] == t["p_raw"] else None
    out["directional_E1_E6"] = tests
    ex = {}
    for xid, spec in d["exploratory"].items():
        gx = [x for x in (derived_measure(r, spec["measure"]) for r, _ in slots
                          if stratum_of[r.repo] == spec["a"]) if x is not None]
        gy = [x for x in (derived_measure(r, spec["measure"]) for r, _ in slots
                          if stratum_of[r.repo] == spec["b"]) if x is not None]
        if len(gx) >= 2 and len(gy) >= 2:
            u, p = st.mann_whitney_one_sided(gx, gy, "two-sided")
            delta, lo, hi = st.cliffs_delta_ci(gx, gy, bcfg["n_boot"], bcfg["seed"], 0.95)
        else:
            u = p = delta = lo = hi = float("nan")
        ex[xid] = {"contrast": f"{spec['measure']} {spec['a']} vs {spec['b']} (two-sided)",
                   "n_x": len(gx), "n_y": len(gy), "U": u, "p_raw_uncorrected": p,
                   "cliffs_delta": delta, "delta_ci95": [lo, hi],
                   "label": "EXPLORATORY, uncorrected"}
    out["exploratory_X1_X2"] = ex
    out["note"] = "None of these results may change a rule or threshold on this sample."
    return out


# =============================================================================
# Orchestration
# =============================================================================
def run_main(args: argparse.Namespace, cfg: dict) -> int:
    deviations: list[dict] = []
    for d in args.deviation or []:
        parts = (d.split("|") + ["", "", ""])[:3]
        deviations.append({"what": parts[0], "why": parts[1], "when": now_iso(),
                           "before_unblinding": parts[2].strip().lower() != "after"})
    pre = preflight(cfg, args, deviations)
    out_dir = Path(pre["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    files = cfg["files"]
    bcfg = dict(cfg["bootstrap"])
    if args.n_boot:
        bcfg["n_boot"] = args.n_boot
    recs, meta = load_population(Path(args.input_dir))
    manifest = build_manifest(cfg, args, pre, meta)
    logger.info("loaded %d population JSONs", len(recs))

    # --- step 1: ground-truth records (structure only), population slots --------
    gt_records = load_gt_records(Path(pre["ground_truth_path"]))
    extra = load_gt_records(Path(args.extra_ground_truth)) if args.extra_ground_truth else []
    slots = assemble_slots(recs, gt_records, extra, manifest)
    if not args.synthetic:
        counts = {s: sum(1 for _, g in slots if g["stratum"] == s) for s in cfg["strata"]}
        if len(slots) != 120 or any(n != 30 for n in counts.values()):
            raise Refusal(f"analysis population is not 4 x 30: {counts}")

    # --- step 2: differential check BEFORE the join (prereg 9.4) ----------------
    diff = differential_check([r for r, _ in slots], cfg)
    manifest["differential_check"] = {k: diff[k] for k in ("status", "n_comparisons", "n_repos")
                                      if k in diff}
    if diff["status"] == "FAILED":
        write_json(out_dir / files["differential_failure"], diff)
        manifest["finished_at"] = now_iso()
        write_json(out_dir / files["manifest"], manifest)
        write_json(out_dir / files["deviations"], deviations)
        logger.error("differential check FAILED (%d mismatches): resolve as an encoding bug before "
                     "the ground truth is joined. See %s", len(diff["mismatches"]),
                     out_dir / files["differential_failure"])
        return 3

    # --- step 3: labels, written and hashed before any agreement -----------------
    label_recs = build_label_records(slots, cfg)
    labels_path = out_dir / files["labels"]
    write_json(labels_path, {"snapshot": cfg["snapshot_date"], "primary_config": primary_cfg_id(cfg),
                             "written_at": now_iso(), "records": label_recs})
    labels_hash = sha256_file(labels_path)
    (out_dir / files["labels_hash"]).write_text(f"{labels_hash}  {files['labels']}\n")
    manifest["labels_sha256"] = labels_hash
    manifest["labels_written_at"] = now_iso()
    write_json(out_dir / files["manifest"], manifest)
    logger.info("labels written, sha256 %s; joining with ground truth", labels_hash)

    # --- step 4: analyses ---------------------------------------------------------
    prim = analyse_primary(label_recs, cfg, bcfg)
    canonical = {"GO": "C1", "REVISE": "C2", "NO-GO": "C1"}[prim["decision"]["action"]]
    sec = analyse_secondary(label_recs, prim, cfg, bcfg)
    conv = analyse_convergent(label_recs, bcfg)
    sens = analyse_sensitivity(slots, label_recs, prim, cfg, bcfg, canonical)
    grid = analyse_grid(slots, label_recs, diff, cfg)
    noise = analyse_noise(label_recs, cfg, bcfg)
    desc = analyse_descriptive(slots, label_recs, cfg, bcfg)
    prim.pop("_res")
    prim.pop("_preds")
    prim["label_file_sha256"] = labels_hash
    write_json(out_dir / files["primary"], prim)
    write_json(out_dir / files["secondary"], sec)
    write_json(out_dir / files["convergent"], conv)
    write_json(out_dir / files["sensitivity"], sens)
    write_json(out_dir / files["grid"], grid)
    write_json(out_dir / files["noise"], noise)
    write_json(out_dir / files["descriptive"], desc)
    if grid.get("status") != "COMPUTED":
        deviations.append({"what": "288-configuration grid not computed",
                           "why": grid.get("reason"), "when": now_iso(), "before_unblinding": False})
    write_json(out_dir / files["deviations"], deviations)
    manifest["finished_at"] = now_iso()
    write_json(out_dir / files["manifest"], manifest)

    dec = prim["decision"]
    logger.info("C1 %s (kappa %.3f, 97.5%% LB %.3f) | C2 %s (kappa %.3f, LB %.3f) | decision %s",
                dec["C1"], prim["classifiers"]["C1"]["verdict"]["kappa"],
                prim["classifiers"]["C1"]["verdict"]["kappa_lower_bound"], dec["C2"],
                prim["classifiers"]["C2"]["verdict"]["kappa"],
                prim["classifiers"]["C2"]["verdict"]["kappa_lower_bound"], dec["action"])
    if dec["action"] == "REVISE":
        logger.warning("REVISE triggered: the holdout is needed. Mine and reason over the holdout "
                       "repositories (positions 30-59 of each stratum's clean seeded order, "
                       "replacements from >= 60) with run_v2_population.py at the SAME rq1-freeze tag, "
                       "then run: python experiments/paper1_ontology_manifests/run_rq1_v2.py "
                       "--holdout --holdout-dir <holdout population dir> "
                       "--holdout-ground-truth <holdout ground-truth json>")
    return 0


def run_holdout(args: argparse.Namespace, cfg: dict) -> int:
    """Holdout confirmation of C2 (prereg 6.5): C2 unchanged, 95% CI, single test."""
    deviations: list[dict] = []
    pre = preflight(cfg, args, deviations)
    out_dir = Path(pre["output_dir"])
    files = cfg["files"]
    prim_path = out_dir / files["primary"]
    if not prim_path.exists():
        raise Refusal(f"{prim_path} missing: run the main analysis first")
    action = json.load(open(prim_path))["decision"]["action"]
    if action != "REVISE":
        raise Refusal(f"holdout only runs when the decision is REVISE (is {action})")
    if not (args.holdout_dir and args.holdout_ground_truth):
        raise Refusal("--holdout needs --holdout-dir and --holdout-ground-truth")
    bcfg = dict(cfg["bootstrap"])
    if args.n_boot:
        bcfg["n_boot"] = args.n_boot
    recs, meta = load_population(Path(args.holdout_dir))
    gt_path = Path(args.holdout_ground_truth)
    gt_records = load_gt_records(gt_path)
    extra = load_gt_records(Path(args.extra_ground_truth)) if args.extra_ground_truth else []
    manifest: dict = {}
    slots = assemble_slots(recs, gt_records, extra, manifest)
    label_recs = build_label_records(slots, cfg)
    lp = out_dir / files["holdout_labels"]
    write_json(lp, {"holdout": True, "written_at": now_iso(), "records": label_recs,
                    "holdout_ground_truth_sha256": sha256_file(gt_path)})
    h = sha256_file(lp)
    (out_dir / (files["holdout_labels"] + ".sha256")).write_text(f"{h}  {files['holdout_labels']}\n")
    truth_l = [r["collapsed_truth"] for r in label_recs]
    strata = [r["stratum"] for r in label_recs]
    truth = enc(truth_l)
    preds = {c: enc([r[c] for r in label_recs]) for c in CLF_NAMES}
    res = agreement(truth, preds, strata, FULL_METRICS, bcfg)
    v = verdict_for(res, "C2", cfg["verdict"], "0.95")
    outcome = "GO with C2 (record D10, amending D6)" if v["verdict"] == "PASS" else "NO-GO"
    out = {"n": len(label_recs), "labels_sha256": h, "ci_level": 0.95, "single_test": True,
           "C2_verdict": v, "decision": outcome,
           "classifiers": {c: {"metrics": {m: metric_block(res, c, m) for m in FULL_METRICS},
                               "confusion_collapsed_truth_x_pred":
                                   confusion_json(truth_l, [r[c] for r in label_recs])}
                           for c in CLF_NAMES},
           "note": "Only C2 carries a verdict. C1 and CF are shown for reference."}
    write_json(out_dir / files["holdout_primary"], out)
    write_json(out_dir / files["deviations"] if not (out_dir / files["deviations"]).exists()
               else out_dir / "rq1_holdout_deviations.json", deviations)
    logger.info("holdout C2: %s (kappa %.3f, 95%% LB %.3f) -> %s", v["verdict"], v["kappa"],
                v["kappa_lower_bound"], outcome)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="RQ1 analysis (pre-registered)")
    ap.add_argument("--config", default=str(CONFIG_PATH))
    ap.add_argument("--input-dir", help="directory of per-repo population JSONs")
    ap.add_argument("--output-dir", help="default: results/real_v2/rq1 (from the config)")
    ap.add_argument("--extra-ground-truth", help="ground-truth records of replacement repositories")
    ap.add_argument("--ground-truth", help="override (only with --synthetic)")
    ap.add_argument("--synthetic", action="store_true",
                    help="pipeline test on fake data: skips the ground-truth sha check")
    ap.add_argument("--allow-dirty", action="store_true", help="synthetic tests only; recorded")
    ap.add_argument("--n-boot", type=int, help="override B (synthetic tests only)")
    ap.add_argument("--deviation", action="append",
                    help="'what|why|before' or 'what|why|after' unblinding; repeatable")
    ap.add_argument("--holdout", action="store_true", help="holdout confirmation (only if REVISE)")
    ap.add_argument("--holdout-dir")
    ap.add_argument("--holdout-ground-truth")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = yaml.safe_load(open(args.config))
    try:
        if args.holdout:
            return run_holdout(args, cfg)
        if not args.input_dir:
            ap.error("--input-dir is required")
        return run_main(args, cfg)
    except Refusal as e:
        logger.error("REFUSING TO RUN: %s", e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
