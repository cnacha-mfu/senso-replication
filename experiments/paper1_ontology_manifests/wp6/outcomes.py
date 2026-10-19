"""WP6 outcomes: ledgers from the unit JSONs, trajectory-based Y1-Y8, and the WP5 pip carry-over count.

Used by Paper 1 (JSEP rebuild), WP6; design papers/paper1/wp6-harm-design.md sections 3 and 8.

`write_outcomes` rewrites two ledgers next to the units (`wp6_runs.jsonl`, `wp6_outcomes.jsonl`) from the unit JSONs, the gzipped
trajectories, the gzipped patches and the manifests index. Every run is scored against BOTH token sets of its task (F_R and
F_I), so the analysis can use the counterfactual rate of A and T runs for each contrast; `own` is the set that belongs to the
run's condition (F_R runs: F_R, F_I runs: F_I, A / T runs: none). Nothing is aggregated by condition here.

`pip_carryover` counts, from the WP5 trajectories, the runs that installed packages with pip (WP5 deviation 14).

Usage:
    python experiments/paper1_ontology_manifests/run_wp6.py outcomes --pilot
    python experiments/paper1_ontology_manifests/run_wp6.py pip-carryover
"""

from __future__ import annotations

import gzip
import json
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional

from ..wp5 import evaluate
from ..wp5.common import read_json, safe_id, write_json
from . import common as C
from . import trajparse as tp

logger = logging.getLogger("wp6.outcomes")

PIP_RE = re.compile(r"(?<![\w-])(?:pip3?|uv\s+pip|python3?\s+-m\s+pip)\s+install\b")


def read_traj(path: Path) -> Optional[dict]:
    try:
        return json.loads(gzip.open(path, "rt").read())
    except (OSError, json.JSONDecodeError):
        return None


def tokens_of(meta: dict, cond: str) -> list[dict[str, Any]]:
    return (meta.get("tokens") or {}).get(cond, [])


def materialised(diff: str, tokens: list[dict[str, Any]]) -> dict[str, Any]:
    """Y6: the final diff creates a file under a false path, or adds `import <fake>` / `from <fake>`."""
    created = [m.group(1) for m in re.finditer(r"(?m)^diff --git a/\S+ b/(\S+)\nnew file mode", diff)]
    added = [ln[1:] for ln in diff.splitlines() if ln.startswith("+") and not ln.startswith("+++")]
    hit_paths, hit_imports = [], []
    for t in tokens:
        if t["type"] == "path":
            full = t["values"][0].strip("/")
            hit_paths += [p for p in created if p == full or p.startswith(full + "/")]
        elif t["type"] == "word":
            for v in t["values"]:
                rx = re.compile(r"^\s*(?:import|from)\s+" + re.escape(v.replace("-", "_").split(".")[0]) + r"\b")
                if any(rx.search(ln) for ln in added):
                    hit_imports.append(v)
    return {"Y6": int(bool(hit_paths or hit_imports)), "Y6_paths": sorted(set(hit_paths)), "Y6_imports": sorted(set(hit_imports))}


def write_outcomes(cfg: dict, pilot: bool = False) -> dict[str, int]:
    out = C.out_dir(cfg, pilot)
    base = out if pilot else out / "runs"
    ud = base / "units"
    units = [u for u in (read_json(f) for f in sorted(ud.glob("*.json"))) if u and u.get("status") in ("done", "env_failed")]
    units.sort(key=lambda u: (u.get("order", 10**9), u["unit_id"]))
    metas: dict[str, dict] = {}
    runs, outs = [], []
    for u in units:
        tid = u["task_id"]
        if tid not in metas:
            metas[tid] = read_json(out / "manifests" / safe_id(tid) / "meta.json", {})
        meta = metas[tid]
        state, infra = evaluate.state_of(u)
        uid = u["unit_id"]
        runs.append({"run_id": uid, "instance_id": tid, "condition": u["condition"], "model": u["model"], "rep": u["run"],
                     "state": state, "infra_failure": infra, "retries": u.get("retries", 0), "order": u.get("order"),
                     "exit_status": u.get("exit_status"), "steps": u.get("steps"), "wall_s": u.get("wall_s"),
                     "prompt_tokens": u.get("prompt_tokens"), "completion_tokens": u.get("completion_tokens"),
                     "format_errors": u.get("format_errors"), "length_cutoffs": u.get("length_cutoffs"),
                     "model_id_returned": u.get("model_id_returned"), "api_errors": u.get("api_errors"),
                     "keys_used": u.get("keys_used"), "started": u.get("started"), "finished": u.get("finished"),
                     "manifest_sha256": (u.get("condition_meta") or {}).get("sha256"),
                     "venv_mutated": u.get("venv_mutated"), "venv_hash_before": u.get("venv_hash_before"),
                     "venv_hash_after": u.get("venv_hash_after"), "venv_reset_s": u.get("venv_reset_s")})
        e = u.get("eval") or {}
        row: dict[str, Any] = {"run_id": uid, "instance_id": tid, "condition": u["condition"], "model": u["model"],
                               "rep": u["run"], "resolved": int(bool(e.get("resolved"))), "eval_reason": e.get("reason"),
                               "hit_step_limit": int(u.get("exit_status") == "LimitsExceeded"), "Y7": int(bool(u.get("venv_mutated"))),
                               "parsed": False}
        traj = read_traj(base / "trajectories" / f"{uid}.traj.json.gz")
        if traj is not None and meta:
            acts = tp.parse_actions(traj["messages"])
            sets = {"F_R": tokens_of(meta, "F_R"), "F_I": tokens_of(meta, "F_I")}
            row["parsed"] = True
            row["n_actions"] = len(acts)
            row["sets"] = {k: tp.score(acts, v, traj["messages"]) for k, v in sets.items()}
            row["sets_sa6"] = {k: tp.score(acts, v, full_path_only=True) for k, v in sets.items()}
            row["sets_sa7"] = {k: tp.score(acts, v, narrow_nf=True) for k, v in sets.items()}
            own = {"F_R": "F_R", "F_I": "F_I"}.get(u["condition"])
            row["own"] = own
            try:
                diff = gzip.open(base / "patches" / f"{uid}.diff.gz", "rt").read()
            except OSError:
                diff = ""
            row["Y6_sets"] = {k: materialised(diff, v) for k, v in sets.items()}
        outs.append(row)
    for name, rows in (("wp6_runs.jsonl", runs), ("wp6_outcomes.jsonl", outs)):
        (base / name).write_text("".join(json.dumps(r, default=str) + "\n" for r in rows))
    logger.info("ledgers rewritten: %d runs, %d parsed", len(runs), sum(1 for r in outs if r["parsed"]))
    return {"runs": len(runs), "parsed": sum(1 for r in outs if r["parsed"])}


