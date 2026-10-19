"""WP5 task validation (human-free): build the env, then check the tests behave as the dataset claims.

Used by Paper 1 (JSEP rebuild), WP5.

A task is kept only if, in its own uv venv:
  1. at base commit + test patch, every FAIL_TO_PASS test is not passing;
  2. at base commit + test patch + gold patch, every FAIL_TO_PASS test passes and at least
     `min_p2p_keep` of the PASS_TO_PASS tests pass, both before and after the gold patch.
Only the PASS_TO_PASS tests that pass in BOTH runs form the task's effective P2P list (env noise such as
network-dependent tests is dropped, and the drop is recorded). Per-task checkpoints go to
<work_dir>/validation/<id>.json; the aggregate is results/real_v2/wp5/validation.json.

Usage:
    python experiments/paper1_ontology_manifests/run_wp5.py validate [--limit N] [--stage S] [--ids ID ...]
"""

from __future__ import annotations

import logging
import random
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from . import conditions, envs, metrics
from .common import (DiskGuard, du_gb, load_task, read_json, rpath, safe_id, wait_for_resources,
                     work_dir, write_json)

logger = logging.getLogger("wp5.validate")
MIN_P2P_KEEP = 0.9


def ckpt_dir(cfg: dict) -> Path:
    d = work_dir(cfg) / "validation"
    d.mkdir(parents=True, exist_ok=True)
    return d


def validate_one(cfg: dict, rec: dict, keep_env: bool = False) -> dict[str, Any]:
    """Validate one pool record. Always returns a result dict (never raises)."""
    iid = rec["instance_id"]
    res: dict[str, Any] = {"instance_id": iid, "repo": rec["repo"], "stage": rec["stage"], "python": rec["python"],
                           "base_commit": rec["base_commit"], "base_date": rec["base_date"], "package": rec["package"],
                           "stage_detail": rec["stage_detail"], "created_at": rec["created_at"],
                           "valid": False, "reason": None, "started": datetime.now(timezone.utc).isoformat()}
    root = envs.task_root(cfg, iid, "validate")
    t_all = time.time()
    try:
        task = load_task(cfg, iid)
        t0 = time.time()
        repo_dir, err = envs.make_workdir(cfg, task, root)
        res["checkout_s"] = round(time.time() - t0, 1)
        if res["checkout_s"] > cfg["validate"].get("max_checkout_s", 150):
            envs.mark_slow(cfg, rec["repo"], res["checkout_s"])
        if repo_dir is None:
            res["reason"] = err.split(":")[0]
            res["detail"] = err
            return res
        btxt = conditions.build_b(cfg, rec["repo"], rec["base_commit"])
        res["b_available"], res["b_chars"] = bool(btxt), len(btxt or "")
        res["real_agent_manifest_at_base"] = conditions.real_agent_manifests_at_base(cfg, rec["repo"], rec["base_commit"])
        res["leakage"] = envs.leakage_checks(repo_dir, rec["base_date"], task["test_patch"])
        lk = res["leakage"]
        if lk["objects_only_after_base"] or not lk["newest_committer_date_le_S"] or not lk["test_patch_applies_cleanly_at_base"]:
            res["reason"] = "leakage_check_failed"
            return res
        b = envs.build_env(cfg, task, root, repo_dir)
        res["env"] = {k: b[k] for k in ("ok", "seconds", "reason", "n_steps")}
        res["env_build_s"] = b["seconds"]
        res["venv_mb"] = round(du_gb(root / ".v") * 1024, 1)
        if not b["ok"]:
            res["reason"] = "env:" + b["reason"]
            res["detail"] = b["log_tail"]
            return res
        f2p, p2p = list(task["FAIL_TO_PASS"]), list(task["PASS_TO_PASS"])
        ok, e = envs.apply_patch(repo_dir, task["test_patch"], "test")
        if not ok:
            res["reason"] = "test_patch_apply_failed"
            res["detail"] = e
            return res
        base = envs.run_tests(cfg, task, root, repo_dir, f2p + p2p)
        res["base_test_s"] = base["seconds"]
        if base["timeout"] or not base["statuses"]:
            res["reason"] = "base_tests_timeout" if base["timeout"] else "base_tests_no_output"
            res["detail"] = base["tail"][-500:]
            return res
        jb = envs.judge_tests(base["statuses"], f2p, p2p)
        res["base"] = {k: jb[k] for k in ("f2p_pass", "f2p_total", "p2p_pass", "p2p_total")}
        if jb["f2p_pass"] > 0:
            res["reason"] = "f2p_passes_at_base"
            return res
        ok, e = envs.apply_patch(repo_dir, task["patch"], "gold")
        if not ok:
            res["reason"] = "gold_patch_apply_failed"
            res["detail"] = e
            return res
        golds = []
        for _ in range(int(cfg.get("gold_repeats", 3))):  # plan 2.1: repeat the gold run, drop flaky tests
            g = envs.run_tests(cfg, task, root, repo_dir, f2p + p2p)
            golds.append(g)
            if g["timeout"]:
                res["reason"] = "gold_tests_timeout"
                return res
        res["gold_test_s"] = round(sum(g["seconds"] for g in golds) / len(golds), 1)
        res["gold_repeats"] = len(golds)
        jg = envs.judge_tests(golds[0]["statuses"], f2p, p2p)
        res["gold"] = {k: jg[k] for k in ("f2p_pass", "f2p_total", "p2p_pass", "p2p_total")}
        f2p_ok = [all(g["statuses"].get(i) == "PASSED" for g in golds) for i in f2p]
        if not all(f2p_ok):
            flaky = any(any(g["statuses"].get(i) == "PASSED" for g in golds) for i, ok in zip(f2p, f2p_ok) if not ok)
            res["reason"] = "f2p_flaky_after_gold" if flaky else "f2p_fail_after_gold"
            res["detail"] = str([i for i, ok in zip(f2p, f2p_ok) if not ok][:5])
            return res
        eff = [i for i in p2p if base["statuses"].get(i) == "PASSED" and all(g["statuses"].get(i) == "PASSED" for g in golds)]
        res["p2p_original"], res["p2p_effective_n"] = len(p2p), len(eff)
        res["p2p_flaky_n"] = sum(1 for i in p2p if len({g["statuses"].get(i) for g in golds}) > 1)
        if p2p and len(eff) < MIN_P2P_KEEP * len(p2p):
            res["reason"] = "p2p_unstable_env"
            return res
        res["valid"] = True
        res["gold_nontest_changed_lines"] = metrics.diff_size(task["patch"], set(metrics.split_diff(task["test_patch"])))["total"]
        res["p2p_effective"] = eff
        res["f2p"] = f2p
        return res
    except Exception as exc:  # noqa: BLE001
        logger.exception("validate %s crashed", iid)
        res["reason"] = "harness_exception"
        res["detail"] = repr(exc)[:300]
        return res
    finally:
        res["total_s"] = round(time.time() - t_all, 1)
        if not keep_env:
            envs.cleanup(root)


