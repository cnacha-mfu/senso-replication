"""Claude Code pilot for RQ4/RQ5: does a SENSO CLAUDE.md help a frontier agent? (exploratory; WP5 deviation 17)

Used by Paper 1 (JSEP rebuild). The author's decision of 2026-10-17 relaxes the NIM-only rule for this pilot only: the agent is
Claude Code (`claude -p`, the author's subscription through CLAUDE_CODE_OAUTH_TOKEN from `claude setup-token`), not
mini-SWE-agent. Same tasks, SENSO manifests, venv reset and evaluation as the WP5 replication; what differs:

  * the agent is Claude Code with its own tools; the condition C manifest is written to the repository root as CLAUDE.md, where
    Claude Code reads it by itself (condition A: no file). The file is removed before the patch is taken;
  * no step limit (Claude Code has none in -p mode); the 30-minute wall-clock limit is kept;
  * every run is inside a docker container (`senso-claude-*`, label project=senso, 4 CPUs, 6 GB, 300 pids) that sees only the task
    root, the uv Pythons and the shared bare clones (read-only) and the claude binary; WebFetch and WebSearch are disabled;
  * tasks: a seeded sample from the replication's complete tasks, without an agent manifest in the tree (Claude Code would load it).

One unit JSON per run in results/real_v2/claude_pilot/units (skipped on re-run when it exists); the stream-json transcript is
gzipped next to it. Ledgers: wp5.evaluate.write_ledgers over the units.

Usage:
    PY=/home/adtgrade/research/wp5_feasibility/.venv/bin/python
    $PY experiments/paper1_ontology_manifests/run_claude_pilot.py --n-tasks 10 --model sonnet          # pilot
    $PY experiments/paper1_ontology_manifests/run_claude_pilot.py --config experiments/paper1_ontology_manifests/configs/claude_rq45.yaml \
        --all-tasks --conditions A C D --replicates 2 --model sonnet                                       # full study

Billing: only the subscription token is passed; ANTHROPIC_API_KEY is removed. After every run the rate-limit event of the
transcript is checked: the run stops if overage is not rejected, waits for the reset above --max-5h of the 5-hour window,
and stops above --max-7d of the weekly window.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from experiments.paper1_ontology_manifests.wp5 import conditions, evaluate  # noqa: E402
from experiments.paper1_ontology_manifests.wp5.agent import clean_repo, extract_diff  # noqa: E402
from experiments.paper1_ontology_manifests.wp5.common import load_task, safe_id, write_gz, write_json  # noqa: E402
from experiments.paper1_ontology_manifests.wp5.envs import venv_env  # noqa: E402
from experiments.paper1_ontology_manifests.wp5.runner import ensure_env, load_valid, release_env  # noqa: E402
from experiments.paper1_ontology_manifests.wp6 import common as C  # noqa: E402
from experiments.paper1_ontology_manifests.wp6.runner import kill_strays, reset_venv, snapshot_venv  # noqa: E402

logger = logging.getLogger("claude_pilot")

CONFIG = PROJECT_ROOT / "experiments/paper1_ontology_manifests/configs/claude_pilot.yaml"
IMAGE = "senso-claude-agent:1"
PROMPT = """Resolve the following issue in the Python repository in the current directory. Its virtual environment is already
active. Change the source code only; do not modify or add tests, and do not commit. Stop when the issue is resolved.

