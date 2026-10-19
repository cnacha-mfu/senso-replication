"""WP5 per-task environments: repo checkout at the base commit, uv venv from SWE-rebench install_config,
and a pytest runner/parser shared by validation and evaluation.

Used by Paper 1 (JSEP rebuild), WP5.

Usage:
    imported by wp5.validate / wp5.runner / wp5.evaluate; not run directly.
"""

from __future__ import annotations

import logging
import os
import re
import shlex
import shutil
import time
from pathlib import Path
from typing import Any, Optional

from .common import UV, rm_tree, run, safe_id, uv_env, work_dir

logger = logging.getLogger("wp5.envs")

STATUS_RE = re.compile(r"^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\s+(.*?)\s*$")


# ----------------------------------------------------------------------------
# Repository checkout
# ----------------------------------------------------------------------------
def bare_cache(cfg: dict, repo: str, sha: str) -> tuple[Optional[Path], str]:
    """Partial bare clone of the repo (shared by all its tasks), containing ``sha``."""
    d = work_dir(cfg) / "repos" / (repo.replace("/", "__") + ".git")
    to = cfg["validate"]["clone_timeout_s"]
    marker = d.with_suffix(".skip")
    if marker.exists():
        return None, "repo_skipped: " + marker.read_text()[:200]
    if not d.exists():
        d.parent.mkdir(parents=True, exist_ok=True)
        rc, out = run(["git", "clone", "--bare", "--filter=blob:none", "--quiet",
                       f"https://github.com/{repo}.git", str(d)], timeout=to,
                      env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
        if rc != 0:
            rm_tree(d)
            return None, f"clone_failed: {out[-300:]}"
        mb = _du_mb(d)
        if mb > cfg["validate"].get("max_repo_mb", 400):
            rm_tree(d)
            marker.write_text(f"repo_too_large: {mb:.0f} MB bare partial clone")
            return None, f"repo_too_large: {mb:.0f} MB"
    run(["git", "config", "uploadpack.allowFilter", "true"], cwd=d)  # needed to clone from this partial repo
    rc, _ = run(["git", "cat-file", "-e", sha + "^{commit}"], cwd=d)
    if rc != 0:
        rc, out = run(["git", "fetch", "--filter=blob:none", "--quiet", "origin", sha], cwd=d, timeout=to,
                      env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
        if rc != 0:
            return None, f"base_commit_unreachable: {out[-300:]}"
    return d, ""


def mark_slow(cfg: dict, repo: str, seconds: float) -> None:
    """Remember repos whose checkout is prohibitively slow so their other tasks fail fast."""
    d = work_dir(cfg) / "repos" / (repo.replace("/", "__") + ".git")
    d.with_suffix(".skip").write_text(f"repo_checkout_too_slow: {seconds:.0f} s")


def _du_mb(path: Path) -> float:
    rc, out = run(["du", "-sm", str(path)], timeout=120)
    try:
        return float(out.split()[0])
    except (ValueError, IndexError):
        return 0.0


def make_workdir(cfg: dict, task: dict, root: Path) -> tuple[Optional[Path], str]:
    """Fresh workspace under ``root/repo`` holding only the ancestry of the base commit (plan 2.4).

    A new repository is initialised and the base commit is fetched from the cache clone (so nothing that
    is reachable only from later commits is present), then checked out detached. Blobs are filled lazily
    from GitHub (promisor remote).
    """
    bare, err = bare_cache(cfg, task["repo"], task["base_commit"])
    if bare is None:
        return None, err
    repo_dir = root / "repo"
    rm_tree(repo_dir)
    repo_dir.mkdir(parents=True, exist_ok=True)
    to = cfg["validate"]["clone_timeout_s"]
    genv = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    run(["git", "config", "--file", str(bare / "config"), "uploadpack.allowAnySHA1InWant", "true"])
    for cmd in (["git", "init", "-q", "."],
                ["git", "config", "extensions.partialClone", "origin"],
                ["git", "remote", "add", "origin", f"file://{bare}"],
                ["git", "config", "remote.origin.promisor", "true"],
                ["git", "config", "remote.origin.partialclonefilter", "blob:none"]):
        run(cmd, cwd=repo_dir)
    rc, out = run(["git", "fetch", "--quiet", "--no-tags", "--filter=blob:none", "origin", task["base_commit"]],
                  cwd=repo_dir, timeout=to, env=genv)
    if rc != 0:
        return None, f"workdir_clone_failed: {out[-300:]}"
    run(["git", "remote", "set-url", "origin", f"https://github.com/{task['repo']}.git"], cwd=repo_dir)
    rc, out = run(["git", "checkout", "--quiet", "--detach", task["base_commit"]], cwd=repo_dir, timeout=to, env=genv)
    if rc != 0:
        return None, f"checkout_failed: {out[-300:]}"
    run(["git", "config", "user.email", "agent@example.com"], cwd=repo_dir)
    run(["git", "config", "user.name", "agent"], cwd=repo_dir)
    return repo_dir, ""


def leakage_checks(repo_dir: Path, base_date_iso: str, test_patch: str) -> dict[str, Any]:
    """Plan 2.4 per-task checks: nothing newer than the base commit, F2P tests not already in the tree."""
    from datetime import datetime
    S = datetime.fromisoformat(base_date_iso)
    _, rest = run(["git", "rev-list", "--all", "--not", "HEAD"], cwd=repo_dir, timeout=300)
    rc, out = run(["git", "log", "--all", "--format=%ct"], cwd=repo_dir, timeout=300)
    newest = max((int(x) for x in out.split() if x.isdigit()), default=0)
    p = repo_dir.parent / "leak_test.patch"
    p.write_text(test_patch if test_patch.endswith("\n") else test_patch + "\n")
    rc2, _ = run(["git", "apply", "--check", str(p)], cwd=repo_dir, timeout=120)
    return {"objects_only_after_base": len(rest.split()), "newest_committer_date_le_S": newest <= S.timestamp() + 1,
            "test_patch_applies_cleanly_at_base": rc2 == 0}


def apply_patch(repo_dir: Path, patch: str, tag: str) -> tuple[bool, str]:
    p = repo_dir.parent / f"{tag}.patch"
    p.write_text(patch if patch.endswith("\n") else patch + "\n")
    for args in (["git", "apply", "--whitespace=nowarn"], ["git", "apply", "--whitespace=nowarn", "--3way"],
                 ["patch", "-p1", "--forward", "--batch", "-i"]):
        rc, out = run([*args, str(p)], cwd=repo_dir, timeout=120)
        if rc == 0:
            return True, ""
    return False, out[-300:]


# ----------------------------------------------------------------------------
# Environment
# ----------------------------------------------------------------------------
def venv_env(cfg: dict, root: Path) -> dict[str, str]:
    """Minimal, scrubbed environment (no API keys) that runs inside the task venv."""
    venv = root / ".v"
    env = {
        "PATH": f"{venv}/bin:{root}/shim:/usr/local/bin:/usr/bin:/bin",
        "VIRTUAL_ENV": str(venv),
        "HOME": str(root / "home"),
        "LANG": "C.UTF-8",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PIP_PROGRESS_BAR": "off",
        "PYTHONDONTWRITEBYTECODE": "1",
        "UV_CACHE_DIR": str(work_dir(cfg) / "uv_cache"),
        "UV_LINK_MODE": "hardlink",
        "TQDM_DISABLE": "1",
        "PAGER": "cat",
        "GIT_PAGER": "cat",
        "GIT_TERMINAL_PROMPT": "0",
        # temp files of agents and test suites stay in the task root and go with it (WP5 deviation 17: ~1M leftover
        # entries filled the shared /tmp inode table by 2026-10-16)
        "TMPDIR": str(root / "tmp"),
    }
    (root / "home").mkdir(parents=True, exist_ok=True)
    (root / "tmp").mkdir(parents=True, exist_ok=True)
    return env


def _write_shim(root: Path) -> None:
    """`pip` shim that routes to `uv pip` against the task venv (fast, hardlinked cache)."""
    sh = root / "shim"
    sh.mkdir(parents=True, exist_ok=True)
    f = sh / "pip"
    f.write_text(f'#!/bin/bash\nexec {UV} pip "$@" --python {root}/.v/bin/python\n')
    f.chmod(0o755)
    (sh / "pip3").write_text(f.read_text())
    (sh / "pip3").chmod(0o755)


def build_env(cfg: dict, task: dict, root: Path, repo_dir: Path) -> dict[str, Any]:
    """Create root/.v and install per install_config. Returns {ok, seconds, reason, log_tail, steps}."""
    ic = task["install_config"] or {}
    t0 = time.time()
    to = cfg["validate"]["env_build_timeout_s"]
    py = str(ic.get("python"))
    py = ".".join(py.split(".")[:2])
    venv = root / ".v"
    rm_tree(venv)
    steps: list[dict] = []
    uenv = uv_env(cfg)

    def step(name: str, cmd: str | list[str], env: dict, timeout: int = to, fatal: bool = True) -> bool:
        rc, out = run(cmd, cwd=repo_dir, env=env, timeout=timeout, shell=isinstance(cmd, str))
        steps.append({"step": name, "rc": rc, "tail": out[-600:]})
        return rc == 0 or not fatal

    if not step("venv", [UV, "venv", "--seed", "--python", py, str(venv)], uenv):
        return _res(False, t0, "python_unavailable", steps)
    _write_shim(root)
    env = venv_env(cfg, root)
    for cmd in ic.get("pre_install") or []:
        if re.match(r"^\s*(sudo\s+)?(apt|apt-get|yum|dnf|apk|conda)\b", cmd):
            steps.append({"step": "pre_install_skipped", "cmd": cmd})
            continue
        if not step("pre_install", cmd, env):
            return _res(False, t0, "pre_install_failed", steps)
    pk = ic.get("packages") or ""
    if pk == "requirements.txt":
        for rp in ic.get("reqs_path") or ["requirements.txt"]:
            if (repo_dir / rp).exists():
                if not step("requirements", f"pip install -r {shlex.quote(rp)}", env):
                    return _res(False, t0, "requirements_install_failed", steps)
    elif pk and pk not in ("environment.yml", "Pipfile", "poetry", "pip", "pytest"):
        if not step("packages", f"pip install {pk}", env):
            return _res(False, t0, "packages_install_failed", steps)
    pips = ic.get("pip_packages") or []
    if pips:
        flat = [x for p in pips for x in shlex.split(p)]  # items may hold several space-separated packages
        if not step("pip_packages", "pip install " + " ".join(shlex.quote(p) for p in flat), env):
            return _res(False, t0, "pip_packages_install_failed", steps)
    if ic.get("install"):
        if not step("install", ic["install"], env):
            return _res(False, t0, "install_failed", steps)
    # pytest must exist even when install_config forgot it
    step("pytest_check", "python -m pytest --version || pip install pytest", env, timeout=300)
    return _res(True, t0, "", steps)


def _res(ok: bool, t0: float, reason: str, steps: list[dict]) -> dict[str, Any]:
    return {"ok": ok, "seconds": round(time.time() - t0, 1), "reason": reason,
            "log_tail": (steps[-1].get("tail", "") if steps else "")[-800:], "n_steps": len(steps)}


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
def test_files_of(ids: list[str]) -> list[str]:
    seen: list[str] = []
    for i in ids:
        f = i.split("::")[0]
        if f not in seen:
            seen.append(f)
    return seen


def parse_pytest_rA(output: str) -> dict[str, str]:
    """test id -> status from a `pytest -rA` short summary (PASSED/FAILED/ERROR/...)."""
    res: dict[str, str] = {}
    for line in output.splitlines():
        m = STATUS_RE.match(line)
        if not m:
            continue
        status, rest = m.groups()
        tid = rest.split(" - ")[0].strip() if status in ("FAILED", "ERROR") else rest
        res[tid] = status
    return res


def run_tests(cfg: dict, task: dict, root: Path, repo_dir: Path, test_ids: list[str]) -> dict[str, Any]:
    """Run the task's test files with the dataset's test_cmd; return per-id statuses."""
    ic = task["install_config"] or {}
    cmd = ic.get("test_cmd") or "pytest --no-header -rA --tb=line --color=no -p no:cacheprovider"
    if "-rA" not in cmd:
        cmd += " -rA"
    files = test_files_of(test_ids)
    full = f"{cmd} {' '.join(shlex.quote(f) for f in files)}"
    env = venv_env(cfg, root)
    for k, v in (ic.get("env_vars") or {}).items():
        env[k] = str(v)
    t0 = time.time()
    rc, out = run(full, cwd=repo_dir, env=env, timeout=cfg["validate"]["test_timeout_s"], shell=True)
    return {"rc": rc, "seconds": round(time.time() - t0, 1), "statuses": parse_pytest_rA(out),
            "timeout": out.endswith("[TIMEOUT]"), "tail": out[-1500:]}


def judge_tests(statuses: dict[str, str], f2p: list[str], p2p: list[str]) -> dict[str, Any]:
    """F2P all pass? P2P all pass? A missing id counts as not passed."""
    def ok(i: str) -> bool:
        return statuses.get(i) in ("PASSED", "XFAIL", "XPASS") if i in statuses else False
    f_fail = [i for i in f2p if not ok(i)]
    p_fail = [i for i in p2p if not ok(i)]
    return {"f2p_pass": len(f2p) - len(f_fail), "f2p_total": len(f2p), "p2p_pass": len(p2p) - len(p_fail),
            "p2p_total": len(p2p), "f2p_failed_ids": f_fail[:20], "p2p_failed_ids": p_fail[:20],
            "f2p_all_pass": not f_fail, "p2p_all_pass": not p_fail}


def task_root(cfg: dict, task_id: str, kind: str = "tasks") -> Path:
    return work_dir(cfg) / kind / safe_id(task_id)


def cleanup(root: Path) -> None:
    shutil.rmtree(root, ignore_errors=True)
