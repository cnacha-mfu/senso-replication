"""WP5 evaluation of agent patches: measured outcomes only, no LLM judging (plan section 4).

Used by Paper 1 (JSEP rebuild), WP5.

resolved = every FAIL_TO_PASS test and every validated PASS_TO_PASS test passes, with the agent's patch applied
on the base commit and the task's test patch applied on top (agent edits to test-patch files are discarded).
Secondary outcomes Y0-Y6 come from `metrics.outcomes`. `run` evaluates each unit right after the agent finished
(the task env is alive). `evaluate` re-evaluates any done unit that has no evaluation (rebuilding the env) and
rewrites the two ledgers `wp5_runs.jsonl` and `wp5_outcomes.jsonl` (formats: run_wp5_analysis.py docstring)
from the unit JSONs. Nothing here aggregates outcomes by condition.

Usage:
    python experiments/paper1_ontology_manifests/run_wp5.py evaluate --pilot
"""

from __future__ import annotations

import gzip
import json
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional

import yaml

from . import agent as agent_mod
from . import envs, metrics
from .common import PROJECT_ROOT, load_task, read_json, rpath, write_json

logger = logging.getLogger("wp5.evaluate")

STATE_MAP = {"Submitted": "Submitted", "LimitsExceeded": "LimitsExceeded", "TimeExceeded": "WallTimeExceeded",
             "WallTimeAbort": "WallTimeExceeded", "RepeatedFormatError": "RepeatedFormatError"}
STAGE_CODE = {"initial_development": "ID", "evolution": "EVO", "servicing": "SERV", "phase_out": "PO"}


def evaluate_diff(cfg: dict, task: dict, vrec: dict, diff: str, root: Path, repo_dir: Path, steps: int = 0,
                  hit_step_limit: bool = False) -> dict[str, Any]:
    """Apply the agent diff on a clean base checkout, compute Y0-Y6, then run F2P + effective P2P."""
    out: dict[str, Any] = {}
    tp = set(metrics.split_diff(task["test_patch"]))
    diff = metrics.filter_diff(diff, tp)
    agent_mod.clean_repo(repo_dir)
    if not diff.strip():
        out.update(resolved=False, reason="empty_patch")
        out["outcomes"] = metrics.outcomes(cfg, task, vrec, "", repo_dir, steps, hit_step_limit)
        return out
    ok, err = envs.apply_patch(repo_dir, diff, "agent")
    if not ok:
        out.update(resolved=False, reason="patch_apply_failed", detail=err)
        o = metrics.outcomes(cfg, task, vrec, "", repo_dir, steps, hit_step_limit)
        o["Y0"] = 1  # a diff was produced, it just does not apply (plan 4.2: not an infra failure)
        out["outcomes"] = o
        return out
    try:
        out["outcomes"] = metrics.outcomes(cfg, task, vrec, diff, repo_dir, steps, hit_step_limit)
    except Exception as exc:  # noqa: BLE001
        logger.exception("outcomes %s", task["instance_id"])
        out["outcomes"] = None
        out["outcomes_error"] = repr(exc)[:200]
    ok, err = envs.apply_patch(repo_dir, task["test_patch"], "test")
    if not ok:
        out.update(resolved=False, reason="test_patch_conflict", detail=err)
        return out
    f2p, p2p = list(task["FAIL_TO_PASS"]), list(vrec["p2p_effective"])
    t = envs.run_tests(cfg, task, root, repo_dir, f2p + p2p)
    j = envs.judge_tests(t["statuses"], f2p, p2p)
    out.update({k: j[k] for k in ("f2p_pass", "f2p_total", "p2p_pass", "p2p_total", "f2p_all_pass", "p2p_all_pass")})
    out["resolved"] = bool(j["f2p_all_pass"] and j["p2p_all_pass"])
    out["reason"] = "resolved" if out["resolved"] else ("test_timeout" if t["timeout"] else
                                                        ("f2p_failing" if not j["f2p_all_pass"] else "p2p_broken"))
    out["test_seconds"] = t["seconds"]
    agent_mod.clean_repo(repo_dir)
    return out


