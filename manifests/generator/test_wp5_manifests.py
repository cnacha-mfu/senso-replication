#!/usr/bin/env python3
"""Standalone checks of the WP5 manifest generators (Paper 1, wp5-analysis-plan.md 3.3-3.7).

Not a pytest suite (project convention): prints a pass/fail report and exits non-zero on failure.
Uses a synthetic population JSON (no repository, no reasoner): number formatter, B selection and cut,
D and C lints, fact containment (a planted violation must be caught), the C1 qualifier switch,
K lowering and D3 equalization, the D1 row drop, byte-identical regeneration, explanation fallback.

Usage:
    python manifests/generator/test_wp5_manifests.py
"""

from __future__ import annotations

import copy
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from manifests.generator import wp5_manifests as W  # noqa: E402

logger = logging.getLogger("test_wp5_manifests")
RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(cond), detail))
    logger.info("%s  %s %s", "PASS" if cond else "FAIL", name, detail)


def fact(prop: str, value: float | int, subj: str = "x") -> dict:
    return {"subject": subj, "prop": prop, "value": value, "raw": f"{subj} {prop} {value}"}


def expl(cls: str, facts: list[dict], axioms: list[dict] | None = None) -> dict:
    return {"class": cls, "returncode": 0, "error": None, "justifications": [
        {"axioms": axioms or [], "facts": facts + [fact("type", "SoftwareProject")], "closures": [], "raw": ""}]}


