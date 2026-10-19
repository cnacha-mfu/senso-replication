"""WP2 step: second-instrument triangulation of verdicts (Paper 1, RQ2; design section 6.2).

Mechanical corroboration of reasoner verdicts with instruments other than the measurement module:

  * T1: GitHub Contents API at ref S (200/404) for every Contradicted T1 and 50 random exact-Supported T1;
  * T2: GitHub commits API with path, since and until=S for Contradicted and Indeterminate T2;
  * T5: CI configs at S (``.github/workflows`` etc.) that invoke a script reported undefined;
  * T3/T4: ``git grep -w -F`` of the name at S outside docs; zero hits corroborate a contradiction, hits flag a
    signature or alias gap (an upper bound on false contradictions);
  * T6: the independent re-parse of recheck.py (PEP 440 vs custom parser), read from recheck.json.

GitHub responses are cached on disk. No human or LLM is involved.

Usage:
    python experiments/paper1_ontology_manifests/wp2_consistency.py triangulate
"""

from __future__ import annotations

import json
import logging
import os
import random
import re
import subprocess
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Optional

import requests

from . import common as C
from .gitutil import ENV

logger = logging.getLogger("wp2.triangulate")
GH = "https://api.github.com"
CACHE = Path("/home/adtgrade/research/data/wp2_cache")
CI_GLOBS = (".github/workflows/", ".gitlab-ci.yml", ".circleci/", "azure-pipelines", "Jenkinsfile", ".travis.yml", ".buildkite/")
CONFIG_PATHSPECS = ["*.json", "*.toml", "*.yml", "*.yaml", "*.cfg", "*.ini", "*.txt", "Makefile", "*.mk", "*.gradle", "*.kts",
                    "*.xml", "*.csproj", "Gemfile", "*.py", "*.js", "*.ts", "*.tsx", "*.rb", "*.php"]


class Gh:
    def __init__(self) -> None:
        self.s = requests.Session()
        tok = os.getenv("GITHUB_TOKEN")
        self.s.headers.update({"Accept": "application/vnd.github+json", "User-Agent": "senso-wp2-triangulation"})
        if tok:
            self.s.headers["Authorization"] = f"Bearer {tok}"
        CACHE.mkdir(parents=True, exist_ok=True)
        self.calls = 0

    def get(self, url: str, params: Optional[dict[str, Any]] = None) -> tuple[int, Any]:
        key = C.sha256_text(url + json.dumps(params or {}, sort_keys=True))
        cp = CACHE / f"{key}.json"
        if cp.exists():
            d = json.loads(cp.read_text())
            return d["status"], d["body"]
        for attempt in range(4):
            r = self.s.get(url, params=params, timeout=60)
            self.calls += 1
            if r.status_code in (403, 429) and "rate limit" in r.text.lower():
                reset = int(r.headers.get("X-RateLimit-Reset", time.time() + 60))
                time.sleep(max(5, min(900, reset - time.time() + 2)))
                continue
            if r.status_code >= 500:
                time.sleep(3 * (attempt + 1))
                continue
            body: Any = None
            if r.status_code in (200, 404):
                try:
                    body = r.json() if r.status_code == 200 else None
                except ValueError:
                    body = None
            if isinstance(body, list):
                body = body[:100]
            elif isinstance(body, dict):
                body = {k: body[k] for k in ("type", "path", "size") if k in body}
            cp.write_text(json.dumps({"status": r.status_code, "body": body}))
            return r.status_code, body
        return 0, None


def git_grep_hits(d: Path, S: str, name: str, n_files: int) -> Optional[int]:
    """Files at S containing ``name`` as a whole word, outside docs; None if the grep was skipped or failed."""
    spec = [":(exclude)*.md", ":(exclude)*.lock", ":(exclude)*lock.json", ":(exclude)*.svg"]
    if n_files > 5000:
        spec = [f":(glob)**/{p}" if "/" not in p else p for p in CONFIG_PATHSPECS] + [":(exclude)*.md", ":(exclude)*lock.json"]
    p = subprocess.run(["git", "-C", str(d), "grep", "-I", "-w", "-F", "-l", name, S, "--", *spec],
                       capture_output=True, env=ENV, timeout=1800)
    if p.returncode not in (0, 1):
        return None
    return len([ln for ln in p.stdout.decode("utf-8", "replace").splitlines() if ln.strip()])


def ci_invocations(d: Path, S: str, kind: str, target: str, runner: str) -> int:
    out = subprocess.run(["git", "-C", str(d), "ls-tree", "-r", "--name-only", S], capture_output=True, env=ENV).stdout.decode().splitlines()
    ci = [f for f in out if any(f.startswith(g) or g in f for g in CI_GLOBS)][:60]
    n = 0
    t = re.escape(target)
    rx = (re.compile(rf"\b(?:npm|pnpm|yarn|bun)\s+(?:run\s+)?{t}\b") if kind == "script"
          else re.compile(rf"\bmake\s+(?:[\w=-]+\s+)*{t}\b") if kind == "make"
          else re.compile(rf"\bcomposer\s+(?:run(?:-script)?\s+)?{t}\b"))
    for f in ci:
        txt = subprocess.run(["git", "-C", str(d), "show", f"{S}:{f}"], capture_output=True, env=ENV).stdout.decode("utf-8", "replace")
        if rx.search(txt):
            n += 1
    return n


