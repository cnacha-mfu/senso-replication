"""WP6 verification gate: every T claim is true and every F claim false at the base commit (design section 2.3).

Used by Paper 1 (JSEP rebuild), WP6.

Every claim of every manifest is a WP2 claim record by construction (`tcode`, `attrs`, `votes = 3`, no LLM extraction)
and is checked by three instruments at `base_commit`:
  1. the RQ2 checker: `wp2/measure.py` (RepoAt on the cache clone) writes an ABox, HermiT with the frozen
     `seo-claims.owl` gives the verdict (the HermiT step runs in the project venv: `hermit_worker.py`);
  2. the independent re-check `wp2/recheck.py` (own git access, plain `if` logic);
  3. a runtime probe in the task workspace (what the agent would experience): `test -e`, `git log -- p`,
     `python -m pytest --collect-only`, `make -n`, `python -c "import ..."`.
Acceptance: every T claim (and every unchanged F claim) is Supported by 1 and 2 and passes its probe; every injected
claim gets its target Contradicted leaf from 1 and 2 and passes its probe. The union of the distinct claims of
T, F_R and F_I is checked once per task (a claim's verdict does not depend on the manifest it sits in).

Usage:
    imported by wp6/generate.py; python run_wp6.py verify-hermit / finalize-verification drive the HermiT and report steps.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

import yaml

from ..wp2 import measure as M
from ..wp2 import recheck as R
from ..wp2 import step_measure as SM
from ..wp2.repo import RepoAt
from ..wp5 import envs
from ..wp5.common import PROJECT_ROOT, run
from .manifests import Claim, Manifest, in_text

logger = logging.getLogger("wp6.verify")
EXP = PROJECT_ROOT / "experiments/paper1_ontology_manifests"


class Oracle:
    """Answers the builder's and the gate's runtime questions in one task workspace (cached)."""

    def __init__(self, cfg: dict, repo_dir: Path, root: Path, bare: Path, base_commit: str) -> None:
        self.cfg, self.repo_dir, self.root, self.bare, self.base = cfg, repo_dir, root, bare, base_commit
        self.env = envs.venv_env(cfg, root)
        self.timeout = cfg["manifest"].get("probe_timeout_s", 300)
        self.git = R.Git(bare, base_commit)
        self.git.prefetch_interesting()
        self.thr = R.load_thr()
        self.sigs = yaml.safe_load((EXP / "configs/wp2_tool_signatures.yaml").read_text(encoding="utf-8"))
        self.vsrc = yaml.safe_load((EXP / "configs/wp2_version_sources.yaml").read_text(encoding="utf-8"))["subjects"]
        self._cache: dict[str, Any] = {}
        self._rc: dict[str, Any] = {}
        self._tool: dict[str, int] = {}
        self.probe_log: dict[str, Any] = {}

    def _memo(self, key: str, fn):
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]

    # ---- builder questions ---------------------------------------------------------------------------------
    def exists(self, path: str) -> bool:
        return (self.repo_dir / path).exists()

    def log_count(self, path: str) -> int:
        def f() -> int:
            rc, out = run(["git", "log", "--oneline", "--", f":(literal){path}"], cwd=self.repo_dir, timeout=300,
                          env={**os.environ, "GIT_NO_LAZY_FETCH": "1"})
            return len([ln for ln in out.splitlines() if ln.strip()]) if rc == 0 else -1
        return self._memo("log:" + path, f)

    def pytest_collect_ok(self, root: str) -> bool:
        def f() -> dict:
            rc, out = run(f"python -m pytest --collect-only -q -p no:cacheprovider {root}", cwd=self.repo_dir,
                          env=self.env, timeout=self.timeout, shell=True)
            return {"rc": rc, "tail": out[-300:]}
        r = self._memo("pytest:" + root, f)
        self.probe_log["pytest:" + root] = r
        if self.cfg["manifest"].get("collect_accept_partial") and r["rc"] == 2 and re.search(r"[1-9]\d* tests? collected", r["tail"]):
            return True      # optional switch (off = design): collection errors in some modules, other tests collected
        return r["rc"] == 0

    def make_n_fails(self, target: str) -> bool:
        def f() -> dict:
            rc, out = run(f"make -n {target}", cwd=self.repo_dir, env=self.env, timeout=60, shell=True)
            return {"rc": rc, "tail": out[-200:]}
        r = self._memo("make:" + target, f)
        self.probe_log["make:" + target] = r
        return r["rc"] != 0 and r["rc"] != 127 and "No rule to make target" in r["tail"]

    def import_ok(self, module: str) -> bool:
        def f() -> dict:
            rc, out = run(["python", "-c", f"import {module}"], cwd=self.repo_dir, env=self.env, timeout=120)
            return {"rc": rc, "tail": out[-200:]}
        r = self._memo("import:" + module, f)
        self.probe_log["import:" + module] = r
        return r["rc"] == 0

    def recheck(self, tcode: str, attrs: dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
        key = tcode + json.dumps(attrs, sort_keys=True)
        if key not in self._rc:
            self._rc[key] = R.recheck_claim(self.git, {"tcode": tcode, "attrs": attrs, "votes": 3}, self.thr, self.sigs,
                                            self.vsrc, self._cache.setdefault("rc_cache", {}), self._tool)
        return self._rc[key]

    def grep_hits(self, pattern: str, extended: bool = False, ignore_case: bool = True, word: bool = True) -> int:
        def f() -> int:
            args = ["git", "grep", "-I", "-c", "-E" if extended else "-F"]
            if ignore_case:
                args.append("-i")
            if word and not extended:
                args.append("-w")
            rc, out = run([*args, "-e", pattern], cwd=self.repo_dir, timeout=300,
                          env={**os.environ, "GIT_NO_LAZY_FETCH": "1"})
            return sum(int(ln.rsplit(":", 1)[-1]) for ln in out.splitlines() if ln.rsplit(":", 1)[-1].isdigit())
        return self._memo(f"grep:{extended}:{ignore_case}:{word}:{pattern}", f)

    # ---- gate: runtime probe of one claim --------------------------------------------------------------------
    def probe(self, c: Claim) -> dict[str, Any]:
        p = c.probe
        if not p:
            return {"ok": True, "type": "none"}
        t = p["type"]
        if t == "exists":
            return {"ok": self.exists(p["path"]), "type": t}
        if t == "absent":
            n = self.log_count(p["path"])
            ok = (not self.exists(p["path"])) and ((n == 0) if p["history"] == "none" else (n >= 1))
            return {"ok": ok, "type": t, "log_count": n}
        if t == "pytest":
            return {"ok": self.pytest_collect_ok(p["root"]), "type": t}
        if t == "make_fail":
            return {"ok": self.make_n_fails(p["target"]), "type": t, "result": self.probe_log.get("make:" + p["target"])}
        if t == "import_ok":
            return {"ok": any(self.import_ok(m) for m in p["modules"]), "type": t}
        if t == "import_fail":
            return {"ok": all(not self.import_ok(m) for m in p["modules"]), "type": t}
        return {"ok": False, "type": t, "error": "unknown probe"}


def union_claims(manifests: dict[str, Manifest]) -> dict[str, Claim]:
    """Distinct claims over T, F_R, F_I by key; the same key must carry the same expectation."""
    out: dict[str, Claim] = {}
    for m in manifests.values():
        for c in m.claims():
            if c.key_str in out:
                o = out[c.key_str]
                if (o.expect_verdict, o.expect_leaves) != (c.expect_verdict, c.expect_leaves):
                    raise ValueError(f"claim {c.key_str} carries two expectations")
                continue
            out[c.key_str] = c
    return out


def measure_and_recheck(task_id: str, oracle: Oracle, claims: dict[str, Claim], abox_dir: Path) -> dict[str, Any]:
    """Instrument 1 (measurement; the ABox is built in hermit_worker) and instrument 2 (re-check) plus the probes, for one task."""
    repo = RepoAt(oracle.bare, oracle.base)
    ctx = M.Ctx(repo)
    items = []
    rows: dict[str, Any] = {}
    for k, c in claims.items():
        rec = {"repo": task_id, "key_str": k, "tcode": c.tcode, "attrs": c.attrs}
        m = SM.measure_claim(ctx, rec)
        items.append({"key_str": k, "tcode": c.tcode, "types": SM.claim_types(rec), "headline": SM.is_headline(rec),
                      "subject": c.quote, "quote": c.quote, "line": 1, "votes": 3, "models": [], "attrs": c.attrs, "m": m})
        v2, l2 = oracle.recheck(c.tcode, c.attrs)
        rows[k] = {"claim": c.to_json(), "recheck": {"verdict": v2, "leaf": l2}, "probe": oracle.probe(c),
                   "measure_error": (m.get("meta") or {}).get("error")}
    abox_dir.mkdir(parents=True, exist_ok=True)   # the ABox itself is written by hermit_worker (needs owlready2)
    (abox_dir / f"{task_id}.items.json").write_text(json.dumps({"repo": task_id, "S": oracle.base, "items": items}, default=str))
    return rows


def run_hermit(cfg: dict, abox_dir: Path, out_dir: Path, workers: int = 2) -> subprocess.CompletedProcess:
    """HermiT over every ABox in `abox_dir`, in the project venv (owlready2 is not installed in the run venv)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [cfg["project_python"], "-m", "experiments.paper1_ontology_manifests.wp6.hermit_worker",
           "--abox-dir", str(abox_dir), "--out-dir", str(out_dir), "--tbox", cfg["tbox_dir"], "--workers", str(workers)]
    return subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=7200,
                          env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)})


def judge(row: dict[str, Any], hermit: Optional[dict[str, Any]]) -> dict[str, Any]:
    """Apply the acceptance criteria to one claim's row (+ HermiT record for the claim, if it ran)."""
    c = row["claim"]
    want_v, want_leaves = c["expect_verdict"], c["expect_leaves"]
    rv, rl = row["recheck"]["verdict"], row["recheck"]["leaf"]
    hv = hl = None
    if hermit is not None:
        hv = (hermit.get("verdicts") or [None])[0]
        hl = (hermit.get("leaves") or [None])[0]

    def good(v: Optional[str], leaf: Optional[str]) -> bool:
        return v == want_v and (not want_leaves or leaf in want_leaves)
    res = {"instrument1_hermit": {"verdict": hv, "leaf": hl, "ok": good(hv, hl) if hermit is not None else None},
           "instrument2_recheck": {"verdict": rv, "leaf": rl, "ok": good(rv, rl)},
           "probe": row["probe"],
           "agree_1_2": (hv == rv and hl == rl) if hermit is not None else None}
    res["ok"] = bool(res["instrument2_recheck"]["ok"] and row["probe"]["ok"] and (res["instrument1_hermit"]["ok"] is not False)
                     and (hermit is not None))
    return res
