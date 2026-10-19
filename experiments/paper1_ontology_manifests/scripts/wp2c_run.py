"""Run the WP2c fresh check over the shuffled eligible list (Paper 1, JSEP; design papers/paper1/wp2c-fresh-check-design.md).

Takes repositories in order until 30 complete `senso_check.py --skip-explain` runs (20 min limit each, 2 at a time),
then runs the `triangulate` step on each completed repository. Failures are logged with a reason and replaced by the
next repository. Outputs under /home/adtgrade/research/data/wp2c/<slug>/; status in wp2c_run_status.jsonl.

Usage:
    python experiments/paper1_ontology_manifests/scripts/wp2c_run.py [--target 30] [--workers 2]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
HERE = PROJECT_ROOT / "experiments" / "paper1_ontology_manifests"
DATA = Path("/home/adtgrade/research/data/wp2c")
ELIG = HERE / "results/real_v2/wp2c/wp2c_eligible_shuffled.json"
TIMEOUT = 1200
logger = logging.getLogger("wp2c_run")
lock = threading.Lock()


def run_group(cmd: list[str], log: Path, timeout: int, env: dict) -> tuple[int | None, str]:
    """Run cmd in its own process group; kill the whole group on timeout. Returns (rc or None, stdout)."""
    with open(log, "ab") as lf:
        p = subprocess.Popen(["nice", "-n", "10", *cmd], stdout=subprocess.PIPE, stderr=lf, env=env, start_new_session=True)
        try:
            out, _ = p.communicate(timeout=timeout)
            return p.returncode, out.decode("utf-8", "replace")
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.communicate()
            return None, ""
        finally:
            try:
                os.killpg(p.pid, signal.SIGKILL)  # no stray children after the unit ends
            except ProcessLookupError:
                pass


def one(c: dict, env: dict) -> dict:
    name = c["full_name"]
    slug = name.replace("/", "__")
    d = DATA / slug
    d.mkdir(parents=True, exist_ok=True)
    row = {"repo": name, "slug": slug, "manifest_path": c["manifest"], "start": time.strftime("%Y-%m-%dT%H:%M:%S")}
    t0 = time.time()
    if c.get("size_kb", 0) > 2 * 1024 * 1024:
        return {**row, "status": "failed", "reason": "repo_larger_than_2GB", "seconds": 0}
    rc, out = run_group([sys.executable, str(HERE / "senso_check.py"), "--repo", name, "--manifest-path", c["manifest"],
                         "--skip-explain", "--format", "json", "--out", str(d)], d / "run.stderr.log", TIMEOUT, env)
    row["seconds"] = round(time.time() - t0, 1)
    if rc is None:
        return {**row, "status": "failed", "reason": "timeout_20min"}
    if rc not in (0, 1):
        tail = (d / "run.stderr.log").read_text(errors="replace")[-400:].replace("\n", " | ")
        return {**row, "status": "failed", "reason": f"senso_check_rc{rc}: {tail}"}
    (d / "check.json").write_text(out)
    t1 = time.time()
    rc2, _ = run_group([sys.executable, str(HERE / "wp2_consistency.py"), "triangulate", "--config", str(d / "config.yaml")],
                       d / "triangulate.log", 1800, env)
    rc3, _ = run_group([sys.executable, str(HERE / "wp2_consistency.py"), "recheck", "--config", str(d / "config.yaml")],
                       d / "recheck.log", 1800, env)  # independent re-parse, used for T6
    row.update(status="completed", triangulate_rc=rc2, recheck_rc=rc3, triangulate_seconds=round(time.time() - t1, 1))
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=30)
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    load_dotenv(PROJECT_ROOT / ".env")
    env = dict(os.environ)
    status_f = DATA / "wp2c_run_status.jsonl"
    done = {}
    if status_f.exists():
        for ln in status_f.read_text().splitlines():
            r = json.loads(ln)
            done[r["repo"]] = r
    queue = [c for c in json.loads(ELIG.read_text())["eligible"] if c["full_name"] not in done]
    state = {"completed": sum(r["status"] == "completed" for r in done.values()), "inflight": 0}

    def worker() -> None:
        while True:
            with lock:
                if state["completed"] + state["inflight"] >= a.target or not queue:
                    return
                c = queue.pop(0)
                state["inflight"] += 1
            logger.info("start %s", c["full_name"])
            try:
                r = one(c, env)
            except Exception as exc:  # noqa: BLE001
                r = {"repo": c["full_name"], "status": "failed", "reason": f"runner_exception {exc}"}
            with lock:
                state["inflight"] -= 1
                state["completed"] += r["status"] == "completed"
                with open(status_f, "a") as f:
                    f.write(json.dumps(r) + "\n")
            logger.info("%s %s (%s) completed=%d", r["repo"], r["status"], r.get("reason", ""), state["completed"])

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for _ in range(a.workers):
            ex.submit(worker)
    logger.info("finished: %d completed", state["completed"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
