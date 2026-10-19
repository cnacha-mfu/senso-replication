"""WP5 measured outcomes Y0-Y6 (plan section 4), computed without any LLM.

Used by Paper 1 (JSEP rebuild), WP5.

  Y0 patch produced; Y1 sum of lizard CCN change over touched functions; Y2 new cross-module import edges;
  Y3 share of changed lines in StableModule modules (+ Y3_gold, Y3_excess, Y3w); Y4 log2(agent changed
  lines / gold changed lines); Y5 files touched; Y6 steps. Modules follow plan 3.2 through
  ontology/population/measures.module_of with the package roots of the base tree. Module labels come from
  the per-task population JSON (`modules` block, written by populate_v2.py --snapshot-commit); without it
  Y3 and friends are None and Y2 uses roots computed from the base tree.

Usage:
    imported by wp5.evaluate; the functions take a working copy where the patch is applied and HEAD = base.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import logging
import math
import re
import sys
from pathlib import Path
from typing import Any, Optional

import lizard

from .common import PROJECT_ROOT, rpath, run

logger = logging.getLogger("wp5.metrics")

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", re.M)
_M = None


def measures():
    """ontology/population/measures.py, loaded by path (it has no heavy dependencies)."""
    global _M
    if _M is None:
        spec = importlib.util.spec_from_file_location("wp5_measures", PROJECT_ROOT / "ontology/population/measures.py")
        _M = importlib.util.module_from_spec(spec)
        sys.modules["wp5_measures"] = _M
        spec.loader.exec_module(_M)
    return _M


def is_test(path: str, test_files: set[str]) -> bool:
    return measures().is_test_path(path, test_files)


def split_diff(diff: str) -> dict[str, str]:
    """new-side path -> its diff block."""
    out: dict[str, str] = {}
    for block in re.split(r"(?m)^(?=diff --git )", diff):
        m = re.match(r"diff --git a/(\S+) b/(\S+)", block)
        if m:
            out[m.group(2)] = block
    return out


def filter_diff(diff: str, drop_paths: set[str]) -> str:
    """Drop test-patch files and binary file changes (an agent edits text; a spurious binary diff, e.g. a
    tracked PNG re-materialised by the partial clone, must not make the whole patch unappliable)."""
    return "".join(b for p, b in split_diff(diff).items()
                   if p not in drop_paths and "GIT binary patch" not in b and not re.search(r"(?m)^Binary files ", b))


def lines_by_file(diff: str, test_files: set[str]) -> dict[str, int]:
    """Changed lines (added + deleted) per non-test file."""
    out: dict[str, int] = {}
    for p, b in split_diff(diff).items():
        if is_test(p, test_files):
            continue
        n = sum(1 for ln in b.splitlines()
                if (ln.startswith("+") and not ln.startswith("+++")) or (ln.startswith("-") and not ln.startswith("---")))
        out[p] = n
    return out


def diff_size(diff: str, test_files: set[str]) -> dict[str, int]:
    f = lines_by_file(diff, test_files)
    return {"total": sum(f.values()), "files": len(f)}


def _ranges(block: str) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    old, new = [], []
    for m in HUNK_RE.finditer(block):
        os_, ol, ns, nl = int(m.group(1)), int(m.group(2) or 1), int(m.group(3)), int(m.group(4) or 1)
        if ol:
            old.append((os_, os_ + ol - 1))
        if nl:
            new.append((ns, ns + nl - 1))
    return old, new


def _funcs(path: str, text: str) -> dict[str, tuple[int, int, int]]:
    try:
        info = lizard.analyze_file.analyze_source_code(path, text)
    except Exception:  # noqa: BLE001
        return {}
    return {f.long_name: (f.cyclomatic_complexity, f.start_line, f.end_line) for f in info.function_list}


def _overlap(a: tuple[int, int], rs: list[tuple[int, int]]) -> bool:
    return any(a[0] <= r[1] and r[0] <= a[1] for r in rs)


def _base_text(repo_dir: Path, p: str) -> str:
    rc, t = run(["git", "show", f"HEAD:{p}"], cwd=repo_dir)
    return t if rc == 0 else ""


def y1_ccn(repo_dir: Path, diff: str, tp: set[str]) -> dict[str, Any]:
    """Plan 4.3 Y1: touched functions matched by (file, long_name); added = base CCN 0, deleted = patched CCN 0."""
    total = touched = 0
    for p, block in split_diff(diff).items():
        if is_test(p, tp) or not p.endswith(".py"):
            continue
        f = repo_dir / p
        new_text = f.read_text(errors="replace") if f.exists() else ""
        old_r, new_r = _ranges(block)
        of, nf = _funcs(p, _base_text(repo_dir, p)), _funcs(p, new_text)
        for name, (c, s, e) in nf.items():
            if name not in of or _overlap((s, e), new_r):
                touched += 1
                total += c - (of[name][0] if name in of else 0)
        for name, (c, s, e) in of.items():
            if name not in nf:
                touched += 1
                total -= c
    return {"delta_ccn": total, "touched_functions": touched}


# ----------------------------------------------------------------------------
# Modules (plan 3.2) and Y2
# ----------------------------------------------------------------------------
def base_roots(repo_dir: Path, tp: set[str]) -> tuple[frozenset[str], set[str]]:
    """Package roots of the base tree and the set of tree paths (HEAD = base)."""
    M = measures()
    rc, out = run(["git", "ls-tree", "-r", "--name-only", "HEAD"], cwd=repo_dir, timeout=120)
    paths = set(out.splitlines())
    src = M.module_source_paths(paths, lambda p: True, tp)
    return M.package_roots(src), paths


def load_population(cfg: dict, task_id: str) -> Optional[dict]:
    from .common import safe_id
    f = rpath(cfg, "output_dir") / "population" / f"{safe_id(task_id)}.json"
    if not f.is_file():
        f = rpath(cfg, "output_dir") / "population" / f"{task_id}.json"
    return json.loads(f.read_text()) if f.is_file() else None


def _resolve_import(file: str, node: Any, tree: set[str], roots: frozenset[str], tp: set[str]) -> list[Optional[str]]:
    """Modules (plan 3.2 partition) that one import statement points to."""
    M = measures()
    out: list[Optional[str]] = []
    if isinstance(node, ast.Import):
        targets = [a.name.split(".") for a in node.names]
    else:
        parts = node.module.split(".") if node.module else []
        if node.level:
            pkg = file.split("/")[:-1]
            pkg = pkg[: len(pkg) - (node.level - 1)] if node.level > 1 else pkg
            base = pkg + parts
        else:
            base = parts
        targets = [base + [a.name] for a in node.names] + [base]
    for t in targets:
        if not t:
            continue
        for prefix in ("", "src/"):
            p = prefix + "/".join(t)
            cands = [p + ".py", p + "/__init__.py"]
            hit = next((c for c in cands if c in tree), None)
            if hit:
                out.append(M.module_of(hit, roots, tp))
                break
    return out


def y2_edges(repo_dir: Path, diff: str, tp: set[str], roots: frozenset[str], tree: set[str]) -> dict[str, Any]:
    M = measures()
    before: set[tuple[str, str]] = set()
    after: set[tuple[str, str]] = set()
    for p in split_diff(diff):
        if is_test(p, tp) or not p.endswith(".py"):
            continue
        m1 = M.module_of(p, roots, tp)
        if m1 is None:
            continue
        for text, acc in ((_base_text(repo_dir, p), before),
                          ((repo_dir / p).read_text(errors="replace") if (repo_dir / p).exists() else "", after)):
            try:
                tr = ast.parse(text)
            except (SyntaxError, ValueError):
                continue
            for node in ast.walk(tr):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for m2 in _resolve_import(p, node, tree | {p}, roots, tp):
                        if m2 and m2 != m1:
                            acc.add((m1, m2))
    return {"new_edges": len(after - before), "removed_edges": len(before - after),
            "examples": sorted(f"{a}->{b}" for a, b in after - before)[:8]}


def _stability(diff: str, tp: set[str], roots: frozenset[str], mods: dict[str, dict]) -> dict[str, Any]:
    """Y3 and Y3w for one diff given the population `modules` block."""
    M = measures()
    churn = sorted(v["measures"]["moduleRelChurnInWindow"] for v in mods.values()
                   if v.get("measures", {}).get("moduleRelChurnInWindow") is not None)
    lab_lines = stable_lines = 0
    pct_sum = pct_n = 0.0
    for p, n in lines_by_file(diff, tp).items():
        m = M.module_of(p, roots, tp)
        info = mods.get(m) if m else None
        if info is None:
            continue
        if info["label"] in ("StableModule", "ActiveModule"):
            lab_lines += n
            if info["label"] == "StableModule":
                stable_lines += n
        rc = info.get("measures", {}).get("moduleRelChurnInWindow")
        if rc is not None and churn:
            pct = sum(1 for c in churn if c <= rc) / len(churn)
            pct_sum += pct * n
            pct_n += n
    return {"Y3": (stable_lines / lab_lines) if lab_lines else None, "labelled_lines": lab_lines,
            "Y3w": (pct_sum / pct_n) if pct_n else None}


def outcomes(cfg: dict, task: dict, vrec: dict, diff: str, repo_dir: Path, steps: int,
             hit_step_limit: bool) -> dict[str, Any]:
    """Y0-Y6 for an agent patch that is currently applied in repo_dir (HEAD = base commit)."""
    tp = set(split_diff(task["test_patch"]))
    sizes = lines_by_file(diff, tp)
    changed = sum(sizes.values())
    gold_lines = vrec.get("gold_nontest_changed_lines") or diff_size(task["patch"], tp)["total"]
    out: dict[str, Any] = {"Y0": int(changed > 0), "Y5": len(sizes), "Y6": steps, "hit_step_limit": int(hit_step_limit),
                           "changed_lines": changed, "gold_changed_lines": gold_lines,
                           "Y1": None, "Y2": None, "Y3": None, "Y3_gold": None, "Y3_excess": None, "Y3w": None, "Y4": None}
    if changed == 0:
        return out
    roots, tree = base_roots(repo_dir, tp)
    pop = load_population(cfg, task["instance_id"])
    if pop and pop.get("modules_meta", {}).get("package_roots"):
        roots = frozenset(pop["modules_meta"]["package_roots"])
    out["Y1"] = y1_ccn(repo_dir, diff, tp)["delta_ccn"]
    out["Y2"] = y2_edges(repo_dir, diff, tp, roots, tree)["new_edges"]
    out["Y4"] = math.log2(changed / gold_lines) if gold_lines else None
    if pop and pop.get("modules"):
        a = _stability(diff, tp, roots, pop["modules"])
        g = _stability(task["patch"], tp, roots, pop["modules"])
        out.update(Y3=a["Y3"], Y3w=a["Y3w"], Y3_gold=g["Y3"],
                   Y3_excess=(a["Y3"] - g["Y3"]) if a["Y3"] is not None and g["Y3"] is not None else None)
    return out
