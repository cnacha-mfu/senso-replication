"""WP5 manifest conditions A-D: one text file per (task, condition), injected into the agent prompt.

Used by Paper 1 (JSEP rebuild), WP5; plan papers/paper1/wp5-analysis-plan.md sections 2.5 and 3.

  A  nothing is appended.
  B  contributor guidance at the base commit, built by the deterministic generator function
     `manifests/generator/wp5_manifests.build_B` (plan 3.7). If `<manifests_dir>/<task>/B.md` exists it is
     used as is (the generator's output); otherwise B is built here with the same function from the cache
     clone. No such file in the base tree means B is unavailable and is not run.
  C, D  `<manifests_dir>/<task>/{C,D}.md`, written by `wp5_manifests.py` (population JSON -> manifests).

Every non-empty text starts with the fixed heading `## Repository context` and is appended after the
problem statement. It is injected into the prompt only: nothing is copied into the repository, and in-tree
CONTRIBUTING / agent files are left in place (they are a recorded covariate, plan 2.4).

Usage:
    imported by wp5.validate / wp5.runner.
"""

from __future__ import annotations

import hashlib
import importlib.util
import logging
from pathlib import Path
from typing import Any

from .common import PROJECT_ROOT

logger = logging.getLogger("wp5.conditions")
HEADING = "## Repository context"
_GEN = None


def _generator():
    """Import manifests/generator/wp5_manifests.py by path (no package install needed)."""
    global _GEN
    if _GEN is None:
        p = PROJECT_ROOT / "manifests/generator/wp5_manifests.py"
        spec = importlib.util.spec_from_file_location("wp5_manifests", p)
        mod = importlib.util.module_from_spec(spec)
        import sys
        sys.modules["wp5_manifests"] = mod
        spec.loader.exec_module(mod)
        _GEN = mod
    return _GEN


def manifest_path(cfg: dict, task_id: str, cond: str) -> Path:
    from .common import rpath, safe_id
    return rpath(cfg, "output_dir") / "manifests" / safe_id(task_id) / f"{cond}.md"


def bare_dir(cfg: dict, repo: str) -> Path:
    from .common import work_dir
    return work_dir(cfg) / "repos" / (repo.replace("/", "__") + ".git")


def real_agent_manifests_at_base(cfg: dict, repo: str, base_commit: str) -> list[str]:
    """Agent-manifest files present in the base tree (recorded covariate, SA3); read from the cache clone."""
    from .common import run
    rc, out = run(["git", "ls-tree", "-r", "--name-only", base_commit], cwd=bare_dir(cfg, repo), timeout=120)
    if rc != 0:
        return []
    tree = set(out.splitlines())
    names = cfg["real_agent_manifest_files"]
    return [n for n in names if n in tree] + sorted(t for t in tree if t.startswith(".cursor/rules/"))[:3]


def build_b(cfg: dict, repo: str, base_commit: str) -> str | None:
    gen = _generator()
    gd = bare_dir(cfg, repo)
    if not gd.exists():
        return None
    return gen.build_B(gd, base_commit, cfg["conditions"]["B"].get("char_cap", 8000))


def condition_text(cfg: dict, cond: str, task_id: str, repo: str, base_commit: str) -> dict[str, Any]:
    """{available, text, meta} for one (task, condition)."""
    if not cfg["conditions"][cond]["manifest"]:
        return {"available": True, "text": "", "meta": {}}
    f = manifest_path(cfg, task_id, cond)
    source = "generator_file"
    if f.is_file():
        text = f.read_text(encoding="utf-8")
    elif cond == "B":
        text, source = build_b(cfg, repo, base_commit), "build_B_direct"
    else:
        return {"available": False, "text": "", "meta": {"missing": str(f)}}
    if not text or not text.strip():
        return {"available": False, "text": "", "meta": {"source": source}}
    if not text.startswith(HEADING):
        logger.warning("%s/%s does not start with the fixed heading", task_id, cond)
    return {"available": True, "text": text.rstrip("\n"),
            "meta": {"source": source, "chars": len(text), "sha256": hashlib.sha256(text.encode()).hexdigest()}}