# ----------------------------------------------------------------------------
# WP5 deviation 14: how many WP5 runs installed packages?
# ----------------------------------------------------------------------------
def pip_carryover(cfg: dict) -> dict[str, Any]:
    wp5 = Path(cfg["wp5_output_dir"])
    wp5 = wp5 if wp5.is_absolute() else C.PROJECT_ROOT / wp5
    runs = wp5 / "runs"
    units = {u["unit_id"]: u for u in (read_json(f) for f in sorted((runs / "units").glob("*.json"))) if u}
    per_run: dict[str, dict[str, Any]] = {}
    n_traj = 0
    for f in sorted((runs / "trajectories").glob("*.traj.json.gz")):
        uid = f.name[: -len(".traj.json.gz")]
        t = read_traj(f)
        if t is None:
            continue
        n_traj += 1
        installs = []
        for a in tp.parse_actions(t["messages"]):
            if PIP_RE.search(a.command):
                pk = re.sub(r"^.*?\binstall\b", "", a.command, count=1, flags=re.S).strip().splitlines()[0][:120] if a.command else ""
                installs.append({"step": a.index, "rc": a.rc, "args": pk})
        per_run[uid] = {"installs": installs}
    attempted = {u for u, v in per_run.items() if v["installs"]}
    succeeded = {u for u, v in per_run.items() if any(i["rc"] == 0 for i in v["installs"])}

    def self_install_only(v: dict) -> bool:
        return all(re.fullmatch(r"(?:(?:-e|--editable)\s+)?\.(?:\[[^\]]*\])?(?:\s+--no-deps)?", i["args"].strip().strip("'\"")) for i in v["installs"])
    other = {u for u in succeeded if not self_install_only(per_run[u])}
    # runs of the same task that started after the finish of an earlier run with a successful install (could inherit its packages)
    by_task: dict[str, list[dict]] = defaultdict(list)
    for uid, u in units.items():
        if uid in per_run:
            by_task[u["task_id"]].append(u)
    exposed: set[str] = set()
    exposed_other: set[str] = set()
    for tid, us in by_task.items():
        us.sort(key=lambda u: u.get("started") or "")
        first_any = first_other = None
        for u in us:
            if first_any and (u.get("started") or "") >= first_any:
                exposed.add(u["unit_id"])
            if first_other and (u.get("started") or "") >= first_other:
                exposed_other.add(u["unit_id"])
            if u["unit_id"] in succeeded and first_any is None:
                first_any = u.get("finished") or u.get("started")
            if u["unit_id"] in other and first_other is None:
                first_other = u.get("finished") or u.get("started")
    tasks_with = sorted({units[u]["task_id"] for u in succeeded if u in units})
    res = {
        "source": "WP5 trajectories (results/real_v2/wp5/runs/trajectories), executed actions parsed with wp6/trajparse.py",
        "pattern": PIP_RE.pattern,
        "n_trajectories": n_traj,
        "runs_with_pip_install_attempt": len(attempted),
        "runs_with_successful_pip_install_rc0": len(succeeded),
        "runs_whose_successful_install_was_not_only_the_editable_self_install": len(other),
        "share_of_runs_with_successful_install": round(len(succeeded) / max(1, n_traj), 4),
        "tasks_with_a_run_with_successful_install": len(tasks_with),
        "n_tasks": len({u["task_id"] for u in units.values()}),
        "runs_that_started_after_an_earlier_successful_install_in_the_same_task": len(exposed),
        "runs_that_started_after_an_earlier_non_self_install_in_the_same_task": len(exposed_other),
        "note": "A pip install inside the shared per-task venv persisted for all later runs of that task (WP5 deviation 14). "
                "'started after' uses the unit timestamps; the run order within a task was seeded random, not aligned with condition.",
        "by_condition_attempted": _by(attempted, units, "condition"),
        "by_model_attempted": _by(attempted, units, "model"),
    }
    out = Path(cfg["output_dir"])
    out = out if out.is_absolute() else C.PROJECT_ROOT / out
    write_json(out / "wp5_pip_carryover.json", res)
    logger.info("pip carry-over: %s", json.dumps({k: v for k, v in res.items() if isinstance(v, (int, float))}))
    return res


def _by(ids: set[str], units: dict[str, dict], key: str) -> dict[str, int]:
    out: dict[str, int] = defaultdict(int)
    for i in ids:
        if i in units:
            out[str(units[i].get(key))] += 1
    return dict(sorted(out.items()))