def run(cfg: dict[str, Any], only: Optional[str] = None, force: bool = False) -> int:
    res = C.results_dir(cfg)
    gh = Gh()
    rng = random.Random(cfg["seeds"]["sample"])
    rows: list[dict[str, Any]] = []
    meas_all: dict[str, Any] = {}
    ver_all: dict[str, Any] = {}
    for e in C.load_corpus(cfg):
        mp, vp = res / "measurements" / f"{e['slug']}.json", res / "verdicts" / f"{e['slug']}.json"
        if mp.exists() and vp.exists():
            meas_all[e["slug"]], ver_all[e["slug"]] = C.read_json(mp), C.read_json(vp)
    t1_supp: list[tuple[str, dict[str, Any]]] = []
    work: list[tuple[str, dict[str, Any], str, str]] = []
    for slug, m in meas_all.items():
        v = ver_all[slug]
        if not v.get("consistent"):
            continue
        for c in m["claims"]:
            rec = v["claims"].get(c["key_str"], {})
            vd = (rec.get("verdicts") or [None])[0]
            leaf = (rec.get("leaves") or [None])[0]
            if not vd or not c["headline"]:
                continue
            t = c["tcode"]
            if t == "T1" and vd == "ContradictedClaim":
                work.append((slug, c, "T1", vd))
            elif t == "T1" and leaf == "PathFoundExact" and not c["attrs"].get("glob"):
                t1_supp.append((slug, c))
            elif t == "T2" and vd in ("ContradictedClaim", "IndeterminateClaim"):
                work.append((slug, c, "T2", vd))
            elif t == "T5" and vd == "ContradictedClaim":
                work.append((slug, c, "T5", vd))
            elif t in ("T3", "T4") and vd == "ContradictedClaim":
                work.append((slug, c, t, vd))
    rng.shuffle(t1_supp)
    for slug, c in t1_supp[: cfg["triangulation"]["t1_random_supported"]]:
        work.append((slug, c, "T1", "SupportedClaim"))
    logger.info("triangulation work items: %d", len(work))

    def do(item: tuple[str, dict[str, Any], str, str]) -> dict[str, Any]:
        slug, c, t, vd = item
        m, repo, S = meas_all[slug], meas_all[slug]["repo"], meas_all[slug]["S"]
        d = Path(cfg["clone_dir"]) / slug
        row: dict[str, Any] = {"repo": repo, "key": c["key_str"], "tcode": t, "reasoner_verdict": vd}
        a = c["attrs"]
        try:
            if t == "T1":
                if a.get("glob"):
                    row["instrument"] = "skipped_glob"
                    return row
                path = c["m"]["meta"].get("alt_path_used") or a["path"]  # the path that was actually measured
                st, body = gh.get(f"{GH}/repos/{repo}/contents/{urllib.parse.quote(path)}", {"ref": S})
                row.update(instrument="github_contents", http_status=st, corroborates=(st == 404 if vd == "ContradictedClaim" else st == 200))
            elif t == "T2":
                path = c["m"]["meta"].get("resolved_path") or a["path"]
                e_ = int(m["S_epoch"]) if "S_epoch" in m else None
                snap = C.read_json(res / "snapshots" / f"{slug}.json")
                until = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(snap["S_epoch"]))
                since = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(snap["S_epoch"] - 180 * 86400))
                n, page = 0, 1
                while page <= 5:
                    st, body = gh.get(f"{GH}/repos/{repo}/commits", {"path": path, "sha": S, "since": since, "until": until, "per_page": 100, "page": page})
                    if st != 200 or not body:
                        break
                    n += len(body)
                    if len(body) < 100:
                        break
                    page += 1
                measured = c["m"]["props"].get("pathCommitsIn180d")
                row.update(instrument="github_commits", api_commits_180d=n, measured_commits_180d=measured, http_status=st,
                           corroborates=(n >= 5 if vd == "ContradictedClaim" else n >= 2))
            elif t == "T5":
                n = ci_invocations(d, S, a["kind"], a["target"], a["runner"])
                row.update(instrument="ci_config", ci_files_invoking=n, corroborates=(n == 0), possible_false_contradiction=(n > 0))
            elif t in ("T3", "T4"):
                name = a["tool"] if t == "T3" else a["name"]
                nf = m.get("n_tree_files", 0)
                hits = git_grep_hits(d, S, name, nf)
                row.update(instrument="git_grep", grep_files=hits, corroborates=(hits == 0) if hits is not None else None,
                           possible_signature_gap=(hits is not None and hits > 0), grep_restricted_to_config_files=nf > 5000)
        except Exception as exc:  # noqa: BLE001
            row["error"] = f"{type(exc).__name__}: {str(exc)[:150]}"
        return row

    with ThreadPoolExecutor(max_workers=3) as ex:
        rows = list(ex.map(do, work))
    summary: dict[str, Any] = {"github_api_calls": gh.calls}
    for t in ("T1", "T2", "T3", "T4", "T5"):
        for vd in ("ContradictedClaim", "SupportedClaim", "IndeterminateClaim"):
            rr = [r for r in rows if r["tcode"] == t and r["reasoner_verdict"] == vd and r.get("corroborates") is not None]
            if rr:
                summary[f"{t}_{vd}"] = {"n": len(rr), "corroborated": sum(1 for r in rr if r["corroborates"]),
                                        "rate": sum(1 for r in rr if r["corroborates"]) / len(rr)}
    rk = C.read_json(res / "recheck.json") if (res / "recheck.json").exists() else None
    if rk:
        summary["T6_reparse_agreement"] = rk["by_type"].get("T6")
    out = {"summary": summary, "rows": rows,
           "notes": {"T3_T4": "grep hits flag a signature or alias gap; zero hits corroborate. Repos above 5000 tracked files are grepped over config-like and source files only.",
                     "T2": "GitHub commits API counts all commits touching the path (merges included), so it can exceed the first-parent non-merge count.",
                     "T5": "A CI file invoking a script reported undefined flags a possible false contradiction or a broken CI."}}
    C.write_json(res / "triangulation.json", out)
    logger.info("triangulation: %s", summary)
    return 0
