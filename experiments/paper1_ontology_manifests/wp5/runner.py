"""WP5 run stage: task x condition x model x run, checkpointed per unit, at most N workers.

Used by Paper 1 (JSEP rebuild), WP5.

One worker owns one task at a time: it builds the task env once (uv venv from install_config), then runs all
pending units of that task sequentially (the editable install is tied to that checkout), evaluates each patch
immediately, and removes the env when the task is done. A unit is skipped on re-run when its JSON exists.
Trajectories are stored gzipped; patches too.

Usage:
    python experiments/paper1_ontology_manifests/run_wp5.py run --pilot
    python experiments/paper1_ontology_manifests/run_wp5.py run --tasks tasks.json --conditions A B C D --runs 2
"""

from __future__ import annotations

import gzip
import json
import logging
import random
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from . import agent as agent_mod
from . import conditions, envs, evaluate
from .common import (DiskGuard, load_task, read_json, rm_tree, rpath, safe_id, wait_for_resources, work_dir,
                     write_gz, write_json)
from .validate import ckpt_dir

logger = logging.getLogger("wp5.runner")


def load_valid(cfg: dict) -> dict[str, dict]:
    out = {}
    for f in ckpt_dir(cfg).glob("*.json"):
        r = read_json(f)
        if r and r.get("valid"):
            out[r["instance_id"]] = r
    return out


def model_short(name: str) -> str:
    return name.split("/")[-1]


def select_pilot(cfg: dict, valid: dict[str, dict], conds: list[str], exclude: frozenset = frozenset()) -> list[str]:
    """Deterministic spread over stages; one task per repo; B-available when B is a pilot condition."""
    pc = cfg["pilot"]
    rng = random.Random(cfg["seed"] + 7)
    quota = {"initial_development": 3, "evolution": 3, "servicing": 3, "phase_out": 1}
    cands: dict[str, list[dict]] = defaultdict(list)
    for r in valid.values():
        if r["instance_id"] in exclude or r["stage"] == "dev":
            continue
        if "B" in conds and not r.get("b_available"):
            continue
        if r.get("total_s", 1e9) > 400:  # keep the pilot cheap
            continue
        cands[r["stage"]].append(r)
    chosen: list[dict] = []
    used_repos: set[str] = set()
    for s, q in quota.items():
        pool = sorted(cands[s], key=lambda r: r["instance_id"])
        rng.shuffle(pool)
        for r in pool:
            if sum(1 for c in chosen if c["stage"] == s) >= q:
                break
            if r["repo"] not in used_repos:
                chosen.append(r)
                used_repos.add(r["repo"])
    rest = [r for s in cands for r in cands[s] if r not in chosen and r["repo"] not in used_repos]
    rng.shuffle(rest)
    while len(chosen) < pc["n_tasks"] and rest:
        r = rest.pop()
        if r["repo"] not in used_repos:
            chosen.append(r)
            used_repos.add(r["repo"])
    return [r["instance_id"] for r in chosen[: pc["n_tasks"]]]


def ensure_env(cfg: dict, task: dict, kind: str) -> tuple[Optional[Path], Optional[Path], str]:
    root = envs.task_root(cfg, task["instance_id"], kind)
    rm_tree(root)
    repo_dir, err = envs.make_workdir(cfg, task, root)
    if repo_dir is None:
        return root, None, err
    b = envs.build_env(cfg, task, root, repo_dir)
    if not b["ok"]:
        return root, None, "env:" + b["reason"]
    return root, repo_dir, ""


def release_env(root: Optional[Path]) -> None:
    if root is not None:
        rm_tree(root)


