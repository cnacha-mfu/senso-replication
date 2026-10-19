"""Shared helpers for the WP6 harness: merged config, paths, the task list and a task-record cache.

Used by Paper 1 (JSEP rebuild), WP6 (do wrong manifests hurt agents?); design papers/paper1/wp6-harm-design.md.

`configs/wp6.yaml` names `configs/wp5.yaml` as its base; the two are deep-merged, so the agent settings, the v2 NIM
panel and the 4-key rotation of WP5 are inherited and not copied. The SWE-rebench rows (gold patch, problem
statement) come from the Hugging Face cache, which only the WP5 run venv can read; `task_record` therefore caches
the few fields WP6 needs as JSON under `<work_dir>/taskdata` so that the project venv can use them too.

Usage:
    imported by experiments/paper1_ontology_manifests/run_wp6.py and wp6/*.py; not run directly.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Optional

import yaml

from ..wp5 import common as c5
from ..wp5.common import PROJECT_ROOT, read_json, rpath, safe_id, write_json  # noqa: F401  (re-exported)

logger = logging.getLogger("wp6")

DEFAULT_CONFIG = PROJECT_ROOT / "experiments/paper1_ontology_manifests/configs/wp6.yaml"
COND_MANIFEST = ("T", "F_R", "F_I")
CONDITIONS = ("A", "T", "F_R", "F_I")
SHARED_LINKS = ("repos", "validation", "uv_cache")


def _deep_merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in over.items():
        out[k] = _deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def load_config(path: Optional[Path | str] = None) -> dict[str, Any]:
    """wp6.yaml merged over wp5.yaml, plus .env (API keys). Also links the shared WP5 work-dir folders."""
    p = Path(path or DEFAULT_CONFIG)
    own = yaml.safe_load(p.read_text())
    base_p = Path(own["base_config"])
    base = c5.load_config(base_p if base_p.is_absolute() else PROJECT_ROOT / base_p)
    cfg = _deep_merge(base, {k: v for k, v in own.items() if k != "base_config"})
    cfg["_root"] = PROJECT_ROOT
    link_shared(cfg)
    return cfg


def link_shared(cfg: dict) -> None:
    """work_dir/{repos,validation,uv_cache} -> the WP5 folders (symlinks; created once)."""
    wd = c5.work_dir(cfg)
    for name in SHARED_LINKS:
        dst, src = wd / name, Path(cfg["shared_work_dir"]) / name
        if not dst.exists() and not dst.is_symlink() and src.exists():
            dst.symlink_to(src)


def out_dir(cfg: dict, pilot: bool = False) -> Path:
    return rpath(cfg, "pilot_dir" if pilot else "output_dir")


def manifests_dir(cfg: dict) -> Path:
    d = rpath(cfg, "output_dir") / "manifests"
    d.mkdir(parents=True, exist_ok=True)
    return d


def wp5_tasks(cfg: dict) -> list[dict]:
    """The 80 frozen WP5 tasks (none excluded or dev)."""
    p = Path(cfg["wp5_tasks"])
    d = read_json(p if p.is_absolute() else PROJECT_ROOT / p)
    return [t for t in d["tasks"] if not t.get("excluded") and not t.get("dev")]


def task_record(cfg: dict, task_id: str) -> dict[str, Any]:
    """{instance_id, repo, base_commit, python, problem_statement, patch, test_patch, f2p, install_config}, cached."""
    cache = c5.work_dir(cfg) / "taskdata" / f"{safe_id(task_id)}.json"
    rec = read_json(cache)
    if rec:
        return rec
    t = c5.load_task(cfg, task_id)  # needs `datasets`: the WP5 run venv
    rec = {k: t[k] for k in ("repo", "base_commit", "problem_statement", "patch", "test_patch", "install_config")}
    rec.update(instance_id=task_id, f2p=list(t["FAIL_TO_PASS"]))
    write_json(cache, rec)
    return rec


def diff_paths(diff: str) -> list[str]:
    """New-side file paths of a unified diff, in order, without duplicates."""
    seen: list[str] = []
    for m in re.finditer(r"(?m)^diff --git a/(\S+) b/(\S+)", diff):
        if m.group(2) not in seen:
            seen.append(m.group(2))
    return seen


def short_model(name: str) -> str:
    return name.split("/")[-1]