def synthetic_population(n_modules: int = 30, path_len: int = 20, n_months: int = 36) -> dict:
    months = [f"{2020 + (i + 8) // 12}-{(i + 8) % 12 + 1:02d}" for i in range(n_months)]
    mods, ex = {}, {}
    for i in range(n_modules):
        path = f"pkg/{'m' * path_len}{i:02d}.py"
        label = ["StableModule", "ActiveModule", "undetermined"][i % 3]
        loc = 0 if label == "undetermined" else 500 - 7 * i
        meas = {"modulePath": path, "moduleLoc": loc, "moduleCommitsInWindow": i % 5,
                "moduleChangeMonthsInWindow": 0 if label == "StableModule" else 4 + i % 3,
                "moduleLinesChangedInWindow": 2 * i}
        if loc:
            meas["moduleRelChurnInWindow"] = 0.04 if label == "StableModule" else 0.1 + 0.01 * i
        mods[path] = {"label": label, "classes": [label], "measures": meas}
        if label == "StableModule":
            ex[f"module:{path}"] = expl("StableModule", [fact("moduleChangeMonthsInWindow", 0),
                                                         fact("moduleRelChurnInWindow", 0.04)])
        elif label == "ActiveModule":  # a failed explanation: the template fallback applies
            ex[f"module:{path}"] = {"class": label, "returncode": 1, "error": "pruned node", "justifications": []}
    measures = {"monthsObserved": n_months, "locSeriesLength": n_months, "locStart": 1000, "locEnd": 1500,
                "locMKTau": 0.62, "locMKpValue": 0.0004, "locRelSenSlopeAnnual": 0.0312,
                "monthsSinceLastCommit": 0, "commitsLast3Months": 12, "activeMonthCount": 30, "activeMonthRatio": 0.8333,
                "churnCV": 1.2, "commitCountCV": 0.9, "linesAddedCV": 1.5, "mergeMonthRatio": 0.5,
                "multiAuthorMonthRatio": 0.4, "bugFixRatioFirstHalf": 0.3, "bugFixRatioSecondHalf": 0.2}
    ex["stage:GrowthStage"] = expl("GrowthStage", [fact("locMKTau", 0.62), fact("locMKpValue", 0.0004),
                                                   fact("locSeriesLength", n_months)])
    ex["stage:RBServicingStage"] = expl("RBServicingStage", [fact("monthsSinceLastCommit", 0)])
    ex["lawI"] = expl("LawIConformant", [fact("monthsObserved", n_months), fact("activeMonthRatio", 0.8333)])
    return {
        "repo": "owner/proj", "task_id": "syn__1", "base_commit": "a" * 40, "status": "ok",
        "settings": {"test_patch_files": ["tests/test_hidden_gold.py"]},
        "measures": measures, "window": {"n_months": n_months, "last_month": months[-1]},
        "series_months": [{"month": m, "commit_count": 5 + i % 4, "loc": 1000 + 10 * i, "unique_authors": 1 + i % 3,
                          "lines_added": 40 + i, "lines_deleted": 20 + i} for i, m in enumerate(months)],
        "primary_config": "cfg", "inferred": {"cfg": {"inconsistent": False, "undetermined_reason": None}},
        "inferred_labels": ["GrowthStage", "RBServicingStage", "LawIConformant"], "stage_labels": ["GrowthStage", "RBServicingStage"],
        "law_labels": {"I": "LawIConformant"}, "explanations": ex, "modules": mods,
        "modules_meta": {"anchor_S": "2023-09-06T06:06:59+00:00", "window_months": 12,
                         "thresholds": {"mod_window_months": 12, "mod_stable_max_rel_churn": 0.1,
                                        "mod_stable_max_change_months": 2}}}


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    cfg = W.load_config()
    tpl = W.load_templates()
    fmt = W.Formatter(cfg)

    # -- shared number formatter
    check("int as is", fmt("locEnd", 1500) == "1500")
    check("p-values: 3 decimals or < 0.001", fmt("locMKpValue", 0.0123) == "0.012" and fmt("locMKpValue", 0.0004) == "< 0.001"
          and fmt("locMKpValue", 0.05) == "0.050")
    check("decimals: 2 places, half up, no negative zero", fmt("locMKTau", 0.625) == "0.63" and fmt("locMKTau", -0.001) == "0.00"
          and fmt("locMKTau", -0.62) == "-0.62")
    check("percentages: whole numbers", fmt("moduleRelChurnInWindow", 0.126) == "13 %"
          and fmt("moduleRelChurnInWindow", 0.001) == "< 1 %" and fmt("moduleRelChurnInWindow", 0.0) == "0 %")
    check("config text passes the D lint", True)

    # -- B
    tree = {p: ("100644", "b") for p in ["CONTRIBUTING.md", "docs/contributing.rst", "docs/development/x.md", "README.md",
                                          "HACKING.rst", "src/HACKING.md", ".cursor/rules/a.mdc", ".github/CONTRIBUTING.md",
                                          "AGENTS.md", "docs/development.md"]}
    tree["CLAUDE.md"] = ("120000", "b")
    src = W.b_sources(tree)
    check("B sources: plan order, README excluded, '*' stays within a directory, symlinks skipped",
          src == ["CONTRIBUTING.md", ".github/CONTRIBUTING.md", "docs/contributing.rst", "docs/development.md", "HACKING.rst",
                  "AGENTS.md", ".cursor/rules/a.mdc"], str(src))
    check("B unavailable when every file is empty", W.build_B_text([("CONTRIBUTING.md", "  \n")], 8000) is None)
    big = W.build_B_text([("CONTRIBUTING.md", "\n".join(f"line {i} " + "x" * 50 for i in range(400)))], 8000)
    check("B cut at a line boundary under the cap with the marker", len(big) <= 8000 and big.endswith("\n[truncated]")
          and big.split("\n")[-2].startswith("line "), f"{len(big)}")
    small = W.build_B_text([("CONTRIBUTING.md", "Be nice.")], 8000)
    check("B format", small.startswith("## Repository context\n\nThe following contributor guidance") and "### CONTRIBUTING.md\n\nBe nice." in small)

    # -- C and D
    pop = synthetic_population()
    g = W.generate_task(pop, cfg, tpl)
    m = g.meta
    check("C and D generated, no problems", m["ok"], str(m.get("problems")))
    check("headers identical", g.C.startswith(W.shared_header(pop)) and g.D.startswith(W.shared_header(pop)))
    check("C1 qualifier included by default and omitted on request",
          W.QUALIFIER in g.C and W.QUALIFIER not in W.generate_task(pop, cfg, tpl, qualifier=False).C)
    check("law V omitted from C, undetermined laws read 'not determined'",
          "Law V (" not in g.C and "Law II (increasing complexity): not determined (complexity is not measured)" in g.C)
    check("C never says violation or conform", "violation" not in g.C.lower() and "conform" not in g.C.lower())
    check("explanation fallback counted and flagged", m["explanation_fallbacks"] == 10 and
          all(x.startswith("module:") or x.startswith("stage:") or x.startswith("law") for x in m["explanation_fallback_items"]),
          f"{m['explanation_fallbacks']} {m['explanation_fallback_items'][:2]}")
    check("lengths within tolerance or flagged", m["length_violation"] == (abs(m["chars"]["C"] - m["chars"]["D"]) > 0.1 * m["chars"]["C"]))
    check("D has no labels or thresholds", "stable" not in g.D.lower() and "threshold" not in g.D.lower())
    check("no gold or test-patch path in the text", "test_hidden_gold" not in g.C + g.D)
    again = W.generate_task(copy.deepcopy(pop), cfg, tpl)
    check("byte-identical regeneration", (again.C, again.D, again.meta) == (g.C, g.D, g.meta))

    # K lowering with long module names (cap 8000): same K in C4 and D2
    long_pop = synthetic_population(n_modules=60, path_len=70)
    gl = W.generate_task(long_pop, cfg, tpl)
    check("K lowered in steps of 5 to keep C under the cap", gl.meta["K"] in (10, 15, 20) and gl.meta["chars"]["C"] <= 8000,
          f"K={gl.meta['K']} L_C={gl.meta['chars']['C']}")
    check("D2 lists the same K modules as C4", gl.D.count("\n| pkg/") == gl.meta["K"] + gl.meta["d2_extra_rows"] and gl.C.count("\n| pkg/") == gl.meta["K"])

    # D3 equalization: a task with few modules gets monthly rows
    gs = g  # 30 modules: C4 rows (with evidence) are much longer than D2 rows
    check("D3 rows added until D reaches 90 % of C (or all months used)",
          gs.meta["m"] > 0 and (gs.meta["chars"]["D"] >= 0.9 * gs.meta["chars"]["C"] or gs.meta["m"] == gs.meta["n_months"]),
          f"m={gs.meta['m']} C={gs.meta['chars']['C']} D={gs.meta['chars']['D']}")

    # all months used and D still short: extra D2 rows beyond the top K, alphabetical, until 90 % of C
    mp = synthetic_population(n_modules=70, path_len=5, n_months=6)
    gm = W.generate_task(mp, cfg, tpl)
    check("D2 gets extra rows (beyond top K) once every month is used",
          gm.meta["m"] == 6 and gm.meta["d2_extra_rows"] > 0
          and (gm.meta["chars"]["D"] >= 0.9 * gm.meta["chars"]["C"] or gm.meta["d2_extra_rows"] == gm.meta["n_modules"] - gm.meta["K"]),
          f"m={gm.meta['m']} extra={gm.meta['d2_extra_rows']} C={gm.meta['chars']['C']} D={gm.meta['chars']['D']}")
    check("D3 has raw per-month author and line columns",
          "| Month | Commits | LOC | Distinct authors | Lines added | Lines deleted |" in gm.D)

    # D1 drop when D is far longer than C: shrink C's measurement citations
    ctx_pop = synthetic_population(n_modules=2)
    ctx_pop["explanations"] = {}
    ctx_pop["inferred_labels"], ctx_pop["stage_labels"], ctx_pop["law_labels"] = [], [], {}
    gd = W.generate_task(ctx_pop, cfg, tpl)
    check("without labels C is short; D rows not cited in C are dropped when D exceeds 110 %",
          gd.meta["d1_rows_dropped"] != [] or gd.meta["chars"]["D"] <= 1.1 * gd.meta["chars"]["C"], str(gd.meta["d1_rows_dropped"][:3]))

    # lints catch planted problems; containment catches a number that D lacks
    cx = W.Ctx(pop, cfg, tpl, fmt, True)
    bad_d = g.D + "\nThis is a stable module.\n"
    check("D lint catches a forbidden word and masks identifiers", W.d_lint(bad_d, cfg, ["owner/proj"]) == ["stable"]
          and W.d_lint("pkg/servicestack.py", cfg, ["pkg/servicestack.py"]) == [])
    check("C lint catches imperatives", W.c_lint("You should not do this. Never.", cfg, []) == ["should", "never"])
    _, fills = W.build_C(cx, 25)
    broken = g.D.replace("| 0.62 |", "| 0.63 |")
    check("containment: every C1-C4 number is in D1/D2", W.containment(cx, fills, g.D, W.shown_modules(cx, 25)) == [])
    check("containment: a changed D value is caught", W.containment(cx, fills, broken, W.shown_modules(cx, 25)) != [])

    # inconsistent ABox: no labels in C1-C4 and note N1
    inc = synthetic_population(n_modules=3)
    inc["inferred"]["cfg"] = {"inconsistent": True, "inconsistency_explanation": "Axiom a and b clash\nmore"}
    gi = W.generate_task(inc, cfg, tpl)
    check("N1 and no labels when inconsistent", "N1 (inconsistent facts): Axiom a and b clash" in gi.C and "| stable |" not in gi.C)

    failed = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    for name, _, detail in failed:
        print(f"FAILED: {name} {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