def schedule(cfg: dict, valid: dict[str, dict], ids: list[str], conds: list[str], n_runs: int,
             models: list[dict]) -> list[tuple[str, list[tuple[str, dict, int]]]]:
    """Seeded order (plan 2.3): tasks interleaved round-robin over stage-wise permutations; runs of a task shuffled."""
    rng = random.Random(cfg["seed"])
    by_stage: dict[str, list[str]] = defaultdict(list)
    for t in sorted(ids):
        by_stage[valid[t]["stage"]].append(t)
    for v in by_stage.values():
        rng.shuffle(v)
    order: list[str] = []
    while any(by_stage.values()):
        for st in sorted(by_stage):
            if by_stage[st]:
                order.append(by_stage[st].pop(0))
    out = []
    for t in order:
        runs = [(c, m, r) for r in range(1, n_runs + 1) for c in conds for m in models]
        rng.shuffle(runs)
        out.append((t, runs))
    return out


def is_infra(res: dict[str, Any]) -> bool:
    """Infra failure by error type alone (plan 5): no usable trajectory / API or harness exception."""
    return res.get("exit_status") not in evaluate.STATE_MAP or res.get("steps", 0) == 0


def run_all(cfg: dict, pilot: bool = False, tasks_file: Optional[str] = None, conditions_: Optional[list[str]] = None,
            runs: Optional[int] = None, models: Optional[list[str]] = None, workers: Optional[int] = None,
            select_only: bool = False) -> None:
    conds = conditions_ or (cfg["pilot"]["conditions"] if pilot else list(cfg["conditions"]))
    n_runs = runs or (cfg["pilot"]["runs"] if pilot else 2)
    base = rpath(cfg, "pilot_dir" if pilot else "output_dir")
    if not pilot:
        base = base / "runs"
        base.mkdir(parents=True, exist_ok=True)
    valid = load_valid(cfg)
    if tasks_file:
        ids = json.loads(Path(tasks_file).read_text())
        if isinstance(ids, dict):  # pilot_tasks.json or wp5_tasks.json
            ids = ids["task_ids"] if "task_ids" in ids else [t["instance_id"] for t in ids["tasks"]
                                                              if not t.get("excluded") and not t.get("dev")]
    elif pilot and (base / "pilot_tasks.json").exists():
        ids = read_json(base / "pilot_tasks.json")["task_ids"]
    elif pilot:
        prev = read_json(rpath({**cfg, "pilot_dir": "experiments/paper1_ontology_manifests/results/real_v2/wp5_pilot"}, "pilot_dir") / "pilot_tasks.json", {"task_ids": []})
        excl = frozenset(prev["task_ids"]) if base.name != "wp5_pilot" else frozenset()
        ids = select_pilot(cfg, valid, conds, excl)
        write_json(base / "pilot_tasks.json", {"task_ids": ids, "conditions": conds, "seed": cfg["seed"],
                                               "stages": {i: valid[i]["stage"] for i in ids}})
    else:
        raise SystemExit("non-pilot runs need --tasks (the frozen wp5_tasks.json id list) and the run freeze")
    logger.info("tasks: %d, conditions %s, runs %d", len(ids), conds, n_runs)
    if select_only:
        return
    mlist = [m for m in cfg["agent"]["models"] if not models or any(x in m["name"] for x in models)]
    ud = base / "units"
    ud.mkdir(parents=True, exist_ok=True)
    guard = DiskGuard(cfg)
    meta_p = base / "run_meta.json"
    meta = read_json(meta_p, {"sessions": []})
    meta["sessions"].append({"start": datetime.now(timezone.utc).isoformat(), "workers": workers or cfg["limits"]["max_workers"],
                             "conditions": conds, "runs": n_runs, "models": [m["name"] for m in mlist],
                             "temperature": cfg["agent"]["temperature"], "top_p": cfg["agent"]["top_p"],
                             "key_pool_env_names": cfg["agent"].get("key_pool")})
    write_json(meta_p, meta)
    sched = schedule(cfg, valid, ids, conds, n_runs, mlist)
    order_of = {}
    k = 0
    for t, rs in sched:
        for c, m, r in rs:
            order_of[f"{safe_id(t)}__{c}__{model_short(m['name'])}__r{r}"] = k
            k += 1

    def work(item: tuple[str, list]) -> None:
        tid, all_units = item
        todo = [(c, m, r) for c, m, r in all_units
                if not (ud / f"{safe_id(tid)}__{c}__{model_short(m['name'])}__r{r}.json").exists()]
        if not todo:
            return
        if not guard.ok():
            logger.error("disk cap reached; skipping %s", tid)
            return
        wait_for_resources(cfg, "run " + tid)
        vrec = valid[tid]
        task = load_task(cfg, tid)
        task["instance_id"] = tid
        t_env = time.time()
        root, repo_dir, err = ensure_env(cfg, task, "run")
        env_s = round(time.time() - t_env, 1)
        try:
            for c, m, r in todo:
                uid = f"{safe_id(tid)}__{c}__{model_short(m['name'])}__r{r}"
                u: dict[str, Any] = {"unit_id": uid, "task_id": tid, "repo": task["repo"], "stage": vrec["stage"],
                                     "condition": c, "model": m["name"], "run": r, "order": order_of[uid],
                                     "env_build_s": env_s,
                                     "real_agent_manifest_at_base": vrec.get("real_agent_manifest_at_base"),
                                     "started": datetime.now(timezone.utc).isoformat()}
                if repo_dir is None:
                    u.update(status="env_failed", reason=err)
                    write_json(ud / f"{uid}.json", u)
                    continue
                agent_mod.clean_repo(repo_dir)
                ct = conditions.condition_text(cfg, c, tid, task["repo"], task["base_commit"])
                u["condition_meta"] = ct["meta"]
                u["condition_available"] = ct["available"]
                if not ct["available"]:
                    u.update(status="skipped", reason=f"{c}_unavailable")
                    write_json(ud / f"{uid}.json", u)
                    continue
                traj = base / "trajectories" / f"{uid}.traj.json"
                res: dict[str, Any] = {}
                for attempt in range(1, cfg["infra_retries"] + 2):
                    logger.info("RUN %s (attempt %d)", uid, attempt)
                    res = agent_mod.run_agent(cfg, task, m, ct["text"], root, repo_dir, traj)
                    u["retries"] = attempt - 1
                    if not is_infra(res) or attempt == cfg["infra_retries"] + 1:
                        break
                    logger.warning("infra failure on %s (%s); retrying from scratch", uid, res.get("exit_status"))
                    agent_mod.clean_repo(repo_dir)
                diff = res.pop("diff")
                text = res.pop("assistant_text", "")
                if traj.exists():  # gzip the raw trajectory
                    write_gz(traj.with_name(traj.name + ".gz"), traj.read_text())
                    traj.unlink()
                write_gz(base / "patches" / f"{uid}.diff.gz", diff)
                u.update(res)
                u["uptake"] = evaluate.uptake(c, text)
                infra = is_infra(res)
                try:
                    if infra:
                        u["eval"] = {"resolved": False, "reason": "infra_failure", "outcomes": None}
                    else:
                        u["eval"] = evaluate.evaluate_diff(cfg, task, vrec, diff, root, repo_dir, res["steps"],
                                                           res["exit_status"] == "LimitsExceeded")
                except Exception as exc:  # noqa: BLE001
                    logger.exception("eval %s", uid)
                    u["eval"] = {"resolved": False, "reason": "harness_exception", "detail": repr(exc)[:200]}
                u["status"] = "done"
                u["finished"] = datetime.now(timezone.utc).isoformat()
                write_json(ud / f"{uid}.json", u)
                logger.info("DONE %s exit=%s steps=%s wall=%.0fs retries=%s", uid, res["exit_status"], res["steps"],
                            res["wall_s"], u["retries"])  # no outcome in the log (plan 11.3)
        finally:
            release_env(root)

    n = min(workers or cfg["limits"]["max_workers"], cfg["limits"]["max_workers"])
    with ThreadPoolExecutor(n) as ex:
        list(ex.map(work, sched))
    meta = read_json(meta_p)
    meta["sessions"][-1]["end"] = datetime.now(timezone.utc).isoformat()
    write_json(meta_p, meta)
    evaluate.write_ledgers(cfg, pilot)
