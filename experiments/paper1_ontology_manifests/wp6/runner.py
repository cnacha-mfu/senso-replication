"""WP6 run stage: task x condition x model x replicate, a venv reset before every run, at most 4 workers.

Used by Paper 1 (JSEP rebuild), WP6; design papers/paper1/wp6-harm-design.md sections 5, 7 and 8 and the coordinator decision
"the task virtual environment is reset before every run".

Thin wrapper over the WP5 harness: the same `agent.run_agent` (mini-SWE-agent text mode, key pool), `conditions.condition_text`
(the manifest is read from `<out>/manifests/<task>/<cond>.md` and injected into the prompt only), `evaluate.evaluate_diff`
(`resolved`) and the WP5 schedule / environment builder. What differs from `wp5.runner`:

  * one pristine copy of the task venv is kept (`.v_golden`) and restored before every run, and again before the evaluation of
    the run's patch, so a package that an agent installed never reaches another run or the test run (WP5 deviation 14);
  * `uv pip freeze` is hashed before and after each agent episode (Y7, venv mutated);
  * the condition list is A, T, F_R, F_I and the output directory comes from `configs/wp6.yaml`.

A unit is skipped on re-run when its JSON exists. Trajectories and patches are gzipped, as in WP5.

Usage:
    python experiments/paper1_ontology_manifests/run_wp6.py run --pilot --ids ID ID --replicates 1
    python experiments/paper1_ontology_manifests/run_wp6.py run --replicates 2            # the full experiment (after the run freeze)
"""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from ..wp5 import agent as agent_mod
from ..wp5 import conditions, envs, evaluate
from ..wp5.common import UV, DiskGuard, load_task, read_json, rm_tree, run, safe_id, uv_env, wait_for_resources, write_gz, write_json
from ..wp5.runner import ensure_env, is_infra, load_valid, release_env, schedule
from . import common as C

logger = logging.getLogger("wp6.runner")


# ----------------------------------------------------------------------------
# Venv reset and freeze hash
# ----------------------------------------------------------------------------
def snapshot_venv(root: Path) -> None:
    """Keep a pristine copy of the freshly built venv (same absolute location after a restore, so shebangs stay valid)."""
    g = root / ".v_golden"
    rm_tree(g)
    shutil.copytree(root / ".v", g, symlinks=True)


def reset_venv(root: Path) -> float:
    """Restore .v from the pristine copy and clear the agent's HOME (pip configs, caches). Returns seconds."""
    t0 = time.time()
    rm_tree(root / ".v")
    shutil.copytree(root / ".v_golden", root / ".v", symlinks=True)
    rm_tree(root / "home")
    (root / "home").mkdir(parents=True, exist_ok=True)
    return round(time.time() - t0, 2)


def kill_strays(root: Path) -> int:
    """SIGKILL every process (other than this one) whose cwd, executable, command line or environment points under the task root.

    mini-swe-agent kills a command's process group only on timeout, so anything an agent left running in the
    background (`cmd &`, a test runner's worker pool, a server) outlived its step and its run. On 2026-10-13 such
    leftovers built up to ~550 processes and the VM ran out of memory (WP6 deviation 24). Called after every agent
    episode and after every evaluation; the agent's behaviour within a run is unchanged.
    """
    import os
    import signal
    r = str(root.resolve())
    me, n = os.getpid(), 0
    for p in Path("/proc").iterdir():
        if not p.name.isdigit() or int(p.name) == me:
            continue
        try:
            links = [os.readlink(p / x) for x in ("cwd", "exe")]
            cmd = (p / "cmdline").read_bytes().replace(b"\0", b" ").decode("utf-8", "replace") + " "
            env = (p / "environ").read_bytes().decode("utf-8", "replace")   # agent commands carry PATH=<root>/.v/bin:...
            hit = any(x == r or x.startswith(r + "/") for x in links) or (r + "/") in cmd or (r + " ") in cmd \
                or (r + "/") in env
            if hit:
                os.kill(int(p.name), signal.SIGKILL)
                n += 1
        except (OSError, ValueError):
            continue
    if n:
        logger.info("killed %d leftover processes under %s", n, root.name)
    return n


def freeze_hash(cfg: dict, root: Path) -> str:
    """sha256 of the sorted `uv pip freeze` of the task venv."""
    rc, out = run([UV, "pip", "freeze", "--python", str(root / ".v/bin/python")], env=uv_env(cfg), timeout=120)
    lines = sorted(ln.strip() for ln in out.splitlines() if ln.strip() and not ln.startswith("Using Python"))
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


# ----------------------------------------------------------------------------
# Run
# ----------------------------------------------------------------------------
def run_dirs(cfg: dict, pilot: bool) -> tuple[Path, Path]:
    """(run_cfg with output_dir pointing at the manifests' parent, base dir for units / trajectories / patches)."""
    out = C.out_dir(cfg, pilot)
    run_cfg = {**cfg, "output_dir": str(out)}
    base = out if pilot else out / "runs"
    base.mkdir(parents=True, exist_ok=True)
    return run_cfg, base


