#!/usr/bin/env python3
"""v2 population pipeline: mine -> measure -> reason -> Fuseki (Paper 1, RQ1/WP1/WP3).

Paper 1 rebuild (JSEP), implementing the measurement protocol of
``papers/paper1/rq1-preregistration.md`` section 3. ``populate.py`` (JSS era) is
untouched. Per repository:

  1. **Mine** (``t_mine``, cached): bare partial clone (``--filter=blob:none``)
     under ``~/research/data/repos``. All commits reachable from the default
     branch HEAD with author date <= S (snapshot day 23:59:59 UTC). One mining
     run covers 48 months ending at the snapshot month M_S; the 24- and
     36-month windows are cut from it. Months before the first commit are
     LEFT-TRUNCATED (never zero-filled); inside the window months are
     zero-filled. The mining output (commits, churn, monthly LOC, stage-A
     labels) is cached under ``~/research/data/rq1_mining`` so sensitivity
     configurations (L, Mann-Kendall variant, TBox thresholds) re-measure
     without re-mining.
  2. **Measure** (``t_measure``): every number comes from
     ``ontology/population/measures.py``; this module has no thresholds. The
     primary configuration (alpha 0.05, L 36, D 12, G 0.05, original MK) and 11
     one-at-a-time sensitivity configurations (S1-S5) are re-measured from the
     cache; alpha, D and G need a rebuilt TBox (``build_tboxes``, once per batch).
  3. **Stage A** (``t_reason_A``, cached with the mining): commit evidence ->
     Pellet over ``seo-evidence`` (chunked; identical evidence tuples are
     reasoned once, sound because the rules are local to a commit). Infers
     ``AgentCommit``, ``BugFixCommit`` (D8), ``FeatureCommit``.
  4. **Aggregate** (``t_aggregate``): counting over the inferred commit labels
     and the repo-level measurements that depend on them.
  5. **Stage B** (``t_reason_B``): HermiT over ``seo-inference``: C1 (Mann-Kendall
     stages), C2 (``RB*Stage``), laws, anti-patterns. Inconsistency is recorded.
  6. **Explain** (``t_explain``, optional): Pellet-CLI justifications for the
     stage labels and one label per Lehman law.
  7. **Write back**: named graphs into the Fuseki dataset ``seo_v2`` (never
     ``seo``) and a per-repo JSON, including the ``rq1`` block that
     ``rq1_labels.json`` needs (everything except the ground-truth join).

Measured LOC instrument (D9, ``LOC_INSTRUMENT``). Monthly LOC is the LOC of the
last FIRST-PARENT default-branch commit with committer date <= the month end
(``measures.month_end_commits``). ``git ls-tree -r`` lists the whole tree;
blobs with a source extension (``SOURCE_EXTENSIONS``), outside vendored
directories (``EXCLUDED_DIRS``) and at most 1 MB are counted as non-blank
physical lines, memoised per blob sha. Same tool and filter for every month.
Missing blobs are fetched in batches. If any month fails (git error, blob that
cannot be fetched, month without a commit inside the truncated window) the
whole LOC series is ABSENT (``loc_instrument.status == "failed"``): the LOC
measurements are not asserted, C1 is UNDETERMINED and C2 can only infer
Dormant. ``--simulate-loc-failure`` forces that path. Mean cyclomatic complexity
(lizard, per blob) is optional (``--complexity``). Churn counts the same source
files only. All dates are UTC.

Usage:
    python ontology/population/populate_v2.py --repo owner/name --snapshot-date 2025-06-30 \\
        --output-dir experiments/paper1_ontology_manifests/results/real_v2/rq1_population
    python ontology/population/populate_v2.py --repo owner/name --output-dir /tmp/o --no-fuseki \\
        --no-explain --no-sensitivity
    python ontology/population/populate_v2.py --repo owner/name --snapshot-commit <sha> --task-id <id> \\
        --test-patch-files <test.diff> --output-dir experiments/paper1_ontology_manifests/results/real_v2/wp5/population

WP5 snapshot mode (``--snapshot-commit``, wp5-analysis-plan.md 3.1-3.2). S is the committer date of the
base commit; the repository-level snapshot is the last day of the last complete month before S's month;
history, mining and month-end LOC walk the ancestry of the base commit only (the mining-cache key includes
the SHA); only the primary configuration runs, with explanations for the stage, law, anti-pattern and
module labels; module measurements (``mine_modules``) are anchored at S itself; the per-task JSON
``{task_id}.json`` has a ``modules`` block (module path -> label, measures) and ``modules_meta``.
The RQ1 mode is unchanged (``check_rq1_mode_unchanged.py``).
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ["TZ"] = "UTC"
time.tzset()

from ontology.population import measures as M  # noqa: E402
from ontology.reasoning import fuseki_graphs as FG  # noqa: E402
from ontology.reasoning.abox import RDF, SEO, XSD, AboxWriter  # noqa: E402

logger = logging.getLogger("senso.populate_v2")

DEFAULT_REPO_CACHE = Path.home() / "research" / "data" / "repos"
DEFAULT_MINING_CACHE = Path.home() / "research" / "data" / "rq1_mining"
DEFAULT_FUSEKI = "http://127.0.0.1:3030"
DEFAULT_DATASET = "seo_v2"
MINING_MONTHS = 48
PRIMARY_WINDOW = 36
MAX_BLOB_BYTES = 1_000_000
FETCH_CHUNK = 500
LOC_INSTRUMENT = "nonblank-source-lines-v1"
SOURCE_EXTENSIONS = frozenset(
    ".py .pyi .js .jsx .mjs .cjs .ts .tsx .java .kt .kts .scala .groovy .c .h .cc .cpp .cxx .hpp .hh "
    ".cs .go .rs .rb .php .swift .m .mm .lua .pl .pm .r .jl .dart .ex .exs .erl .hs .ml .clj .sh .bash "
    ".vue .svelte .sql .f90 .zig .nim".split())
EXCLUDED_DIRS = ("node_modules", "vendor", "vendored", "third_party", "site-packages", "bower_components")
LAW_RE = re.compile(r"^Law([IVX]+?)(NonConformant|Conformant)(.*)$")
STAGE_LABELS = ("GrowthStage", "DeclineStage", "StabilizationStage",
                "RBActiveDevelopmentStage", "RBServicingStage", "RBPhaseOutStage")
C1_MAP = {"GrowthStage": ("Growth", "A"), "StabilizationStage": ("Stabilization", "S"),
          "DeclineStage": ("Decline", "P")}
C2_MAP = {"RBActiveDevelopmentStage": "A", "RBServicingStage": "S", "RBPhaseOutStage": "P"}
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
MODULE_LABEL_CLASSES = ("StableModule", "ActiveModule", "LowRelChurnModule", "HighRelChurnModule",
                        "RarelyChangedModule", "OftenChangedModule")
MODULE_EXPLAIN_TOP = 25
"""Largest labelled modules (by LOC) whose labels get a Pellet justification; = K_MAX of condition C4."""
DEFAULT_WP5_REPO_CACHE = Path.home() / "research" / "data" / "wp5" / "repos"
DEFAULT_WP5_DATASET = "seo_v2_wp5"
GIT_ENV = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "TZ": "UTC", "LC_ALL": "C.UTF-8"}


# ---------------------------------------------------------------------------
# git helpers
# ---------------------------------------------------------------------------

def is_source_path(path: str) -> bool:
    """True if a repository path counts as source code (extension whitelist, no vendored dirs)."""
    if os.path.splitext(path)[1].lower() not in SOURCE_EXTENSIONS or path.endswith(".min.js"):
        return False
    parts = path.split("/")
    return not any(p in EXCLUDED_DIRS for p in parts[:-1])


def source_pathspecs() -> list[str]:
    """Git pathspecs equivalent to ``is_source_path`` (for ``git log -- ...``)."""
    specs = [f"*{e}" for e in sorted(SOURCE_EXTENSIONS)]
    specs += [f":(exclude,glob)**/{d}/**" for d in EXCLUDED_DIRS]
    specs += [f":(exclude,glob){d}/**" for d in EXCLUDED_DIRS]
    specs.append(":(exclude,glob)**/*.min.js")
    return specs


def _git(git_dir: Path, *args: str, check: bool = True, env: Optional[Mapping[str, str]] = None,
         input_bytes: Optional[bytes] = None, timeout: int = 3600) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", "-C", str(git_dir), *args], capture_output=True, input=input_bytes,
                       env=dict(env or GIT_ENV), timeout=timeout)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args[:3])} failed: {r.stderr.decode('utf-8', 'replace')[:500]}")
    return r


def git_version() -> str:
    """Installed git version string (provenance)."""
    return subprocess.run(["git", "--version"], capture_output=True, text=True).stdout.strip()


def safe_name(repo: str) -> str:
    """Filesystem-safe name of ``owner/name``."""
    return repo.replace("/", "__")


def ensure_clone(repo: str, cache_dir: Path) -> Path:
    """Bare partial clone of a GitHub repo (reused if present); raises on failure."""
    dest = cache_dir / f"{safe_name(repo)}.git"
    if dest.exists():
        logger.info("reusing clone %s", dest)
        return dest
    cache_dir.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".git.partial")
    shutil.rmtree(tmp, ignore_errors=True)
    r = subprocess.run(
        ["git", "clone", "--bare", "--filter=blob:none", "--no-tags", "-q",
         f"https://github.com/{repo}.git", str(tmp)],
        capture_output=True, env=GIT_ENV, timeout=3600)
    if r.returncode != 0:
        shutil.rmtree(tmp, ignore_errors=True)
        raise RuntimeError(f"clone of {repo} failed: {r.stderr.decode('utf-8', 'replace')[:500]}")
    tmp.rename(dest)
    return dest


def ensure_commit(git_dir: Path, sha: str) -> None:
    """Fetch ``sha`` into the clone if it is missing (WP5 snapshot mode); raises if it cannot be had."""
    if _git(git_dir, "cat-file", "-e", f"{sha}^{{commit}}", check=False).returncode == 0:
        return
    logger.info("fetching missing base commit %s", sha)
    _git(git_dir, "fetch", "origin", "--no-tags", "--no-write-fetch-head", "--recurse-submodules=no", sha)
    _git(git_dir, "cat-file", "-e", f"{sha}^{{commit}}")


def commit_dates(git_dir: Path, sha: str) -> tuple[datetime, datetime]:
    """(author date, committer date), both UTC, of a commit."""
    r = _git(git_dir, "show", "-s", "--format=%aI%x1f%cI", sha)
    a, c = r.stdout.decode().strip().split("\x1f")
    return (datetime.fromisoformat(a).astimezone(timezone.utc),
            datetime.fromisoformat(c).astimezone(timezone.utc))


def snapshot_end(snapshot: date) -> datetime:
    """S: the last second (UTC) of the snapshot day."""
    return datetime(snapshot.year, snapshot.month, snapshot.day, 23, 59, 59, tzinfo=timezone.utc)


def history_index(git_dir: Path, S: datetime, ref: str = "HEAD") -> list[tuple[str, datetime]]:
    """(sha, UTC author date) of every commit reachable from ``ref`` with author date <= S.

    ``ref`` is HEAD for the RQ1 population and the task's base commit in the WP5
    snapshot mode (ancestry only).
    """
    r = _git(git_dir, "log", ref, "--format=%H%x1f%aI")
    out = []
    for ln in r.stdout.decode("utf-8", "replace").splitlines():
        sha, _, d = ln.partition("\x1f")
        if not d:
            continue
        dt = datetime.fromisoformat(d).astimezone(timezone.utc)
        if dt <= S:
            out.append((sha, dt))
    return out


def mine_commits(git_dir: Path, wanted: set[str], first_month: str, ref: str = "HEAD") -> list[dict[str, Any]]:
    """Commit details (author, message, merge flag) for the wanted shas (walking from ``ref``)."""
    fmt = "%x1e%H%x1f%an%x1f%ae%x1f%aI%x1f%P%x1f%B%x1f"
    r = _git(git_dir, "log", ref, f"--since={first_month}-01T00:00:00", f"--format={fmt}")
    out: list[dict[str, Any]] = []
    for rec in r.stdout.decode("utf-8", "replace").split("\x1e"):
        f = rec.split("\x1f")
        if len(f) < 6 or f[0].strip() not in wanted:
            continue
        out.append({"hash": f[0].strip(), "author_name": f[1], "author_email": f[2],
                    "author_date": datetime.fromisoformat(f[3]).astimezone(timezone.utc),
                    "merge": len(f[4].split()) > 1, "message": f[5],
                    "insertions": 0, "deletions": 0, "files_changed": 0})
    return out


def missing_blobs(git_dir: Path, shas: Sequence[str]) -> list[str]:
    """Blob shas absent from the (partial) clone, found without triggering lazy fetches."""
    if not shas:
        return []
    env = {**GIT_ENV, "GIT_NO_LAZY_FETCH": "1"}
    r = _git(git_dir, "cat-file", "--batch-check", env=env, check=False,
             input_bytes=("\n".join(shas) + "\n").encode())
    return [ln.split()[0] for ln in r.stdout.decode().splitlines() if ln.endswith(" missing")]


def _fetch_chunk(git_dir: Path, shas: Sequence[str]) -> int:
    """Fetch blobs like git's own lazy fetch (``--filter=blob:none --stdin``); bisect on failure.

    These are the exact options of git's internal promisor fetch, including the
    ``noop`` negotiation: with default negotiation some blob-only wants fail the
    connectivity check ("bad revision ... did not send all necessary objects").

    Returns:
        The number of shas that could not be fetched.
    """
    if not shas:
        return 0
    r = _git(git_dir, "-c", "fetch.negotiationAlgorithm=noop", "fetch", "origin", "--no-tags",
             "--no-write-fetch-head", "--recurse-submodules=no", "--filter=blob:none", "--stdin",
             check=False, input_bytes=("\n".join(shas) + "\n").encode())
    if r.returncode == 0:
        return 0
    if len(shas) == 1:
        logger.warning("blob %s could not be fetched: %s", shas[0], r.stderr.decode("utf-8", "replace")[:200])
        return 1
    mid = len(shas) // 2
    return _fetch_chunk(git_dir, shas[:mid]) + _fetch_chunk(git_dir, shas[mid:])


def fetch_blobs(git_dir: Path, shas: Sequence[str]) -> int:
    """Fetch the missing blobs of ``shas`` in batches; returns how many were requested."""
    miss = missing_blobs(git_dir, shas)
    for i in range(0, len(miss), FETCH_CHUNK):
        _fetch_chunk(git_dir, miss[i:i + FETCH_CHUNK])
    return len(miss)


def attach_churn(git_dir: Path, commits: list[dict[str, Any]]) -> dict[str, float]:
    """Add source-file churn (insertions/deletions/files_changed) to the commits, in place.

    Pass 1 (``--raw``, tree-only) lists the blobs the diffs need; they are
    fetched in batches; pass 2 (``--numstat``) reads the line counts. Exactly the
    given commits are diffed (``--stdin --no-walk``); merges carry no diff.
    """
    t0 = time.perf_counter()
    stdin = ("\n".join(c["hash"] for c in commits) + "\n").encode()
    base = ["log", "--stdin", "--no-walk=unsorted", "--no-renames"]
    spec = ["--", *source_pathspecs()]
    r = _git(git_dir, *base, "--raw", "--no-abbrev", "--format=%x1e%H", *spec, input_bytes=stdin)
    blobs: set[str] = set()
    zero = "0" * 40
    for ln in r.stdout.decode("utf-8", "replace").splitlines():
        if ln.startswith(":"):
            f = ln.split()  # ":oldmode newmode oldsha newsha status path"; mode 160000 = submodule
            blobs.update(h for mode, h in ((f[0][1:], f[2]), (f[1], f[3])) if h != zero and mode != "160000")
    t_raw = time.perf_counter() - t0
    n_fetched = fetch_blobs(git_dir, sorted(blobs))
    t_fetch = time.perf_counter() - t0 - t_raw
    r = _git(git_dir, *base, "--numstat", "--format=%x1e%H", *spec, input_bytes=stdin)
    by_sha = {c["hash"]: c for c in commits}
    for rec in r.stdout.decode("utf-8", "replace").split("\x1e"):
        lines = rec.strip().splitlines()
        c = by_sha.get(lines[0].strip()) if lines else None
        if c is None:
            continue
        for ln in lines[1:]:
            a = ln.split("\t")
            if len(a) >= 3 and a[0].isdigit() and a[1].isdigit():
                c["insertions"] += int(a[0])
                c["deletions"] += int(a[1])
                c["files_changed"] += 1
    return {"t_churn_raw_s": t_raw, "t_churn_fetch_s": t_fetch,
            "t_churn_numstat_s": time.perf_counter() - t0 - t_raw - t_fetch, "blobs_fetched_churn": n_fetched}


def _read_blobs(git_dir: Path, shas: Sequence[str]) -> dict[str, bytes]:
    """Contents of blobs through one ``git cat-file --batch`` call."""
    env = {**GIT_ENV, "GIT_NO_LAZY_FETCH": "1"}
    r = _git(git_dir, "cat-file", "--batch", env=env, check=False,
             input_bytes=("\n".join(shas) + "\n").encode())
    data, out, pos = r.stdout, {}, 0
    while pos < len(data):
        nl = data.index(b"\n", pos)
        head = data[pos:nl].split()
        if len(head) == 3 and head[1] == b"blob":
            size = int(head[2])
            out[head[0].decode()] = data[nl + 1: nl + 1 + size]
            pos = nl + 1 + size + 1
        else:
            pos = nl + 1
    return out


def count_loc_series(
    git_dir: Path, months: Sequence[str], *, complexity: bool = False, simulate_failure: bool = False,
    ref: str = "HEAD",
) -> tuple[dict[str, Optional[int]], dict[str, Optional[float]], dict[str, Any]]:
    """Whole-repository LOC (and optionally mean CCN) at every month end (D9, ``LOC_INSTRUMENT``).

    Any failure makes the whole series absent: every month maps to None and
    ``info['status'] == 'failed'`` with the reason. Months are those of the
    truncated window, so every month has a commit on the first-parent spine
    unless the history is odd (then that is a failure too).

    Args:
        git_dir: Bare clone.
        months: Window months (truncated at the first commit).
        complexity: Also compute mean function CCN with lizard (cached per blob).
        simulate_failure: Test hook that raises inside the instrument.
        ref: Ref whose first-parent spine is walked (HEAD; the base commit in WP5 snapshot mode).

    Returns:
        (LOC by month, mean CCN by month, info dict with counts and timings).
    """
    none = {m: None for m in months}
    t0 = time.perf_counter()
    info: dict[str, Any] = {"instrument": LOC_INSTRUMENT, "status": "ok", "months": len(months)}
    try:
        if simulate_failure:
            raise RuntimeError("simulated LOC instrument failure")
        shas = M.month_end_commits(git_dir, months, ref, first_parent=True)
        if any(s is None for s in shas.values()):
            raise RuntimeError("no first-parent commit at or before month end: "
                               + ",".join(m for m, s in shas.items() if s is None))
        trees: dict[str, list[tuple[str, str]]] = {}
        for sha in sorted(set(shas.values())):
            r = _git(git_dir, "ls-tree", "-r", "-z", str(sha))  # no -l: sizes would fetch blobs
            ents = []
            for rec in r.stdout.decode("utf-8", "replace").split("\0"):
                meta, _, path = rec.partition("\t")
                f = meta.split()
                if len(f) == 3 and f[1] == "blob" and is_source_path(path):
                    ents.append((f[2], path))
            trees[sha] = ents
        all_blobs = sorted({b for e in trees.values() for b, _ in e})
        t_ls = time.perf_counter() - t0
        n_fetched = fetch_blobs(git_dir, all_blobs)
        still = missing_blobs(git_dir, all_blobs)
        if still:
            raise RuntimeError(f"{len(still)} source blobs could not be fetched")
        t_fetch = time.perf_counter() - t0 - t_ls
        path_of = {b: p for e in trees.values() for b, p in e}
        loc_of: dict[str, int] = {}
        ccn_of: dict[str, tuple[int, int]] = {}
        for i in range(0, len(all_blobs), 300):
            got = _read_blobs(git_dir, all_blobs[i:i + 300])
            if len(got) != len(all_blobs[i:i + 300]):
                raise RuntimeError("cat-file returned fewer blobs than requested")
            for sha, content in got.items():
                if b"\0" in content[:8000] or len(content) > MAX_BLOB_BYTES:  # binary or generated
                    loc_of[sha] = 0
                    continue
                loc_of[sha] = sum(1 for ln in content.split(b"\n") if ln.strip())
                if complexity:
                    ccn_of[sha] = _ccn(path_of[sha], content)
        loc: dict[str, Optional[int]] = {}
        ccn: dict[str, Optional[float]] = {}
        for m in months:
            ents = trees[shas[m]]
            loc[m] = sum(loc_of[b] for b, _ in ents)
            if complexity:
                cnt = sum(ccn_of.get(b, (0, 0))[1] for b, _ in ents)
                ccn[m] = (sum(ccn_of.get(b, (0, 0))[0] for b, _ in ents) / cnt) if cnt else 0.0
            else:
                ccn[m] = None
        info.update({"month_end_commits_distinct": len(trees), "source_blobs": len(all_blobs),
                     "blobs_fetched": n_fetched, "t_ls_tree_s": t_ls, "t_fetch_s": t_fetch,
                     "t_read_s": time.perf_counter() - t0 - t_ls - t_fetch})
        return loc, ccn, info
    except Exception as exc:
        logger.error("LOC instrument failed: %s", exc)
        info.update({"status": "failed", "reason": f"{type(exc).__name__}: {exc}"[:500]})
        return none, dict(none), info


MODULE_MAX_WINDOW = 24
"""Months of per-commit numstat kept in the module cache (SA9 re-measures W = 6 and 24 from it)."""
MODULE_CACHE_VERSION = "modules-v1"


def parse_test_patch_files(text: str) -> list[str]:
    """Paths touched by a unified diff (``diff --git a/x b/y`` headers, both sides)."""
    out: set[str] = set()
    for ln in text.splitlines():
        m = re.match(r"^diff --git a/(.+?) b/(.+)$", ln)
        if m:
            out.update(m.groups())
    out.discard("/dev/null")
    return sorted(out)


def load_test_patch_files(arg: Optional[str]) -> list[str]:
    """Test-patch paths from a diff file or a one-path-per-line list (None -> empty)."""
    if not arg:
        return []
    text = Path(arg).read_text(encoding="utf-8", errors="replace")
    if re.search(r"^diff --git ", text, re.M):
        return parse_test_patch_files(text)
    return sorted({ln.strip() for ln in text.splitlines() if ln.strip()})


def _py_history(git_dir: Path, ref: str) -> list[dict[str, Any]]:
    """Non-merge ancestors of ``ref`` with their changed ``*.py`` source paths (tree-only ``--raw`` pass).

    Returns dicts ``{hash, author_date, paths, blobs}`` newest first; commits that touch no
    Python source file are not listed (path-limited history).
    """
    r = _git(git_dir, "-c", "core.quotepath=false", "log", ref, "--no-merges", "--no-renames", "--raw",
             "--no-abbrev", "--format=%x1e%H%x1f%aI", "--", "*.py")
    out: list[dict[str, Any]] = []
    zero = "0" * 40
    for rec in r.stdout.decode("utf-8", "replace").split("\x1e"):
        lines = rec.strip("\n").splitlines()
        if not lines or "\x1f" not in lines[0]:
            continue
        sha, _, d = lines[0].partition("\x1f")
        paths: list[str] = []
        blobs: list[str] = []
        for ln in lines[1:]:
            if not ln.startswith(":"):
                continue
            meta, _, path = ln.partition("\t")
            f = meta.split()  # ":oldmode newmode oldsha newsha status"
            if path.startswith('"') or not is_source_path(path) or not path.endswith(".py"):
                continue
            paths.append(path)
            blobs += [h for mode, h in ((f[0][1:], f[2]), (f[1], f[3])) if h != zero and mode != "160000"]
        if paths:
            out.append({"hash": sha.strip(), "author_date": datetime.fromisoformat(d).astimezone(timezone.utc),
                        "paths": paths, "blobs": blobs})
    return out


def _numstat_files(git_dir: Path, hashes: Sequence[str]) -> dict[str, list[tuple[str, int, int]]]:
    """Per-commit ``(path, insertions, deletions)`` of ``*.py`` source files (``--numstat --no-renames``)."""
    if not hashes:
        return {}
    r = _git(git_dir, "-c", "core.quotepath=false", "log", "--stdin", "--no-walk=unsorted", "--no-renames",
             "--numstat", "--format=%x1e%H", "--", "*.py", input_bytes=("\n".join(hashes) + "\n").encode())
    out: dict[str, list[tuple[str, int, int]]] = {h: [] for h in hashes}
    for rec in r.stdout.decode("utf-8", "replace").split("\x1e"):
        lines = rec.strip().splitlines()
        if not lines or lines[0].strip() not in out:
            continue
        for ln in lines[1:]:
            a = ln.split("\t")
            if len(a) >= 3 and a[0].isdigit() and a[1].isdigit() and not a[2].startswith('"') \
                    and is_source_path(a[2]):
                out[lines[0].strip()].append((a[2], int(a[0]), int(a[1])))
    return out


def mine_modules(
    git_dir: Path, base_commit: str, S: datetime, test_files: Sequence[str], *,
    mining_cache: Optional[Path] = None, cache_name: str = "",
) -> dict[str, Any]:
    """Module partition and raw module history at the base commit (WP5 3.2); cached by SHA.

    Reads the base tree (Python source files, partition, per-module LOC with the
    ``LOC_INSTRUMENT`` rules), then walks the non-merge ancestry once: the last change
    month of every module over the full history, and per-commit numstat of the commits
    inside ``MODULE_MAX_WINDOW`` months before S. ``M.module_measurements`` cuts the
    window W from it.

    Args:
        git_dir: Bare clone containing ``base_commit``.
        base_commit: The task's base commit.
        S: Committer date of the base commit (UTC).
        test_files: Paths touched by the task's test patch (excluded from the partition).
        mining_cache: Cache directory (None disables caching).
        cache_name: File-name prefix of the cache entry (repo and SHA).

    Returns:
        ``{"roots", "module_loc", "n_source_files", "commits", "last_change_month", "timings"}``.
    """
    th = hashlib.sha256("\n".join(sorted(test_files)).encode()).hexdigest()[:10]
    cpath = (mining_cache / f"{cache_name}.{MODULE_CACHE_VERSION}.{th}.json.gz") if mining_cache else None
    if cpath is not None and cpath.exists():
        d = json.loads(gzip.decompress(cpath.read_bytes()))
        for c in d["commits"]:
            c["author_date"] = datetime.fromisoformat(c["author_date"])
        d["cached"] = True
        return d
    T: dict[str, float] = {}
    t0 = time.perf_counter()
    r = _git(git_dir, "-c", "core.quotepath=false", "ls-tree", "-r", "-z", base_commit)
    blob_of: dict[str, str] = {}
    for rec in r.stdout.decode("utf-8", "replace").split("\0"):
        meta, _, path = rec.partition("\t")
        f = meta.split()
        if len(f) == 3 and f[1] == "blob" and path.endswith(".py") and is_source_path(path):
            blob_of[path] = f[2]
    src = M.module_source_paths(blob_of, is_source_path, test_files)
    roots = M.package_roots(src)

    def mod_fn(p: str) -> Optional[str]:
        return M.module_of(p, roots, test_files)

    blobs = sorted({blob_of[p] for p in src})
    fetch_blobs(git_dir, blobs)
    still = missing_blobs(git_dir, blobs)
    if still:
        raise RuntimeError(f"{len(still)} module source blobs could not be fetched")
    loc_of: dict[str, int] = {}
    for i in range(0, len(blobs), 300):
        got = _read_blobs(git_dir, blobs[i:i + 300])
        if len(got) != len(blobs[i:i + 300]):
            raise RuntimeError("cat-file returned fewer blobs than requested")
        for sha, content in got.items():
            loc_of[sha] = 0 if (b"\0" in content[:8000] or len(content) > MAX_BLOB_BYTES) else sum(
                1 for ln in content.split(b"\n") if ln.strip())
    module_loc: dict[str, int] = {}
    for p in src:
        m = mod_fn(p)
        if m is not None:
            module_loc[m] = module_loc.get(m, 0) + loc_of[blob_of[p]]
    T["t_tree_loc"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    hist = [c for c in _py_history(git_dir, base_commit) if c["author_date"] <= S]
    last: dict[str, str] = {}
    for c in hist:  # newest first by commit order; keep the latest author-date month per module
        mk = M.month_key(c["author_date"])
        for m in {mod_fn(p) for p in c["paths"]} - {None}:
            if m in module_loc and mk > last.get(m, ""):
                last[m] = mk
    T["t_history"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    lo = M.add_months(S, -MODULE_MAX_WINDOW)
    win = [c for c in hist if lo < c["author_date"] <= S]
    fetch_blobs(git_dir, sorted({b for c in win for b in c["blobs"]}))
    files = _numstat_files(git_dir, [c["hash"] for c in win])
    T["t_numstat"] = time.perf_counter() - t0
    out = {"roots": sorted(roots), "module_loc": module_loc, "n_source_files": len(src),
           "commits": [{"hash": c["hash"], "author_date": c["author_date"], "merge": False,
                        "files": files.get(c["hash"], [])} for c in win],
           "last_change_month": last, "timings": {k: round(v, 3) for k, v in T.items()}, "cached": False}
    if cpath is not None:
        cpath.parent.mkdir(parents=True, exist_ok=True)
        ser = {**out, "commits": [{**c, "author_date": c["author_date"].isoformat()} for c in out["commits"]]}
        tmp = cpath.with_suffix(".tmp")
        tmp.write_bytes(gzip.compress(json.dumps(ser).encode()))
        tmp.replace(cpath)
    return out


def _ccn(path: str, content: bytes) -> tuple[int, int]:
    """(sum of function CCNs, function count) of one file, via lizard."""
    try:
        import lizard

        info = lizard.analyze_file.analyze_source_code(path, content.decode("utf-8", "replace"))
        return sum(f.cyclomatic_complexity for f in info.function_list), len(info.function_list)
    except Exception:  # pragma: no cover - lizard edge cases
        return 0, 0


# ---------------------------------------------------------------------------
# Fuseki
# ---------------------------------------------------------------------------

def ensure_dataset(base_url: str, dataset: str) -> bool:
    """Create the TDB2 dataset through the admin API if absent; True if created."""
    import requests

    if dataset in FG.PROTECTED_DATASETS:
        raise PermissionError(f"refusing to use protected dataset {dataset}")
    r = requests.get(f"{base_url.rstrip('/')}/$/datasets", timeout=30)
    r.raise_for_status()
    if any(d["ds.name"] == f"/{dataset}" for d in r.json().get("datasets", [])):
        return False
    r = requests.post(f"{base_url.rstrip('/')}/$/datasets", data={"dbName": dataset, "dbType": "tdb2"},
                      timeout=60)
    r.raise_for_status()
    logger.info("created Fuseki dataset %s", dataset)
    return True


def _lit(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r") + '"'


def _safe(key: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", key)


def label_triples(iri: str, labels: Sequence[str]) -> str:
    """rdf:type triples for inferred label classes (Fuseki does no subclass inference)."""
    return "".join(f"<{iri}> <{RDF}type> <{SEO}{c}> .\n" for c in labels)


# ---------------------------------------------------------------------------
# Mining (cached) and stage A
# ---------------------------------------------------------------------------

def _commit_to_json(c: dict[str, Any], evid: Mapping[str, Any], labels: Sequence[str]) -> dict[str, Any]:
    return {"h": c["hash"], "d": c["author_date"].isoformat(), "e": c["author_email"], "m": c["merge"],
            "i": c["insertions"], "x": c["deletions"], "f": c["files_changed"],
            "ev": {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in evid.items()},
            "l": sorted(labels)}


def _commit_from_json(j: Mapping[str, Any]) -> dict[str, Any]:
    ev = dict(j["ev"])
    ev["authorDate"] = datetime.fromisoformat(ev["authorDate"])
    return {"hash": j["h"], "author_date": datetime.fromisoformat(j["d"]), "author_email": j["e"],
            "merge": j["m"], "insertions": j["i"], "deletions": j["x"], "files_changed": j["f"],
            "evidence": ev, "labels": set(j["l"])}


def mine_and_stage_a(
    repo: str, snapshot: date, *, cache_dir: Path, mining_cache: Path, complexity: bool,
    simulate_loc_failure: bool, dedup: bool, jvm_mb: int, chunk_size: int, temp_dir: Path,
    tbox_dir: Optional[Path] = None, snapshot_commit: Optional[str] = None,
) -> dict[str, Any]:
    """Mine 48 months once (cached) and classify the commits with stage A.

    Args:
        repo: ``owner/name``.
        snapshot: Snapshot date (S is its last second, UTC).
        cache_dir: Clone cache.
        mining_cache: Directory of the gzip-JSON mining caches.
        complexity: Also measure mean CCN at month ends.
        simulate_loc_failure: Force the LOC-instrument failure path.
        dedup: Reason once per identical commit-evidence tuple.
        jvm_mb: Reasoner heap in MB.
        chunk_size: Commits per stage-A reasoning call.
        temp_dir: Scratch directory for the reasoner.
        tbox_dir: Alternative module directory (sensitivity rebuilds).
        snapshot_commit: WP5 snapshot mode: walk the ancestry of this commit instead of
            HEAD (the clone fetches it if missing); the cache key then includes the SHA.

    Returns:
        Dict with ``commits`` (rich dicts), ``first_commit_month``,
        ``last_commit_date``, ``loc``, ``ccn``, ``loc_info``, ``timings``,
        ``stage_a`` and ``cached``; or ``{"unmineable": reason}``.
    """
    from ontology.reasoning.reasoner import PelletReasoner

    key = f"{safe_name(repo)}.{snapshot.isoformat()}.{LOC_INSTRUMENT}.{'cx' if complexity else 'nocx'}"
    if snapshot_commit:
        key += f".{snapshot_commit}"
    ref = snapshot_commit or "HEAD"
    cache_path = mining_cache / f"{key}{'.locfail' if simulate_loc_failure else ''}.json.gz"
    if cache_path.exists():
        d = json.loads(gzip.decompress(cache_path.read_bytes()))
        d["commits"] = [_commit_from_json(j) for j in d["commits"]]
        d["last_commit_date"] = datetime.fromisoformat(d["last_commit_date"])
        d["cached"] = True
        logger.info("mining cache hit %s", cache_path.name)
        return d

    S = snapshot_end(snapshot)
    T: dict[str, float] = {}
    t0 = time.perf_counter()
    try:
        git_dir = ensure_clone(repo, cache_dir)
        if snapshot_commit:
            ensure_commit(git_dir, snapshot_commit)
    except Exception as exc:
        return {"unmineable": f"clone_failed: {exc}"[:500]}
    T["t_clone"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    hist = history_index(git_dir, S, ref)
    if not hist:
        return {"unmineable": "no_commits_up_to_snapshot"}
    first_dt, last_dt = min(d for _, d in hist), max(d for _, d in hist)
    M_S = f"{snapshot.year:04d}-{snapshot.month:02d}"
    months48 = M.truncated_window(M_S, MINING_MONTHS, M.month_key(first_dt))
    in_window = {s for s, d in hist if M.month_key(d) in set(months48)}
    commits = mine_commits(git_dir, in_window, months48[0], ref)
    churn_info = attach_churn(git_dir, commits) if commits else {}
    T["t_mine"] = time.perf_counter() - t0 + T["t_clone"]
    t0 = time.perf_counter()
    loc, ccn, loc_info = count_loc_series(git_dir, months48, complexity=complexity,
                                          simulate_failure=simulate_loc_failure, ref=ref)
    T["t_loc"] = time.perf_counter() - t0
    # stage A
    evid = {c["hash"]: M.extract_commit_evidence(
        author_name=c["author_name"], author_email=c["author_email"], message=c["message"],
        author_date=c["author_date"]) for c in commits}
    reps: dict[tuple, str] = {}
    rep_of: dict[str, str] = {}
    for sha, e in evid.items():
        sig = ((e["authorName"], e["authorEmail"], e["commitSubject"], tuple(e["coAuthorTrailer"]),
                tuple(e["branchName"])) if dedup else (sha,))
        rep_of[sha] = reps.setdefault(sig, sha)
    pellet = PelletReasoner(**({"tbox_dir": tbox_dir} if tbox_dir else {}), memory_mb=jvm_mb,
                            chunk_size=chunk_size, temp_dir=temp_dir)
    t0 = time.perf_counter()
    sa = pellet.stage_a([{"id": s, **evid[s]} for s in reps.values()])
    T["t_reason_A"] = time.perf_counter() - t0
    base_iri = AboxWriter().base + "commit/"
    for c in commits:
        c["evidence"] = evid[c["hash"]]
        c["labels"] = set(sa.labels.get(base_iri + _safe(rep_of[c["hash"]]), ()))
    stage_a = {"commits": len(commits), "reasoned_commits": len(reps),
               "inconsistent_chunks": sa.inconsistent_chunks, "chunk_timings": sa.chunk_timings,
               "tbox_sha256": pellet.tbox_sha256()}
    d = {"commits": commits, "first_commit_month": M.month_key(first_dt), "last_commit_date": last_dt,
         "n_commits_history": len(hist), "months48": months48, "loc": loc, "ccn": ccn, "loc_info": loc_info,
         "churn_info": churn_info, "timings": {k: round(v, 3) for k, v in T.items()}, "stage_a": stage_a,
         "cached": False}
    out = {**d, "commits": [_commit_to_json(c, c["evidence"], c["labels"]) for c in commits],
           "last_commit_date": last_dt.isoformat()}
    mining_cache.mkdir(parents=True, exist_ok=True)
    tmp = cache_path.with_suffix(".tmp")
    tmp.write_bytes(gzip.compress(json.dumps(out, default=str).encode()))
    tmp.replace(cache_path)
    return d


# ---------------------------------------------------------------------------
# One repository, one configuration
# ---------------------------------------------------------------------------

def pick_law_labels(labels: Sequence[str]) -> dict[str, str]:
    """One label class per Lehman law (exact ``LawXConformant``/``LawXNonConformant`` preferred)."""
    best: dict[str, tuple[int, str]] = {}
    for c in sorted(labels):
        m = LAW_RE.match(c)
        if not m or m.group(1) not in ROMAN:
            continue
        rank = 0 if not m.group(3) else 1
        if m.group(1) not in best or rank < best[m.group(1)][0]:
            best[m.group(1)] = (rank, c)
    return {k: v[1] for k, v in sorted(best.items(), key=lambda kv: ROMAN.index(kv[0]))}


def cf_label(counts: Sequence[int], months_since_last: int, alpha: float, dormancy: int,
             variant: str) -> str:
    """LOC-free comparator CF (pre-registration 2.3): A / S / P / U from commit counts and recency.

    An independent implementation on purpose: it calls pymannkendall directly and
    shares no code with ``measures.mann_kendall`` or the ontology.
    """
    if months_since_last >= dormancy:
        return "P"
    if len(counts) < 4:
        return "U"
    import warnings

    import pymannkendall as mk

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        r = (mk.original_test if variant == "original" else mk.hamed_rao_modification_test)(list(counts))
    return "S" if (r.p < alpha and r.Tau < 0) else "A"


PRIMARY = {"alpha": 0.05, "L": PRIMARY_WINDOW, "D": 12, "G": 0.05, "mk": "orig"}
"""Primary configuration of the pre-registration (values mirror thresholds.yaml; checked at start-up)."""
MK_LONG = {"orig": "original", "hr": "hamed_rao"}
SENSITIVITY = (  # one factor at a time (prereg 8): S1 alpha, S2 L, S3 D, S4 G, S5 MK variant
    [{"alpha": a} for a in (0.01, 0.1)] + [{"L": v} for v in (24, 48)] + [{"D": v} for v in (6, 18, 24)]
    + [{"G": v} for v in (0.0, 0.02, 0.1)] + [{"mk": "hr"}])


def cfg_id(alpha: float, L: int, D: int, G: float, mk: str) -> str:
    """Config id used as the key of ``inferred`` (same format as run_rq1_v2.cfg_id)."""
    return f"a{alpha:g}_L{int(L)}_D{int(D)}_G{G:g}_{mk}"


def config_list(sensitivity: bool = True) -> list[dict[str, Any]]:
    """The primary configuration followed by the one-at-a-time sensitivity configurations."""
    cfgs = [dict(PRIMARY)]
    if sensitivity:
        cfgs += [{**PRIMARY, **ch} for ch in SENSITIVITY]
    return cfgs


def tbox_key(cfg: Mapping[str, Any]) -> str:
    """Key of the TBox a configuration needs (only alpha, D and G change the TBox)."""
    return f"a{cfg['alpha']:g}_D{int(cfg['D'])}_G{cfg['G']:g}"


def check_primary_matches_register() -> None:
    """The hard-coded primary configuration must equal thresholds.yaml (pre-registration 2.2)."""
    from ontology.modules.build_ontology import load_thresholds

    t = load_thresholds()
    got = {"alpha": t["mk_alpha"]["value"], "D": t["rb_dormancy_months"]["value"],
           "G": t["rb_min_rel_loc_growth_per_year"]["value"]}
    want = {k: PRIMARY[k] for k in got}
    if got != want:
        raise RuntimeError(f"thresholds.yaml {got} differs from the pre-registered primary {want}")


def build_tboxes(root: Path, configs: Sequence[Mapping[str, Any]]) -> dict[str, Optional[Path]]:
    """Build each distinct (alpha, D, G) TBox once; the primary one is the committed modules (None).

    Args:
        root: Directory for the variant modules (``root/<tbox_key>/``).
        configs: Configurations that will be reasoned.

    Returns:
        ``{tbox_key: module directory or None for the default modules}``.
    """
    import yaml

    from ontology.modules import build_ontology as BO

    primary_key = tbox_key(PRIMARY)
    out: dict[str, Optional[Path]] = {}
    doc = yaml.safe_load(BO.THRESHOLDS_FILE.read_text())
    for cfg in configs:
        k = tbox_key(cfg)
        if k in out:
            continue
        if k == primary_key:
            out[k] = None
            continue
        d = root / k
        if not (d / "seo-full.owl").exists():
            d.mkdir(parents=True, exist_ok=True)
            vals = {"mk_alpha": float(cfg["alpha"]), "rb_dormancy_months": int(cfg["D"]),
                    "rb_min_rel_loc_growth_per_year": float(cfg["G"])}
            variant = {**doc, "thresholds": [
                {**t, "value": vals[t["id"]]} if t["id"] in vals else t for t in doc["thresholds"]]}
            (d / "thresholds.yaml").write_text(yaml.safe_dump(variant, sort_keys=False))
            BO.build_all(d / "thresholds.yaml", d)
        out[k] = d
    return out


def result_path(out_dir: Path, repo: str) -> Path:
    """Per-repo JSON path (all configurations are in one file)."""
    return out_dir / f"{safe_name(repo)}.json"


def _lib_versions() -> dict[str, str]:
    import importlib.metadata as md

    out = {}
    for p in ("owlready2", "pymannkendall", "lizard", "numpy", "scipy"):
        try:
            out[p] = md.version(p)
        except Exception:
            out[p] = "?"
    out["python"] = sys.version.split()[0]
    out["git"] = git_version()
    return out


def _measure_config(mined: Mapping[str, Any], snapshot: date, L: int, mk: str) -> dict[str, Any]:
    """Re-measure one (L, MK variant) configuration from the cached mining output."""
    M_S = f"{snapshot.year:04d}-{snapshot.month:02d}"
    months = M.truncated_window(M_S, L, mined["first_commit_month"])
    month_set = set(months)
    commits = [c for c in mined["commits"] if M.month_key(c["author_date"]) in month_set]
    last_month = M.month_key(mined["last_commit_date"])
    loc_ok = mined["loc_info"]["status"] == "ok" and all(mined["loc"].get(m) is not None for m in months)
    loc = {m: mined["loc"][m] for m in months} if loc_ok else {m: None for m in months}
    ccn = {m: mined["ccn"].get(m) for m in months} if loc_ok else {m: None for m in months}

    def build_series(use_labels: bool) -> list[dict[str, Any]]:
        def has(cls: str) -> Any:
            return lambda c: cls in c["labels"]
        s = M.monthly_series(
            commits, months[0], months[-1],
            bug_fix_predicate=has("BugFixCommit") if use_labels else None,
            feature_predicate=has("FeatureCommit") if use_labels else None, loc_by_month=loc)
        for row in s:  # None (not measured) leaves the complexity measurements unasserted
            row["complexity_mean"] = ccn[row["month"]]
        if use_labels:
            per = {m: [0, 0] for m in months}
            for c in commits:
                k = M.month_key(c["author_date"])
                per[k][0] += 1
                per[k][1] += "AgentCommit" in c["labels"]
            for row in s:
                n, a = per[row["month"]]
                row["agent_commit_ratio"] = a / max(n, 1)
        return s

    kw = dict(mk_variant=MK_LONG[mk], snapshot_month=M_S, last_commit_month=last_month,
              distinct_authors_in_window=M.distinct_authors(commits))
    series0 = build_series(False)
    base = M.project_measurements(series0, **kw)
    series1 = build_series(True)
    full = M.project_measurements(series1, **kw)
    return {"months": months, "commits": commits, "loc_ok": loc_ok, "series0": series0, "series1": series1,
            "base": base, "full": full, "derived": {k: v for k, v in full.items() if base.get(k) != v},
            "snaps": M.month_snapshots(series0), "last_month": last_month,
            "label_counts": {cls: sum(1 for c in commits if cls in c["labels"])
                             for cls in ("BugFixCommit", "FeatureCommit", "AgentCommit")}}


def populate_repo(
    repo: str,
    snapshot: date,
    out_dir: Path,
    *,
    sensitivity: bool = True,
    tboxes: Optional[Mapping[str, Optional[Path]]] = None,
    replaces: Optional[str] = None,
    cache_dir: Path = DEFAULT_REPO_CACHE,
    mining_cache: Path = DEFAULT_MINING_CACHE,
    fuseki_url: Optional[str] = DEFAULT_FUSEKI,
    dataset: str = DEFAULT_DATASET,
    explain: bool = True,
    complexity: bool = False,
    simulate_loc_failure: bool = False,
    dedup: bool = True,
    jvm_mb: int = 1800,
    chunk_size: int = 1000,
    snapshot_commit: Optional[str] = None,
    task_id: Optional[str] = None,
    test_files: Sequence[str] = (),
) -> dict[str, Any]:
    """Run the pipeline for one repository (primary plus sensitivity configurations); write its JSON.

    The output is the population JSON read by ``run_rq1_v2.adapt_population_json``.
    Mining and stage A run once (cached); each configuration re-measures from the
    cache and runs stage B (HermiT) over the TBox of its (alpha, D, G). Explanations,
    Fuseki write-back and the detailed record cover the primary configuration only.

    Args:
        repo: ``owner/name``.
        snapshot: Snapshot date.
        out_dir: Directory for the per-repo JSON (and scratch files).
        sensitivity: Also reason over the 11 one-at-a-time sensitivity configurations.
        tboxes: ``build_tboxes`` result (built into ``out_dir/_tboxes`` when None).
        replaces: Ground-truth repo this repo replaces (prereg 4), recorded verbatim.
        cache_dir: Clone cache.
        mining_cache: Mining-cache directory.
        fuseki_url: Fuseki base URL, or None to skip write-back.
        dataset: Fuseki dataset (never ``seo``).
        explain: Run the Pellet-CLI explanations (primary only).
        complexity: Also measure mean CCN at month ends.
        simulate_loc_failure: Force the LOC-instrument failure path (test hook).
        dedup: Reason once per identical commit-evidence tuple.
        jvm_mb: Reasoner JVM heap in MB (at most 2000).
        chunk_size: Commits per stage-A reasoning call.
        snapshot_commit: WP5 snapshot mode (``--snapshot-commit``): ancestry-only history from this
            base commit, primary configuration only, module measurements anchored at the commit's
            committer date S, explanations for stage, laws, anti-patterns and module labels, and a
            ``modules`` block. ``snapshot`` must then be the last day of M_S (see ``resolve_task_snapshot``).
        task_id: Task id (names the per-task JSON and keys the IRIs); required with ``snapshot_commit``.
        test_files: Paths touched by the task's test patch (excluded from the module partition).

    Returns:
        The result dict.
    """
    from ontology.modules.build_ontology import load_thresholds
    from ontology.reasoning import explain as EX
    from ontology.reasoning.reasoner import HermitReasoner

    check_primary_matches_register()
    wp5 = snapshot_commit is not None
    if wp5 and not task_id:
        raise ValueError("snapshot mode needs a task id")
    key = task_id if wp5 else repo  # IRI and graph key; one task = one project individual
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out_dir / "_tmp" / safe_name(key)
    T: dict[str, Any] = {}
    t_all = time.perf_counter()
    M_S = f"{snapshot.year:04d}-{snapshot.month:02d}"
    configs = config_list(sensitivity and not wp5)
    if tboxes is None:
        tboxes = build_tboxes(out_dir / "_tboxes", configs)
    result: dict[str, Any] = {
        "repo": repo, "snapshot_date": snapshot.isoformat(), "status": "ok", "unmineable": False,
        "unmineable_reason": None, "replaces": replaces,
        "settings": {"dedup": dedup, "complexity": complexity, "dataset": dataset if fuseki_url else None,
                     "sensitivity": sensitivity},
        "versions": _lib_versions()}
    if wp5:
        result["task_id"], result["base_commit"] = task_id, snapshot_commit
        result["settings"].update({"snapshot_commit": snapshot_commit, "sensitivity": False,
                                   "mode": "wp5_snapshot_commit", "test_patch_files": sorted(test_files)})
        path = out_dir / f"{safe_name(task_id)}.json"
    else:
        path = result_path(out_dir, repo)

    mined = mine_and_stage_a(repo, snapshot, cache_dir=cache_dir, mining_cache=mining_cache,
                             complexity=complexity, simulate_loc_failure=simulate_loc_failure,
                             dedup=dedup, jvm_mb=jvm_mb, chunk_size=chunk_size, temp_dir=tmp,
                             snapshot_commit=snapshot_commit)
    if "unmineable" in mined:
        result.update(status="unmineable", unmineable=True, unmineable_reason=mined["unmineable"])
        return _write(path, result)
    T.update(mined["timings"])
    T["mining_cached"] = mined["cached"]

    # -- primary measurements and the 48-month series for the analysis script
    prim = _measure_config(mined, snapshot, PRIMARY["L"], "orig")
    m48 = M.truncated_window(M_S, MINING_MONTHS, mined["first_commit_month"])
    c48 = {m: 0 for m in m48}
    for c in mined["commits"]:
        c48[M.month_key(c["author_date"])] += 1
    loc48_ok = mined["loc_info"]["status"] == "ok" and all(mined["loc"].get(m) is not None for m in m48)
    full = prim["full"]
    commits = prim["commits"]
    last_dt: datetime = mined["last_commit_date"]
    result["measures"] = {
        **full,
        "featCommitCount": prim["label_counts"]["FeatureCommit"],
        "bugFixCommitCount": prim["label_counts"]["BugFixCommit"],
        "commitCount": len(commits),
        "monthly_series": {"months": m48, "commits": [c48[m] for m in m48],
                           "loc": [mined["loc"][m] for m in m48] if loc48_ok else None}}
    result["window"] = {
        "L": PRIMARY["L"], "first_month": prim["months"][0], "last_month": prim["months"][-1],
        "n_months": len(prim["months"]), "left_truncated": len(prim["months"]) < PRIMARY["L"],
        "first_commit_month": mined["first_commit_month"], "mined_months": len(m48),
        "commits_in_window": len(commits), "commits_in_history": mined["n_commits_history"]}
    result["loc_instrument"] = {**mined["loc_info"], "series_present": loc48_ok,
                                "extensions": sorted(SOURCE_EXTENSIONS), "excluded_dirs": list(EXCLUDED_DIRS),
                                "max_blob_bytes": MAX_BLOB_BYTES, "first_parent": True}
    result["mining"] = {"churn": mined["churn_info"], "timings": mined["timings"], "cached": mined["cached"]}
    result["stage_a"] = mined["stage_a"]
    result["activity"] = {
        "last_commit_date": last_dt.isoformat(),
        "months_since_last_commit": M.months_since_last_commit(M_S, prim["last_month"]),
        "distinct_authors_in_window": M.distinct_authors(commits),
        "merge_commits_in_window": sum(1 for c in commits if c["merge"])}
    agent_dates = sorted(c["author_date"] for c in commits if "AgentCommit" in c["labels"])
    result["agent_adoption_date"] = agent_dates[0].isoformat() if agent_dates else None
    result["commit_label_counts"] = prim["label_counts"]
    result["series_months"] = prim["series0"]
    result["measures_derived"] = prim["derived"]

    # -- WP5: module partition and module measurements anchored at S (commit date of the base)
    mod_rows: dict[str, dict[str, Any]] = {}
    if wp5:
        t0 = time.perf_counter()
        git_dir = cache_dir / f"{safe_name(repo)}.git"
        S_base = commit_dates(git_dir, snapshot_commit)[1]
        modmine = mine_modules(git_dir, snapshot_commit, S_base, test_files, mining_cache=mining_cache,
                               cache_name=f"{safe_name(repo)}.{snapshot_commit}")
        roots = frozenset(modmine["roots"])
        W = load_thresholds()["mod_window_months"]["value"]
        mod_rows = M.module_measurements(
            modmine["commits"], modmine["module_loc"], S_base, int(W),
            lambda p: M.module_of(p, roots, test_files), modmine["last_change_month"])
        result["modules_meta"] = {
            "anchor_S": S_base.isoformat(), "window_months": int(W), "package_roots": sorted(roots),
            "n_modules": len(mod_rows), "n_source_files": modmine["n_source_files"],
            "n_window_commits": sum(1 for c in modmine["commits"]
                                    if M.add_months(S_base, -int(W)) < c["author_date"] <= S_base),
            "cached": modmine["cached"], "timings": modmine["timings"],
            "module_loc_instrument": LOC_INSTRUMENT}
        T["t_modules"] = time.perf_counter() - t0
        result["settings"]["package_roots"] = sorted(roots)

    # -- stage B for every configuration
    thr = load_thresholds()
    inferred: dict[str, Any] = {}
    cache: dict[tuple[int, str], dict[str, Any]] = {(PRIMARY["L"], "orig"): prim}
    t_b = 0.0
    primary_hermit = primary_abox = primary_rb = primary_iri = None
    primary_mods: dict[str, str] = {}
    for cfg in configs:
        cid = cfg_id(cfg["alpha"], cfg["L"], cfg["D"], cfg["G"], cfg["mk"])
        mc = cache.get((cfg["L"], cfg["mk"])) or _measure_config(mined, snapshot, cfg["L"], cfg["mk"])
        cache[(cfg["L"], cfg["mk"])] = mc
        wb = AboxWriter()
        iri = wb.project(key, mc["full"], None, close_months=False)
        mod_iris = {m: wb.module(iri, m, M.module_abox_properties(row)) for m, row in mod_rows.items()}
        abox = wb.ntriples()
        tdir = tboxes[tbox_key(cfg)]
        hermit = HermitReasoner(**({"tbox_dir": tdir} if tdir else {}), memory_mb=jvm_mb, temp_dir=tmp)
        t0 = time.perf_counter()
        rb = hermit.infer(abox)
        dt = time.perf_counter() - t0
        t_b += dt
        labels = sorted(rb.labels_of(iri))
        stage_found = [c for c in labels if c in STAGE_LABELS]
        entry: dict[str, Any] = {
            "classes": labels, "inconsistent": not rb.consistent, "inconsistency_explanation": None,
            "undetermined_reason": None, "explanation_graph": None, "tbox_sha256": rb.tbox_sha256,
            "abox_triples": wb.n_triples, "t_reason_B_s": round(dt, 3)}
        if not rb.consistent:
            entry["inconsistency_error"] = rb.error
        c1_found = [c for c in stage_found if c in C1_MAP]
        c2_found = [c for c in stage_found if c in C2_MAP]
        reasons = []
        if not rb.consistent:
            reasons.append("reasoner_inconsistent")
        if not mc["loc_ok"]:
            reasons.append("loc_instrument_failed")
        elif "locMKTau" not in mc["full"]:
            reasons.append("loc_series_too_short_for_mk")
        if not (c1_found and c2_found):
            entry["undetermined_reason"] = ";".join(reasons) or "no_stage_class_inferred"
        inferred[cid] = entry
        if cfg == PRIMARY:
            primary_hermit, primary_abox, primary_rb, primary_iri = hermit, abox, rb, iri
            primary_mods = mod_iris
    T["t_reason_B"] = t_b
    T["n_configs"] = len(configs)

    pid = cfg_id(**PRIMARY)
    pe = inferred[pid]
    labels = pe["classes"]
    stages = [c for c in labels if c in STAGE_LABELS]
    laws = pick_law_labels(labels)
    tb = primary_rb.tbox_sha256 or "0" * 12
    pe["explanation_graph"] = FG.explanations_graph(key, tb)
    result.update({
        "inferred": inferred, "primary_config": pid, "project_iri": primary_iri,
        "consistent": primary_rb.consistent, "inferred_labels": labels, "stage_labels": stages,
        "law_labels": laws, "tbox_sha256_stage_b": primary_rb.tbox_sha256,
        "tbox_sha256_stage_a": mined["stage_a"]["tbox_sha256"],
        "summary": {
            "c1": next((C1_MAP[c][1] for c in labels if c in C1_MAP), "U"),
            "c2": next((C2_MAP[c] for c in labels if c in C2_MAP), "U"),
            "cf": cf_label([r["commit_count"] for r in prim["series0"]],
                           result["activity"]["months_since_last_commit"], thr["mk_alpha"]["value"],
                           thr["rb_dormancy_months"]["value"], "original"),
            "note": "debug summary; run_rq1_v2.py reads `inferred` and recomputes CF itself"}})

    # -- WP5: module labels (inferred in the same HermiT pass) and the `modules` block
    mod_labels: dict[str, str] = {}
    if wp5:
        result["modules"] = {}
        for m, row in sorted(mod_rows.items()):
            cl = sorted(c for c in primary_rb.labels_of(primary_mods[m]) if c in MODULE_LABEL_CLASSES)
            lab = next((c for c in ("StableModule", "ActiveModule") if c in cl), "undetermined")
            mod_labels[m] = lab
            result["modules"][m] = {"label": lab, "classes": cl, "measures": row,
                                    "iri": primary_mods[m], "abox_asserted": M.module_abox_properties(row) == row}
        result["modules_meta"]["label_counts"] = {
            k: sum(1 for v in mod_labels.values() if v == k) for k in ("StableModule", "ActiveModule", "undetermined")}
        result["modules_meta"]["thresholds"] = {
            k: thr[k]["value"] for k in ("mod_window_months", "mod_stable_max_rel_churn",
                                         "mod_stable_max_change_months")}

    # -- explanations (primary only)
    T["t_explain"] = 0.0
    expl_nt = ""
    if explain:
        t0 = time.perf_counter()
        exps: dict[str, Any] = {}
        try:
            rdfxml = EX.merged_rdfxml(primary_hermit, primary_abox)
            if not primary_rb.consistent:
                ex = EX.explain_inconsistent(primary_hermit, rdfxml)
                exps["_inconsistent"] = ex.to_json()
                pe["inconsistency_explanation"] = ex.raw_text[:4000]
            else:
                targets = {("stage:" + c): c for c in stages}
                targets.update({f"law{k}": v for k, v in laws.items()})
                inds = {tag: primary_iri for tag in targets}
                if wp5:  # anti-patterns and the module labels C can show (the K_MAX largest by LOC)
                    for c in labels:
                        if c.startswith("Exhibits"):
                            targets[f"anti:{c}"], inds[f"anti:{c}"] = c, primary_iri
                    shown = sorted((m for m in mod_labels if mod_labels[m] != "undetermined"),
                                   key=lambda m: (-mod_rows[m]["moduleLoc"], m))[:MODULE_EXPLAIN_TOP]
                    for m in shown:
                        targets[f"module:{m}"], inds[f"module:{m}"] = mod_labels[m], primary_mods[m]
                for tag, cls in targets.items():
                    ex = EX.explain_instance(primary_hermit, rdfxml, inds[tag], cls)
                    attempts = 1
                    while wp5 and ex.error and "pruned node" in ex.error and attempts < 3:
                        # Pellet 2.3.1 fails non-deterministically on datatype restrictions (WP1 note);
                        # the same call is repeated twice at most before the template fallback applies.
                        ex = EX.explain_instance(primary_hermit, rdfxml, inds[tag], cls)
                        attempts += 1
                    exps[tag] = {"class": cls, **({"individual": inds[tag], "attempts": attempts} if wp5 else {}),
                                 **ex.to_json()}
                    for i, j in enumerate(ex.justifications):
                        node = f"{AboxWriter().base}{_safe(key)}/justification/{cls}/{i}"
                        expl_nt += EX.justification_ntriples(inds[tag], SEO + cls, j, node)
        except Exception as exc:  # explanation is best effort
            logger.exception("explain failed for %s", repo)
            exps["_error"] = str(exc)[:500]
        result["explanations"] = exps
        T["t_explain"] = time.perf_counter() - t0
        T["n_explain_calls"] = sum(1 for k in exps if not k.startswith("_"))

    # -- write back (primary only)
    t0 = time.perf_counter()
    if fuseki_url:
        try:
            result["fuseki"] = _write_fuseki(fuseki_url, dataset, key, prim["base"], prim["snaps"], commits,
                                             prim["derived"], primary_rb, labels, expl_nt, primary_iri,
                                             snapshot, modules=({m: (primary_mods[m], M.module_abox_properties(r),
                                                                     [mod_labels[m]] if mod_labels[m] != "undetermined" else [])
                                                                 for m, r in mod_rows.items()} if wp5 else None))
        except Exception as exc:
            logger.exception("Fuseki write-back failed for %s", repo)
            result["fuseki"] = {"error": str(exc)[:500]}
    T["t_writeback"] = time.perf_counter() - t0
    T["t_total"] = time.perf_counter() - t_all
    result["timings"] = {k: round(v, 3) if isinstance(v, float) else v for k, v in T.items()}
    shutil.rmtree(tmp, ignore_errors=True)
    return _write(path, result)


def _write_fuseki(base_url: str, dataset: str, repo: str, base: Mapping[str, Any],
                  snaps: Sequence[Mapping[str, Any]], commits: Sequence[Mapping[str, Any]],
                  derived: Mapping[str, Any], rb: Any, labels: Sequence[str], expl_nt: str,
                  proj_iri: str, snapshot: date,
                  modules: Optional[Mapping[str, tuple[str, Mapping[str, Any], Sequence[str]]]] = None,
                  ) -> dict[str, Any]:
    """PUT the five named graphs of one repository (WP5: one task); returns the triple counts."""
    ensure_dataset(base_url, dataset)
    wa = AboxWriter()
    wa.project(repo, base, snaps, close_months=False)
    for m, (_, props, _) in (modules or {}).items():
        wa.module(proj_iri, m, props)
    wc = AboxWriter()
    for c in commits:
        wc.commit(c["hash"], c["evidence"])
    wd = AboxWriter()
    wd._props(wd._iri(proj_iri), derived)  # derived measurements attach to the asserted project
    inferred = rb.inferred_ntriples + label_triples(proj_iri, labels)
    for m_iri, _, m_labels in (modules or {}).values():
        inferred += label_triples(m_iri, m_labels)
    for c in commits:
        inferred += label_triples(AboxWriter().base + "commit/" + _safe(c["hash"]), sorted(c["labels"]))
    tb = rb.tbox_sha256 or "0" * 12
    g_inf = FG.inferred_graph(repo, tb)
    prov = (f"<{g_inf}> <{SEO}reasoner> {_lit('HermiT (Owlready2 0.51 bundle), stage A: Pellet 2.3.1')} .\n"
            f"<{g_inf}> <{SEO}tboxSha256> {_lit(tb)} .\n"
            f"<{g_inf}> <{SEO}snapshotDate> \"{snapshot.isoformat()}\"^^<{XSD}date> .\n"
            f"<{g_inf}> <http://www.w3.org/ns/prov#generatedAtTime> "
            f"\"{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\"^^<{XSD}dateTime> .\n")
    graphs = {
        FG.abox_graph(repo): wa.ntriples(),
        f"urn:senso:commits:{repo}": wc.ntriples(),
        FG.derived_graph(repo): wd.ntriples(),
        g_inf: inferred + prov,
        FG.explanations_graph(repo, tb): expl_nt or "\n",
    }
    out = {}
    for g, nt in graphs.items():
        FG.put_graph(base_url, dataset, g, nt)
        out[g] = nt.count("\n")
    return {"dataset": dataset, "graph_triples": out}


def _write(path: Path, result: dict[str, Any]) -> dict[str, Any]:
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(result, indent=1, default=str))
    tmp.replace(path)
    return result


def parse_snapshot(s: str) -> date:
    """Parse ``YYYY-MM-DD``."""
    return date.fromisoformat(s)


def add_common_args(ap: argparse.ArgumentParser) -> None:
    """CLI options shared with ``run_v2_population.py``."""
    ap.add_argument("--no-sensitivity", action="store_true",
                    help="primary configuration only (default: primary + 11 one-at-a-time configs)")
    ap.add_argument("--cache-dir", type=Path, default=DEFAULT_REPO_CACHE)
    ap.add_argument("--mining-cache", type=Path, default=DEFAULT_MINING_CACHE)
    ap.add_argument("--fuseki-url", default=DEFAULT_FUSEKI)
    ap.add_argument("--dataset", default=DEFAULT_DATASET, help="Fuseki dataset (never 'seo')")
    ap.add_argument("--no-fuseki", action="store_true", help="skip the Fuseki write-back")
    ap.add_argument("--no-explain", action="store_true", help="skip Pellet-CLI explanations (~2 s each)")
    ap.add_argument("--complexity", action="store_true", help="also measure mean CCN at month ends (lizard)")
    ap.add_argument("--simulate-loc-failure", action="store_true",
                    help="test hook: force the LOC-instrument failure path")
    ap.add_argument("--no-dedup", action="store_true", help="reason over every commit, not unique evidence")
    ap.add_argument("--jvm-mb", type=int, default=1800, help="reasoner JVM heap (MB, at most 2000)")


def options_from_args(a: argparse.Namespace) -> dict[str, Any]:
    """Keyword arguments for ``populate_repo`` from parsed CLI options."""
    if a.dataset in FG.PROTECTED_DATASETS:
        raise SystemExit(f"dataset '{a.dataset}' is protected (JSS-era data)")
    return dict(sensitivity=not a.no_sensitivity, cache_dir=a.cache_dir, mining_cache=a.mining_cache,
                fuseki_url=None if a.no_fuseki else a.fuseki_url, dataset=a.dataset,
                explain=not a.no_explain, complexity=a.complexity,
                simulate_loc_failure=a.simulate_loc_failure, dedup=not a.no_dedup,
                jvm_mb=min(a.jvm_mb, 2000))


def resolve_task_snapshot(repo: str, base_commit: str, cache_dir: Path) -> dict[str, Any]:
    """WP5 reference point of a task (plan 3.1 item 1): S, M_S and the repository-level snapshot date.

    S is the committer date of ``base_commit`` (UTC). M_S is the last complete calendar
    month before the month of S; the snapshot date is the last day of M_S. Clones the
    repository and fetches the commit if needed.
    """
    import calendar

    git_dir = ensure_clone(repo, cache_dir)
    ensure_commit(git_dir, base_commit)
    _, S = commit_dates(git_dir, base_commit)
    y, m = (S.year, S.month - 1) if S.month > 1 else (S.year - 1, 12)
    snap = date(y, m, calendar.monthrange(y, m)[1])
    return {"S": S, "M_S": f"{y:04d}-{m:02d}", "snapshot_date": snap}


def main() -> int:
    """CLI entry point for one repository (RQ1 snapshot date) or one WP5 task (snapshot commit)."""
    ap = argparse.ArgumentParser(description="v2 population pipeline for one repo (Paper 1)")
    ap.add_argument("--repo", required=True, help="owner/name")
    ap.add_argument("--snapshot-date", default="2025-06-30")
    ap.add_argument("--snapshot-commit", metavar="SHA", default=None,
                    help="WP5 mode: ancestry-only history from this base commit (needs --task-id); "
                         "primary configuration only; --snapshot-date is ignored")
    ap.add_argument("--task-id", default=None, help="WP5 task id (names the output JSON)")
    ap.add_argument("--test-patch-files", default=None, metavar="FILE",
                    help="WP5: the task's test patch (unified diff) or a list of its paths, one per line")
    ap.add_argument("--output-dir", type=Path, required=True)
    add_common_args(ap)
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    if a.snapshot_commit:
        if not a.task_id:
            ap.error("--snapshot-commit needs --task-id")
        if a.dataset == DEFAULT_DATASET:
            a.dataset = DEFAULT_WP5_DATASET
        if a.dataset in FG.PROTECTED_DATASETS | {DEFAULT_DATASET}:
            raise SystemExit(f"dataset '{a.dataset}' is reserved for earlier runs; WP5 uses {DEFAULT_WP5_DATASET}")
        if a.cache_dir == DEFAULT_REPO_CACHE:
            a.cache_dir = DEFAULT_WP5_REPO_CACHE
        if a.mining_cache == DEFAULT_MINING_CACHE:
            a.mining_cache = DEFAULT_WP5_REPO_CACHE.parent / "mining"
        ref = resolve_task_snapshot(a.repo, a.snapshot_commit, a.cache_dir)
        logger.info("task %s: S=%s M_S=%s", a.task_id, ref["S"].isoformat(), ref["M_S"])
        res = populate_repo(a.repo, ref["snapshot_date"], a.output_dir, **options_from_args(a),
                            snapshot_commit=a.snapshot_commit, task_id=a.task_id,
                            test_files=load_test_patch_files(a.test_patch_files))
        logger.info("%s: status=%s summary=%s timings=%s", a.task_id, res["status"], res.get("summary"),
                    res.get("timings"))
        return 0
    res = populate_repo(a.repo, parse_snapshot(a.snapshot_date), a.output_dir, **options_from_args(a))
    logger.info("%s: status=%s summary=%s timings=%s", a.repo, res["status"], res.get("summary"),
                res.get("timings"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
