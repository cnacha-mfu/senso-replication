#!/usr/bin/env python3
"""Standalone checks of the WP5 module partition and module measurements (Paper 1, wp5-analysis-plan.md 3.2).

Not a pytest suite (project convention): prints a pass/fail report and exits non-zero on failure.
Covers the partition rules (test files, package roots, ``src/`` layout, root files), the window
arithmetic (month clamping, (S - W, S] bounds, merges, lines changed, LOC 0 handling), the ABox
assertions of a module (``AboxWriter.module``) and, with ``--reason``, the module classes through
HermiT (Stable, Active, undetermined; boundary values of the thresholds).

Usage:
    python ontology/population/test_wp5_modules.py [--reason]
"""

from __future__ import annotations

import argparse
import logging
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ontology.population import measures as M  # noqa: E402
from ontology.population import populate_v2 as P  # noqa: E402
from ontology.reasoning.abox import AboxWriter  # noqa: E402

logger = logging.getLogger("test_wp5_modules")
RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(cond), detail))
    logger.info("%s  %s %s", "PASS" if cond else "FAIL", name, detail)


def utc(y: int, m: int, d: int, h: int = 12) -> datetime:
    return datetime(y, m, d, h, tzinfo=timezone.utc)


def test_partition() -> None:
    paths = [
        "pkg/__init__.py", "pkg/core.py", "pkg/sub/__init__.py", "pkg/sub/deep/x.py", "pkg/sub/y.py",
        "pkg/tests/test_a.py", "pkg/test_b.py", "pkg/c_test.py", "pkg/conftest.py",
        "src/lib/__init__.py", "src/lib/m.py", "src/lib/sp/z.py", "src/loose/q.py", "src/top.py",
        "tests/__init__.py", "tests/helper.py", "tests/test_x.py", "docs/conf.py", "docs/gen.py",
        "setup.py", "noxfile.py", "run.py", "scripts/a.py", "tools/b.py", "plain/a.py", "plain/b/c.py",
        "node_modules/x/y.py", "pkg/notpython.txt", "newtest/helpers.py"]
    src = M.module_source_paths(paths, P.is_source_path)
    check("test files and non-python paths excluded",
          not any(p in src for p in ["pkg/tests/test_a.py", "pkg/test_b.py", "pkg/c_test.py", "pkg/conftest.py",
                                     "tests/test_x.py", "pkg/notpython.txt", "node_modules/x/y.py"]))
    roots = M.package_roots(src)
    check("roots: top-level dirs with __init__ and src subdirs, excluded names removed",
          roots == frozenset({"pkg", "src/lib", "src/loose"}), str(sorted(roots)))
    f = lambda p: M.module_of(p, roots)  # noqa: E731
    check("R/name.py module file", f("pkg/core.py") == "pkg/core.py")
    check("R/__init__.py is its own module", f("pkg/__init__.py") == "pkg/__init__.py")
    check("R/sub subpackage (any depth)", f("pkg/sub/deep/x.py") == "pkg/sub" and f("pkg/sub/y.py") == "pkg/sub")
    check("src layout roots", f("src/lib/m.py") == "src/lib/m.py" and f("src/lib/sp/z.py") == "src/lib/sp")
    check("src subdir without __init__ is a root", f("src/loose/q.py") == "src/loose/q.py")
    check("file directly under src/ falls to its top-level directory", f("src/top.py") == "src")
    check("everything under a tests/ directory is a test file; 'newtest' is not", f("tests/helper.py") is None
          and f("newtest/helpers.py") == "newtest")
    check("excluded names are never roots", "tests" not in roots and "docs" not in roots)
    check("docs/conf.py maps to its top-level directory", f("docs/conf.py") == "docs")
    check("root files excluded: setup/noxfile", f("setup.py") is None and f("noxfile.py") is None)
    check("other root files are their own module", f("run.py") == "run.py")
    check("non-root dirs map to the top-level dir", f("plain/b/c.py") == "plain" and f("scripts/a.py") == "scripts")
    check("test patch files are excluded", M.module_of("pkg/core.py", roots, ["pkg/core.py"]) is None)
    src2 = M.module_source_paths(paths, P.is_source_path, ["pkg/core.py"])
    check("test patch files leave the source list", "pkg/core.py" not in src2)
    check("src/__init__.py makes src an ordinary root",
          M.package_roots(["src/__init__.py", "src/a/b.py"]) == frozenset({"src"})
          and M.module_of("src/a/b.py", frozenset({"src"})) == "src/a")