def d1_display_names() -> list[str]:
    f = PROJECT_ROOT / "experiments/paper1_ontology_manifests/configs/wp5_manifests.yaml"
    try:
        return [r["display"] for r in yaml.safe_load(f.read_text()).get("phi", [])]
    except Exception:  # noqa: BLE001
        return []


def uptake(cond: str, assistant_text: str) -> dict[str, Any]:
    """Plan 4.4 descriptive manipulation check on the assistant messages."""
    t = assistant_text.lower()
    return {"repo_context": "repository context" in t,
            "label_term": bool(cond == "C" and re.search(r"stable|active|servicing|law ", t)),
            "d1_name": bool(cond == "D" and any(n.lower() in t for n in d1_display_names()))}


def units_dir(cfg: dict, pilot: bool) -> Path:
    base = rpath(cfg, "pilot_dir" if pilot else "output_dir")
    d = base / ("units" if pilot else "runs/units")
    d.mkdir(parents=True, exist_ok=True)
    return d


def state_of(u: dict) -> tuple[str, bool]:
    if u.get("status") == "env_failed":
        return "infra_failure", True
    st = STATE_MAP.get(u.get("exit_status", ""))
    return (st, False) if st else ("infra_failure", True)


def write_ledgers(cfg: dict, pilot: bool) -> dict[str, int]:
    """Rewrite wp5_runs.jsonl and wp5_outcomes.jsonl from the unit JSONs (schedule order, then id)."""
    ud = units_dir(cfg, pilot)
    base = ud.parent if pilot else rpath(cfg, "output_dir")  # full run: ledgers sit next to wp5_tasks.json (plan 12)
    units = [u for u in (read_json(f) for f in sorted(ud.glob("*.json"))) if u and u.get("status") in ("done", "env_failed")]
    units.sort(key=lambda u: (u.get("order", 10**9), u["unit_id"]))
    runs, outs = [], []
    for u in units:
        state, infra = state_of(u)
        runs.append({"run_id": u["unit_id"], "instance_id": u["task_id"], "condition": u["condition"],
                     "model": u["model"], "rep": u["run"], "state": state, "infra_failure": infra,
                     "retries": u.get("retries", 0), "order": u.get("order"), "exit_status": u.get("exit_status"),
                     "prompt_tokens": u.get("prompt_tokens"), "completion_tokens": u.get("completion_tokens"),
                     "steps": u.get("steps"), "wall_s": u.get("wall_s"), "model_id_returned": u.get("model_id_returned"),
                     "api_errors": u.get("api_errors"), "temperature": u.get("temperature"), "top_p": u.get("top_p"),
                     "started": u.get("started"), "finished": u.get("finished"), "manifest_sha256": (u.get("condition_meta") or {}).get("sha256")})
        e = u.get("eval") or {}
        o = e.get("outcomes") or {}
        outs.append({"run_id": u["unit_id"], "resolved": int(bool(e.get("resolved"))), "eval_reason": e.get("reason"),
                     **{k: o.get(k) for k in ("Y0", "Y1", "Y2", "Y3", "Y3_gold", "Y3_excess", "Y3w", "Y4", "Y5", "Y6",
                                              "hit_step_limit")}, "uptake": u.get("uptake")})
    for name, rows in (("wp5_runs.jsonl", runs), ("wp5_outcomes.jsonl", outs)):
        (base / name).write_text("".join(json.dumps(r, default=str) + "\n" for r in rows))
    return {"runs": len(runs), "outcomes": len(outs)}


