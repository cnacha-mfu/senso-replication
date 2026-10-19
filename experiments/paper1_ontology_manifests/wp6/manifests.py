"""WP6 mechanical manifest generator: the true manifest T and the two false variants F_R and F_I (no LLM).

Used by Paper 1 (JSEP rebuild), WP6; design papers/paper1/wp6-harm-design.md section 2.

`gather_context` reads one task (workspace checkout at the base commit, the WP2 dependency census, the gold patch and
the history of deleted files). `build_manifests` is a pure function of that context, the fixed vocabulary in
`configs/wp6.yaml` and an `Oracle` that answers the runtime questions a candidate must pass (does the path exist, does
`make -n` fail, does `import` work, what does the independent re-check say). A candidate that fails moves the builder to
the next one in a fixed order; a falsification slot that cannot be filled is dropped from ALL manifests of the task.

  T     8 layout entries, 3 key files, 2 commands, up to 5 dependencies, 1 Python line (bare facts).
  F_R   T with 4 claims replaced by false ones in the task-relevant area (the gold directory, the test command, a
        dependency that a gold-touched file imports).
  F_I   the same 4 slots replaced by false ones in an unrelated area.

Usage:
    imported by wp6/generate.py and wp6/verify.py; not run directly.
"""

from __future__ import annotations

import ast
import hashlib
import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any, Callable, Optional

import yaml

from ..wp2 import depparse as D
from ..wp2.normalize import version_code
from ..wp5.common import PROJECT_ROOT
from .common import diff_paths

logger = logging.getLogger("wp6.manifests")

HEADING = "## Repository context"
_MEASURES = None


def measures():
    """ontology/population/measures.py by path (is_test_path, MODULE_ROOT_EXCLUDED)."""
    global _MEASURES
    if _MEASURES is None:
        import importlib.util
        import sys
        spec = importlib.util.spec_from_file_location("wp6_measures", PROJECT_ROOT / "ontology/population/measures.py")
        _MEASURES = importlib.util.module_from_spec(spec)
        sys.modules["wp6_measures"] = _MEASURES
        spec.loader.exec_module(_MEASURES)
    return _MEASURES


# ----------------------------------------------------------------------------
# Data types
# ----------------------------------------------------------------------------
@dataclass
class Claim:
    """One checkable claim (a WP2 claim record by construction: tcode, attrs, votes = 3)."""
    key_str: str
    tcode: str
    attrs: dict[str, Any]
    quote: str
    role: str                         # "true" | "false"
    slot: str                         # layout, key_file, test_cmd, install_cmd, dep, python, P1, P2, C_R, C_I, D
    kind: Optional[int] = None        # injected kind 1..4 for false claims
    expect_verdict: str = "SupportedClaim"
    expect_leaves: list[str] = field(default_factory=list)   # [] = any leaf of the verdict
    probe: Optional[dict[str, Any]] = None    # runtime probe (design 2.3 table), run in the task workspace
    mode: Optional[str] = None                # false claims: "replace" (a T line is replaced) | "add" (line added, deviation 13)

    def to_json(self) -> dict[str, Any]:
        return {"key_str": self.key_str, "tcode": self.tcode, "attrs": self.attrs, "quote": self.quote,
                "role": self.role, "slot": self.slot, "kind": self.kind, "expect_verdict": self.expect_verdict,
                "expect_leaves": self.expect_leaves, "probe": self.probe, "mode": self.mode}


@dataclass
class Entry:
    """One manifest line item: its text and the claims it makes."""
    text: str
    claims: list[Claim]
    slot: Optional[str] = None


@dataclass
class Manifest:
    cond: str
    sections: list[tuple[str, list[Entry]]]
    inline: Optional[Entry] = None    # the Python line

    def render(self) -> str:
        out = [HEADING, ""]
        for title, entries in self.sections:
            if not entries:
                continue
            out.append(f"{title}:")
            out += [f"- {e.text}" for e in entries]
            out.append("")
        if self.inline:
            out.append(self.inline.text)
        return "\n".join(out).rstrip("\n") + "\n"

    def claims(self) -> list[Claim]:
        cs = [c for _, es in self.sections for e in es for c in e.claims]
        return cs + (self.inline.claims if self.inline else [])


