"""WP6 per-task manifest generation with the verification gate, and the verification report.

Used by Paper 1 (JSEP rebuild), WP6; design papers/paper1/wp6-harm-design.md sections 2 and 2.3.

For each task: build the task workspace and venv (as the WP5 validator does), gather the context, build T / F_R / F_I with
the runtime oracle, then check every distinct claim with the re-check (instrument 2) and the runtime probes; a claim that
fails sends the builder to the next candidate (at most 3 rounds). The measured ABox is written for the HermiT step
(instrument 1, project venv). `finalize` joins all three instruments into `wp6_verification.json` and writes the manifests
index `wp6_manifests_index.json` (sha256, lengths, token sets, flags).

Usage:
    python experiments/paper1_ontology_manifests/run_wp6.py generate [--ids ID ...] [--dev] [--pilot]
    python experiments/paper1_ontology_manifests/run_wp6.py verify-hermit [--pilot]
    python experiments/paper1_ontology_manifests/run_wp6.py finalize-verification [--pilot]
"""

from __future__ import annotations

import json
import logging
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Optional

from ..wp2 import depparse as D
from ..wp2.repo import RepoAt
from ..wp5 import conditions, envs
from ..wp5.common import DiskGuard, rm_tree, run, safe_id, wait_for_resources
from ..wp5.runner import ensure_env, load_valid, release_env
from . import common as C
from . import manifests as MF
from . import verify as V

logger = logging.getLogger("wp6.generate")
MAX_ROUNDS = 3


_DIST_SCRIPT = r"""
import importlib.metadata as m, json, re
out = {}
for d in m.distributions():
    name = d.metadata["Name"]
    if not name:
        continue
    tops = set()
    t = d.read_text("top_level.txt")
    if t:
        tops.update(x.strip() for x in t.split() if x.strip())
    else:
        for f in (d.files or []):
            parts = f.parts
            if not parts or parts[0].endswith((".dist-info", ".egg-info", ".data")) or parts[0] == "..":
                continue
            tops.add(parts[0][:-3] if len(parts) == 1 and parts[0].endswith(".py") else parts[0])
    out[name] = sorted(x for x in tops if x and not x.startswith("_") and not x.endswith(".pth") and "/" not in x)
print(json.dumps(out))
"""


def dist_import_map(cfg: dict, root: Path) -> dict[str, list[str]]:
    """normalized distribution -> top-level import names, as installed in the task venv (works on Python 3.8+)."""
    rc, out = run(["python", "-c", _DIST_SCRIPT], env=envs.venv_env(cfg, root), timeout=120)
    res: dict[str, list[str]] = {}
    if rc == 0:
        try:
            for name, tops in json.loads(out.strip().splitlines()[-1]).items():
                if tops:
                    res[D.norm_name(name)] = tops
        except (json.JSONDecodeError, IndexError):
            pass
    return res