def run_all(cfg: dict, pilot: bool = False, ids: Optional[list[str]] = None, conditions_: Optional[list[str]] = None,
            replicates: Optional[int] = None, models: Optional[list[str]] = None, workers: Optional[int] = None) -> None:
    conds = conditions_ or list(C.CONDITIONS)
    n_runs = replicates or cfg["replicates"]
    rcfg, base = run_dirs(cfg, pilot)
    valid = load_valid(cfg)
    ids = ids or [t["instance_id"] for t in C.wp5_tasks(cfg)]
    missing = [i for i in ids if i not in valid]
    if missing:
        raise SystemExit(f"tasks without a validation record: {missing}")
    for t in ids:
        for c in conds:
            if cfg["conditions"][c]["manifest"] and not conditions.manifest_path(rcfg, t, c).is_file():
                raise SystemExit(f"manifest {c} missing for {t}: run `generate` first")
    mlist = [m for m in cfg["agent"]["models"] if not models or any(x in m["name"] for x in models)]
    ud = base / "units"
    ud.mkdir(parents=True, exist_ok=True)
    guard = DiskGuard(cfg)
    meta_p = base / "run_meta.json"
    meta = read_json(meta_p, {"sessions": []})
    n = min(workers or cfg["limits"]["max_workers"], cfg["limits"]["max_workers"])
    meta["sessions"].append({"start": datetime.now(timezone.utc).isoformat(), "workers": n, "conditions": conds, "runs": n_runs,
                             "models": [m["name"] for m in mlist], "n_tasks": len(ids), "temperature": cfg["agent"]["temperature"],
                             "top_p": cfg["agent"]["top_p"], "step_limit": cfg["agent"]["step_limit"],
                             "key_pool_env_names": cfg["agent"].get("key_pool"), "seed": cfg["seed"]})
    write_json(meta_p, meta)
    logger.info("tasks: %d, conditions %s, replicates %d, models %s, %d workers -> %s", len(ids), conds, n_runs,
                [m["name"] for m in mlist], n, base)
    sched = schedule(cfg, valid, ids, conds, n_runs, mlist)
    order_of: dict[str, int] = {}
    k = 0
    for t, rs in sched:
        for c, m, r in rs:
            order_of[f"{safe_id(t)}__{c}__{C.short_model(m['name'])}__r{r}"] = k
            k += 1

    def work(item: tuple[str, list]) -> None:
        tid, all_units = item
        todo = [(c, m, r) for c, m, r in all_units
                if not (ud / f"{safe_id(tid)}__{c}__{C.short_model(m['name'])}__r{r}.json").exists()]
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
        if repo_dir is not None:
            snapshot_venv(root)
        env_s = round(time.time() - t_env, 1)
        try:
            for c, m, r in todo:
                uid = f"{safe_id(tid)}__{c}__{C.short_model(m['name'])}__r{r}"
                u: dict[str, Any] = {"unit_id": uid, "task_id": tid, "repo": task["repo"], "stage": vrec["stage"],
                                     "condition": c, "model": m["name"], "run": r, "order": order_of[uid],
                                     "env_build_s": env_s, "started": datetime.now(timezone.utc).isoformat()}
                if repo_dir is None:
                    u.update(status="env_failed", reason=err)
                    write_json(ud / f"{uid}.json", u)
                    continue
                ct = conditions.condition_text(rcfg, c, tid, task["repo"], task["base_commit"])
                u["condition_meta"], u["condition_available"] = ct["meta"], ct["available"]
                if not ct["available"]:
                    u.update(status="skipped", reason=f"{c}_unavailable")
                    write_json(ud / f"{uid}.json", u)
                    continue
                traj = base / "trajectories" / f"{uid}.traj.json"
                res: dict[str, Any] = {}
                for attempt in range(1, cfg["infra_retries"] + 2):
                    u["venv_reset_s"] = reset_venv(root)
                    agent_mod.clean_repo(repo_dir)
                    h0 = freeze_hash(cfg, root)
                    logger.info("RUN %s (attempt %d)", uid, attempt)
                    res = agent_mod.run_agent(cfg, task, m, ct["text"], root, repo_dir, traj)
                    u["stray_procs_killed"] = kill_strays(root)
                    h1 = freeze_hash(cfg, root)
                    u.update(retries=attempt - 1, venv_hash_before=h0[:16], venv_hash_after=h1[:16], venv_mutated=h0 != h1)
                    if not is_infra(res) or attempt == cfg["infra_retries"] + 1:
                        break
                    logger.warning("infra failure on %s (%s); retrying from scratch", uid, res.get("exit_status"))
                diff = res.pop("diff")
                text = res.pop("assistant_text", "")
                if traj.exists():
                    write_gz(traj.with_name(traj.name + ".gz"), traj.read_text())
                    traj.unlink()
                write_gz(base / "patches" / f"{uid}.diff.gz", diff)
                u.update(res)
                u["uptake"] = evaluate.uptake(c, text)
                try:
                    if is_infra(res):
                        u["eval"] = {"resolved": False, "reason": "infra_failure", "outcomes": None}
                    else:
                        reset_venv(root)    # evaluate the patch in the pristine environment, never in the agent's
                        u["eval"] = evaluate.evaluate_diff(cfg, task, vrec, diff, root, repo_dir, res["steps"],
                                                           res["exit_status"] == "LimitsExceeded")
                except Exception as exc:  # noqa: BLE001
                    logger.exception("eval %s", uid)
                    u["eval"] = {"resolved": False, "reason": "harness_exception", "detail": repr(exc)[:200]}
                kill_strays(root)
                u["status"] = "done"
                u["finished"] = datetime.now(timezone.utc).isoformat()
                write_json(ud / f"{uid}.json", u)
                logger.info("DONE %s exit=%s steps=%s wall=%.0fs retries=%s mutated=%s", uid, res["exit_status"], res["steps"],
                            res["wall_s"], u["retries"], u["venv_mutated"])   # no outcome in the log (design 8, no peeking)
        finally:
            if root is not None:
                kill_strays(root)
            release_env(root)

    with ThreadPoolExecutor(n) as ex:
        list(ex.map(work, sched))
    meta = read_json(meta_p)
    meta["sessions"][-1]["end"] = datetime.now(timezone.utc).isoformat()
    write_json(meta_p, meta)
    from . import outcomes
    outcomes.write_outcomes(cfg, pilot)
