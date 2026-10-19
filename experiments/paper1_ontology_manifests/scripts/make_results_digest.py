"""Traced results digest for the Paper 1 rebuild (RQ1-RQ4, WP1-WP5).

Used by: Paper 1 (JSEP rebuild). Reads ONLY committed result files under
``experiments/paper1_ontology_manifests/results/real_v2/`` (plus the deviation-log
markdown files, for entry counts only) and writes
``papers/paper1/results-digest.md`` and ``papers/paper1/results-digest.json``.

Every number in the digest is read from a JSON/JSONL file and printed with its
source as ``file::json.path``. Keys that contain dots or odd characters are written
as ``["key"]``. Tables with several value columns give the parent object as the
source; the columns are its child keys. Cells holding lists give one number per
element (``path[0]``, ``path[1]``). Rows marked "derived" are tallies over a
JSONL ledger and give the grouping in the source, e.g.
``wp5_runs.jsonl::count(state=Submitted)``.

Nothing is hand-typed: if a curated key is absent the digest prints
``MISSING(file::path)`` and lists all such entries at the end. No experiment or
analysis is run.

Usage:
    python experiments/paper1_ontology_manifests/scripts/make_results_digest.py
"""
from __future__ import annotations

import collections
import hashlib
import json
import logging
import math
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG = logging.getLogger("results_digest")

PROJECT_ROOT = Path(__file__).resolve().parents[3]
EXP = PROJECT_ROOT / "experiments" / "paper1_ontology_manifests"
RES = "experiments/paper1_ontology_manifests/results/real_v2"  # prefix shown in sources
PAPER = PROJECT_ROOT / "papers" / "paper1"
OUT_MD = PAPER / "results-digest.md"
OUT_JSON = PAPER / "results-digest.json"

LIST_MAX = 120
SCALAR_LIST_MAX = 12


# ---------------------------------------------------------------- tracing core
class Digest:
    def __init__(self) -> None:
        self.cache: dict[str, object] = {}
        self.sha: dict[str, str] = {}
        self.records: list[dict] = []
        self.missing: list[str] = []
        self.out: list[str] = []

    # files
    def load(self, rel: str):
        """rel is relative to results/real_v2 (or a repo-root path starting with papers/)."""
        if rel not in self.cache:
            p = (PROJECT_ROOT / rel) if rel.startswith("papers/") else (EXP / "results" / "real_v2" / rel)
            raw = p.read_bytes()
            full = rel if rel.startswith("papers/") else f"{RES}/{rel}"
            self.sha[full] = hashlib.sha256(raw).hexdigest()
            if rel.endswith(".jsonl"):
                self.cache[rel] = [json.loads(l) for l in raw.decode().splitlines() if l.strip()]
            elif rel.endswith(".json"):
                self.cache[rel] = json.loads(raw)
            else:
                self.cache[rel] = raw.decode()
        return self.cache[rel]

    @staticmethod
    def full(rel: str) -> str:
        return rel if rel.startswith("papers/") else f"{RES}/{rel}"

    # paths
    @staticmethod
    def pstr(comps) -> str:
        s = ""
        for c in comps:
            if isinstance(c, int):
                s += f"[{c}]"
            elif re.fullmatch(r"[A-Za-z_][A-Za-z0-9_\-]*", c):
                s += ("." if s else "") + c
            else:
                s += f'["{c}"]'
        return s

    def src(self, rel: str, comps) -> str:
        return f"{self.full(rel)}::{self.pstr(comps)}"

    # recording
    def rec(self, rel: str, comps, value, derived: bool = False) -> None:
        self.records.append({"source": self.src(rel, comps), "value": value, "derived": derived})

    def rec_value(self, rel: str, comps, v) -> None:
        """Record every scalar inside v (lists expanded)."""
        if isinstance(v, list):
            for i, x in enumerate(v):
                self.rec_value(rel, list(comps) + [i], x)
        elif isinstance(v, dict):
            for k, x in v.items():
                self.rec_value(rel, list(comps) + [k], x)
        else:
            self.rec(rel, comps, v)

    def get(self, rel: str, comps):
        """Curated lookup: records and returns the value, or a MISSING marker."""
        node = self.load(rel)
        for c in comps:
            try:
                node = node[c]
            except (KeyError, IndexError, TypeError):
                m = f"MISSING({self.src(rel, comps)})"
                self.missing.append(m)
                return m
        self.rec_value(rel, comps, node)
        return node

    # output
    def w(self, s: str = "") -> None:
        self.out.append(s)


D = Digest()