def test_measurements() -> None:
    check("add_months clamps the day", M.add_months(utc(2024, 3, 31), -1) == utc(2024, 2, 29)
          and M.add_months(utc(2023, 1, 15), -12) == utc(2022, 1, 15) and M.add_months(utc(2023, 1, 31), 1) == utc(2023, 2, 28))
    S = utc(2023, 9, 6)
    roots = frozenset({"pkg"})
    fn = lambda p: M.module_of(p, roots)  # noqa: E731
    loc = {"pkg/a.py": 100, "pkg/sub": 50, "pkg/empty.py": 0}
    commits = [
        {"author_date": utc(2023, 9, 6), "merge": False, "files": [("pkg/a.py", 10, 5), ("pkg/sub/x.py", 1, 1)]},  # == S: in
        {"author_date": utc(2022, 9, 6), "merge": False, "files": [("pkg/a.py", 100, 0)]},  # == S - 12 months: out (open)
        {"author_date": utc(2022, 9, 7), "merge": False, "files": [("pkg/a.py", 3, 0)]},  # in
        {"author_date": utc(2023, 1, 10), "merge": True, "files": [("pkg/a.py", 50, 50)]},  # merge: out
        {"author_date": utc(2023, 1, 11), "merge": False, "files": [("pkg/gone.py", 7, 7), ("pkg/tests/test_q.py", 9, 9)]},  # not base / test
        {"author_date": utc(2023, 9, 7), "merge": False, "files": [("pkg/a.py", 1, 1)]},  # after S: out
        {"author_date": utc(2023, 2, 3), "merge": False, "files": [("pkg/a.py", 2, 2), ("pkg/empty.py", 1, 0)]},
        {"author_date": utc(2023, 2, 20), "merge": False, "files": [("pkg/a.py", 1, 0)]},
    ]
    out = M.module_measurements(commits, loc, S, 12, fn, {"pkg/a.py": "2023-09", "pkg/sub": "2020-01"})
    a = out["pkg/a.py"]
    check("window (S-W, S]: commits", a["moduleCommitsInWindow"] == 4, str(a))
    check("distinct UTC months", a["moduleChangeMonthsInWindow"] == 3, str(a))
    check("lines changed = insertions + deletions", a["moduleLinesChangedInWindow"] == 15 + 3 + 4 + 1, str(a))
    check("relative churn = lines / LOC", abs(a["moduleRelChurnInWindow"] - 0.23) < 1e-9, str(a))
    check("months since last change", a["moduleMonthsSinceLastChange"] == 0 and out["pkg/sub"]["moduleMonthsSinceLastChange"] == 44)
    check("module with LOC 0: no relative churn", "moduleRelChurnInWindow" not in out["pkg/empty.py"])
    check("paths of modules absent at base are ignored", set(out) == set(loc))
    w6 = M.module_measurements(commits, loc, S, 6, fn)
    check("W = 6", w6["pkg/a.py"]["moduleCommitsInWindow"] == 1 and "moduleMonthsSinceLastChange" not in w6["pkg/a.py"])
    ab = M.module_abox_properties(out["pkg/empty.py"])
    check("ABox: LOC-0 module withholds the rule inputs", "moduleChangeMonthsInWindow" not in ab
          and "moduleRelChurnInWindow" not in ab and ab["moduleLoc"] == 0)
    w = AboxWriter()
    pi = w.project("t1", {"monthsObserved": 3}, None, close_months=False)
    mi = w.module(pi, "pkg/a.py", M.module_abox_properties(a))
    nt = w.ntriples()
    check("ABox: module typed, linked and measured", f"<{mi}> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://senso-framework.org/ontology/seo#Module>" in nt
          and "seo#hasModule" in nt and '"0.23"^^<http://www.w3.org/2001/XMLSchema#decimal>' in nt
          and w.module(pi, "pkg/a.py", {}) == mi)
    check("module slug is collision-free for look-alike paths",
          AboxWriter.module_slug("a/b") != AboxWriter.module_slug("a_b"))
    check("test patch parser", P.parse_test_patch_files("diff --git a/t/x.py b/t/x.py\n--- a/t/x.py\n+++ b/t/x.py\n"
                                                       "diff --git a/n.py b/n2.py\n") == ["n.py", "n2.py", "t/x.py"])


def test_reasoning() -> None:
    from ontology.reasoning.reasoner import HermitReasoner

    # (rel churn or None, change months, LOC) -> expected label
    cases = {
        "stable": (0.0999, 2, 100, "StableModule"), "stable_edge_months": (0.0, 2, 10, "StableModule"),
        "active_churn_edge": (0.10, 0, 100, "ActiveModule"), "active_months_edge": (0.0, 3, 100, "ActiveModule"),
        "active_both": (0.5, 6, 100, "ActiveModule"), "undetermined_loc0": (None, 5, 0, None)}
    w = AboxWriter()
    pi = w.project("t2", {"monthsObserved": 3}, None, close_months=False)
    iris = {}
    for name, (rel, mo, loc, _) in cases.items():
        row = {"modulePath": name, "moduleLoc": loc, "moduleChangeMonthsInWindow": mo,
               "moduleCommitsInWindow": mo, "moduleLinesChangedInWindow": 1}
        if rel is not None:
            row["moduleRelChurnInWindow"] = rel
        iris[name] = w.module(pi, name, M.module_abox_properties(row))
    with tempfile.TemporaryDirectory() as td:
        rb = HermitReasoner(temp_dir=Path(td)).infer(w.ntriples())
    check("HermiT consistent over module ABox", rb.consistent, str(rb.error))
    for name, (_, _, _, want) in cases.items():
        got = rb.labels_of(iris[name]) & {"StableModule", "ActiveModule"}
        check(f"module label {name}", got == ({want} if want else set()), str(sorted(got)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--reason", action="store_true", help="also run the HermiT checks (needs Java)")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    test_partition()
    test_measurements()
    if a.reason:
        test_reasoning()
    failed = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    for name, _, detail in failed:
        print(f"FAILED: {name} {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