class NullOracle:
    """Accepts every candidate (unit tests of the pure logic)."""

    def exists(self, path: str) -> bool:
        return False

    def log_count(self, path: str) -> int:
        return 0

    def pytest_collect_ok(self, root: str) -> bool:
        return True

    def make_n_fails(self, target: str) -> bool:
        return True

    def import_ok(self, module: str) -> bool:
        return False

    def recheck(self, tcode: str, attrs: dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
        return None, None

    def grep_hits(self, pattern: str, extended: bool = False, ignore_case: bool = True, word: bool = True) -> int:
        return 0


@dataclass
class TaskContext:
    """Everything the builder needs about one task at its base commit."""
    task_id: str
    repo: str
    base_commit: str
    problem_statement: str
    files: list[str]                  # tracked files
    sizes: dict[str, int]             # bytes of the non-test .py files
    gold_files: list[str]             # non-test files of the gold (source) patch
    gold_dirs: list[str]              # existing directories, depth <= 2, sorted
    test_root: Optional[str]
    decls: list[dict[str, Any]]       # pypi declarations from the WP2 census {name, spec, file}
    dist_imports: dict[str, list[str]]       # normalized dist -> top-level import names (task venv)
    file_imports: dict[str, set[str]]        # non-test source file -> imported top-level names
    deleted_py: list[str]             # .py paths deleted in history before base (most recent first)
    python_spec: Optional[str]
    has_install_file: bool
    competitors: dict[str, list[str]]
    cfg: dict[str, Any]
    n_parsed: int = 1                 # dependency manifests parsed by the WP2 census (0: the checker answers DependencyNoManifest)

    @cached_property
    def src_counts(self) -> dict[str, int]:
        """directory -> number of non-test source modules in its subtree."""
        out: dict[str, int] = {}
        for p in self.files:
            if is_source(p):
                parts = p.split("/")
                for i in range(1, len(parts)):
                    d = "/".join(parts[:i])
                    out[d] = out.get(d, 0) + 1
        return out

    @cached_property
    def direct_src_dirs(self) -> set[str]:
        return {p.rsplit("/", 1)[0] for p in self.files if "/" in p and is_source(p)}

    @cached_property
    def dirs(self) -> set[str]:
        out: set[str] = set()
        for p in self.files:
            parts = p.split("/")
            for i in range(1, len(parts)):
                out.add("/".join(parts[:i]))
        return out

    @cached_property
    def components(self) -> set[str]:
        out: set[str] = set()
        for p in self.files:
            for part in p.split("/"):
                out.add(part.lower())
                if part.endswith(".py"):
                    out.add(part[:-3].lower())
        return out


# ----------------------------------------------------------------------------
# Context
# ----------------------------------------------------------------------------
def _git(d: Path, *args: str, timeout: int = 600, env: Optional[dict] = None) -> str:
    p = subprocess.run(["git", "-C", str(d), *args], capture_output=True, text=True, errors="replace", timeout=timeout,
                       env=env)
    return p.stdout if p.returncode == 0 else ""


def top_imports(source: str) -> set[str]:
    """Top-level module names imported by a Python source (ast, falls back to a regex)."""
    names: set[str] = set()
    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names.add(node.module.split(".")[0])
    except (SyntaxError, ValueError, RecursionError):
        for m in re.finditer(r"(?m)^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", source):
            names.add((m.group(1) or m.group(2)).split(".")[0])
    return names


def is_source(path: str) -> bool:
    """Non-test .py file outside the directories that never become package roots (WP5 plan 3.2)."""
    m = measures()
    if not path.endswith(".py") or m.is_test_path(path):
        return False
    first = path.split("/")[0]
    if "/" not in path:
        return False
    return first not in m.MODULE_ROOT_EXCLUDED and not first.startswith(".")


def python_requirement(read: Callable[[str], Optional[str]]) -> Optional[str]:
    """The declared requires-python / python_requires specifier (first source found), else None."""
    import tomllib
    t = read("pyproject.toml")
    if t:
        try:
            d = tomllib.loads(t)
            s = (d.get("project") or {}).get("requires-python")
            if s:
                return str(s)
            s = (((d.get("tool") or {}).get("poetry") or {}).get("dependencies") or {}).get("python")
            if isinstance(s, str):
                return s
        except Exception:  # noqa: BLE001
            pass
    for path, rx in (("setup.cfg", r"(?m)^\s*python_requires\s*=\s*(.+?)\s*$"),
                     ("setup.py", r"python_requires\s*=\s*['\"]([^'\"]+)['\"]")):
        t = read(path)
        if t:
            m = re.search(rx, t)
            if m:
                return m.group(1).strip()
    return None


def pick_test_root(files: list[str]) -> Optional[str]:
    """Most common test directory (the shallowest ancestor named test/tests/testing); '.' when tests sit at the root."""
    m = measures()
    tally: dict[str, int] = {}
    for p in files:
        if not p.endswith(".py") or not m.is_test_path(p):
            continue
        parts = p.split("/")[:-1]
        root = None
        for i, part in enumerate(parts):
            if re.fullmatch(r"tests?|testing", part):
                root = "/".join(parts[: i + 1])
                break
        if root is None and parts:
            root = parts[0]
        if root is None:
            root = "."
        tally[root] = tally.get(root, 0) + 1
    if not tally:
        return None
    return sorted(tally, key=lambda r: (-tally[r], r.count("/"), r))[0]


def gather_context(cfg: dict, rec: dict, repo_dir: Path, bare: Path, rev_files: list[str],
                   decls: list[dict[str, Any]], dist_imports: dict[str, list[str]]) -> TaskContext:
    """Collect the task facts. `repo_dir` is the checkout at the base commit, `bare` the cache clone (history)."""
    import yaml as _y
    m = measures()
    files = rev_files
    sizes: dict[str, int] = {}
    file_imports: dict[str, set[str]] = {}
    for p in files:
        if is_source(p):
            fp = repo_dir / p
            try:
                sizes[p] = fp.stat().st_size
                if sizes[p] <= 1_000_000:
                    file_imports[p] = top_imports(fp.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
    fset = set(files)
    dirs: set[str] = set()
    for p in files:
        parts = p.split("/")
        dirs.update("/".join(parts[:i]) for i in range(1, len(parts)))
    tp = set(diff_paths(rec["test_patch"]))
    gold_files = [p for p in diff_paths(rec["patch"]) if not m.is_test_path(p, tp)]
    gold_dirs: set[str] = set()
    for p in gold_files:
        parts = p.split("/")[:-1][:2]
        while parts and "/".join(parts) not in dirs:
            parts.pop()
        if parts:
            gold_dirs.add("/".join(parts))
    deleted: list[str] = []
    out = _git(bare, "log", "--no-renames", "--diff-filter=D", "--name-only", "--format=", "--max-count=20000",
               rec["base_commit"], "--", "*.py", timeout=900, env={**os.environ, "GIT_NO_LAZY_FETCH": "1"})
    seen: set[str] = set()
    for ln in out.splitlines():
        ln = ln.strip()
        if ln and ln not in seen:
            seen.add(ln)
            if ln not in fset:
                deleted.append(ln)

    def read(path: str) -> Optional[str]:
        try:
            return (repo_dir / path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None

    comp = _y.safe_load(Path(cfg["competitors"] if os.path.isabs(cfg["competitors"]) else PROJECT_ROOT / cfg["competitors"]).read_text())
    return TaskContext(
        task_id=rec["instance_id"], repo=rec["repo"], base_commit=rec["base_commit"],
        problem_statement=rec["problem_statement"], files=files, sizes=sizes, gold_files=gold_files,
        gold_dirs=sorted(gold_dirs), test_root=pick_test_root(files), decls=decls, dist_imports=dist_imports,
        file_imports=file_imports, deleted_py=deleted, python_spec=python_requirement(read),
        has_install_file=("pyproject.toml" in fset or "setup.py" in fset), competitors=comp, cfg=cfg)


# ----------------------------------------------------------------------------
# Constraints shared by the candidates
# ----------------------------------------------------------------------------
def in_text(token: str, text: str) -> bool:
    return re.search(r"(?<![\w])" + re.escape(token) + r"(?![\w])", text, re.I) is not None


def final_ok(ctx: TaskContext, name: str, allow_in_history: bool = False) -> bool:
    """The false token occurs nowhere among base-tree path components and not in the issue text."""
    low = name.lower()
    stem = low[:-3] if low.endswith(".py") else low
    if low in ctx.components or stem in ctx.components:
        return False
    return not (in_text(name, ctx.problem_statement) or in_text(stem, ctx.problem_statement))


def related(a: str, b: str) -> bool:
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def py_count(ctx: "TaskContext", prefix: str) -> int:
    return ctx.src_counts.get(prefix, 0)


def dep_modules(ctx: TaskContext, dist: str) -> list[str]:
    return ctx.dist_imports.get(dist, [])


def dep_importers(ctx: TaskContext, dist: str, files: Optional[list[str]] = None) -> int:
    mods = set(dep_modules(ctx, dist))
    if not mods:
        return 0
    return sum(1 for p, imps in ctx.file_imports.items() if (files is None or p in files) and imps & mods)


def to_import_name(dist: str) -> str:
    return dist.replace("-", "_")


# ----------------------------------------------------------------------------
# The true manifest
# ----------------------------------------------------------------------------
def path_claim(path: str, is_dir: bool, slot: str, role: str = "true", kind: Optional[int] = None,
               verdict: str = "SupportedClaim", leaves: Optional[list[str]] = None, quote: str = "") -> Claim:
    probe = ({"type": "exists", "path": path} if role == "true" else
             {"type": "absent", "path": path, "history": "none" if leaves == ["PathNeverExisted"] else "some"})
    return Claim(key_str=f"T1|{path}", tcode="T1", attrs={"path": path, "is_dir": is_dir, "glob": False, "bracket": False},
                 quote=quote or path, role=role, slot=slot, kind=kind, expect_verdict=verdict, expect_leaves=leaves or [],
                 probe=probe)


def build_layout(ctx: TaskContext, n: int, reject: set[str]) -> list[str]:
    gold = list(ctx.gold_dirs)
    chosen = set(gold)
    if ctx.test_root and ctx.test_root != ".":
        chosen.add(ctx.test_root)
    dirs = ctx.dirs
    cand: list[tuple[int, str]] = []
    m = measures()
    for d in sorted(dirs):
        parts = d.split("/")
        if len(parts) > 2 or parts[0] in m.MODULE_ROOT_EXCLUDED or any(x.startswith(".") for x in parts) \
                or any(x.endswith(".egg-info") for x in parts) or m.is_test_path(d + "/x.py"):
            continue
        if d not in ctx.direct_src_dirs:
            continue    # a package directory holds at least one source module of its own
        cand.append((py_count(ctx, d), d))
    cand.sort(key=lambda x: (-x[0], x[1]))
    for _, d in cand:
        if len(chosen) >= n:
            break
        if d not in reject:
            chosen.add(d)
    if ctx.test_root == ".":
        pass    # tests at the repository root: the test root is the repository itself, not a layout entry
    return sorted(chosen)


def unrelated_dirs(ctx: "TaskContext") -> list[str]:
    """Non-gold, non-test, non-hidden directories of the base tree with no gold-touched file in their subtree (shallow first)."""
    gold = ctx.gold_files
    out = []
    for d in ctx.dirs:
        parts = d.split("/")
        if any(x.startswith(".") or x.endswith(".egg-info") for x in parts) or measures().is_test_path(d + "/x.py"):
            continue
        if any(g.startswith(d + "/") for g in gold):
            continue
        out.append(d)
    return sorted(out, key=lambda d: (d.count("/"), -ctx.src_counts.get(d, 0), d))


def pick_key_files(ctx: TaskContext, layout: list[str], n: int) -> list[str]:
    listed = [d for d in layout if d != ctx.test_root and not measures().is_test_path(d + "/x.py")]
    ranked = sorted(listed, key=lambda d: (-py_count(ctx, d), d))[:n]
    out: list[str] = []
    for d in ranked:
        pre = d + "/"
        cands = sorted((p for p in ctx.sizes if p.startswith(pre) and p not in out), key=lambda p: (-ctx.sizes[p], p))
        if cands:
            out.append(cands[0])
    return out


def pick_deps(ctx: TaskContext, n: int, deny: list[str], reject: set[str]) -> list[dict[str, Any]]:
    """Declared runtime dependencies, ranked by the number of non-test source files that import them."""
    by_name: dict[str, dict[str, Any]] = {}
    for d in sorted(ctx.decls, key=lambda d: (d["file"].count("/"), d["file"])):
        by_name.setdefault(d["name"], d)
    ranked = []
    gold = set(ctx.gold_files)
    for name, d in by_name.items():
        if name in deny or name in reject or not ctx.dist_imports.get(name):
            continue
        k = dep_importers(ctx, name)
        if k > 0:
            ranked.append({**d, "rank_n": k, "gold_imports": dep_importers(ctx, name, gold) > 0})
    ranked.sort(key=lambda r: (-r["rank_n"], r["name"]))
    return ranked[:n]


def dep_text(d: dict[str, Any]) -> str:
    return f"`{d['name']}{d['spec']}`" if d["spec"] else f"`{d['name']}`"


def dep_claim(name: str, quote: str, slot: str, role: str = "true", kind: Optional[int] = None,
              modules: Optional[list[str]] = None) -> Claim:
    probe = ({"type": "import_ok", "modules": modules or [to_import_name(name)]} if role == "true" else
             {"type": "import_fail", "modules": [to_import_name(name)]})
    return Claim(key_str=f"T4|{name}|", tcode="T4", attrs={"name": name, "major": None, "ecosystem_hint": "pypi"},
                 quote=quote, role=role, slot=slot, kind=kind,
                 expect_verdict="SupportedClaim" if role == "true" else "ContradictedClaim",
                 expect_leaves=[] if role == "true" else ["DependencyUndeclared"], probe=probe)


def make_claim(target: str, quote: str, slot: str, kind: Optional[int] = None) -> Claim:
    return Claim(key_str=f"T5|make|{target}", tcode="T5", attrs={"runner": "make", "kind": "make", "target": target},
                 quote=quote, role="false", slot=slot, kind=kind, expect_verdict="ContradictedClaim",
                 expect_leaves=["ScriptUndefined", "ScriptHostMissing"], probe={"type": "make_fail", "target": target})


def python_entry(ctx: TaskContext, oracle: Any) -> Optional[Entry]:
    spec = ctx.python_spec
    if not spec:
        return None
    m = re.search(r">=\s*(\d+(?:\.\d+){0,2})", spec) or re.search(r"[\^~]\s*(\d+(?:\.\d+){0,2})", spec)
    if not m:
        return None
    ver = m.group(1)
    vc = version_code(ver)
    if vc is None:
        return None
    code, prec = vc
    attrs = {"subject_type": "python", "version": ver, "code": code, "precision": prec, "qualifier": "min"}
    c = Claim(key_str=f"T6|python|{code}@{prec}", tcode="T6", attrs=attrs, quote=f"Python: >={ver}", role="true",
              slot="python")
    v, _ = oracle.recheck("T6", attrs)
    if v != "SupportedClaim":
        logger.info("%s: python line %r rejected by the re-check (%s)", ctx.task_id, ver, v)
        return None
    return Entry(f"Python: `>={ver}`", [c], "python")


# ----------------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------------
@dataclass
class Built:
    manifests: dict[str, Manifest]
    tokens: dict[str, list[dict[str, Any]]]       # cond -> token specs
    info: dict[str, Any]
    flags: list[str]


def build_manifests(ctx: TaskContext, oracle: Any, reject: Optional[dict[str, set[str]]] = None) -> Built:
    """T, F_R and F_I for one task. `reject` = candidates the verification gate refused (kind -> set of strings)."""
    mc = ctx.cfg["manifest"]
    reject = reject or {}
    flags: list[str] = []
    info: dict[str, Any] = {"slots": {}, "why": {}}
    why = info["why"]
    ps = ctx.problem_statement

    # ---- layout ---------------------------------------------------------------------------------------------
    layout = build_layout(ctx, mc["n_layout"], reject.get("layout", set()))
    gold_set = set(ctx.gold_dirs)
    layout_entries = [Entry(f"`{d}/`", [path_claim(d, True, "layout", quote=f"{d}/")], "layout") for d in layout]
    if not ctx.gold_dirs:
        flags.append("no_gold_dir")
    if not ctx.test_root:
        flags.append("no_test_root")
    # ---- key files ------------------------------------------------------------------------------------------
    keyfiles = pick_key_files(ctx, layout, mc["n_key_files"])
    key_entries = [Entry(f"`{p}`", [path_claim(p, False, "key_file", quote=p)], "key_file") for p in keyfiles]
    # ---- commands ---------------------------------------------------------------------------------------------
    cmd_entries: list[Entry] = []
    test_ok = False
    roots = [r for r in dict.fromkeys([ctx.test_root, *sorted({p.split("/")[0] for p in ctx.files
                                                                if re.fullmatch(r"tests?", p.split("/")[0]) and "/" in p})])
             if r]
    for root in ([] if "test_cmd" in reject.get("drop", set()) else roots):
        pc = Claim(key_str="T3|test_framework|pytest", tcode="T3", attrs={"tool": "pytest", "category": "test_framework"},
                   quote=f"python -m pytest {root}", role="true", slot="test_cmd",
                   probe={"type": "pytest", "root": root})
        rc = path_claim(root, True, "test_cmd", quote=root) if root != "." else None
        v3, _ = oracle.recheck("T3", pc.attrs)
        v1 = oracle.recheck("T1", rc.attrs)[0] if rc else "SupportedClaim"
        collect = oracle.pytest_collect_ok(root) if (v3 == "SupportedClaim" and v1 == "SupportedClaim") else None
        why.setdefault("test_command", []).append({"root": root, "T3": v3, "T1": v1, "collect_ok": collect})
        if collect:
            cmd_entries.append(Entry(f"Run the tests: `python -m pytest {root}`", [pc] + ([rc] if rc else []), "test_cmd"))
            test_ok = True
            info["slots"]["test_root"] = root
            break
    if not test_ok:
        flags.append("no_test_command")
    install_ok = False
    for f in (() if "install_cmd" in reject.get("drop", set()) else ("pyproject.toml", "setup.py")):
        if f in set(ctx.files):
            ic = path_claim(f, False, "install_cmd", quote=f)
            if oracle.recheck("T1", ic.attrs)[0] == "SupportedClaim":
                cmd_entries.append(Entry("Install for development: `pip install -e .`", [ic], "install_cmd"))
                install_ok = True
                break
    if not install_ok:
        flags.append("no_install_command")
    # ---- dependencies -----------------------------------------------------------------------------------------
    dep_rows: list[dict[str, Any]] = []
    rej_deps = reject.get("dep", set())
    for d in pick_deps(ctx, mc["n_deps"] + 6, mc["runtime_deny"], rej_deps):
        if len(dep_rows) >= mc["n_deps"]:
            break
        mods = ctx.dist_imports.get(d["name"], [])
        if not any(oracle.import_ok(mod) for mod in mods):
            continue
        cl = dep_claim(d["name"], dep_text(d), "dep")
        if oracle.recheck("T4", cl.attrs)[0] != "SupportedClaim":
            continue
        dep_rows.append(d)
    dep_entries = [Entry(dep_text(d), [dep_claim(d["name"], dep_text(d), "dep", modules=ctx.dist_imports[d["name"]])], "dep")
                   for d in dep_rows]
    py_entry = None if "python" in reject.get("drop", set()) else python_entry(ctx, oracle)

    T = Manifest("T", [("Layout", layout_entries), ("Key files", key_entries), ("Commands", cmd_entries),
                       ("Dependencies", dep_entries)], py_entry)
    FR = Manifest("F_R", [(t, list(es)) for t, es in T.sections], py_entry)
    FI = Manifest("F_I", [(t, list(es)) for t, es in T.sections], py_entry)
    tokens: dict[str, list[dict[str, Any]]] = {"F_R": [], "F_I": []}
    fallbacks: dict[str, list[str]] = {"F_R": [], "F_I": []}
    sec = {t: i for i, (t, _) in enumerate(T.sections)}

    def slot_index(title: str, slot: str, which: str = "last") -> Optional[int]:
        es = T.sections[sec[title]][1]
        idx = [i for i, e in enumerate(es) if e.slot == slot]
        return idx[-1] if (idx and which == "last") else (idx[0] if idx else None)

    modes: dict[str, dict[str, str]] = {"F_R": {}, "F_I": {}}     # cond -> kind -> "replace" | "add"

    def place(M: Manifest, title: str, idx: Optional[int], entry: Entry, kind: int) -> str:
        """Replace the T entry at `idx` (current behaviour); if there is none, ADD the false line to the section (deviation 13)."""
        es = M.sections[sec[title]][1]
        mode = "replace" if idx is not None else "add"
        if idx is not None:
            es[idx] = entry
        else:
            es.append(entry)
        for c in entry.claims:
            c.mode = mode
        modes[M.cond][str(kind)] = mode
        return mode

    def join(base: str, name: str) -> str:
        return f"{base}/{name}" if base else name

    unrel_dirs = unrelated_dirs(ctx)

    # ---- kind 1: path that never existed (P1 = the last non-gold, non-test layout entry; else ADD) -------------------------
    p1_idx = None
    for i in range(len(layout_entries) - 1, -1, -1):
        d = layout[i]
        if d not in gold_set and d != ctx.test_root:
            p1_idx = i
            break
    gold0 = ctx.gold_dirs[0] if ctx.gold_dirs else None
    # the task's area = the directories that contain gold-touched files; "unrelated" = a listed directory with none
    unrel = next((d for d in layout if d != ctx.test_root
                  and not any(g.startswith(d + "/") or g.rsplit("/", 1)[0] == d for g in ctx.gold_files)), None)
    base_r = gold0 or ""
    mode_r = "replace" if (p1_idx is not None and gold0) else "add"
    if p1_idx is not None and unrel:
        base_i, mode_i = unrel, "replace"
    else:    # no unrelated listed directory: any non-gold, non-test directory of the base tree, else the repository root
        base_i, mode_i = (unrel_dirs[0] if unrel_dirs else ""), "add"
    k1 = None
    why["kind1"] = {"p1_idx": p1_idx, "gold0": gold0, "unrelated": unrel, "base_R": base_r, "base_I": base_i}
    for name in mc["names"]:
        if name in reject.get("k1", set()) or not final_ok(ctx, name):
            continue
        pr, pi = join(base_r, name), join(base_i, name)
        if all(not oracle.exists(p) and oracle.log_count(p) == 0 and not in_text(p, ps) for p in (pr, pi)) \
                and all(oracle.recheck("T1", path_claim(p, True, "P1").attrs) == ("ContradictedClaim", "PathNeverExisted")
                        for p in (pr, pi)):
            k1 = (name, pr, pi)
            break
    if k1:
        name, pr, pi = k1
        for M, p, cond, md in ((FR, pr, "F_R", mode_r), (FI, pi, "F_I", mode_i)):
            place(M, "Layout", p1_idx if md == "replace" else None,
                  Entry(f"`{p}/`", [path_claim(p, True, "P1", "false", 1, "ContradictedClaim", ["PathNeverExisted"],
                                               quote=f"{p}/")], "P1"), 1)
            tokens[cond].append({"kind": 1, "type": "path", "values": [p, name]})
        info["slots"]["P1"] = {"replaced": layout[p1_idx] if p1_idx is not None else None, "name": name, "F_R": pr, "F_I": pi}
    else:
        flags.append("kind1_dropped")

    # ---- kind 2: path removed (P2 = the third key file; else ADD) --------------------------------------------------------
    p2_idx = 2 if len(key_entries) >= 3 else None
    k2 = None
    why["kind2"] = {"p2_idx": p2_idx, "n_deleted_py": len(ctx.deleted_py)}
    if ctx.deleted_py:      # "if the history has no deleted .py file at all, the slot stays empty"
        gold_pkg = {g.split("/")[0] for g in ctx.gold_dirs}

        def pick_removed(area: Callable[[str], bool], used: set[str]) -> Optional[str]:
            for p in ctx.deleted_py:
                if p in used or p in reject.get("k2", set()) or not area(p):
                    continue
                fn = p.rsplit("/", 1)[-1]
                if not final_ok(ctx, fn) or in_text(p, ps):
                    continue
                if oracle.exists(p) or oracle.log_count(p) < 1:
                    continue
                if oracle.recheck("T1", path_claim(p, False, "P2").attrs) == ("ContradictedClaim", "PathRemoved"):
                    return p
            return None

        def pick_never(base: str, used: set[str]) -> Optional[str]:
            for name in mc["names"]:
                p = join(base, name + ".py")
                if (k1 and name == k1[0]) or p in used or p in reject.get("k2", set()) or not final_ok(ctx, name + ".py"):
                    continue
                if not oracle.exists(p) and oracle.log_count(p) == 0 and not in_text(p, ps) \
                        and oracle.recheck("T1", path_claim(p, False, "P2").attrs) == ("ContradictedClaim", "PathNeverExisted"):
                    return p
            return None

        used: set[str] = set()
        res: dict[str, tuple[str, bool]] = {}
        # F_R: widen step by step: gold dir, then top package, then anywhere
        r_path = pick_removed(lambda p: any(p.startswith(g + "/") for g in ctx.gold_dirs), used) or \
            pick_removed(lambda p: p.split("/")[0] in gold_pkg and "/" in p, used) or \
            pick_removed(lambda p: True, used)
        if r_path:
            res["F_R"] = (r_path, False)
        else:
            nv = pick_never(base_r, used)
            if nv:
                res["F_R"] = (nv, True)
        used |= {v[0] for v in res.values()}
        i_path = pick_removed(lambda p: p.split("/")[0] not in gold_pkg, used)
        if i_path:
            res["F_I"] = (i_path, False)
        else:
            nv = pick_never(base_i, used)
            if nv:
                res["F_I"] = (nv, True)
        why["kind2"]["found"] = {k: v[0] for k, v in res.items()}
        if len(res) == 2:
            k2 = res
    if k2:
        for M, cond in ((FR, "F_R"), (FI, "F_I")):
            p, fb = k2[cond]
            leaf = "PathNeverExisted" if fb else "PathRemoved"
            place(M, "Key files", p2_idx, Entry(f"`{p}`", [path_claim(p, False, "P2", "false", 2, "ContradictedClaim", [leaf],
                                                                    quote=p)], "P2"), 2)
            tokens[cond].append({"kind": 2, "type": "path", "values": [p, p.rsplit("/", 1)[-1]]})
            if fb:
                fallbacks[cond].append("kind2_never_existed_fallback")
        info["slots"]["P2"] = {"replaced": keyfiles[p2_idx] if p2_idx is not None else None, "F_R": k2["F_R"][0], "F_I": k2["F_I"][0]}
    else:
        flags.append("kind2_dropped")

    # ---- kind 3: undefined command (C_R = the test command, C_I = the install command; else ADD the line) ----------------
    c_r = slot_index("Commands", "test_cmd", "first")
    c_i = slot_index("Commands", "install_cmd", "first")

    def pick_target(options: list[str]) -> Optional[str]:
        for t in options:
            if t in reject.get("k3", set()):
                continue
            rx = r"\bmake\b[^|;&\n]*\b" + re.escape(t) + r"\b"
            if re.search(rx, ps):
                continue
            if oracle.grep_hits(rx, extended=True, ignore_case=False, word=False) > 0:
                continue
            if not oracle.make_n_fails(t):
                continue
            if oracle.recheck("T5", make_claim(t, "", "C_R").attrs)[0] != "ContradictedClaim":
                continue
            return t
        return None

    tr, ti = pick_target(mc["make_targets_run"]), pick_target(mc["make_targets_install"])
    why["kind3"] = {"run": tr, "install": ti, "test_ok": test_ok, "install_ok": install_ok}
    if tr and ti:
        place(FR, "Commands", c_r, Entry(f"Run the tests: `make {tr}`", [make_claim(tr, f"make {tr}", "C_R", 3)], "C_R"), 3)
        tokens["F_R"].append({"kind": 3, "type": "regex", "regex": r"\bmake\b[^|;&\n]*\b" + re.escape(tr) + r"\b", "target": tr})
        place(FI, "Commands", c_i, Entry(f"Install for development: `make {ti}`", [make_claim(ti, f"make {ti}", "C_I", 3)], "C_I"), 3)
        tokens["F_I"].append({"kind": 3, "type": "regex", "regex": r"\bmake\b[^|;&\n]*\b" + re.escape(ti) + r"\b", "target": ti})
        info["slots"]["C"] = {"F_R": f"make {tr}", "F_I": f"make {ti}"}
    else:
        flags.append("kind3_dropped")

    # ---- kind 4: undeclared dependency (D = the lowest-ranked dependency that no gold file imports; else ADD) -------------
    declared = {d["name"] for d in ctx.decls}
    generic = list(mc["generic_dependency_fallback"])

    def pick_comp(dist: Optional[str], avoid: set[str]) -> Optional[str]:
        for c in (ctx.competitors.get(dist, []) if dist else []) + generic:
            cn = D.norm_name(c)
            imp = to_import_name(cn)
            if cn in declared or cn in avoid or cn in reject.get("k4", set()):
                continue
            if in_text(c, ps) or in_text(imp, ps):
                continue
            if oracle.grep_hits(c) > 0 or oracle.grep_hits(imp) > 0:
                continue
            if oracle.import_ok(imp):
                continue
            if oracle.recheck("T4", dep_claim(cn, "", "D").attrs) != ("ContradictedClaim", "DependencyUndeclared"):
                continue
            return cn
        return None

    d_idx = None
    for i in range(len(dep_rows) - 1, -1, -1):
        if not dep_rows[i]["gold_imports"]:
            d_idx = i
            break
    gold_deps = [r for r in dep_rows if r["gold_imports"]]
    decl_names = [d["name"] for d in sorted(ctx.decls, key=lambda d: (d["file"].count("/"), d["file"], d["name"]))
                  if d["name"] not in mc["runtime_deny"]]
    decl_names = list(dict.fromkeys(decl_names))
    if d_idx is not None:
        src_i = dep_rows[d_idx]["name"]
        src_r = gold_deps[0]["name"] if gold_deps else src_i
    else:    # add mode: competitors of declared dependencies (a gold-imported one for F_R when there is one), else generic
        src_r = gold_deps[0]["name"] if gold_deps else (decl_names[0] if decl_names else None)
        src_i = next((n for n in decl_names if n != src_r), src_r)
    ci = pick_comp(src_i, set())
    cr = pick_comp(src_r, {ci} if (ci and src_r != src_i) else set()) if src_r != src_i else ci
    if cr is None and ci is not None:
        cr = ci
    why["kind4"] = {"deps": [(r["name"], r["gold_imports"]) for r in dep_rows], "d_idx": d_idx, "src_R": src_r, "src_I": src_i,
                    "n_decls": len(ctx.decls), "n_dist": len(ctx.dist_imports)}
    if d_idx is not None and not gold_deps:
        flags.append("kind4_R_used_I_competitor")
        fallbacks["F_R"].append("kind4_I_competitor")
    if ctx.n_parsed == 0:
        ci = cr = None    # no parsed manifest: HermiT says Unverifiable (DependencyNoManifest), so no dependency can be contradicted
        why["kind4"]["no_parsed_manifest"] = True
    if ci and cr:
        for M, cond, c in ((FR, "F_R", cr), (FI, "F_I", ci)):
            row = {"name": c, "spec": ""}    # a false dependency carries no specifier (a copied one would be nonsense)
            place(M, "Dependencies", d_idx, Entry(dep_text(row), [dep_claim(c, dep_text(row), "D", "false", 4)], "D"), 4)
            tokens[cond].append({"kind": 4, "type": "word", "values": sorted({c, to_import_name(c)})})
        info["slots"]["D"] = {"replaced": dep_rows[d_idx]["name"] if d_idx is not None else None, "F_R": cr, "F_I": ci}
    else:
        flags.append("kind4_dropped")

    # ---- length ---------------------------------------------------------------------------------------------------
    lt = len(T.render())
    for M in (FR, FI):
        if abs(len(M.render()) - lt) > mc["length_tolerance"] * lt:
            flags.append(f"length_violation_{M.cond}")
    info["length"] = {c: len(M.render()) for c, M in (("T", T), ("F_R", FR), ("F_I", FI))}
    info["fallbacks"] = fallbacks
    info["modes"] = modes
    info["length_diff"] = {c: len(M.render()) - lt for c, M in (("F_R", FR), ("F_I", FI))}
    info["n_claims_T"] = len(T.claims())
    info["n_false"] = {c: sum(1 for x in M.claims() if x.role == "false") for c, M in (("F_R", FR), ("F_I", FI))}
    info["pointer_in_issue"] = bool(ctx.gold_dirs and any(in_text(g, ps) or in_text(g.split("/")[-1], ps)
                                                         for g in ctx.gold_dirs)) or \
        any(in_text(p, ps) or in_text(p.rsplit("/", 1)[-1], ps) for p in ctx.gold_files)
    info["gold_dirs"] = ctx.gold_dirs
    info["gold_files"] = ctx.gold_files
    return Built({"T": T, "F_R": FR, "F_I": FI}, tokens, info, flags)


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()
