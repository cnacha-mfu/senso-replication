"""Shared helpers for the WP5 harness: config, paths, resource guard, subprocess and task access.

Used by Paper 1 (JSEP rebuild), WP5 (execution-based agent evaluation).

Usage:
    imported by experiments/paper1_ontology_manifests/run_wp5.py; not run directly.
"""

from __future__ import annotations

import gzip
import json
import logging
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = PROJECT_ROOT / "experiments/paper1_ontology_manifests/configs/wp5.yaml"
UV = str(Path.home() / ".local/bin/uv")

logger = logging.getLogger("wp5")

# never let git run an automatic gc/repack (it can take GBs of RAM on the shared VM)
os.environ.update({"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "gc.auto", "GIT_CONFIG_VALUE_0": "0"})


def load_config(path: Optional[Path | str] = None) -> dict[str, Any]:
    """Load wp5.yaml and the project .env (API keys, GITHUB_TOKEN)."""
    for env_file in (PROJECT_ROOT / ".env", *[p / ".env" for p in PROJECT_ROOT.parents]):
        if env_file.exists():  # a linked checkout has no .env of its own; fall back to the main one
            load_dotenv(env_file)
            break
    cfg = yaml.safe_load(Path(path or DEFAULT_CONFIG).read_text())
    cfg["_root"] = PROJECT_ROOT
    return cfg


def rpath(cfg: dict, key: str) -> Path:
    """Resolve a config path (relative -> project root) and create it."""
    p = Path(cfg[key])
    p = p if p.is_absolute() else PROJECT_ROOT / p
    p.mkdir(parents=True, exist_ok=True)
    return p


def work_dir(cfg: dict) -> Path:
    return rpath(cfg, "work_dir")


def uv_env(cfg: dict) -> dict[str, str]:
    """Environment for uv calls: private cache inside work_dir so it is counted and removable."""
    env = dict(os.environ)
    env["UV_CACHE_DIR"] = str(work_dir(cfg) / "uv_cache")
    env["UV_PYTHON_INSTALL_DIR"] = str(Path.home() / ".local/share/uv/python")
    env["UV_LINK_MODE"] = "hardlink"
    return env


# ----------------------------------------------------------------------------
# Resource guard (shared VM with a production system)
# ----------------------------------------------------------------------------
def du_gb(path: Path) -> float:
    try:
        out = subprocess.run(["du", "-sk", str(path)], capture_output=True, text=True, timeout=300).stdout
        return int(out.split()[0]) / 1024 / 1024
    except Exception:  # noqa: BLE001
        return 0.0


def free_mem_gb() -> float:
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable"):
            return int(line.split()[1]) / 1024 / 1024
    return 99.0


def wait_for_resources(cfg: dict, what: str = "", max_wait_s: int = 3600) -> None:
    """Block while the 1-min load is too high or memory too low (back off, never abort)."""
    lim = cfg["limits"]
    waited = 0
    while waited < max_wait_s:
        load1 = os.getloadavg()[0]
        mem = free_mem_gb()
        if load1 <= lim["max_load1"] and mem >= lim["min_free_mem_gb"]:
            return
        logger.info("backing off (%s): load1=%.1f mem=%.1fGB", what, load1, mem)
        time.sleep(30)
        waited += 30


class DiskGuard:
    """Cheap periodic check that work_dir stays under the disk cap."""

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self._last = 0.0
        self._gb = 0.0
        self._lock = threading.Lock()

    def usage_gb(self, max_age_s: float = 60) -> float:
        with self._lock:
            if time.time() - self._last > max_age_s:
                self._gb = du_gb(work_dir(self.cfg))
                self._last = time.time()
            return self._gb

    def ok(self) -> bool:
        return self.usage_gb() < self.cfg["limits"]["max_work_disk_gb"]


# ----------------------------------------------------------------------------
# Subprocess + files
# ----------------------------------------------------------------------------
def run(cmd: list[str] | str, *, cwd: Optional[Path | str] = None, timeout: int = 600,
        env: Optional[dict[str, str]] = None, shell: bool = False) -> tuple[int, str]:
    """Run a command in its own process group; kill the group on timeout. Returns (rc, output)."""
    proc = subprocess.Popen(cmd, cwd=cwd, env=env, shell=shell, text=True, errors="replace",
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True,
                            executable="/bin/bash" if shell else None)
    try:
        out, _ = proc.communicate(timeout=timeout)
        return proc.returncode, out or ""
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, 9)
        except ProcessLookupError:
            pass
        out, _ = proc.communicate()
        return 124, (out or "") + "\n[TIMEOUT]"


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, default=str))
    tmp.replace(path)


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(Path(path).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def write_gz(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write(text)


def safe_id(task_id: str) -> str:
    return task_id.replace("/", "__")


def rm_tree(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)


# ----------------------------------------------------------------------------
# Tasks (SWE-rebench rows are read from the HF cache; the committed pool is slim)
# ----------------------------------------------------------------------------
_DS: dict[str, Any] = {}
_IDX: dict[str, dict[str, int]] = {}


def hf_dataset(cfg: dict):
    key = cfg["pool"]["hf_dataset"] + ":" + cfg["pool"]["hf_split"]
    if key not in _DS:
        import datasets  # local import: heavy
        datasets.disable_progress_bars()
        _DS[key] = datasets.load_dataset(cfg["pool"]["hf_dataset"], split=cfg["pool"]["hf_split"])
        _IDX[key] = {iid: i for i, iid in enumerate(_DS[key]["instance_id"])}
    return _DS[key], _IDX[key]


def load_task(cfg: dict, instance_id: str) -> dict[str, Any]:
    """Full SWE-rebench row (patch, test_patch, problem_statement, install_config, F2P, P2P...)."""
    ds, idx = hf_dataset(cfg)
    return dict(ds[idx[instance_id]])