def fmt(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if math.isnan(v):
            return "NaN"
        if v == 0:
            return "0"
        if abs(v) < 1e-3:
            return f"{v:.3e}"
        s = f"{v:.4f}".rstrip("0").rstrip(".")
        return s if s not in ("", "-0") else "0"
    if isinstance(v, str):
        t = v.replace("|", "\\|").replace("\n", " ")
        return t if len(t) <= 70 else t[:67] + "..."
    if isinstance(v, list):
        return "[" + ", ".join(fmt(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ", ".join(f"{k}: {fmt(x)}" for k, x in v.items()) + "}"
    return str(v)


def esc(s: str) -> str:
    return s.replace("|", "\\|")


def table(headers, rows) -> None:
    D.w("| " + " | ".join(headers) + " |")
    D.w("|" + "|".join("---" for _ in headers) + "|")
    for r in rows:
        D.w("| " + " | ".join(esc(str(x)) if not isinstance(x, str) else x for x in r) + " |")
    D.w()


# ------------------------------------------------------------ generic renderer
def _is_scalar(x) -> bool:
    return not isinstance(x, (dict, list))


def _is_scalar_list(x, depth=0) -> bool:
    if not isinstance(x, list) or len(x) > SCALAR_LIST_MAX:
        return False
    return all(_is_scalar(e) or (depth == 0 and _is_scalar_list(e, 1)) for e in x)


def _skip_str(v) -> bool:
    return isinstance(v, str) and (len(v) > 80 or re.fullmatch(r"[0-9a-f]{40,64}", v) is not None)


def _flatten_elem(d: dict, prefix=()) -> dict:
    """Flatten nested dicts of a list element into dotted columns."""
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out.update(_flatten_elem(v, prefix + (k,)))
        elif isinstance(v, list) and not _is_scalar_list(v):
            continue
        elif _skip_str(v):
            continue
        else:
            out[".".join(prefix + (k,))] = v
    return out


def tree(rel: str, comps=(), skip=lambda comps: False, title: str | None = None, heading: str | None = None) -> None:
    """Render the subtree at comps as compact tables with per-row sources."""
    node = D.load(rel)
    for c in comps:
        node = node[c]
    base = list(comps)
    if heading:
        D.w(f"**{heading}**")
        D.w()
    D.w(f"Source file: `{D.full(rel)}`" + (f", subtree `{D.pstr(base)}`" if base else ""))
    D.w()
    rows: list[tuple[list, dict]] = []
    omitted: list[str] = []

    def walk(n, cs):
        if isinstance(n, dict):
            scal, kids = {}, []
            for k, v in n.items():
                kc = cs + [k]
                if skip(kc):
                    continue
                if isinstance(v, dict):
                    kids.append((kc, v))
                elif isinstance(v, list):
                    if _is_scalar_list(v):
                        scal[k] = v
                    elif v and all(isinstance(e, dict) for e in v) and len(v) <= LIST_MAX:
                        kids.append((kc, v))
                    elif v and all(isinstance(e, (str, int, float)) for e in v):
                        omitted.append(f"{D.pstr(kc)} (list of {len(v)})")
                    elif v:
                        omitted.append(f"{D.pstr(kc)} (list of {len(v)} rows)")
                elif _skip_str(v):
                    omitted.append(f"{D.pstr(kc)} (long text/hash)")
                else:
                    scal[k] = v
            if scal:
                rows.append((cs, scal))
            for kc, v in kids:
                walk(v, kc)
        elif isinstance(n, list):
            # list of dicts: one row per element with nested dicts flattened to dotted columns
            for i, e in enumerate(n):
                rows.append((cs + [i], _flatten_elem(e)))

    walk(node, base)

    def rel_label(cs):
        r = D.pstr(cs[len(base):]) if len(cs) > len(base) else "(root)"
        return r.lstrip(".")

    groups: dict[tuple, list] = collections.OrderedDict()
    for cs, sc in rows:
        groups.setdefault(tuple(sc.keys()), []).append((cs, sc))
    single_rows = []
    multi = []
    for sig, grp in groups.items():
        if len(grp) == 1:
            cs, sc = grp[0]
            for k, v in sc.items():
                kcs = cs + k.split(".") if cs and isinstance(cs[-1], int) and "." in k else cs + [k]
                lab = rel_label(cs)
                single_rows.append((k if lab == "(root)" else f"{lab}.{k}", fmt(v), D.src(rel, kcs)))
                D.rec_value(rel, kcs, v)
        else:
            multi.append((sig, grp))
    if single_rows:
        table(["key", "value", "source"], single_rows)
    for sig, grp in multi:
        hdr = ["node"] + list(sig) + ["source"]
        trs = []
        for cs, sc in grp:
            cells = [f"`{rel_label(cs)}`"]
            for k in sig:
                cells.append(fmt(sc[k]))
                kcs = cs + k.split(".") if cs and isinstance(cs[-1], int) and "." in k else cs + [k]
                D.rec_value(rel, kcs, sc[k])
            cells.append(f"`{D.src(rel, cs)}`")
            trs.append(cells)
        table(hdr, trs)
    if omitted:
        D.w("Not rendered (text, hashes or long lists; see source): " + "; ".join(f"`{o}`" for o in omitted[:40]) +
            (f" and {len(omitted) - 40} more" if len(omitted) > 40 else ""))
        D.w()


def matrix(rel: str, comps, heading: str) -> None:
    """Confusion-style matrix with rows_true, cols_pred, counts."""
    node = D.load(rel)
    for c in comps:
        node = node[c]
    cols = node["cols_pred"]
    trs = []
    for i, rname in enumerate(node["rows_true"]):
        row = node["counts"][i]
        for j, x in enumerate(row):
            D.rec(rel, list(comps) + ["counts", i, j], x)
        trs.append([f"`{rname}`"] + [str(x) for x in row] + [f"`{D.src(rel, list(comps) + ['counts', i])}`"])
    D.w(f"**{heading}** (rows = truth, columns = prediction; labels from `{D.pstr(list(comps) + ['rows_true'])}`, `cols_pred`)")
    D.w()
    table(["truth"] + [f"pred {c}" for c in cols] + ["source"], trs)


def no_skip(_c):
    return False


def skipper(*names, prefixes=()):
    names = set(names)

    def f(cs):
        k = cs[-1]
        if isinstance(k, str) and (k in names or any(k.startswith(p) for p in prefixes)):
            return True
        return False
    return f


def skip_paths(*paths):
    ps = {tuple(p) for p in paths}
    return lambda cs: tuple(cs) in ps


# -------------------------------------------------------------------- sections
def sec1():
    D.w("## 1. WP3 ground truth")
    D.w()
    f = "wp3/summary.json"
    D.w("Key quantities: `pool_size`, `candidates_passing_filters`, `stratum_sampling.*.sampled`, `noise.*`. "
        "Per-package `duplicate_repo_of:*` exclusion counts are omitted from the table (see source).")
    D.w()
    tree(f, (), skip=skipper(prefixes=("duplicate_repo_of:",)))
    n_dup = sum(1 for k in D.load(f)["exclusions"] if k.startswith("duplicate_repo_of:"))
    D.w(f"Omitted `exclusions` keys with prefix `duplicate_repo_of:`: {n_dup} keys.")
    D.w()


def sec2():
    D.w("## 2. WP1: differential test and TBox regression")
    D.w()
    tree("wp1/differential_report.json", (),
         skip=lambda cs: (cs[0] in ("args",) or cs[:2] == ["timings", "batches"] or cs[:2] == ["commit_rules", "rows"]
                          or cs[:1] == ["structure_check"] and len(cs) == 2 and False),
         heading="Differential test (`agreement`, `summary`, `mismatch_classes`, `timings`)")
    D.w("Reasoning times: `timings.*` above; Stage-A chunk timings under `commit_rules.stage_a_chunk_timings`; "
        "per-manifest HermiT times in section 4 (`timings.hermit_reason_s_per_manifest`).")
    D.w()
    tree("wp5/wp5_tbox_regression.json", (), skip=skipper("results", "different", "tbox_dir"),
         heading="WP5 TBox regression")


def rq1_sens_variants():
    f = "rq1/rq1_sensitivity.json"
    variants = D.load(f)["variants"]
    trs = []
    for i, v in enumerate(variants):
        for cls, cd in v.get("classifiers", {}).items():
            base = ["variants", i, "classifiers", cls]
            kap = cd.get("metrics", {}).get("kappa", {})
            ver = cd.get("verdict")
            for nm in ("kappa",):
                D.rec_value(f, base + ["metrics", nm], kap)
            D.rec(f, base + ["verdict"], ver)
            ur = cd.get("metrics", {}).get("undetermined_rate", {})
            D.rec_value(f, base + ["metrics", "undetermined_rate"], ur)
            trs.append([v.get("id"), v.get("factor"), fmt(v.get("value")), cls, fmt(kap.get("point")),
                        fmt(kap.get("ci95")), fmt(kap.get("ci975")), fmt(ver), fmt(ur.get("point")),
                        f"`{D.src(f, base)}`"])
        D.rec(f, ["variants", i, "value"], v.get("value")) if isinstance(v.get("value"), (int, float)) else None
    table(["id", "factor", "value", "clf", "kappa", "95% CI", "97.5% CI", "verdict", "undet. rate", "source"], trs)


def rq1_noise():
    f = "rq1/rq1_noise_subsets.json"
    nz = D.load(f)
    trs = []
    for sname, s in nz["subsets"].items():
        base = ["subsets", sname]
        D.rec(f, base + ["n"], s["n"])
        D.rec(f, base + ["n_dropped"], s["n_dropped"])
        for st, c in s["stratum_counts"].items():
            D.rec(f, base + ["stratum_counts", st], c)
        for cls, cd in s["classifiers"].items():
            kap = cd["metrics"]["kappa"]
            D.rec_value(f, base + ["classifiers", cls, "metrics", "kappa"], kap)
            ver = cd.get("verdict")
            vv = ver.get("verdict") if isinstance(ver, dict) else ver
            if vv is not None:
                D.rec(f, base + ["classifiers", cls, "verdict"], vv) if not isinstance(ver, dict) else \
                    D.rec(f, base + ["classifiers", cls, "verdict", "verdict"], vv)
            trs.append([sname, s["n"], s["n_dropped"], fmt(s["stratum_counts"]), cls, fmt(kap["point"]), fmt(kap["ci95"]),
                        fmt(kap["ci975"]), fmt(vv), f"`{D.src(f, base + ['classifiers', cls])}`"])
    table(["subset", "n", "dropped", "stratum counts (ID,EVO,SERV,PO)", "clf", "kappa", "95% CI", "97.5% CI", "verdict", "source"], trs)
    tree(f, ("close_down_split_descriptive",), heading="Close-down split (descriptive)")
    D.w(f"Noise subset definitions: `{D.src(f, ['definitions'])}` = {fmt(D.get(f, ['definitions']))}")
    D.w()


def sec3():
    D.w("## 3. RQ1 (stage classifiers)")
    D.w()
    p = "rq1/rq1_primary.json"
    D.w(f"Sample size `n` = {fmt(D.get(p, ['n']))} (`{D.src(p, ['n'])}`); bootstrap draws "
        f"{fmt(D.get(p, ['bootstrap', 'n_boot']))} (`{D.src(p, ['bootstrap', 'n_boot'])}`), seed "
        f"{fmt(D.get(p, ['bootstrap', 'seed']))}; CI levels {fmt(D.get(p, ['bootstrap', 'levels']))} "
        f"(`{D.src(p, ['bootstrap', 'levels'])}`).")
    D.w()
    for cls in ("C1", "C2", "CF"):
        D.w(f"### 3.{['C1', 'C2', 'CF'].index(cls) + 1} Classifier {cls}")
        D.w()
        base = ("classifiers", cls)
        tree(p, base, skip=lambda cs: len(cs) > 2 and isinstance(cs[2], str) and cs[2].startswith("confusion_"),
             heading=f"{cls}: metrics (kappa, weighted kappa, macro-F1, balanced accuracy with 95% and 97.5% CIs), per-class P/R/F1, undetermined, complete-case, verdict, claimable")
        node = D.load(p)["classifiers"][cls]
        for ck in ("confusion_collapsed_truth_x_pred", "confusion_strata_x_pred", "confusion_strata_x_unmapped_phase"):
            if ck in node:
                matrix(p, list(base) + [ck], f"{cls} {ck}")
    D.w("### 3.4 Decision and paired differences")
    D.w()
    tree(p, ("decision",), heading="Decision")
    tree(p, ("paired_differences",), heading="Paired differences (point and CIs)")
    D.w("### 3.5 Convergent validity")
    D.w()
    tree("rq1/rq1_convergent.json", ())
    D.w("### 3.6 Sensitivity")
    D.w()
    s = "rq1/rq1_sensitivity.json"
    tree(s, ("robustness",), heading="Robustness statement per classifier")
    D.w("**One-at-a-time variants**")
    D.w()
    rq1_sens_variants()
    g = "rq1/rq1_sensitivity_grid.json"
    tree(g, (), skip=lambda cs: cs[0] in ("C1", "C2", "CF") and len(cs) >= 1 and cs[0] in ("C1", "C2", "CF") or cs[:2] == ["differential_test", "configs_checked"],
         heading="Sensitivity grid summary (full grid not expanded; per-config rows are in the source file lists `C1`, `C2`, `CF`)")
    D.w("### 3.7 Ground-truth noise subsets")
    D.w()
    rq1_noise()
    D.w("### 3.8 Descriptive measures (E1-E6 with Holm, X1-X2)")
    D.w()
    tree("rq1/rq1_descriptive.json", ())
    D.w("### 3.9 Secondary: ablation ladder, 4-class reporting, population-weighted")
    D.w()
    tree("rq1/rq1_secondary.json", ())
    D.w("### 3.10 Deviations and manifest")
    D.w()
    dv = D.load("rq1/rq1_deviations.json")
    D.rec("rq1/rq1_deviations.json", ["(length)"], len(dv), derived=True)
    D.w(f"Entries in `{D.full('rq1/rq1_deviations.json')}`: {len(dv)} (length of the top-level list; derived).")
    D.w()
    tree("rq1/rq1_run_manifest.json", (), skip=lambda cs: cs[0] in ("tbox_sha256", "reasoner_run_meta", "command", "ground_truth") ,
         heading="Run manifest (scalars; hashes and long metadata omitted)")


def tally_runs():
    runs = D.load("wp5/wp5_runs.jsonl")
    outs = {o["run_id"]: o for o in D.load("wp5/wp5_outcomes.jsonl")}
    rf, of = "wp5/wp5_runs.jsonl", "wp5/wp5_outcomes.jsonl"

    def cnt(label, rows):
        return len(rows)

    D.w("**Runs ledger tallies (derived from the JSONL ledgers)**")
    D.w()
    D.rec(rf, ["count(all)"], len(runs), derived=True)
    D.w(f"Runs in ledger: {len(runs)} (`{D.full(rf)}::count(all)`).")
    D.w()
    # terminal state by condition
    states = sorted({r["state"] for r in runs})
    conds = sorted({r["condition"] for r in runs})
    trs = []
    for c in conds:
        row = [c]
        for s in states:
            n = sum(1 for r in runs if r["condition"] == c and r["state"] == s)
            D.rec(rf, [f"count(condition={c},state={s})"], n, derived=True)
            row.append(str(n))
        ni = sum(1 for r in runs if r["condition"] == c and r["infra_failure"])
        D.rec(rf, [f"count(condition={c},infra_failure=true)"], ni, derived=True)
        row.append(str(ni))
        row.append(f"`{D.full(rf)}::count(condition={c},state=*)`")
        trs.append(row)
    table(["condition"] + states + ["infra_failure=true", "source"], trs)
    # resolve by condition and condition x model
    trs = []
    models = sorted({r["model"] for r in runs})
    for c in conds:
        for m in [None] + models:
            sel = [r for r in runs if r["condition"] == c and (m is None or r["model"] == m)]
            res = sum(outs[r["run_id"]]["resolved"] for r in sel if r["run_id"] in outs)
            n = len(sel)
            tag = f"condition={c}" + (f",model={m}" if m else "")
            D.rec(of, [f"sum(resolved where {tag})"], res, derived=True)
            D.rec(of, [f"n(runs where {tag})"], n, derived=True)
            D.rec(of, [f"mean(resolved where {tag})"], res / n if n else None, derived=True)
            trs.append([c, m or "(all)", n, res, fmt(res / n if n else None), f"`{D.full(of)}::sum(resolved where {tag})`"])
    table(["condition", "model", "runs", "resolved", "rate", "source"], trs)
    D.w("Join: `wp5_outcomes.jsonl` to `wp5_runs.jsonl` on `run_id`. Condition B runs are exploratory and not part of the primary set.")
    D.w()


def sec4():
    D.w("## 4. RQ2 (WP2 claim verification)")
    D.w()
    D.w("Pellet could not classify the claims TBox, so the HermiT-vs-Pellet cross-check has no verdict comparison; see `hermit_vs_pellet` below.")
    D.w()
    tree("wp2/report.json", (), skip=lambda cs: cs[0] == "per_manifest" or cs[-1] in ("pellet_errors_sample", "errors_sample"),
         heading="`report.json` (flow, prevalence, verdicts, contradiction rates, extraction agreement, drift, sensitivity, timings)")
    tree("wp2/first_pass_summary.json", (), heading="First-pass summary (before normalization fixes)")
    tree("wp2/recheck.json", (), skip=skipper("disagreements", "leaf_only_disagreements", "note"),
         heading="Independent recheck (`recheck.json`)")
    tree("wp2/drift.json", (), skip=skipper("rows"), heading="Drift (`drift.json`)")
    tree("wp2/triangulation.json", ("summary",), heading="Triangulation summary (`triangulation.json`)")
    tree("wp2/explanations_summary.json", (), skip=skipper("errors_sample"), heading="Explanation coverage")
    tree("wp2/selftest.json", (), skip=skipper("cases", "failures", "tbox_sha256"), heading="Self-test")
    tree("wp2/timings_verdicts.json", (), skip=skipper("per_manifest_reason_s"), heading="Verdict-reasoning wall time (HermiT)")
    tree("wp2/timings_verdicts_pellet.json", (), heading="Verdict-reasoning wall time (Pellet; failed runs)")
    naive_check_baseline()


def sec4b():
    D.w("## 4b. RQ2b (WP2b persistence of manifest errors)")
    D.w()
    D.w("Design and decision wording: `papers/paper1/wp2b-persistence-design.md` (tag `wp2b-prereg`) sections 5 and 9. The wording strings below are "
        "assigned mechanically from the CI by `wp2/step_persist_report.py` and read from `report.json`.")
    D.w()
    rep = "wp2b/report.json"
    tree(rep, (), skip=lambda cs: cs[-1] in ("design", "wording") or (cs[0] == "robustness" and cs[-1] == "wording"),
         heading="`report.json` (outcomes, A1, A2, robustness, exploratory)")
    trs = []
    for lab, comps in (("A1", ["A1", "wording"]), ("A2", ["A2", "wording"]),
                       ("robustness pooled RR", ["robustness", "pooled_rr", "wording"]),
                       ("robustness (c) A1", ["robustness", "c_edited_manifests", "A1", "wording"]),
                       ("robustness (c) A2", ["robustness", "c_edited_manifests", "A2", "wording"]),
                       ("robustness (d) A1", ["robustness", "d_excl_archived_and_non_ancestor", "A1", "wording"]),
                       ("robustness (d) A2", ["robustness", "d_excl_archived_and_non_ancestor", "A2", "wording"]),
                       ("robustness (e) A1", ["robustness", "e_reasoner_recheck_agree", "A1", "wording"]),
                       ("robustness (e) A2", ["robustness", "e_reasoner_recheck_agree", "A2", "wording"]),
                       ("robustness (f)", ["robustness", "f_removed_by_quote_disappearance", "wording"])):
        v = D.get(rep, comps)
        trs.append([lab, v, f"`{D.src(rep, comps)}`"])
    table(["analysis", "pre-registered wording", "source"], trs)
    tree("wp2b/head_fetch.json", (), skip=skipper("repos"), heading="Head fetch (`head_fetch.json`)")
    tree("wp2b/s_reproduction.json", (), skip=skipper("manifests"), heading="Reproduction at S and matcher self-test (`s_reproduction.json`)")
    tree("wp2b/timings.json", (), heading="Run timings")
    cf = "wp2b/claims.jsonl"
    rows = D.load(cf)
    trs = []
    for v in ("ContradictedClaim", "SupportedClaim"):
        for o in ("U", "G", "R", "P-C", "P-S", "P-O"):
            n = sum(1 for r in rows if r["verdict_S"] == v and r["outcome"] == o)
            D.rec(cf, [f"count(verdict_S={v},outcome={o})"], n, derived=True)
            trs.append([v, o, n, f"`{D.full(cf)}::count(verdict_S={v},outcome={o})`"])
    D.w("**Outcome tallies (derived from the claims ledger)**")
    D.w()
    table(["verdict at S", "outcome", "claims", "source (derived)"], trs)


def naive_check_baseline() -> None:
    """Derived: what an exact-match snapshot check would report for T1/T5 claims (paper Section 4.3.2)."""
    rel = "wp2/report.json"
    t1 = D.get(rel, ["verdict_distribution_by_type", "T1", "leaves"])
    t5 = D.get(rel, ["verdict_distribution_by_type", "T5", "leaves"])
    false_alarm = {
        "T1.PathFoundBySuffix": t1["PathFoundBySuffix"],
        "T1.PathUntrackedByDesign": t1["PathUntrackedByDesign"],
        "T1.PathInSubmodule": t1["PathInSubmodule"],
        "T5.ScriptDefinedNested": t5["ScriptDefinedNested"],
    }
    real = {
        "T1.PathNeverExisted": t1["PathNeverExisted"],
        "T1.PathRemoved": t1["PathRemoved"],
        "T5.ScriptUndefined": t5["ScriptUndefined"],
    }
    D.w("**Naive exact-match baseline (derived from the T1/T5 leaf counts above)**")
    D.w()
    D.w("A check that looks up each path exactly from the repository root, and each script only in the root "
        "`package.json`, at the snapshot would report these leaves as missing although the checker finds them "
        "supported or unverifiable (false alarms), next to the leaves it reports as contradicted (real errors).")
    D.w()
    rows = []
    for k, v in {**false_alarm, **real}.items():
        rows.append([k, "false alarm" if k in false_alarm else "real error", v])
    rows.append(["sum(false alarms)", "", sum(false_alarm.values())])
    rows.append(["sum(real errors)", "", sum(real.values())])
    table(["leaf", "naive check outcome", "count"], rows)
    D.rec(rel, ["naive_baseline", "false_alarms"], sum(false_alarm.values()), derived=True)
    D.rec(rel, ["naive_baseline", "real_errors"], sum(real.values()), derived=True)
    D.w()


def sec5():
    D.w("## 5. RQ3/RQ4 (WP5 agent study)")
    D.w()
    D.w("### 5.1 Pool, validation, tasks")
    D.w()
    tree("wp5/pool_summary.json", ())
    tree("wp5/validation_summary.json", ())
    tree("wp5/wp5_tasks.json", (), skip=skipper("tasks", "exclusions", "dev_tasks_excluded", "pilot_tasks_included", "counts_by_repo"),
         heading="Task set (counts per stage, B availability, supply)")
    D.w("### 5.2 Runs and terminal states")
    D.w()
    tally_runs()
    tree("wp5/wp5_run_manifest.json", ("full_run",), skip=skipper("ledger_sha256", "harness_config_sha256_final", "note", "infra_rerun"),
         heading="Run manifest, full run")
    tree("wp5/wp5_gold_drift.json", (), skip=skipper("tasks", "gold_drift_fail"), heading="Gold-drift check")
    D.w("### 5.3 Power")
    D.w()
    tree("wp5/wp5_power.json", (), skip=skipper("cells", "alpha_levels", "icc_grid", "or_grid") ,
         heading="Power: label, MDE, design, p0, power at P0-hat")
    tree("wp5/wp5_power.json", ("cells",), heading="Power table (all cells; `power.H*` columns are keyed by alpha)")
    D.w("### 5.4 Confirmatory (H1-H3)")
    D.w()
    tree("wp5/wp5_primary.json", (), skip=skipper("scope", "config_sha256"))
    D.w("### 5.5 Secondary outcomes (Y0-Y6), condition B, within-stage")
    D.w()
    tree("wp5/wp5_secondary.json", (), skip=skipper("config_sha256"))
    D.w("### 5.6 Sensitivity analyses SA1-SA9")
    D.w()
    tree("wp5/wp5_sensitivity.json", (), skip=skipper("config_sha256", "note"))
    tree("wp5/wp5_sa9_check.json", (), heading="SA9 outcome check")
    D.w("### 5.7 Exploratory (resolve rates by model/stage/condition, uptake, interactions)")
    D.w()
    tree("wp5/wp5_exploratory.json", (), skip=skipper("config_sha256"))
    D.w("### 5.8 Pilots (not evidence)")
    D.w()
    for pf in ("wp5/wp5_pilot1_summary.json", "wp5/wp5_pilot_summary.json", "wp5_pilot/wp5_pilot_summary.json",
               "wp5_pilot2/wp5_pilot_summary.json", "wp5_pilot_mt8192/wp5_pilot_summary.json"):
        tree(pf, (), heading=pf)
    D.w("### 5.9 Deviations")
    D.w()
    dv = D.load("wp5/wp5_deviations.json")["deviations"]
    D.rec("wp5/wp5_deviations.json", ["deviations", "(length)"], len(dv), derived=True)
    D.w(f"Entries in `{D.full('wp5/wp5_deviations.json')}::deviations`: {len(dv)} (length of list; derived).")
    D.w()


def tally_wp6_runs():
    rf, of, mf = "wp6/runs/wp6_runs.jsonl", "wp6/runs/wp6_outcomes.jsonl", "wp6/wp6_manifests_index.json"
    runs = D.load(rf)
    outs = {o["run_id"]: o for o in D.load(of)}
    D.w("**WP6 runs ledger tallies (derived from the JSONL ledgers)**")
    D.w()
    D.rec(rf, ["count(all)"], len(runs), derived=True)
    D.w(f"Runs in ledger: {len(runs)} (`{D.full(rf)}::count(all)`). Joined to `wp6_outcomes.jsonl` on `run_id`. "
        "Y1 and Y8 are read from `sets[F_I]` for F_I runs and from `sets[F_R]` for all other conditions (the run's own token set).")
    D.w()
    conds = [c for c in ("A", "T", "F_R", "F_I") if any(r["condition"] == c for r in runs)]
    states = sorted({r["state"] for r in runs})
    trs = []
    for c in conds:
        row = [c]
        for st in states:
            n = sum(1 for r in runs if r["condition"] == c and r["state"] == st)
            D.rec(rf, [f"count(condition={c},state={st})"], n, derived=True)
            row.append(str(n))
        ni = sum(1 for r in runs if r["condition"] == c and r["infra_failure"])
        D.rec(rf, [f"count(condition={c},infra_failure=true)"], ni, derived=True)
        row += [str(ni), f"`{D.full(rf)}::count(condition={c},state=*)`"]
        trs.append(row)
    table(["condition"] + states + ["infra_failure=true", "source"], trs)
    models = sorted({r["model"] for r in runs})
    trs = []
    for c in conds:
        for m in [None] + models:
            sel = [r for r in runs if r["condition"] == c and (m is None or r["model"] == m)]
            tag = f"condition={c}" + (f",model={m}" if m else "")
            n = len(sel)
            res = y1_runs = y1_tot = y8_runs = mut = 0
            steps = 0
            for r in sel:
                o = outs[r["run_id"]]
                own = "F_I" if c == "F_I" else "F_R"
                st = o["sets"][own]
                res += o["resolved"]
                y1_runs += 1 if st["Y1"] > 0 else 0
                y1_tot += st["Y1"]
                y8_runs += 1 if (st.get("Y8") or 0) > 0 else 0
                steps += r["steps"]
                mut += 1 if r.get("venv_mutated") else 0
            for lab, f, v in (("n(runs", of, n), ("sum(resolved", of, res), ("mean(resolved", of, res / n if n else None),
                              ("count(Y1>0", of, y1_runs), ("sum(Y1", of, y1_tot), ("count(Y8>0", of, y8_runs),
                              ("mean(steps", rf, steps / n if n else None), ("count(venv_mutated", rf, mut)):
                D.rec(f, [f"{lab} where {tag})"], v, derived=True)
            trs.append([c, m or "(all)", n, res, fmt(res / n if n else None), y1_runs, y1_tot, y8_runs,
                        fmt(steps / n if n else None), mut, f"`{D.full(of)}::count(Y1>0 where {tag})`"])
    table(["condition", "model", "runs", "resolved", "resolve rate", "runs with Y1>0", "total Y1", "runs with Y8>0",
           "mean steps", "venv_mutated", "source (derived)"], trs)
    # false-lead actions by kind (Y4_by_kind, run's own token set)
    D.w("**WP6 false-lead actions by kind (sum of `Y4_by_kind`, run's own token set)**")
    D.w()
    trs = []
    for c in conds:
        row = [c]
        for k in ("1", "2", "3", "4"):
            v = sum(outs[r["run_id"]]["sets"]["F_I" if c == "F_I" else "F_R"]["Y4_by_kind"].get(k, 0)
                    for r in runs if r["condition"] == c)
            D.rec(of, [f"sum(Y4_by_kind.{k} where condition={c})"], v, derived=True)
            row.append(str(v))
        row.append(f"`{D.full(of)}::sum(Y4_by_kind.* where condition={c})`")
        trs.append(row)
    table(["condition", "kind 1 (path never existed)", "kind 2 (deleted file)", "kind 3 (make target)",
           "kind 4 (dependency)", "source (derived)"], trs)
    # dose
    idx = D.load(mf)["tasks"]
    D.w("**WP6 dose (derived from the manifests index)**")
    D.w()
    trs = []
    for c in ("F_R", "F_I"):
        dist = collections.Counter(t["n_false"][c] for t in idx.values())
        for k in sorted(dist):
            D.rec(mf, [f"count(tasks where n_false.{c}={k})"], dist[k], derived=True)
            trs.append([c, k, dist[k], f"`{D.full(mf)}::count(tasks where n_false.{c}={k})`"])
        tot = sum(t["n_false"][c] for t in idx.values())
        D.rec(mf, [f"sum(n_false.{c})"], tot, derived=True)
        D.rec(mf, [f"mean(n_false.{c})"], tot / len(idx), derived=True)
        trs.append([c, "total / mean per task", f"{tot} / {fmt(tot / len(idx))}", f"`{D.full(mf)}::sum(n_false.{c})`"])
    table(["manifest", "false claims in manifest", "tasks", "source (derived)"], trs)
    trs = []
    for c in ("F_R", "F_I"):
        cnt = collections.Counter((fc["kind"], fc["mode"]) for t in idx.values() for fc in t["false_claims"] if fc["cond"] == c)
        for kind in sorted({k for k, _ in cnt}):
            for mode in ("replace", "add"):
                D.rec(mf, [f"count(false_claims where cond={c},kind={kind},mode={mode})"], cnt.get((kind, mode), 0), derived=True)
                trs.append([c, kind, mode, cnt.get((kind, mode), 0),
                            f"`{D.full(mf)}::count(false_claims where cond={c},kind={kind},mode={mode})`"])
    table(["manifest", "kind", "mode", "false claims", "source (derived)"], trs)


def sec5b():
    D.w("## 5b. WP6 (harm of false manifest claims to agents)")
    D.w()
    D.w("Design: `papers/paper1/wp6-harm-design.md`; deviations: `papers/paper1/wp6-deviations-log.md`. Conditions: A no manifest, T all-true, "
        "F_R false claims near the task (relevant), F_I false claims elsewhere (irrelevant). Values come from `real_v2/wp6/`.")
    D.w()
    D.w("### 5b.1 Manifests: verification, dose, index")
    D.w()
    tree("wp6/wp6_verification.json", ("summary",), skip=skipper("tasks_with_fallback", "length_violations"),
         heading="Verification summary (`wp6_verification.json`)")
    tree("wp6/wp6_manifests_index.json", (), skip=lambda cs: len(cs) >= 1 and cs[0] == "tasks",
         heading="Manifests index (summary only; per-task entries not rendered)")
    D.w("### 5b.2 WP5 pip carry-over")
    D.w()
    tree("wp6/wp5_pip_carryover.json", (), skip=skipper("pattern", "note"))
    D.w("### 5b.3 Power")
    D.w()
    tree("wp6/wp6_power.json", ())
    D.w("### 5b.4 Runs")
    D.w()
    tree("wp6/runs/run_meta.json", ())
    tally_wp6_runs()
    D.w("### 5b.5 Confirmatory (H1-H4)")
    D.w()
    tree("wp6/analysis/wp6_primary.json", ())
    D.w("### 5b.6 Secondary")
    D.w()
    tree("wp6/analysis/wp6_secondary.json", ())
    D.w("### 5b.7 Sensitivity")
    D.w()
    tree("wp6/analysis/wp6_sensitivity.json", ())
    D.w("### 5b.8 Exploratory")
    D.w()
    tree("wp6/analysis/wp6_exploratory.json", ())


def sec5c():
    D.w("## 5c. Stronger-agent replications (exploratory; WP6 deviations 21-24, WP5 deviations 15-18)")
    D.w()
    D.w("nemotron-3-ultra on RQ6 and RQ4/RQ5 (all 80 tasks); Claude Code (Sonnet 5.5) on RQ4/RQ5 (A/C/D, 74 tasks). "
        " Tallies: `rep_summary.json` (scripts/rep_summary.py). Files not yet written are skipped.")
    D.w()
    for rel, comps, heading in (
            ("rep_summary.json", (), "Replication tallies by condition"),
            ("wp6_rep/analysis_ultra/wp6_primary.json", (), "RQ6, Ultra: confirmatory H1-H4 (same estimators)"),
            ("wp5_rep/analysis_ultra/wp5_primary.json", (), "RQ4/RQ5, Ultra: confirmatory H1-H3 (same estimators)"),
            ("wp5_rep/reeval_tmp_fix.json", (), "Re-evaluation after the /tmp incident (WP5 deviation 17)"),
            ("wp5_rep/analysis_ultra/wp5_exploratory.json", (), "RQ4/RQ5, Ultra: exploratory (D vs A)"),
            ("claude_rq45/claude_summary.json", (), "RQ4/RQ5, Claude Code (Sonnet 5.5), with Ultra and the original models on its tasks"),
            ("claude_rq45/claude_analysis.json", (), "RQ4/RQ5, Claude Code: H1-H3 (same estimators, one model)")):
        if (PROJECT_ROOT / RES / rel).exists():
            tree(rel, comps, skip=skipper("units", "config_sha256", "scope"), heading=heading)


def sec5d():
    D.w("## 5d. Fresh check of 30 new repositories with the released tool (WP2c; exploratory)")
    D.w()
    D.w("Design: `papers/paper1/wp2c-fresh-check-design.md`. Summary: scripts/wp2c_summary.py; authors' inspection of every "
        "contradicted claim: scripts/wp2c_inspection.py (descriptive, design deviation of 2026-10-19).")
    D.w()
    for rel, comps, heading in (
            ("wp2c/glob_fix_effect_rq2.json", (), "Wildcard fix: offline effect on the committed RQ2 claims"),
            ("wp2c/wp2c_summary.json", (), "Outcomes 1-5"),
            ("wp2c/wp2c_inspection.json", (), "Inspection: real errors and false alarms")):
        if (PROJECT_ROOT / RES / rel).exists():
            tree(rel, comps, skip=skipper("claims", "kinds", "flips", "examples"), heading=heading)


def md_entries(rel: str) -> int:
    text = D.load(rel)
    return sum(1 for l in text.splitlines() if re.match(r"^\|\s*\d+\s*\|", l))


def sec6():
    D.w("## 6. Deviation logs")
    D.w()
    trs = []
    for name, js, key in (("rq1-deviations-log.md", "rq1/rq1_deviations.json", None),
                          ("wp2-deviations-log.md", None, None),
                          ("wp2b-deviations-log.md", None, None),
                          ("wp5-deviations-log.md", "wp5/wp5_deviations.json", "deviations"),
                          ("wp6-deviations-log.md", None, None)):
        rel = f"papers/paper1/{name}"
        n = md_entries(rel)
        D.rec(rel, ["table rows numbered"], n, derived=True)
        jn = ""
        if js:
            d = D.load(js)
            d = d[key] if key else d
            jn = str(len(d))
            D.rec(js, ["(length)"], len(d), derived=True)
        trs.append([f"`{rel}`", n, jn or "n/a (no JSON)", f"`{D.full(js)}`" if js else "-"])
    table(["log (markdown table rows with a numeric first cell)", "entries in log", "entries in JSON", "JSON source"], trs)


def sec7():
    D.w("## 7. Pre-registered claim rules applied to extracted verdicts")
    D.w()
    D.w("Mapping only. Rule text: `papers/paper1/rq1-preregistration.md` section 6.6 and `papers/paper1/wp5-analysis-plan.md` section 15. "
        "Values are read from the JSON files named in the source column.")
    D.w()
    p = "rq1/rq1_primary.json"
    dec = {k: D.get(p, ["decision", k]) for k in ("C1", "C2", "action", "no_go_category")}
    trs = [
        ["RQ1", "decision.C1", dec["C1"], f"`{D.src(p, ['decision', 'C1'])}`", "prereg 6.4 verdict"],
        ["RQ1", "decision.C2", dec["C2"], f"`{D.src(p, ['decision', 'C2'])}`", "prereg 6.4 verdict"],
        ["RQ1", "decision.action", dec["action"], f"`{D.src(p, ['decision', 'action'])}`", "prereg 6.5 decision table"],
        ["RQ1", "decision.no_go_category", dec["no_go_category"], f"`{D.src(p, ['decision', 'no_go_category'])}`",
         f"prereg 6.6 bullet 'NO-GO with {dec['no_go_category']}'"],
    ]
    for cls in ("C1", "C2"):
        pc = D.get(p, ["classifiers", cls, "per_class_claimable"])
        trs.append(["RQ1", f"{cls}.per_class_claimable", fmt(pc), f"`{D.src(p, ['classifiers', cls, 'per_class_claimable'])}`",
                    "prereg 6.6: per-class claims only for classes marked true"])
    rb = "rq1/rq1_sensitivity.json"
    for cls in ("C1", "C2"):
        v = D.get(rb, ["robustness", cls, "statement"])
        trs.append(["RQ1", f"robustness.{cls}.statement", v, f"`{D.src(rb, ['robustness', cls, 'statement'])}`", "prereg section 8 (sensitivity never changes the verdict)"])
    table(["study", "extracted item", "value", "source", "rule reference"], trs)

    pr = "wp5/wp5_primary.json"
    pw = "wp5/wp5_power.json"
    trs = []
    for h in ("H1", "H2", "H3"):
        v = D.get(pr, ["verdicts", h])
        hp = D.get(pr, ["holm", "holm_p", h])
        trs.append(["WP5", f"verdicts.{h} (Holm p {fmt(hp)})", v, f"`{D.src(pr, ['verdicts', h])}`", ""])
    verd = {h: D.load(pr)["verdicts"][h] for h in ("H1", "H2", "H3")}
    if verd["H1"] == "not rejected" and verd["H2"] == "not rejected":
        trs.append(["WP5", "H1 and H2 verdicts", "both not rejected", f"`{D.src(pr, ['verdicts'])}`",
                    "analysis plan 15, bullet 'H1 and H2 not rejected (null)'"])
    elif verd["H1"] != "not rejected" and verd["H2"] == "not rejected":
        trs.append(["WP5", "H1 and H2 verdicts", "H1 rejected, H2 not", f"`{D.src(pr, ['verdicts'])}`", "analysis plan 15, bullet 'H1 positive, H2 null'"])
    elif verd["H2"] != "not rejected":
        trs.append(["WP5", "H1 and H2 verdicts", "H2 rejected", f"`{D.src(pr, ['verdicts'])}`", "analysis plan 15, bullet 'H2 positive (C != D)'"])
    trs.append(["WP5", "H3 verdict", verd["H3"], f"`{D.src(pr, ['verdicts', 'H3'])}`",
                "analysis plan 15, bullet 'H3'" + (" (non-rejection form)" if verd["H3"] == "not rejected" else " (rejection form)")])
    for k in ("label", "label_power", "mde_or_c"):
        trs.append(["WP5", f"power.{k}", fmt(D.get(pw, [k])), f"`{D.src(pw, [k])}`", "analysis plan 15, null bullet: MDE and power statement"])
    rd = D.get(pr, ["risk_difference"])
    for k in ("C-A", "C-D"):
        e = D.get(pr, ["risk_difference", k, "estimate"])
        ci = D.get(pr, ["risk_difference", k, "ci"])
        trs.append(["WP5", f"risk_difference.{k} estimate and CI", f"{fmt(e)} {fmt(ci)}", f"`{D.src(pr, ['risk_difference', k])}`",
                    "analysis plan 15, 'Negative (C < A or C < D)' bullet (sign and CI shown)"])
    sc = "wp5/wp5_secondary.json"
    boot = D.load(sc)["bootstrap"]
    for y, d in boot.items():
        for k, e in d.items():
            if isinstance(e, dict) and "ci" in e and e["ci"]:
                excl = e["ci"][0] > 0 or e["ci"][1] < 0
                D.rec_value(sc, ["bootstrap", y, k, "ci"], e["ci"])
                guard = D.load(sc)["holm_descriptive_guard"].get(f"{y}:{k}")
                if guard is not None:
                    D.rec(sc, ["holm_descriptive_guard", f"{y}:{k}"], guard)
                trs.append(["WP5", f"secondary {y} {k}: bootstrap CI excludes 0 = {str(excl).lower()}; Holm guard p {fmt(guard)}",
                            fmt(e["ci"]), f"`{D.src(sc, ['bootstrap', y, k])}`",
                            "analysis plan 15 (secondary differences)"])
    trs.append(["WP5", "B-subset and pilots", "exploratory / not evidence", f"`{D.src(pr, ['scope'])}`", "analysis plan 15, 'Under every outcome'"])
    table(["study", "extracted item", "value", "source", "rule reference"], trs)
    D.w("Scope sentence required by analysis plan 15 (read from the primary file): "
        f"`{D.src(pr, ['scope'])}` = {fmt(D.get(pr, ['scope']))}")
    D.w()
    D.w("Neither study speaks to the validity of Lehman's laws (prereg 6.6 and analysis plan 15, 'Under every outcome').")
    D.w()


# ------------------------------------------------------------------------ main
def git(*args) -> str:
    try:
        return subprocess.run(["git", "-C", str(PROJECT_ROOT), *args], capture_output=True, text=True, check=True).stdout.strip()
    except Exception as exc:  # noqa: BLE001
        LOG.warning("git %s failed: %s", args, exc)
        return "unknown"


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    head = git("rev-parse", "HEAD")
    results_status = git("status", "--porcelain", "--", "experiments/paper1_ontology_manifests/results/real_v2")
    D.w("# Paper 1 results digest (traced)")
    D.w()
    D.w("Generated by `experiments/paper1_ontology_manifests/scripts/make_results_digest.py`. Every number below is read from a committed "
        "result file; the `source` column (or the sentence next to a value) gives `file::json.path`. Paths with dots in a key use `[\"key\"]`. "
        "Rows with several value columns give the parent object as the source. Rows labelled derived are tallies over JSONL ledgers.")
    D.w()
    placeholder = len(D.out)
    sections = [sec1, sec2, sec3, sec4, sec4b, sec5, sec5b, sec5c, sec5d, sec6, sec7]
    for fn in sections:
        fn()
    nums = [r for r in D.records if isinstance(r["value"], (int, float)) and not isinstance(r["value"], bool)]
    uniq = len({r["source"] for r in nums})
    meta = [
        f"- Git commit at generation time: `{head}`",
        f"- Uncommitted changes under results/real_v2 at generation time: {'none' if not results_status else 'YES (' + str(len(results_status.splitlines())) + ' paths)'}",
        f"- Generated at: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"- Traced numeric values: {len(nums)} ({uniq} distinct sources; {sum(1 for r in nums if r['derived'])} derived tallies)",
        f"- MISSING entries: {len(D.missing)}",
        "",
        "Source file hashes (sha256):",
        "",
        "| file | sha256 |",
        "|---|---|",
    ] + [f"| `{f}` | `{h}` |" for f, h in sorted(D.sha.items())] + [""]
    D.out[placeholder:placeholder] = meta
    D.w("## 8. MISSING entries")
    D.w()
    if D.missing:
        for m in D.missing:
            D.w(f"- {m}")
    else:
        D.w("None.")
    D.w()
    OUT_MD.write_text("\n".join(D.out) + "\n", encoding="utf-8")
    OUT_JSON.write_text(json.dumps({
        "git_commit": head,
        "results_dirty": bool(results_status),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_traced_numbers": len(nums),
        "n_distinct_number_sources": uniq,
        "missing": D.missing,
        "files_sha256": D.sha,
        "values": D.records,
    }, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    LOG.info("wrote %s and %s; %d traced numbers, %d MISSING", OUT_MD, OUT_JSON, len(nums), len(D.missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