def audit_tokens(ctx: MF.TaskContext, oracle: V.Oracle, tokens: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Uniqueness audit of every false token (design 2.2): absent from the base-tree path components (paths), the issue text,
    and the repository text (commands: regex, dependencies: zero git-grep hits and a failing import)."""
    import re
    rows = []
    ps = ctx.problem_statement
    for cond, toks in tokens.items():
        for t in toks:
            r: dict[str, Any] = {"cond": cond, "kind": t["kind"], "type": t["type"]}
            if t["type"] == "path":
                final = t["values"][1]
                r["name"] = t["values"][0]
                r["final_component_absent_from_tree"] = final.lower() not in ctx.components and \
                    (final[:-3].lower() if final.endswith(".py") else final.lower()) not in ctx.components
                r["absent_from_issue"] = not MF.in_text(t["values"][0], ps) and not MF.in_text(final, ps)
                r["ok"] = r["final_component_absent_from_tree"] and r["absent_from_issue"]
            elif t["type"] == "regex":
                r["name"] = "make " + t["target"]
                r["absent_from_issue"] = re.search(t["regex"], ps) is None
                r["repo_hits"] = oracle.grep_hits(t["regex"], extended=True, ignore_case=False, word=False)
                r["ok"] = r["absent_from_issue"] and r["repo_hits"] == 0
            else:
                r["name"] = t["values"][0]
                r["absent_from_issue"] = not any(MF.in_text(v, ps) for v in t["values"])
                r["repo_hits"] = sum(oracle.grep_hits(v) for v in t["values"])
                r["import_fails"] = all(not oracle.import_ok(v.replace("-", "_")) for v in t["values"])
                r["ok"] = r["absent_from_issue"] and r["repo_hits"] == 0 and r["import_fails"]
            rows.append(r)
    return rows


def base_dirs(cfg: dict, pilot: bool) -> tuple[Path, Path]:
    out = C.out_dir(cfg, pilot)
    return out, out / "verification"


def _reject_from(claims: dict[str, dict[str, Any]], bad: list[str], reject: dict[str, set[str]]) -> bool:
    """Add the failed candidates (claim dicts: slot, attrs) to the reject sets; True if a failure could be acted on."""
    acted = False
    for k in bad:
        s, a = claims[k]["slot"], claims[k]["attrs"]
        if s == "layout":
            reject.setdefault("layout", set()).add(a["path"])
        elif s == "P1":
            reject.setdefault("k1", set()).add(a["path"].rsplit("/", 1)[-1])
        elif s == "P2":
            reject.setdefault("k2", set()).add(a["path"])
        elif s in ("C_R", "C_I"):
            reject.setdefault("k3", set()).add(a["target"])
        elif s == "D":
            reject.setdefault("k4", set()).add(a["name"])
        elif s == "dep":
            reject.setdefault("dep", set()).add(a["name"])
        elif s in ("test_cmd", "install_cmd", "python"):
            reject.setdefault("drop", set()).add(s)        # the slot's own line is dropped from all manifests of the task
        else:
            continue
        acted = True
    return acted


def rejects_path(out: Path) -> Path:
    return out / "wp6_rejects.json"


def load_rejects(out: Path, tid: str) -> dict[str, set[str]]:
    return {k: set(v) for k, v in (C.read_json(rejects_path(out), {}).get(tid) or {}).items()}


def process_task(cfg: dict, tid: str, pilot: bool, valid: dict[str, dict]) -> dict[str, Any]:
    out, vdir = base_dirs(cfg, pilot)
    t0 = time.time()
    rec = C.task_record(cfg, tid)
    task = dict(rec)
    wait_for_resources(cfg, "gen " + tid)
    root, repo_dir, err = ensure_env(cfg, task, "gen")
    if repo_dir is None:
        release_env(root)
        return {"task_id": tid, "status": "env_failed", "reason": err}
    try:
        bare = conditions.bare_dir(cfg, rec["repo"])
        files = [f for f in run(["git", "ls-files"], cwd=repo_dir, timeout=120)[1].splitlines() if f]
        census = D.census(RepoAt(bare, rec["base_commit"]))
        decls = [{"name": d.name, "spec": d.spec, "file": d.file} for d in census.decls if d.ecosystem == "pypi"]
        dist_imports = dist_import_map(cfg, root)
        ctx = MF.gather_context(cfg, rec, repo_dir, bare, files, decls, dist_imports)
        ctx.n_parsed = len(census.parsed)
        oracle = V.Oracle(cfg, repo_dir, root, bare, rec["base_commit"])
        reject: dict[str, set[str]] = load_rejects(out, tid)    # candidates that the HermiT gate refused earlier
        rounds = 0
        for rounds in range(1, MAX_ROUNDS + 1):
            built = MF.build_manifests(ctx, oracle, reject)
            claims = V.union_claims(built.manifests)
            rows = V.measure_and_recheck(tid, oracle, claims, vdir / "abox")
            bad = [k for k, r in rows.items() if not (r["recheck"]["verdict"] == claims[k].expect_verdict
                                                       and (not claims[k].expect_leaves or r["recheck"]["leaf"] in claims[k].expect_leaves)
                                                       and r["probe"]["ok"])]
            if not bad or not _reject_from({k: claims[k].to_json() for k in claims}, bad, reject):
                break
            logger.info("%s round %d: %d claims failed the gate, trying the next candidates", tid, rounds, len(bad))
        mdir = out / "manifests" / safe_id(tid)
        mdir.mkdir(parents=True, exist_ok=True)
        meta: dict[str, Any] = {"task_id": tid, "repo": rec["repo"], "stage": valid[tid]["stage"], "rounds": rounds,
                                "rejects": {k: sorted(v) for k, v in reject.items()}, "flags": built.flags,
                                "info": built.info, "tokens": built.tokens, "unresolved_pre_hermit": bad,
                                "sha256": {}, "chars": {}, "claims": {}, "python_spec": ctx.python_spec,
                                "token_audit": audit_tokens(ctx, oracle, built.tokens),
                                "dist_imports_used": {c.attrs["name"]: ctx.dist_imports.get(c.attrs["name"])
                                                      for m in built.manifests.values() for c in m.claims() if c.tcode == "T4"}}
        for cond, m in built.manifests.items():
            text = m.render()
            (mdir / f"{cond}.md").write_text(text, encoding="utf-8")
            meta["sha256"][cond], meta["chars"][cond] = MF.sha256(text), len(text)
            meta["claims"][cond] = [c.key_str for c in m.claims()]
        C.write_json(mdir / "meta.json", meta)
        C.write_json(vdir / "rows" / f"{safe_id(tid)}.json", {"task_id": tid, "claims": rows, "probe_log": oracle.probe_log})
        return {"task_id": tid, "status": "ok", "rounds": rounds, "flags": built.flags, "unresolved": bad,
                "seconds": round(time.time() - t0, 1)}
    except Exception as exc:  # noqa: BLE001
        logger.exception("generate %s", tid)
        return {"task_id": tid, "status": "exception", "reason": repr(exc)[:300]}
    finally:
        release_env(root)


def generate(cfg: dict, ids: Optional[list[str]] = None, pilot: bool = False, dev: bool = False,
             workers: Optional[int] = None, force: bool = False) -> list[dict[str, Any]]:
    valid = load_valid(cfg)
    if ids is None:
        ids = sorted(v["instance_id"] for v in valid.values() if v["stage"] == "dev") if dev else \
            [t["instance_id"] for t in C.wp5_tasks(cfg)]
    out, _ = base_dirs(cfg, pilot)
    todo = [i for i in ids if force or not (out / "manifests" / safe_id(i) / "meta.json").exists()]
    n = min(workers or cfg["limits"]["max_workers"], cfg["limits"]["max_workers"])
    logger.info("generating manifests for %d of %d tasks with %d workers into %s", len(todo), len(ids), n, out)
    DiskGuard(cfg)
    with ThreadPoolExecutor(n) as ex:
        res = list(ex.map(lambda t: process_task(cfg, t, pilot, valid), todo))
    for r in res:
        logger.info("%s", json.dumps(r))
    return res


# ----------------------------------------------------------------------------
# Verification report
# ----------------------------------------------------------------------------
def finalize(cfg: dict, pilot: bool = False, ids: Optional[list[str]] = None, reject_failures: bool = False) -> dict[str, Any]:
    """Join the three instruments per claim and write wp6_verification.json + wp6_manifests_index.json."""
    out, vdir = base_dirs(cfg, pilot)
    metas = {}
    for mp in sorted((out / "manifests").glob("*/meta.json")):
        m = C.read_json(mp)
        if not ids or m["task_id"] in ids:
            metas[m["task_id"]] = m
    tasks_out: dict[str, Any] = {}
    n_claims = n_ok = n_agree = n_agree_den = 0
    by_kind: Counter = Counter()
    by_kind_ok: Counter = Counter()
    fail: list[dict[str, Any]] = []
    for tid, meta in metas.items():
        rows = C.read_json(vdir / "rows" / f"{safe_id(tid)}.json")["claims"]
        hm = C.read_json(vdir / "hermit" / f"{tid}.json", {})
        hclaims = hm.get("claims") or {}
        per: dict[str, Any] = {}
        for k, r in rows.items():
            j = V.judge(r, hclaims.get(k) if hm.get("consistent") else None)
            per[k] = {"claim": r["claim"], **j}
            n_claims += 1
            n_ok += j["ok"]
            if j["agree_1_2"] is not None:
                n_agree_den += 1
                n_agree += j["agree_1_2"]
            lab = f"kind{r['claim']['kind']}" if r["claim"]["role"] == "false" else "true"
            by_kind[lab] += 1
            by_kind_ok[lab] += j["ok"]
            if not j["ok"]:
                fail.append({"task": tid, "key": k, "slot": r["claim"]["slot"], "role": r["claim"]["role"],
                             "i1": j["instrument1_hermit"], "i2": j["instrument2_recheck"], "probe": r["probe"]})
        manifests_ok = {c: all(per[k]["ok"] for k in meta["claims"][c]) for c in ("T", "F_R", "F_I")}
        tasks_out[tid] = {"claims": per, "manifest_all_ok": manifests_ok, "hermit_consistent": hm.get("consistent"),
                          "flags": meta["flags"]}
    idx = {}
    for tid, meta in metas.items():
        idx[tid] = {k: meta[k] for k in ("repo", "stage", "sha256", "chars", "flags", "tokens", "rejects", "rounds",
                                          "python_spec")}
        idx[tid]["slots"] = meta["info"]["slots"]
        idx[tid]["fallbacks"] = meta["info"]["fallbacks"]
        idx[tid]["n_claims_T"] = meta["info"]["n_claims_T"]
        idx[tid]["n_false"] = meta["info"]["n_false"]
        idx[tid]["pointer_in_issue"] = meta["info"]["pointer_in_issue"]
        idx[tid]["gold_dirs"] = meta["info"]["gold_dirs"]
        idx[tid]["manifest_all_ok"] = tasks_out[tid]["manifest_all_ok"]
        idx[tid]["modes"] = meta["info"]["modes"]
        idx[tid]["length_diff"] = meta["info"]["length_diff"]
        idx[tid]["false_claims"] = [
            {"cond": c, "key": k, "kind": tasks_out[tid]["claims"][k]["claim"]["kind"], "mode": tasks_out[tid]["claims"][k]["claim"]["mode"]}
            for c in ("F_R", "F_I") for k in meta["claims"][c] if tasks_out[tid]["claims"][k]["claim"]["role"] == "false"]
    flag_counts = Counter(f for m in metas.values() for f in m["flags"])
    summary = {
        "n_tasks": len(metas), "n_claims_checked": n_claims, "n_claims_ok": n_ok, "n_claims_failing": n_claims - n_ok,
        "ok_by_kind": {k: f"{by_kind_ok[k]}/{by_kind[k]}" for k in sorted(by_kind)},
        "instrument_1_2_agreement": {"agree": n_agree, "of": n_agree_den,
                                     "rate": (n_agree / n_agree_den) if n_agree_den else None},
        "tasks_with_all_manifests_ok": sum(1 for t in tasks_out.values() if all(t["manifest_all_ok"].values())),
        "tasks_hermit_missing_or_inconsistent": [t for t, v in tasks_out.items() if not v["hermit_consistent"]],
        "flag_counts": dict(flag_counts),
        "tasks_with_four_false_claims_F_R": sum(1 for m in metas.values() if m["info"]["n_false"]["F_R"] == 4),
        "tasks_with_four_false_claims_F_I": sum(1 for m in metas.values() if m["info"]["n_false"]["F_I"] == 4),
        "tasks_with_fallback": sorted(t for t, m in metas.items() if any(m["info"]["fallbacks"].values())),
        "length_violations": sorted(t for t, m in metas.items() if any(f.startswith("length_violation") for f in m["flags"])),
        "chars_T": _stats([m["chars"]["T"] for m in metas.values()]),
        "pointer_in_issue": sum(1 for m in metas.values() if m["info"]["pointer_in_issue"]),
        "dose_distribution_F_R": dict(sorted(Counter(m["info"]["n_false"]["F_R"] for m in metas.values()).items())),
        "dose_distribution_F_I": dict(sorted(Counter(m["info"]["n_false"]["F_I"] for m in metas.values()).items())),
        "false_claims_by_mode": dict(Counter(f"{c['cond']}:{c['mode']}" for v in idx.values() for c in v["false_claims"])),
        "false_claims_by_kind_mode": dict(Counter(f"kind{c['kind']}:{c['mode']}" for v in idx.values() for c in v["false_claims"])),
        "length_diff_chars_F_minus_T": {c: _stats([m["info"]["length_diff"][c] for m in metas.values()]) for c in ("F_R", "F_I")},
        "length_diff_rel": {c: _stats([round(100 * m["info"]["length_diff"][c] / max(1, m["chars"]["T"])) for m in metas.values()])
                            for c in ("F_R", "F_I")},
        "tasks_with_no_false_claim": sorted(t for t, m in metas.items() if m["info"]["n_false"]["F_R"] == 0),
        "token_audit": {"n_tokens": sum(len(m.get("token_audit", [])) for m in metas.values()),
                        "n_failing": sum(1 for m in metas.values() for a in m.get("token_audit", []) if not a["ok"]),
                        "failing": [{"task": t, **a} for t, m in metas.items() for a in m.get("token_audit", []) if not a["ok"]]},
        "failures": fail,
    }
    if reject_failures and fail:
        rj = C.read_json(rejects_path(out), {})
        for tid in sorted({f["task"] for f in fail}):
            rows = C.read_json(vdir / "rows" / f"{safe_id(tid)}.json")["claims"]
            rej = {k: set(v) for k, v in (rj.get(tid) or {}).items()}
            bad_keys = [f["key"] for f in fail if f["task"] == tid]
            if _reject_from({k: r["claim"] for k, r in rows.items()}, bad_keys, rej):
                rj[tid] = {k: sorted(v) for k, v in rej.items()}
                summary.setdefault("rejected_and_to_regenerate", []).append(tid)
        C.write_json(rejects_path(out), rj)
    C.write_json(out / "wp6_verification.json", {"summary": summary, "tasks": tasks_out,
                                                  "design": "papers/paper1/wp6-harm-design.md section 2.3"})
    C.write_json(out / "wp6_manifests_index.json", {"tasks": idx})
    logger.info("verification: %s", json.dumps({k: v for k, v in summary.items() if k != "failures"}))
    return summary


def _stats(xs: list[int]) -> dict[str, Any]:
    if not xs:
        return {}
    xs = sorted(xs)
    return {"min": xs[0], "median": xs[len(xs) // 2], "max": xs[-1], "mean": round(sum(xs) / len(xs), 1)}
