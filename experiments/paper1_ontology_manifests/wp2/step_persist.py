"""WP2b step: do contradicted manifest claims persist at the default-branch head? (Paper 1, RQ2b).

Design and pre-registration: papers/paper1/wp2b-persistence-design.md (tag ``wp2b-prereg``). The analysed claims are
the frozen RQ2 Supported/Contradicted claims (types T1, T3-T6, from ``drift.json``). Each is followed from the
snapshot commit S to the default-branch head H (fetched once into ``refs/wp2b/head``) and given exactly one outcome:
U (repository unavailable), G (manifest gone), R (claim removed), P-C / P-S / P-O (retained, Contradicted /
Supported / other verdict at H, measured with the unchanged RQ2 code and HermiT). No language model is called.
Results go to ``results/real_v2/wp2b/``; ``results/real_v2/wp2/`` is only read.

Stages (run in this order, each checkpointed):
    verify  re-measure and re-check at S, matcher self-test on the S manifest text; must reproduce RQ2 exactly
    fetch   one fetch of the default-branch head per repository (+ one REST call); writes head_fetch.json once
    run     outcomes, measurement and re-check at H, HermiT, removal-commit search; writes persistence/ and claims.jsonl

Usage:
    python experiments/paper1_ontology_manifests/wp2_consistency.py persist --stage verify
    python experiments/paper1_ontology_manifests/wp2_consistency.py persist --stage fetch
    python experiments/paper1_ontology_manifests/wp2_consistency.py persist --stage run
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

from . import common as C
from . import measure as M
from . import normalize as N
from . import recheck as R
from .gitutil import ENV, GitError, commit_epoch, git
from .repo import RepoAt
from .step_measure import measure_claim
from .step_reason import ensure_tbox, tbox_sha

logger = logging.getLogger("wp2.step_persist")

REF = "refs/wp2b/head"
DRIFT_TYPES = {"T1", "T3", "T4", "T5", "T6"}
SUBJECT_WORDS = {"python": ["python"], "node": ["node", "nodejs", "node.js"], "go": ["go", "golang"],
                 "java": ["java", "jdk"], "dotnet": [".net", "dotnet"], "rust": ["rust"], "php": ["php"],
                 "ruby": ["ruby"]}


def out_dir(cfg: dict[str, Any]) -> Path:
    p = C.results_dir(cfg).parent / "wp2b"
    p.mkdir(parents=True, exist_ok=True)
    return p


# ---------------------------------------------------------------------------
# Frozen inputs
# ---------------------------------------------------------------------------
def load_analysed(cfg: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """slug -> {entry, meas, ver, claims[...]} for the analysed (Supported/Contradicted, T1/T3-T6) claims."""
    res = C.results_dir(cfg)
    drift = {}
    for r in C.read_json(res / "drift.json")["rows"]:
        drift[r["key"]] = r  # keys are unique per manifest only; resolved per slug below
    out: dict[str, dict[str, Any]] = {}
    for e in C.load_corpus(cfg):
        slug = e["slug"]
        dp = res / "drift" / f"{slug}.json"
        mp = res / "measurements" / f"{slug}.json"
        if not (dp.exists() and mp.exists()):
            continue
        meas = C.read_json(mp)
        by_key = {c["key_str"]: c for c in meas["claims"]}
        claims = []
        for r in C.read_json(dp)["rows"]:
            if r["verdict_at_S"] not in ("SupportedClaim", "ContradictedClaim") or r["tcode"] not in DRIFT_TYPES:
                continue
            c = by_key[r["key"]]
            claims.append({**c, "drift": r})
        if claims:
            out[slug] = {"entry": e, "meas": meas, "claims": claims,
                         "snap": C.read_json(res / "snapshots" / f"{slug}.json")}
    return out


# ---------------------------------------------------------------------------
# Manifest location and key matcher
# ---------------------------------------------------------------------------
def _ls(d: Path, rev: str, path: str) -> Optional[tuple[str, str]]:
    out = str(git(d, "ls-tree", "-z", rev, "--", path, check=False))
    for rec in out.split("\0"):
        if rec:
            meta, _p = rec.split("\t", 1)
            mode, typ, sha = meta.split()
            return mode, sha
    return None


def manifest_at(d: Path, rev: str, path: str) -> Optional[tuple[str, str, str]]:
    """(resolved path, text, via) of the manifest at ``rev``; a symlink is followed one level."""
    e = _ls(d, rev, path)
    if e is None:
        return None
    mode, _sha = e
    p, via = path, "path"
    if mode == "120000":
        tgt = subprocess.run(["git", "-C", str(d), "show", f"{rev}:{path}"], capture_output=True, env=ENV, timeout=300)
        link = tgt.stdout.decode("utf-8", "replace").strip()
        p = os.path.normpath(os.path.join(os.path.dirname(path), link)).lstrip("./") if link else ""
        if not p or _ls(d, rev, p) is None:
            return None
        via = "symlink"
    b = subprocess.run(["git", "-C", str(d), "show", f"{rev}:{p}"], capture_output=True, env=ENV, timeout=300)
    if b.returncode != 0:
        return None
    return p, b.stdout.decode("utf-8-sig", "replace"), via


def find_rename(d: Path, S: str, H: str, path: str) -> Optional[str]:
    out = str(git(d, "diff", "-M50%", "--name-status", S, H, check=False, timeout=1800))
    for ln in out.splitlines():
        parts = ln.split("\t")
        if len(parts) == 3 and parts[0].startswith("R") and parts[1] == path:
            return parts[2]
    return None


def norm_lines(text: str) -> list[str]:
    """Normalised lowercase lines; a leading ``./`` or ``/`` before a path is dropped."""
    return [_norm1(ln) for ln in text.replace("\r\n", "\n").split("\n")]


def _norm1(s: str) -> str:
    return re.sub(r"(?<![\w.)\]])/(?=[\w.])", "", re.sub(r"(?<![\w.])\./", "", N.norm_text(s))).lower()


def _tok(s: str, extra_before: str = "") -> str:
    return rf"(?<![\w@/{extra_before}-]){re.escape(_norm1(s))}(?![\w-]|\.\w)"


def key_alternatives(c: dict[str, Any], tree_derived: bool = False) -> list[list[re.Pattern[str]]]:
    """Alternatives (any may match); each is a list of patterns that must all hold on one line."""
    t, a = c["tcode"], c["attrs"]
    alts: list[list[str]] = []
    if t == "T1":
        for p in dict.fromkeys([a["path"], a.get("alt_path") or "", a["path"].lstrip("/").rstrip("/")]):
            if p:
                alts.append([_tok(p.rstrip("/"), "." )])
        if tree_derived:
            base = a["path"].rstrip("/").rsplit("/", 1)[-1]
            alts.append([_tok(base, ".")])
    elif t == "T3":
        al = [k for k, v in N.tool_aliases().items() if v == N.canonical_tool(a["tool"])] or [a["tool"].lower()]
        alts = [[_tok(x)] for x in dict.fromkeys(al + [a["tool"].lower()])]
    elif t == "T4":
        pats = [_tok(a["name"])]
        if a.get("major") is not None:
            pats.append(rf"(?<![\d.]){int(a['major'])}(?!\d)")
        alts = [pats]
    elif t == "T5":
        tgt, runner = re.escape(N.norm_text(a["target"]).lower()), a["runner"].lower()
        if runner in N.SCRIPT_RUNNERS:
            rx = rf"(?<![\w-]){runner}\s+(?:run(?:-script)?\s+)?{tgt}(?![\w:-])"
        elif runner == "make":
            rx = rf"(?<![\w-])make\s+(?:-\S+\s+)*{tgt}(?![\w:-])"
        else:
            rx = rf"(?<![\w-])composer\s+(?:run(?:-script)?\s+)?{tgt}(?![\w:-])"
        alts = [[rx]]
    elif t == "T6":
        v = re.search(r"\d+(?:\.\d+){0,3}", a["version"]).group(0)
        pats = [rf"(?<![\d.]){re.escape(v)}(?!\d|\.\d)"]
        st = a["subject_type"]
        if st in SUBJECT_WORDS:
            pats.append("(?:" + "|".join(rf"(?<![\w-]){re.escape(w)}(?![\w-])" for w in SUBJECT_WORDS[st]) + ")")
        alts = [pats]
    return [[re.compile(p, re.I) for p in alt] for alt in alts]


def key_present(lines: list[str], alts: list[list[re.Pattern[str]]]) -> bool:
    return any(all(p.search(ln) for p in alt) for ln in lines for alt in alts)


def needle(c: dict[str, Any]) -> str:
    t, a = c["tcode"], c["attrs"]
    return {"T1": a.get("path"), "T3": a.get("tool"), "T4": a.get("name"), "T5": a.get("target"),
            "T6": re.search(r"\d+(?:\.\d+){0,3}", a.get("version", "") or "").group(0) if t == "T6" else None}[t] or ""


def quote_present(text: str, quote: str) -> bool:
    q = N.norm_text(N.strip_prefixes(quote)).lower()
    return bool(q) and q in N.norm_text(text).lower()


# ---------------------------------------------------------------------------
# Stage verify
# ---------------------------------------------------------------------------
def _loads(o: Any) -> Any:
    return json.loads(json.dumps(o, default=str))


def verify_repo(cfg: dict[str, Any], slug: str, rec: dict[str, Any], thr: dict[str, Any], sigs: dict[str, Any],
                vsrc: dict[str, Any], rows_rc: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    d = Path(cfg["clone_dir"]) / slug
    meas, snap = rec["meas"], rec["snap"]
    S = snap["S"]
    ctx = M.Ctx(RepoAt(d, S))
    g = R.Git(d, S)
    g.prefetch_interesting()
    cache: dict[str, Any] = {}
    tool_cache: dict[str, int] = {}
    mi = manifest_at(d, S, snap["manifest_path"])
    lines = norm_lines(mi[1]) if mi else []
    out = {"slug": slug, "n": 0, "props_mismatch": [], "evidence_mismatch": [], "recheck_mismatch": [], "matcher_miss": [],
           "tree_derived": []}
    for c in rec["claims"]:
        out["n"] += 1
        m = measure_claim(ctx, {"repo": meas["repo"], "tcode": c["tcode"], "attrs": c["attrs"], "key_str": c["key_str"]})
        if _loads(m["props"]) != _loads(c["m"]["props"]):
            out["props_mismatch"].append(c["key_str"])
        if _loads(m["evidences"]) != _loads(c["m"]["evidences"]):
            out["evidence_mismatch"].append(c["key_str"])
        v, _ = R.recheck_claim(g, {"tcode": c["tcode"], "attrs": c["attrs"], "votes": c["votes"]}, thr, sigs, vsrc, cache, tool_cache)
        frozen = rows_rc.get((meas["repo"], c["key_str"]))
        if frozen is None or (v or "none") != frozen["recheck_verdict"]:
            out["recheck_mismatch"].append(c["key_str"])
        if not key_present(lines, key_alternatives(c)):
            if t1_basename_ok(c, lines):
                out["tree_derived"].append(c["key_str"])
            else:
                out["matcher_miss"].append(c["key_str"])
    logger.info("verify %s: n=%d props_mm=%d recheck_mm=%d matcher_miss=%d", slug, out["n"], len(out["props_mismatch"]),
                len(out["recheck_mismatch"]), len(out["matcher_miss"]))
    return out


def t1_basename_ok(c: dict[str, Any], lines: list[str]) -> bool:
    return c["tcode"] == "T1" and key_present(lines, key_alternatives(c, tree_derived=True))


def run_verify(cfg: dict[str, Any]) -> int:
    od = out_dir(cfg)
    res = C.results_dir(cfg)
    data = load_analysed(cfg)
    thr = R.load_thr()
    sigs = yaml.safe_load((C.EXP_DIR / "configs" / "wp2_tool_signatures.yaml").read_text(encoding="utf-8"))
    vsrc = yaml.safe_load((C.EXP_DIR / "configs" / "wp2_version_sources.yaml").read_text(encoding="utf-8"))["subjects"]
    rows_rc = {(r["repo"], r["key"]): r for r in C.read_jsonl(res / "recheck_rows.jsonl")}
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=3) as ex:
        parts = list(ex.map(lambda kv: verify_repo(cfg, kv[0], kv[1], thr, sigs, vsrc, rows_rc), data.items()))
    n = sum(p["n"] for p in parts)
    summ = {"n_claims": n, "n_manifests": len(parts),
            "n_props_mismatch": sum(len(p["props_mismatch"]) for p in parts),
            "n_evidence_mismatch": sum(len(p["evidence_mismatch"]) for p in parts),
            "n_recheck_mismatch": sum(len(p["recheck_mismatch"]) for p in parts),
            "n_matcher_miss": sum(len(p["matcher_miss"]) for p in parts),
            "n_tree_derived_t1": sum(len(p["tree_derived"]) for p in parts), "seconds": round(time.time() - t0, 1),
            "reproduces_rq2_exactly": False, "manifests": parts}
    summ["reproduces_rq2_exactly"] = (summ["n_props_mismatch"] == 0 and summ["n_evidence_mismatch"] == 0
                                      and summ["n_recheck_mismatch"] == 0)
    summ["matcher_selftest_ok"] = summ["n_matcher_miss"] == 0
    C.write_json(od / "s_reproduction.json", summ)
    logger.info("verify: %d claims, reproduces=%s, matcher_ok=%s (tree-derived T1=%d)", n, summ["reproduces_rq2_exactly"],
                summ["matcher_selftest_ok"], summ["n_tree_derived_t1"])
    return 0 if summ["reproduces_rq2_exactly"] and summ["matcher_selftest_ok"] else 2


# ---------------------------------------------------------------------------
# Stage fetch
# ---------------------------------------------------------------------------
def _rest(full_name: str, token: Optional[str]) -> dict[str, Any]:
    req = urllib.request.Request(f"https://api.github.com/repos/{full_name}",
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": "senso-wp2b",
                                          **({"Authorization": f"Bearer {token}"} if token else {})})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            j = json.load(r)
        return {"status": 200, "default_branch": j.get("default_branch"), "archived": bool(j.get("archived")),
                "full_name_now": j.get("full_name"), "disabled": bool(j.get("disabled"))}
    except urllib.error.HTTPError as exc:
        return {"status": exc.code}
    except Exception as exc:  # noqa: BLE001
        return {"status": None, "error": f"{type(exc).__name__}: {exc}"[:200]}


def fetch_repo(cfg: dict[str, Any], slug: str, rec: dict[str, Any], token: Optional[str]) -> dict[str, Any]:
    d = Path(cfg["clone_dir"]) / slug
    full = rec["entry"]["full_name"]
    rest = _rest(full, token)
    branch = rest.get("default_branch") or rec["snap"].get("default_branch") or "main"
    out: dict[str, Any] = {"repo": full, "slug": slug, "S": rec["snap"]["S"], "rest": rest, "default_branch": branch,
                           "archived": rest.get("archived"), "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    ok, err = False, ""
    for attempt in range(2):
        p = subprocess.run(["git", "-C", str(d), "fetch", "--filter=blob:none", "--no-tags", "--no-write-fetch-head", "origin",
                            f"+refs/heads/{branch}:{REF}"], capture_output=True, env=ENV, timeout=3600)
        ok, err = p.returncode == 0, p.stderr.decode("utf-8", "replace")[-300:]
        if ok:
            break
        time.sleep(5)
    out["fetch_ok"], out["fetch_error"] = ok, (None if ok else err)
    if ok:
        out["H"] = str(git(d, "rev-parse", REF)).strip()
        out["H_epoch"] = commit_epoch(d, out["H"])
        a = subprocess.run(["git", "-C", str(d), "merge-base", "--is-ancestor", out["S"], out["H"]], env=ENV, capture_output=True)
        out["S_is_ancestor_of_H"] = a.returncode == 0
    out["unavailable"] = not ok
    logger.info("fetch %s: ok=%s branch=%s rest=%s", full, ok, branch, rest.get("status"))
    return out


def run_fetch(cfg: dict[str, Any]) -> int:
    od = out_dir(cfg)
    p = od / "head_fetch.json"
    if p.exists():
        logger.info("head_fetch.json exists: H is frozen, no re-fetch")
        return 0
    token = os.environ.get("GITHUB_TOKEN")
    data = load_analysed(cfg)
    t0 = datetime.now(timezone.utc)
    with ThreadPoolExecutor(max_workers=3) as ex:
        recs = list(ex.map(lambda kv: fetch_repo(cfg, kv[0], kv[1], token), data.items()))
    t1 = datetime.now(timezone.utc)
    C.write_json(p, {"fetch_started": t0.isoformat(timespec="seconds"), "fetch_finished": t1.isoformat(timespec="seconds"),
                     "fetch_date": t0.date().isoformat(), "ref": REF, "n_repos": len(recs),
                     "n_unavailable": sum(1 for r in recs if r["unavailable"]),
                     "n_archived": sum(1 for r in recs if r.get("archived")),
                     "n_S_not_ancestor": sum(1 for r in recs if r.get("fetch_ok") and not r["S_is_ancestor_of_H"]),
                     "repos": {r["slug"]: r for r in recs}})
    return 0


# ---------------------------------------------------------------------------
# Stage run
# ---------------------------------------------------------------------------
def removal_search(d: Path, S: str, H: str, paths: list[str], c: dict[str, Any], tree_derived: bool) -> dict[str, Any]:
    """First first-parent commit in (S, H] whose manifest diff drops the key (git log -S, then a scan fallback)."""
    alts = key_alternatives(c, tree_derived)
    nd = needle(c)

    def cands(*extra: str) -> list[str]:
        p = subprocess.run(["git", "-C", str(d), "log", "--first-parent", "--reverse", "--format=%H", *extra, f"{S}..{H}", "--", *paths],
                           capture_output=True, env=ENV, timeout=900)
        return p.stdout.decode().split()

    def present(rev: str) -> Optional[bool]:
        for pth in paths:
            mi = manifest_at(d, rev, pth)
            if mi:
                return key_present(norm_lines(mi[1]), alts)
        return None  # manifest absent at rev

    for method, cs in (("pickaxe", cands("-S", nd) if nd else []), ("scan", None)):
        if cs is None:
            cs = cands()[:300]
        for cm in cs[:300]:
            try:
                before, after = present(f"{cm}^1"), present(cm)
            except subprocess.TimeoutExpired:
                continue
            if before and not after:
                ct = commit_epoch(d, cm)
                msg = str(git(d, "show", "-s", "--format=%B", cm, check=False))
                shape = hunk_shape(d, cm, paths, alts)
                return {"commit": cm, "epoch": ct, "method": method, "shape": shape, "agent_signal": agent_signal(msg)}
    return {"commit": None, "method": "not_found"}


def hunk_shape(d: Path, cm: str, paths: list[str], alts: list[list[re.Pattern[str]]]) -> str:
    out = str(git(d, "diff", "-U0", f"{cm}^1", cm, "--", *paths, check=False))
    hunks: list[list[str]] = []
    for ln in out.splitlines():
        if ln.startswith("@@"):
            hunks.append([])
        elif hunks and ln[:1] in "+-" and not ln.startswith(("+++", "---")):
            hunks[-1].append(ln)
    for h in hunks:
        removed = [x[1:] for x in h if x[0] == "-"]
        if key_present(norm_lines("\n".join(removed)), alts):
            return "replacement" if any(x[0] == "+" for x in h) else "pure_deletion"
    mi = [manifest_at(d, cm, pth) for pth in paths]
    return "file_deleted" if not any(mi) else "other"


def agent_signal(msg: str) -> Optional[str]:
    from shared.mining.agent_detector import COAUTHOR_PATTERNS, MESSAGE_PATTERNS

    low = msg.lower()
    for table in (COAUTHOR_PATTERNS, MESSAGE_PATTERNS):
        for agent, pats in table.items():
            if any(re.search(p, low) for p in pats):
                return agent
    return None


def process_repo(cfg: dict[str, Any], slug: str, rec: dict[str, Any], hf: dict[str, Any], thr: dict[str, Any],
                 sigs: dict[str, Any], vsrc: dict[str, Any], tree_derived: set[str]) -> dict[str, Any]:
    from ontology.reasoning.abox import DATA_BASE, _safe
    from ontology.reasoning.claims_abox import ClaimsAboxWriter, claim_id

    od = out_dir(cfg)
    res = C.results_dir(cfg)
    d = Path(cfg["clone_dir"]) / slug
    meas, snap = rec["meas"], rec["snap"]
    S, mpath = snap["S"], snap["manifest_path"]
    base = {"repo": meas["repo"], "slug": slug, "S": S, "S_epoch": snap["S_epoch"], "manifest_path_S": mpath,
            "fetch": {k: hf.get(k) for k in ("default_branch", "archived", "fetch_ok", "H", "H_epoch", "S_is_ancestor_of_H",
                                              "fetched_at")}}
    if hf["unavailable"]:
        rows = [{"key": c["key_str"], "tcode": c["tcode"], "outcome": "U"} for c in rec["claims"]]
        out = {**base, "manifest_status": "U", "rows": rows}
        C.write_json(od / "persistence" / f"{slug}.json", out)
        return out
    H = hf["H"]
    sm = manifest_at(d, S, mpath)
    # locate the manifest at H: same path, symlink, or rename
    hm = manifest_at(d, H, mpath)
    status, via, hpath = "present", "path", mpath
    if hm is None:
        rn = find_rename(d, S, H, mpath)
        hm = manifest_at(d, H, rn) if rn else None
        if hm:
            hpath, via = rn, "rename"
        else:
            status = "gone"
    elif hm[2] == "symlink":
        via, hpath = "symlink", hm[0]
    text = hm[1] if hm else ""
    lines = norm_lines(text)
    paths = list(dict.fromkeys([mpath] + ([hpath] if hm else [])))
    n_commits = int(str(git(d, "rev-list", "--first-parent", "--count", f"{S}..{H}", check=False)).strip() or 0)
    n_mcommits = int(str(git(d, "rev-list", "--first-parent", "--count", f"{S}..{H}", "--", *paths, check=False)).strip() or 0)
    base.update({"manifest_status": status, "manifest_path_H": hpath if hm else None, "manifest_via": via,
                 "n_commits_S_H": n_commits, "n_manifest_commits_S_H": n_mcommits,
                 "manifest_sha_changed": (sm[1] != text) if sm and hm else None})
    if status == "gone":
        gc = str(git(d, "log", "--first-parent", "--diff-filter=DR", "-1", "--format=%H %ct", f"{S}..{H}", "--", mpath, check=False)).split()
        base["manifest_removal_commit"] = {"commit": gc[0], "epoch": int(gc[1])} if len(gc) == 2 else None
    rows: list[dict[str, Any]] = []
    retained: list[dict[str, Any]] = []
    for c in rec["claims"]:
        td = c["key_str"] in tree_derived
        dr = c["drift"]
        row = {"key": c["key_str"], "tcode": c["tcode"], "quote": c["quote"][:160], "verdict_S": dr["verdict_at_S"],
               "leaf_S": dr.get("leaf_at_S"), "drifted": dr.get("drifted"), "born_wrong": dr.get("born_wrong"),
               "tree_derived": td}
        if status == "gone":
            row["outcome"], row["key_present"], row["quote_verbatim"] = "G", False, False
        else:
            kp = key_present(lines, key_alternatives(c, td))
            row["key_present"], row["quote_verbatim"] = kp, quote_present(text, c["quote"])
            row["outcome"] = None if kp else "R"
            if kp:
                retained.append(c)
        if row["outcome"] == "R":
            row["removal"] = removal_search(d, S, H, paths, c, td)
        rows.append(row)
    # measure retained claims at H and write the ABox copies (/head)
    nt_name = od / "abox_head" / f"{slug}.nt"
    if retained:
        ctx = M.Ctx(RepoAt(d, H))
        w = ClaimsAboxWriter()
        w.lines = (res / "abox" / f"{slug}.nt").read_text(encoding="utf-8").splitlines()
        w._bn = 10**6
        g = R.Git(d, H)
        g.prefetch_interesting()
        cache: dict[str, Any] = {}
        tool_cache: dict[str, int] = {}
        by_key = {r["key"]: r for r in rows}
        for c in retained:
            m = measure_claim(ctx, {"repo": meas["repo"], "tcode": c["tcode"], "attrs": c["attrs"], "key_str": c["key_str"]})
            props = {"claimQuote": c["quote"][:300], "claimSubject": c["subject"], "claimKey": c["key_str"],
                     "claimLine": c["line"], "extractionVotes": c["votes"], **m["props"]}
            iri = w.claim(meas["repo"], c["key_str"], c["types"], props, suffix="/head")
            eis = [w.evidence(iri, i, e) for i, e in enumerate(m["evidences"])]
            w.close_evidence(iri, eis)
            v, leaf = R.recheck_claim(g, {"tcode": c["tcode"], "attrs": c["attrs"], "votes": c["votes"]}, thr, sigs, vsrc, cache, tool_cache)
            r = by_key[c["key_str"]]
            r["head_iri"], r["recheck_verdict_H"], r["recheck_leaf_H"] = iri, v or "none", leaf
            r["measure_error_H"] = m["meta"].get("error")
        nt_name.parent.mkdir(parents=True, exist_ok=True)
        nt_name.write_text(w.ntriples(), encoding="utf-8")
    # age of the error: introduction and flip commits (contradicted claims only)
    for c, r in zip(rec["claims"], rows):
        dr = c["drift"]
        if r["verdict_S"] == "ContradictedClaim":
            for k in ("intro_commit", "flip_commit"):
                if dr.get(k):
                    try:
                        r[k + "_epoch"] = commit_epoch(d, dr[k])
                    except GitError:
                        pass
    out = {**base, "abox_head": str(nt_name.relative_to(od)) if retained else None, "rows": rows}
    C.write_json(od / "persistence" / f"{slug}.json", out)
    logger.info("%s: %s, %d claims, %d retained, %d commits since S", meas["repo"], status, len(rows), len(retained), n_commits)
    return out


def reason_head(args: tuple[str, str, str, str]) -> dict[str, Any]:
    """HermiT over ``abox_head/{slug}.nt`` (original S claims + /head copies); regression guard at S included."""
    cfg_path, slug, tbox_dir, od_s = args
    from ontology.reasoning.abox import DATA_BASE, _safe
    from ontology.reasoning.claims_abox import claim_id
    from ontology.modules.claims_module import VERDICTS
    from ontology.reasoning.reasoner import CLAIMS_MODULES, HermitReasoner

    cfg = C.load_config()
    res, od, tbox = C.results_dir(cfg), Path(od_s), Path(tbox_dir)
    pj = C.read_json(od / "persistence" / f"{slug}.json")
    if not pj.get("abox_head"):
        return {"slug": slug, "guard_ok": True, "skipped": True}
    ver = C.read_json(res / "verdicts" / f"{slug}.json")
    meas = C.read_json(res / "measurements" / f"{slug}.json")
    nt = (od / pj["abox_head"]).read_text(encoding="utf-8")
    inf = HermitReasoner(tbox, modules=CLAIMS_MODULES, temp_dir=Path(f"/tmp/wp2b_reason_{os.getpid()}")).infer(nt)
    guard_bad: list[str] = []
    if not inf.consistent:
        guard_bad.append("inconsistent ABox")
    else:
        for c in meas["claims"]:  # regression guard: the original claims keep their RQ2 verdicts
            iri = f"{DATA_BASE}claim/{_safe(meas['repo'])}/{claim_id(c['key_str'])}"
            got = sorted(set(inf.labels.get(iri, ())) & set(VERDICTS))
            if got != ver["claims"].get(c["key_str"], {}).get("verdicts", []):
                guard_bad.append(c["key_str"])
    leaves = set(C.read_json(tbox / "leaf_verdict.json"))
    for r in pj["rows"]:
        if r.get("head_iri") and inf.consistent:
            ls = set(inf.labels.get(r["head_iri"], ()))
            r["verdict_H"] = (sorted(ls & set(VERDICTS)) or ["none"])[0]
            r["leaf_H"] = (sorted(ls & leaves) or [None])[0]
            r["outcome"] = {"ContradictedClaim": "P-C", "SupportedClaim": "P-S"}.get(r["verdict_H"], "P-O")
    pj["guard_ok"], pj["guard_bad"] = not guard_bad, guard_bad
    C.write_json(od / "persistence" / f"{slug}.json", pj)
    return {"slug": slug, "guard_ok": not guard_bad, "guard_bad": guard_bad, "reason_s": inf.timings.get("reason_s")}


def run_main(cfg: dict[str, Any], only: Optional[str] = None) -> int:
    od = out_dir(cfg)
    hf_all = C.read_json(od / "head_fetch.json")
    sv = od / "s_reproduction.json"
    if not sv.exists() or not C.read_json(sv).get("reproduces_rq2_exactly"):
        raise RuntimeError("S reproduction check missing or failed; run --stage verify first")
    td = {k for p in C.read_json(sv)["manifests"] for k in p["tree_derived"]}
    data = {s: r for s, r in load_analysed(cfg).items() if not only or r["entry"]["full_name"] == only}
    thr = R.load_thr()
    sigs = yaml.safe_load((C.EXP_DIR / "configs" / "wp2_tool_signatures.yaml").read_text(encoding="utf-8"))
    vsrc = yaml.safe_load((C.EXP_DIR / "configs" / "wp2_version_sources.yaml").read_text(encoding="utf-8"))["subjects"]
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=3) as ex:
        list(ex.map(lambda kv: process_repo(cfg, kv[0], kv[1], hf_all["repos"][kv[0]], thr, sigs, vsrc,
                                            {k for k in td}), data.items()))
    t1 = time.time()
    tbox = ensure_tbox("baseline")
    frozen_sha = {C.read_json(C.results_dir(cfg) / "verdicts" / f"{s}.json")["tbox_sha256"] for s in data}
    if frozen_sha != {tbox_sha(tbox)}:
        raise RuntimeError("TBox sha differs from the frozen RQ2 verdicts")
    with ProcessPoolExecutor(max_workers=2) as ex:  # owlready2 worlds are not thread safe
        guards = list(ex.map(reason_head, [("", s, str(tbox), str(od)) for s in data]))
    bad = [g for g in guards if not g["guard_ok"]]
    if bad:
        C.write_json(od / "guard_failures.json", bad)
        raise RuntimeError(f"regression guard failed for {[b['slug'] for b in bad]}")
    rows = []
    for s in data:
        pj = C.read_json(od / "persistence" / f"{s}.json")
        for r in pj["rows"]:
            rows.append({"repo": pj["repo"], "slug": s, "manifest_status": pj["manifest_status"], "S": pj["S"],
                         "S_epoch": pj["S_epoch"], "H_epoch": pj["fetch"].get("H_epoch"), "archived": pj["fetch"].get("archived"),
                         "S_is_ancestor_of_H": pj["fetch"].get("S_is_ancestor_of_H"),
                         "n_commits_S_H": pj.get("n_commits_S_H"), "n_manifest_commits_S_H": pj.get("n_manifest_commits_S_H"),
                         **{k: v for k, v in r.items() if k != "head_iri"}})
    C.write_jsonl(od / "claims.jsonl", rows)
    C.write_json(od / "timings.json", {"measure_wall_s": round(t1 - t0, 1), "reason_wall_s": round(time.time() - t1, 1),
                                       "total_wall_s": round(time.time() - t0, 1), "n_rows": len(rows),
                                       "guards_ok": len(guards) - len(bad)})
    logger.info("run done: %d rows, total %.0fs", len(rows), time.time() - t0)
    return 0


def run(cfg: dict[str, Any], only: Optional[str] = None, force: bool = False, stage: str = "run") -> int:
    if stage == "verify":
        return run_verify(cfg)
    if stage == "fetch":
        return run_fetch(cfg)
    return run_main(cfg, only)