<issue>
{problem}
</issue>
"""


def pick_tasks(cfg: dict, n: int | None, seed: int) -> list[str]:
    rep = json.loads((PROJECT_ROOT / cfg["rep_tasks"]).read_text())["tasks"]
    ok = sorted(t["instance_id"] for t in rep if not t.get("excluded") and not t.get("agent_manifest_in_tree"))
    return ok if n is None else sorted(random.Random(seed).sample(ok, n))


def docker_run(cfg: dict, name: str, root: Path, repo_dir: Path, prompt: str, model: str, limit_s: int) -> tuple[str, float, bool]:
    """Run claude -p in a capped container. Returns (stream-json stdout, wall seconds, timed_out)."""
    env = venv_env(cfg, root)
    env["HOME"] = "/tmp/home"
    bare = (C.c5.work_dir(cfg) / "repos").resolve()
    claude_bin = Path.home().joinpath(".local/bin/claude").resolve()
    uvpy = Path.home() / ".local/share/uv/python"
    cmd = ["docker", "run", "--rm", "-i", "--name", name, "--label", "project=senso", "--cpus", "4", "--memory", "6g",
           "--pids-limit", "300", "--user", f"{os.getuid()}:{os.getgid()}", "--tmpfs", "/tmp:exec",
           "-v", f"{root}:{root}", "-v", f"{uvpy}:{uvpy}:ro", "-v", f"{bare}:{bare}:ro",
           "-v", f"{claude_bin}:/usr/local/bin/claude:ro", "-w", str(repo_dir),
           "-e", "CLAUDE_CODE_OAUTH_TOKEN", "-e", "DISABLE_AUTOUPDATER=1", "-e", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1"]
    for k, v in env.items():
        cmd += ["-e", f"{k}={v}"]
    cmd += [IMAGE, "claude", "-p", "--model", model, "--output-format", "stream-json", "--verbose",
            "--dangerously-skip-permissions", "--disallowedTools", "WebFetch", "WebSearch", "--no-session-persistence"]
    t0 = time.time()
    try:
        p = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=limit_s,
                           env={**os.environ, "CLAUDE_CODE_OAUTH_TOKEN": os.environ["CLAUDE_CODE_OAUTH_TOKEN"]})
        return p.stdout + (("\n" + json.dumps({"type": "stderr", "text": p.stderr[-2000:]})) if p.stderr else ""), \
            time.time() - t0, False
    except subprocess.TimeoutExpired as e:
        subprocess.run(["docker", "kill", name], capture_output=True)
        out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        return out, time.time() - t0, True


def summarise(stream: str) -> dict:
    """Result line of the stream-json transcript: turns, usage, model ids, cost estimate, error flag."""
    res: dict = {}
    rl: dict = {}
    tools = 0
    for line in stream.splitlines():
        try:
            m = json.loads(line)
        except json.JSONDecodeError:
            continue
        if m.get("type") == "assistant":
            tools += sum(1 for c in m.get("message", {}).get("content", []) if c.get("type") == "tool_use")
        if m.get("type") == "result":
            res = m
        if m.get("type") == "rate_limit_event":
            rl = m.get("rate_limit_info") or {}
    return {"exit_status": ("Submitted" if res.get("subtype") == "success" and not res.get("is_error") else
                            (res.get("subtype") or "NoResult")),
            "steps": res.get("num_turns"), "tool_calls": tools, "usage": res.get("usage"),
            "model_usage": res.get("modelUsage"), "cost_estimate_usd": res.get("total_cost_usd"),
            "result_text": (res.get("result") or "")[:2000], "rate_limit": rl}


def usage_guard(rl: dict, max_5h: float, max_7d: float) -> None:
    """Never run on paid overage; leave head-room in the author's shared Max-plan windows (this session and other Claude
    sessions on the VM use the same limits). Waits for the 5-hour window to reset, stops at the weekly cap."""
    if not rl:
        return
    if rl.get("isUsingOverage") or rl.get("overageStatus") not in (None, "rejected"):
        raise SystemExit(f"stopping: overage not rejected ({rl.get('overageStatus')}, using={rl.get('isUsingOverage')})")
    w = rl.get("unifiedWindows") or {}
    u7 = (w.get("seven_day") or {}).get("utilization") or 0
    if u7 >= max_7d:
        raise SystemExit(f"stopping: weekly utilization {u7:.2f} >= {max_7d}")
    h5 = w.get("five_hour") or {}
    if (h5.get("utilization") or 0) >= max_5h and h5.get("resetsAt"):
        wait = max(0, h5["resetsAt"] - time.time()) + 120
        logger.info("5-hour utilization %.2f >= %.2f; waiting %.0f min for the reset", h5["utilization"], max_5h, wait / 60)
        time.sleep(wait)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-tasks", type=int, default=10)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--conditions", nargs="+", default=["A", "C"])
    ap.add_argument("--seed", type=int, default=20261017)
    ap.add_argument("--config", default=str(CONFIG))
    ap.add_argument("--all-tasks", action="store_true", help="every complete task of the replication instead of a sample")
    ap.add_argument("--replicates", type=int, default=1)
    ap.add_argument("--max-5h", type=float, default=0.5, help="wait for the reset above this 5-hour utilization")
    ap.add_argument("--max-7d", type=float, default=0.6, help="stop above this weekly utilization")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    cfg = C.load_config(a.config)   # also loads .env
    os.environ.pop("ANTHROPIC_API_KEY", None)   # subscription only: never fall back to paid API billing
    if not os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        raise SystemExit("CLAUDE_CODE_OAUTH_TOKEN is not set (run `claude setup-token` and put the token in .env)")
    out = PROJECT_ROOT / cfg["output_dir"]
    ud, td = out / "units", out / "transcripts"
    ud.mkdir(parents=True, exist_ok=True)
    td.mkdir(parents=True, exist_ok=True)
    valid = load_valid(cfg)
    ids = pick_tasks(cfg, None if a.all_tasks else a.n_tasks, a.seed)
    limit = cfg["agent"]["wall_time_limit_seconds"]
    logger.info("tasks %s, conditions %s, model %s", ids, a.conditions, a.model)
    for tid in ids:
        task = load_task(cfg, tid)
        task["instance_id"] = tid
        sfx = (lambda r: f"__r{r}") if a.replicates > 1 else (lambda r: "")
        todo = [(c, r) for c in a.conditions for r in range(1, a.replicates + 1)
                if not (ud / f"{safe_id(tid)}__{c}__claude-{a.model}{sfx(r)}.json").exists()]
        random.Random(f"{a.seed}{tid}").shuffle(todo)
        if not todo:
            continue
        root, repo_dir, err = ensure_env(cfg, task, "run")
        try:
            if repo_dir is None:
                for c, r in todo:
                    write_json(ud / f"{safe_id(tid)}__{c}__claude-{a.model}{sfx(r)}.json",
                               {"unit_id": f"{safe_id(tid)}__{c}__claude-{a.model}{sfx(r)}", "task_id": tid, "condition": c,
                                "run": r, "status": "env_failed", "reason": err})
                continue
            snapshot_venv(root)
            for c, r in todo:
                uid = f"{safe_id(tid)}__{c}__claude-{a.model}{sfx(r)}"
                ct = conditions.condition_text(cfg, c, tid, task["repo"], task["base_commit"])
                reset_venv(root)
                clean_repo(repo_dir)
                if ct["text"]:
                    (repo_dir / "CLAUDE.md").write_text(ct["text"] + "\n")
                u = {"unit_id": uid, "task_id": tid, "repo": task["repo"], "stage": valid[tid]["stage"], "condition": c,
                     "model": f"claude-code/{a.model}", "run": r, "condition_meta": ct["meta"],
                     "started": datetime.now(timezone.utc).isoformat()}
                logger.info("RUN %s", uid)
                stream, wall, timed_out = docker_run(cfg, "senso-claude-" + uid[:60].lower().replace("_", "-"), root,
                                                     repo_dir, PROMPT.format(problem=task["problem_statement"]),
                                                     a.model, limit)
                u["stray_procs_killed"] = kill_strays(root)
                s = summarise(stream)
                if timed_out:
                    s["exit_status"] = "TimeExceeded"
                (repo_dir / "CLAUDE.md").unlink(missing_ok=True)
                diff = extract_diff(repo_dir)
                write_gz(td / f"{uid}.jsonl.gz", stream)
                write_gz(td / f"{uid}.diff.gz", diff)
                u.update(s, wall_s=round(wall, 1))
                u["uptake"] = evaluate.uptake(c, s["result_text"])
                infra = s["exit_status"] not in ("Submitted", "TimeExceeded") or not s["steps"]
                if infra:
                    u["eval"] = {"resolved": False, "reason": "infra_failure", "outcomes": None}
                else:
                    reset_venv(root)
                    u["eval"] = evaluate.evaluate_diff(cfg, task, valid[tid], diff, root, repo_dir, s["steps"] or 0,
                                                       s["exit_status"] == "TimeExceeded")
                kill_strays(root)
                u["status"] = "done"
                u["finished"] = datetime.now(timezone.utc).isoformat()
                write_json(ud / f"{uid}.json", u)
                logger.info("DONE %s exit=%s turns=%s wall=%.0fs", uid, s["exit_status"], s["steps"], wall)
                if infra:   # e.g. the subscription's usage limit: stop rather than run on (author: no extra charges)
                    raise SystemExit(f"stopping: {uid} ended as {s['exit_status']}: {s['result_text'][:300]}")
                usage_guard(s["rate_limit"], a.max_5h, a.max_7d)
        finally:
            if root is not None:
                kill_strays(root)
            release_env(root)


if __name__ == "__main__":
    main()