def evaluate_all(cfg: dict, pilot: bool = False, workers: Optional[int] = None) -> None:
    ud = units_dir(cfg, pilot)
    base = ud.parent
    units = [u for u in (read_json(f) for f in sorted(ud.glob("*.json"))) if u]
    missing = [u for u in units if u.get("status") == "done" and u.get("eval") is None]
    if missing:
        from .runner import ensure_env, load_valid, release_env
        valid = load_valid(cfg)
        by_task: dict[str, list[dict]] = defaultdict(list)
        for u in missing:
            by_task[u["task_id"]].append(u)
        for tid, us in by_task.items():
            task = load_task(cfg, tid)
            root, repo_dir, err = ensure_env(cfg, task, "eval")
            for u in us:
                if repo_dir is None:
                    u["eval"] = {"resolved": False, "reason": "env_rebuild_failed", "detail": err}
                else:
                    p = base / "patches" / f"{u['unit_id']}.diff.gz"
                    diff = gzip.open(p, "rt").read() if p.exists() else ""
                    u["eval"] = evaluate_diff(cfg, task, valid[tid], diff, root, repo_dir, u.get("steps", 0),
                                              u.get("exit_status") == "LimitsExceeded")
                write_json(ud / f"{u['unit_id']}.json", u)
            release_env(root)
    n = write_ledgers(cfg, pilot)
    logger.info("evaluated; ledgers rewritten: %s (%d re-evaluated)", n, len(missing))


def gold_drift(cfg: dict, workers: Optional[int] = None, ids: Optional[list[str]] = None) -> dict[str, Any]:
    """Plan 5: after all runs, re-evaluate the gold patch for every sample task (SA5 only).

    Same path as an agent patch (evaluate_diff with the gold diff). Writes wp5_gold_drift.json next to wp5_tasks.json.
    """
    from concurrent.futures import ThreadPoolExecutor
    from .runner import ensure_env, load_valid, release_env
    base = rpath(cfg, "output_dir")
    tasks = read_json(base / "wp5_tasks.json")["tasks"]
    prev = read_json(base / "wp5_gold_drift.json") if ids else None  # --ids: re-check, keep the earlier attempt
    if ids:
        tasks = [t for t in tasks if t["instance_id"] in ids]
    valid = load_valid(cfg)
    n_workers = min(int(workers or 3), int(cfg.get("limits", {}).get("max_workers", 4)))

    def one(t: dict) -> dict[str, Any]:
        tid = t["instance_id"]
        task = load_task(cfg, tid)
        root, repo_dir, err = ensure_env(cfg, task, "drift")
        try:
            if repo_dir is None:
                return {"instance_id": tid, "gold_pass": False, "reason": "env_rebuild_failed", "detail": err}
            e = evaluate_diff(cfg, task, valid[tid], task["patch"], root, repo_dir)
            return {"instance_id": tid, "gold_pass": bool(e.get("resolved")), "reason": e.get("reason"),
                    **{k: e.get(k) for k in ("f2p_pass", "f2p_total", "p2p_pass", "p2p_total")}}
        except Exception as exc:  # noqa: BLE001
            logger.exception("drift %s", tid)
            return {"instance_id": tid, "gold_pass": False, "reason": "drift_exception", "detail": repr(exc)[:200]}
        finally:
            release_env(root)

    with ThreadPoolExecutor(n_workers) as ex:
        rows = list(ex.map(one, tasks))
    from datetime import datetime, timezone
    if prev:
        new = {r["instance_id"]: r for r in rows}
        rows = [({**new[r["instance_id"]], "attempt1": {k: r[k] for k in r if k != "instance_id"}}
                 if r["instance_id"] in new else r) for r in prev["tasks"]]
    out = {"checked_at": datetime.now(timezone.utc).isoformat(), "n_tasks": len(rows),
           "n_gold_fail": sum(1 for r in rows if not r["gold_pass"]),
           "gold_drift_fail": sorted(r["instance_id"] for r in rows if not r["gold_pass"]), "tasks": rows}
    write_json(base / "wp5_gold_drift.json", out)
    logger.info("gold drift: %d of %d tasks fail", out["n_gold_fail"], len(rows))
    return out
