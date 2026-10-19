"""WP5 integration with the committed analysis plan: dev tasks, population, manifests, task ledger, run manifest.

Used by Paper 1 (JSEP rebuild), WP5; papers/paper1/wp5-analysis-plan.md sections 2.1, 3, 11, 12.

  dev-pool   Python tasks that can never be in the sample (repo not in the pool, or no classifier history at the
             base date), used only to debug the generators and the harness (plan 2.1 development set).
  populate   per task: ontology/population/populate_v2.py --snapshot-commit ... --no-fuseki (project venv, Java).
  manifests  manifests/generator/wp5_manifests.py over the population JSONs (B, C, D; deterministic, no LLM).
  tasks      wp5_tasks.json from the validation checkpoints (declared stage codes ID/EVO/SERV/PO, evidence, flags).
  manifest   wp5_run_manifest.json (hashes, versions, seeds).

Usage:
    python experiments/paper1_ontology_manifests/run_wp5.py dev-pool
    python experiments/paper1_ontology_manifests/run_wp5.py populate --ids ID ... [--dev]
    python experiments/paper1_ontology_manifests/run_wp5.py manifests --ids ID ...
    python experiments/paper1_ontology_manifests/run_wp5.py tasks [--ids ID ...]
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

from . import pool as P
from .common import PROJECT_ROOT, load_task, read_json, rpath, run, safe_id, work_dir, write_json
from .evaluate import STAGE_CODE

logger = logging.getLogger("wp5.ledgers")
PROJECT_PY = "/home/adtgrade/research/senso-framework/.venv/bin/python"
JAVA_BIN = str(Path.home() / "research/tools/jdk/bin")


def build_dev_pool(cfg: dict, n: int = 8) -> list[dict]:
    """Seeded dev candidates: mapped to PyPI, repo absent from the pool, python/test filters as the pool."""
    from datetime import timezone as tz
    wcfg = yaml.safe_load((PROJECT_ROOT / cfg["wp3_config"]).read_text())
    http = P.wp3.Http(Path(cfg["wp3_cache"]), os.environ.get("GITHUB_TOKEN"), wcfg["network"]["timeout_s"],
                      wcfg["network"]["max_retries"])
    pool_repos = {t["repo"] for t in read_json(rpath(cfg, "output_dir") / "pool.json")["tasks"]}
    tasks, _ = P.base_filter(cfg)
    rng = random.Random(cfg["seed"] + 3)
    rev = P.reverse_package_map(Path(cfg["wp3_cache"]))
    by_repo: dict[str, list[dict]] = {}
    for t in tasks:
        if t["repo"] not in pool_repos and t["n_f2p"] <= 5 and t["n_p2p"] <= 100:
            by_repo.setdefault(t["repo"], []).append(t)
    repos = sorted(by_repo)
    rng.shuffle(repos)
    out: list[dict] = []
    for repo in repos:
        if len(out) >= n:
            break
        pkg = P.map_repo_to_package(repo, rev, http)
        if not pkg:
            continue
        t = rng.choice(sorted(by_repo[repo], key=lambda x: x["instance_id"]))
        d = P.gh_commit_date(http, repo, t["base_commit"])
        if d is None:
            continue
        t.update(package=pkg, base_date=d.isoformat(), base_date_source="base_commit_committer_date",
                 stage="dev", stage_detail={"note": "development set: never in the sample"}, dev=True)
        out.append(t)
    write_json(rpath(cfg, "output_dir") / "dev_pool.json", {"tasks": out})
    logger.info("dev pool: %d tasks", len(out))
    return out


def _env_for_java() -> dict[str, str]:
    env = dict(os.environ)
    env["PATH"] = JAVA_BIN + ":" + env.get("PATH", "")
    env["JAVA_HOME"] = str(Path(JAVA_BIN).parent)
    return env


def populate_tasks(cfg: dict, ids: list[str], workers: int = 2) -> dict[str, str]:
    """Run populate_v2 --snapshot-commit for each task (nice/ionice, at most `workers` concurrent)."""
    from concurrent.futures import ThreadPoolExecutor
    out_dir = rpath(cfg, "output_dir") / "population"
    out_dir.mkdir(parents=True, exist_ok=True)
    recs = {t["instance_id"]: t for f in ("pool.json", "dev_pool.json") for t in
            (read_json(rpath(cfg, "output_dir") / f, {"tasks": []})["tasks"])}
    tpdir = work_dir(cfg) / "testpatches"
    tpdir.mkdir(parents=True, exist_ok=True)
    status: dict[str, str] = {}

    def one(tid: str) -> None:
        t = recs[tid]
        if (out_dir / f"{tid}.json").exists():
            status[tid] = "exists"
            return
        task = load_task(cfg, tid)
        tp = tpdir / f"{safe_id(tid)}.diff"
        tp.write_text(task["test_patch"])
        cmd = ["nice", "-n", "15", "ionice", "-c", "3", PROJECT_PY, str(PROJECT_ROOT / "ontology/population/populate_v2.py"),
               "--repo", t["repo"], "--snapshot-commit", t["base_commit"], "--task-id", tid,
               "--test-patch-files", str(tp), "--output-dir", str(out_dir), "--no-fuseki",
               "--cache-dir", str(work_dir(cfg) / "repos")]
        rc, o = run(cmd, cwd=PROJECT_ROOT, env=_env_for_java(), timeout=3600)
        ok = (out_dir / f"{tid}.json").exists()
        status[tid] = "ok" if ok and rc == 0 else f"FAILED rc={rc}"
        logger.info("populate %s %s %s", tid, status[tid], "" if ok else o[-300:].replace("\n", " | "))

    with ThreadPoolExecutor(min(workers, 2)) as ex:
        list(ex.map(one, ids))
    write_json(out_dir.parent / "wp5_population_status.json", status)
    return status


def generate_manifests(cfg: dict, ids: Optional[list[str]] = None) -> int:
    out_dir = rpath(cfg, "output_dir")
    ids = ids or [t["instance_id"] for t in read_json(out_dir / "wp5_tasks.json")["tasks"]]
    cmd = ["nice", "-n", "15", PROJECT_PY, str(PROJECT_ROOT / "manifests/generator/wp5_manifests.py"), "--population-dir",
           str(out_dir / "population"), "--repo-cache", str(work_dir(cfg) / "repos"), "--out-dir", str(out_dir),
           "--rq1-verdict", cfg["rq1_verdict"], "--task-ids", *ids]
    rc, o = run(cmd, cwd=PROJECT_ROOT, env=_env_for_java(), timeout=3600)
    logger.info("manifests rc=%s %s", rc, o[-600:].replace("\n", " | "))
    return rc


def write_tasks(cfg: dict, ids: Optional[list[str]] = None) -> Path:
    """wp5_tasks.json per plan 2.1 / the run_wp5_analysis.py input schema."""
    from .runner import load_valid
    valid = load_valid(cfg)
    pool = read_json(rpath(cfg, "output_dir") / "pool.json")["tasks"]
    in_pool = {t["instance_id"]: t for t in pool}
    dev_ids = {t["instance_id"] for t in read_json(rpath(cfg, "output_dir") / "dev_pool.json", {"tasks": []})["tasks"]}
    tasks = []
    for tid in sorted(ids or valid):
        v = valid[tid]
        t = in_pool.get(tid, {})
        tasks.append({
            "instance_id": tid, "repo": v["repo"], "declared_stage": STAGE_CODE.get(v["stage"], v["stage"]),
            "stage": v["stage"], "stage_evidence": v.get("stage_detail"), "base_commit": v["base_commit"],
            "base_date": v["base_date"], "package": v.get("package"), "python": v["python"],
            "f2p": v.get("f2p"), "p2p_effective": v.get("p2p_effective"), "p2p_original_n": v.get("p2p_original"),
            "b_available": v.get("b_available"), "b_chars": v.get("b_chars"),
            "agent_manifest_in_tree": bool(v.get("real_agent_manifest_at_base")),
            "agent_manifest_files": v.get("real_agent_manifest_at_base"), "leakage_checks": v.get("leakage"),
            "gold_nontest_changed_lines": v.get("gold_nontest_changed_lines"), "gold_drift_fail": False,
            "excluded": False, "dev": tid in dev_ids})
    p = rpath(cfg, "output_dir") / "wp5_tasks.json"
    write_json(p, {"tasks": tasks, "generated_at": datetime.now(timezone.utc).isoformat(), "seed": cfg["seed"],
                   "cap_per_repo": cfg["pool"]["cap_per_repo"]})
    return p


def sha256(p: Path) -> Optional[str]:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def write_run_manifest(cfg: dict) -> Path:
    from . import agent as agent_mod
    out = rpath(cfg, "output_dir")
    tpl = agent_mod.base_config()["agent"]["instance_template"]
    _, head = run(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT)

    def rev(ref: str) -> Optional[str]:
        rc, o = run(["git", "rev-parse", "--verify", "--quiet", ref + "^{commit}"], cwd=PROJECT_ROOT)
        return o.strip() if rc == 0 and o.strip() else None
    m = {"generated_at": datetime.now(timezone.utc).isoformat(), "harness_commit": head.strip(),
         "plan_commit": rev("fd75b6b"),
         "tags": {"wp5-generator-freeze": rev("wp5-generator-freeze"), "wp5-run-freeze": rev("wp5-run-freeze")},
         "hashes": {"tasks": sha256(out / "wp5_tasks.json"), "manifests_index": sha256(out / "wp5_manifests_index.json"),
                    "analysis_config": sha256(PROJECT_ROOT / "experiments/paper1_ontology_manifests/configs/wp5_analysis.yaml"),
                    "harness_config": sha256(PROJECT_ROOT / "experiments/paper1_ontology_manifests/configs/wp5.yaml"),
                    "prompt_template": hashlib.sha256(tpl.encode()).hexdigest()},
         "agent": {"mini_swe_agent": __import__("minisweagent").__version__, "step_limit": cfg["agent"]["step_limit"],
                   "wall_time_limit_seconds": cfg["agent"]["wall_time_limit_seconds"],
                   "temperature": cfg["agent"]["temperature"], "top_p": cfg["agent"]["top_p"],
                   "max_tokens": cfg["agent"]["max_tokens"], "models": [m["name"] for m in cfg["agent"]["models"]]},
         "seeds": {"global": cfg["seed"]}, "python": sys.version.split()[0]}
    p = out / "wp5_run_manifest.json"
    write_json(p, m)
    return p