def aggregate(cfg: dict) -> dict[str, Any]:
    """Merge checkpoints into results/real_v2/wp5/validation.json with before/after stage counts."""
    pool = read_json(rpath(cfg, "output_dir") / "pool.json")
    stages = cfg["pool"]["stages"]
    results = []
    for f in sorted(ckpt_dir(cfg).glob("*.json")):
        r = read_json(f)
        if r:
            results.append(r)
    by_id = {r["instance_id"]: r for r in results}
    pool_counts = Counter(t["stage"] for t in pool["tasks"])
    attempted = Counter(r["stage"] for r in results)
    valid = Counter(r["stage"] for r in results if r["valid"])
    fail_reason: dict[str, Counter] = defaultdict(Counter)
    for r in results:
        if not r["valid"]:
            fail_reason[r["stage"]][r["reason"]] += 1
    times = [r["env_build_s"] for r in results if "env_build_s" in r]
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pool_stage_counts_before_validation": {s: pool_counts.get(s, 0) for s in stages},
        "attempted_per_stage": {s: attempted.get(s, 0) for s in stages},
        "validated_per_stage": {s: valid.get(s, 0) for s in stages},
        "validated_repos_per_stage": {s: len({r["repo"] for r in results if r["valid"] and r["stage"] == s}) for s in stages},
        "validation_rate": {s: round(valid.get(s, 0) / attempted[s], 3) if attempted.get(s) else None for s in stages},
        "failures_by_reason": dict(sum((c for c in fail_reason.values()), Counter())),
        "failures_by_reason_per_stage": {s: dict(fail_reason[s]) for s in stages},
        "env_build_seconds": {"median": sorted(times)[len(times) // 2] if times else None,
                              "max": max(times) if times else None, "n": len(times)},
        "venv_mb_median": (sorted(r["venv_mb"] for r in results if "venv_mb" in r) or [None])[
            len([r for r in results if "venv_mb" in r]) // 2],
        "mean_total_s_per_task": round(sum(r["total_s"] for r in results) / len(results), 1) if results else None,
        "n_validated": sum(valid.values()), "n_attempted": len(results),
    }
    write_json(rpath(cfg, "output_dir") / "validation.json", {"summary": summary, "results": results})
    write_json(rpath(cfg, "output_dir") / "validation_summary.json", summary)
    return summary


def validate_pool(cfg: dict, limit: Optional[int] = None, stage: Optional[str] = None,
                  workers: Optional[int] = None, keep_env: bool = False, ids: Optional[list[str]] = None,
                  dev: bool = False) -> None:
    pool = read_json(rpath(cfg, "output_dir") / ("dev_pool.json" if dev else "pool.json"))
    stages = ["dev"] if dev else ([stage] if stage else cfg["pool"]["stages"])
    targets = cfg["validate"]["per_stage_target"]
    ck = ckpt_dir(cfg)
    rng = random.Random(cfg["seed"] + 1)
    done_ids = {f.stem for f in ck.glob("*.json")}
    valid_n: Counter = Counter()
    for f in ck.glob("*.json"):
        r = read_json(f)
        if r and r["valid"]:
            valid_n[r["stage"]] += 1

    queues: dict[str, list[dict]] = {}
    for s in stages:
        recs = [t for t in pool["tasks"] if t["stage"] == s and safe_id(t["instance_id"]) not in done_ids]
        by_repo: dict[str, list[dict]] = defaultdict(list)
        for t in recs:
            by_repo[t["repo"]].append(t)
        repos = sorted(by_repo)
        rng.shuffle(repos)
        for v in by_repo.values():
            rng.shuffle(v)
        order: list[dict] = []
        while any(by_repo.values()):  # round-robin over repos: one task per repo per round
            for r in repos:
                if by_repo[r]:
                    order.append(by_repo[r].pop())
        queues[s] = order
    if ids:
        sel = [t for t in pool["tasks"] if t["instance_id"] in set(ids)]
        queues = {"_ids": sel}
        stages = ["_ids"]

    lock = threading.Lock()
    started = [0]
    guard = DiskGuard(cfg)
    rr = [0]

    def next_task() -> Optional[dict]:
        with lock:
            if limit is not None and started[0] >= limit:
                return None
            for _ in range(len(stages)):  # round-robin across stages
                s = stages[rr[0] % len(stages)]
                rr[0] += 1
                q = queues[s]
                if s != "_ids" and valid_n[s] >= targets.get(s, 10**9):
                    continue
                if q:
                    started[0] += 1
                    return q.pop(0)
            return None

    def worker() -> None:
        while True:
            if not guard.ok():
                logger.error("work_dir over disk cap (%.1f GB); worker stopping", guard.usage_gb())
                return
            t = next_task()
            if t is None:
                return
            wait_for_resources(cfg, "validate")
            logger.info("validate %s [%s] (%d valid so far in stage)", t["instance_id"], t["stage"], valid_n[t["stage"]])
            r = validate_one(cfg, t, keep_env=keep_env)
            write_json(ck / f"{safe_id(t['instance_id'])}.json", r)
            with lock:
                if r["valid"]:
                    valid_n[t["stage"]] += 1
            logger.info("  -> %s %s (%.0fs, env %.0fs)", "VALID" if r["valid"] else "invalid", r["reason"] or "",
                        r["total_s"], r.get("env_build_s", 0))

    n = workers or cfg["limits"]["max_workers"]
    n = min(n, cfg["limits"]["max_workers"])
    with ThreadPoolExecutor(n) as ex:
        futs = [ex.submit(worker) for _ in range(n)]
        for f in futs:
            f.result()
    s = aggregate(cfg)
    logger.info("validation summary: %s", s["validated_per_stage"])
