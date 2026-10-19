#!/usr/bin/env python3
"""Deterministic B, C and D manifests of the WP5 agent study (Paper 1, RQ3/RQ4).

Implements ``papers/paper1/wp5-analysis-plan.md`` sections 3.3-3.7. No LLM is called at any step.

  * **B** (3.7): the human contributor guidance found in the base tree of the task, cut at the
    length cap; unavailable when none of the listed files exists.
  * **C** (3.3): the SENSO manifest. Sections C0-C5 are filled from the per-task population JSON
    written by ``populate_v2.py --snapshot-commit``: the inferred stage and LOC-trend labels, the
    Lehman-law lines, anti-patterns, the module-stability table and the reasoner notes. Every number
    comes from the facts of the label's Pellet justification (``explanations`` block of the JSON);
    a placeholder the justification does not contain is read from the asserted measurement of the same
    individual (counted as ``placeholders_from_abox``); if the explanation itself failed the template is
    filled from asserted values and flagged ``explanation_fallback``.
  * **D** (3.4): the same facts without labels, thresholds, explanations or ranking: header, the fixed
    measurement set Phi (``configs/wp5_manifests.yaml``), the module table (same K modules as C4,
    alphabetical) and a monthly table whose length equalizes D to C.
  * Length equalization (3.5), the D and C lints, fact containment, the shared number formatter and
    the byte-identical determinism check (3.6).

The only RQ1-dependent element is the qualifier sentence in C1 (3.8): included unless the recorded
RQ1 verdict is ``GO`` (default ``UNRESOLVED``, i.e. included; the parameter is recorded in the index).

Usage:
    python manifests/generator/wp5_manifests.py \\
        --population-dir experiments/paper1_ontology_manifests/results/real_v2/wp5/population \\
        --repo-cache ~/research/data/wp5/repos \\
        --out-dir experiments/paper1_ontology_manifests/results/real_v2/wp5 [--task-ids ID ...] \\
        [--rq1-verdict GO|NOGO|UNRESOLVED] [--skip-b]
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import logging
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger("senso.wp5_manifests")

DEFAULT_CONFIG = PROJECT_ROOT / "experiments" / "paper1_ontology_manifests" / "configs" / "wp5_manifests.yaml"
DEFAULT_TBOX = PROJECT_ROOT / "ontology" / "modules"
DEFAULT_REPO_CACHE = Path.home() / "research" / "data" / "wp5" / "repos"
DEFAULT_OUT = (PROJECT_ROOT / "experiments" / "paper1_ontology_manifests" / "results" / "real_v2" / "wp5")
HEADING = "## Repository context"
QUALIFIER = ("This label is a rule-based inference; it has not been shown to agree with "
             "maintainer-declared status.")
B_INTRO = "The following contributor guidance is taken from the repository at the task's base commit."
TRUNCATED = "[truncated]"
B_PATTERNS = (  # plan 3.7, in this order; '*' never crosses '/'
    "CONTRIBUTING", "CONTRIBUTING.md", "CONTRIBUTING.rst", "CONTRIBUTING.txt", ".github/CONTRIBUTING*",
    "docs/CONTRIBUTING*", "docs/contributing*", "docs/development*.md", "docs/development*.rst",
    "HACKING*", "DEVELOPMENT*", "CLAUDE.md", "AGENTS.md", "GEMINI.md", ".cursorrules", ".cursor/rules/*",
    ".github/copilot-instructions.md")

STAGE_C1 = {"GrowthStage": "growth", "StabilizationStage": "stabilization", "DeclineStage": "decline"}
STAGE_C2 = {"RBActiveDevelopmentStage": "active development", "RBServicingStage": "servicing",
            "RBPhaseOutStage": "phase-out"}
C1_KEY = {"GrowthStage": "G", "StabilizationStage": "S", "DeclineStage": "D"}
C2_KEY = {"RBActiveDevelopmentStage": "A", "RBServicingStage": "S", "RBPhaseOutStage": "P"}
LAWS = (("I", "continuing change"), ("II", "increasing complexity"), ("III", "self-regulation"),
        ("IV", "conservation of organisational stability"), ("VI", "continuing growth"),
        ("VII", "declining quality"), ("VIII", "feedback system"))
LAW_RE = re.compile(r"^Law([IVX]+)(NonConformant|Conformant)")
ANTI_NAMES = {
    "ExhibitsAgentAssociatedComplexityGrowth": "agent-associated complexity growth",
    "ExhibitsDependencySprawl": "dependency sprawl",
    "ExhibitsRefactoringAvoidance": "refactoring avoidance",
    "ExhibitsCopyPasteOverReuse": "copy-paste over reuse"}
MODULE_LABEL = {"StableModule": "stable", "ActiveModule": "active", "undetermined": "undetermined"}
GROUP_ORDER = ("StableModule", "ActiveModule", "undetermined")
PH_RE = re.compile(r"\{(\w+)\}")


# ---------------------------------------------------------------------------
# Configuration, number formatter, templates
# ---------------------------------------------------------------------------

def _half_up(x: float, nd: int) -> Decimal:
    return Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)


class Formatter:
    """The one number formatter shared by C and D (plan 3.6).

    Integers as is; p-values to 3 decimals or ``< 0.001``; other decimals to 2 decimals;
    percentages to whole numbers (``< 1 %`` for a positive value that rounds to 0).
    The kind of a property comes from the config (``phi`` and ``module_columns``); unknown
    properties are an int if the value is an int, ``p`` if the name ends in ``pValue``, else ``dec``.
    """

    def __init__(self, cfg: Mapping[str, Any]) -> None:
        self.kinds = {r["property"]: r["kind"] for r in cfg["phi"]}
        self.kinds.update({r["property"]: r["kind"] for r in cfg["module_columns"]})

    def kind(self, prop: str, value: Any) -> str:
        """Format kind of a property."""
        if prop in self.kinds:
            return self.kinds[prop]
        if prop.endswith("pValue"):
            return "p"
        return "int" if isinstance(value, int) and not isinstance(value, bool) else "dec"

    def __call__(self, prop: str, value: Any) -> str:
        """Formatted text of a measured value."""
        return self.fmt(self.kind(prop, value), value)

    @staticmethod
    def fmt(kind: str, value: Any) -> str:
        """Format a value of the given kind."""
        v = float(value)
        if kind == "int":
            return str(int(round(v)))
        if kind == "p":
            return "< 0.001" if v < 0.001 else f"{_half_up(v, 3)}"
        if kind == "pct":
            n = int(_half_up(v * 100, 0))
            return "< 1 %" if (n == 0 and v > 0) else f"{n} %"
        s = f"{_half_up(v, 2)}"
        return "0.00" if s == "-0.00" else s


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    """Load the generator config and check its display names and definitions against the D lint."""
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    bad = []
    for r in cfg["phi"]:
        for fld in ("display", "definition"):
            bad += [(r["property"], fld, w) for w in cfg["d_lint_words"] if w in r[fld].lower()]
    for r in cfg["module_columns"]:
        bad += [(r["property"], "header", w) for w in cfg["d_lint_words"] if w in r["header"].lower()]
    for r in cfg["monthly_columns"]:
        bad += [(r["key"], "header", w) for w in cfg["d_lint_words"] if w in r["header"].lower()]
    if bad:
        raise ValueError(f"config text trips the D lint: {bad}")
    cfg["_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return cfg


def load_templates(tbox_dir: Path = DEFAULT_TBOX) -> dict[str, dict[str, Any]]:
    """``{class: {"template": str, "thr": [ids]}}`` from the explanation annotations of seo-inference.owl."""
    ns = {"owl": "http://www.w3.org/2002/07/owl#", "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
          "seo": "http://senso-framework.org/ontology/seo#"}
    root = ET.parse(tbox_dir / "seo-inference.owl").getroot()
    out: dict[str, dict[str, Any]] = {}
    for c in root.findall("owl:Class", ns):
        about = c.get("{%s}about" % ns["rdf"])
        t = c.find("seo:explanationTemplate", ns)
        if about is None or t is None or t.text is None:
            continue
        out[about.split("#")[-1]] = {
            "template": t.text,
            "thr": sorted(e.text for e in c.findall("seo:thresholdId", ns) if e.text)}
    return out


# ---------------------------------------------------------------------------
# Facts and template filling
# ---------------------------------------------------------------------------

@dataclass
class Ctx:
    """Everything the builders share for one task."""

    pop: Mapping[str, Any]
    cfg: Mapping[str, Any]
    tpl: Mapping[str, Mapping[str, Any]]
    fmt: Formatter
    qualifier: bool
    modules: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    expl: Mapping[str, Any] = field(default_factory=dict)
    measures: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.modules = self.pop.get("modules") or {}
        self.expl = self.pop.get("explanations") or {}
        self.measures = self.pop.get("measures") or {}


@dataclass
class Fills:
    """What the C builder cites and where facts came from (inputs of the checks and the index)."""

    tokens: list[tuple] = field(default_factory=list)  # ("repo", prop, text) / ("mod", path, prop, text)
    cited_props: set[str] = field(default_factory=set)
    fallbacks: list[str] = field(default_factory=list)
    from_abox: int = 0


def first_justification(entry: Optional[Mapping[str, Any]]) -> Optional[Mapping[str, Any]]:
    """First justification of an explanation entry, or None if it failed or is empty."""
    if not entry or entry.get("error") or entry.get("returncode", 0) != 0:
        return None
    js = entry.get("justifications") or []
    return js[0] if js else None


def justification_facts(j: Optional[Mapping[str, Any]]) -> dict[str, Any]:
    """Property -> value of the (non-type) facts of a justification."""
    if not j:
        return {}
    return {f["prop"]: f["value"] for f in j["facts"] if f["prop"] != "type"}


def branch_template(cls: str, j: Optional[Mapping[str, Any]], tpl: Mapping[str, Mapping[str, Any]]) -> str:
    """Class whose template to show: a named branch ``X subClassOf cls`` of the justification, else ``cls``."""
    if j:
        pat = re.compile(rf"^(\S+) subClassOf {re.escape(cls)}$")
        for name in sorted(m.group(1) for a in j["axioms"] if (m := pat.match(a["text"]))):
            if name in tpl:
                return name
    return cls


def fill(cls: str, ctx: Ctx, entry: Optional[Mapping[str, Any]], asserted: Mapping[str, Any],
         fills: Fills, scope: tuple, *, what: str) -> tuple[str, list[str]]:
    """Fill the explanation template of ``cls`` from a justification (plan 3.3).

    Returns the text and the threshold ids of the template actually used.
    """
    j = first_justification(entry)
    use = branch_template(cls, j, ctx.tpl)
    t = ctx.tpl[use]["template"]
    facts = justification_facts(j)
    if j is None:
        fills.fallbacks.append(what)

    def rep(m: re.Match) -> str:
        prop = m.group(1)
        if prop in facts:
            v = facts[prop]
        elif prop in asserted:
            v = asserted[prop]
            if j is not None:
                fills.from_abox += 1
        else:
            return "n/a"
        s = ctx.fmt(prop, v)
        fills.tokens.append((*scope, prop, s))
        fills.cited_props.add(prop)
        return s

    return PH_RE.sub(rep, t).replace("= < ", "< "), list(ctx.tpl[use]["thr"])


def _mask(text: str, identifiers: Sequence[str]) -> str:
    for ident in sorted({i for i in identifiers if i}, key=len, reverse=True):
        text = text.replace(ident, "ID")
    return text


# ---------------------------------------------------------------------------
# Shared header
# ---------------------------------------------------------------------------

def shared_header(pop: Mapping[str, Any]) -> str:
    """C0 and D0: the shared header (identical text in C and D)."""
    s_date = pop["modules_meta"]["anchor_S"][:10]
    w = pop["window"]
    return (f"{HEADING}\n\nThe following information about {pop['repo']} was computed from its git history up "
            f"to the base commit of this task ({s_date}). Repository-level figures cover {w['n_months']} "
            f"complete months ending {w['last_month']}; module-level figures cover the "
            f"{pop['modules_meta']['window_months']} months before the base commit. "
            "Use it as background when working on the task.\n")


# ---------------------------------------------------------------------------
# Condition C
# ---------------------------------------------------------------------------

N3_TEXT = {  # (C1 key, C2 key) -> text; numbers are tau, p, rel (rb_min_rel_loc_growth_per_year is G) and months
    ("G", "A"): "LOC grows significantly (τ = {tau}, p {p}) and by {rel} of median size per year, at or above "
                "{G}; the stage rule therefore infers active development.",
    ("G", "S"): "LOC grows significantly (τ = {tau}, p {p}) but by only {rel} of median size per year, below "
                "{G}; the stage rule therefore infers servicing.",
    ("G", "P"): "LOC grows significantly (τ = {tau}, p {p}), but the last commit was {months} months before "
                "the end of the window, at or above the {D}-month dormancy limit; the stage rule therefore "
                "infers phase-out.",
    ("S", "S"): "There is no significant LOC trend (τ = {tau}, p {p}); the stage rule therefore infers "
                "servicing.",
    ("S", "P"): "There is no significant LOC trend (τ = {tau}, p {p}), and the last commit was {months} "
                "months before the end of the window, at or above the {D}-month dormancy limit; the stage "
                "rule therefore infers phase-out.",
    ("D", "S"): "LOC shrinks significantly (τ = {tau}, p {p}); active development needs growth, so the stage "
                "rule infers servicing.",
    ("D", "P"): "LOC shrinks significantly (τ = {tau}, p {p}), and the last commit was {months} months "
                "before the end of the window, at or above the {D}-month dormancy limit; the stage rule "
                "therefore infers phase-out.",
}


def _stage_classes(pop: Mapping[str, Any]) -> tuple[Optional[str], Optional[str]]:
    labels = pop.get("stage_labels") or []
    return (next((c for c in labels if c in STAGE_C1), None), next((c for c in labels if c in STAGE_C2), None))


def _law_label(pop: Mapping[str, Any], roman: str) -> Optional[str]:
    return (pop.get("law_labels") or {}).get(roman)


def _reason_text(cfg: Mapping[str, Any], pop: Mapping[str, Any]) -> str:
    code = (pop["inferred"][pop["primary_config"]].get("undetermined_reason") or "no_stage_class_inferred")
    texts = [cfg["undetermined_reason_text"].get(c, c) for c in code.split(";")]
    return "; ".join(texts)


def build_C(ctx: Ctx, K: int) -> tuple[str, Fills]:
    """Condition C with K modules in C4. Returns the text and what it cites."""
    pop, cfg, fmt = ctx.pop, ctx.cfg, ctx.fmt
    pe = pop["inferred"][pop["primary_config"]]
    inconsistent = bool(pe.get("inconsistent"))
    fills = Fills()
    asserted = ctx.measures
    out = [shared_header(pop)]
    c1, c2 = _stage_classes(pop)

    # -- C1
    sec = ["### Lifecycle stage (inferred)\n"]
    if inconsistent:
        sec.append("Not shown: the reasoner found the measurements inconsistent (see the notes).")
    else:
        if c2:
            txt, _ = fill(c2, ctx, ctx.expl.get(f"stage:{c2}"), asserted, fills, ("repo",), what=f"stage:{c2}")
            sec.append(f"- Lifecycle stage (rule-based): {STAGE_C2[c2]}. Evidence: {txt}.")
        else:
            sec.append(f"- Lifecycle stage (rule-based): not determined ({_reason_text(cfg, pop)}).")
        if c1:
            txt, _ = fill(c1, ctx, ctx.expl.get(f"stage:{c1}"), asserted, fills, ("repo",), what=f"stage:{c1}")
            sec.append(f"- LOC trend: {STAGE_C1[c1]}. Evidence: {txt}.")
        else:
            sec.append(f"- LOC trend: not determined ({_reason_text(cfg, pop)}).")
        if ctx.qualifier:
            sec.append(QUALIFIER)
    out.append("\n".join(sec) + "\n")

    # -- C2
    sec = ["### Observed evolution regularities (Lehman's laws, descriptive)\n"]
    if inconsistent:
        sec.append("Not shown: the reasoner found the measurements inconsistent (see the notes).")
    else:
        undetermined_laws: list[tuple[str, str]] = []
        for roman, name in LAWS:
            lab = _law_label(pop, roman)
            head = f"- Law {roman} ({name}): "
            if lab is None:
                req = cfg["law_required"][roman]
                reason = (cfg["law_not_measured"][roman] if not any(r in asserted for r in req)
                          else cfg["law_guard_not_met"])
                undetermined_laws.append((roman, reason))
                sec.append(head + f"not determined ({reason}).")
                continue
            m = LAW_RE.match(lab)
            verdict = "consistent with" if m and m.group(2) == "Conformant" else "not consistent with"
            txt, thr = fill(lab, ctx, ctx.expl.get(f"law{roman}"), asserted, fills, ("repo",),
                            what=f"law{roman}")
            ids = f" Thresholds: {', '.join(thr)}." if thr else ""
            sec.append(head + f"{verdict} this regularity. {txt[0].upper() + txt[1:]}.{ids}")
    out.append("\n".join(sec) + "\n")

    # -- C3
    sec = ["### Inferred anti-patterns\n"]
    if inconsistent:
        sec.append("Not shown: the reasoner found the measurements inconsistent (see the notes).")
    else:
        anti = [c for c in pop.get("inferred_labels", []) if c in ANTI_NAMES]
        for c in anti:
            txt, thr = fill(c, ctx, ctx.expl.get(f"anti:{c}"), asserted, fills, ("repo",), what=f"anti:{c}")
            sec.append(f"- {ANTI_NAMES[c][0].upper() + ANTI_NAMES[c][1:]}: {txt}. "
                       f"Thresholds: {', '.join(thr)}.")
        if not anti:
            sec.append("none inferred")
    out.append("\n".join(sec) + "\n")

    # -- C4
    thr_meta = pop["modules_meta"]["thresholds"]
    rule = {"StableModule": f"rule: at most {thr_meta['mod_stable_max_change_months']} change months and "
                            f"under {fmt.fmt('pct', thr_meta['mod_stable_max_rel_churn'])} relative churn",
            "ActiveModule": f"rule: more than {thr_meta['mod_stable_max_change_months']} change months or at "
                            f"least {fmt.fmt('pct', thr_meta['mod_stable_max_rel_churn'])} relative churn"}
    sec = ["### Module stability (inferred)\n"]
    shown = shown_modules(ctx, K)
    if inconsistent:
        sec.append("Not shown: the reasoner found the measurements inconsistent (see the notes).")
    else:
        sec += ["| Module | Label | Evidence |", "|---|---|---|"]
        for path in sorted(shown, key=lambda p: (GROUP_ORDER.index(ctx.modules[p]["label"]), p)):
            mod = ctx.modules[path]
            lab = mod["label"]
            if lab == "undetermined":
                ev = "not determined (the module has no non-blank lines)"
            else:
                txt, _ = fill(lab, ctx, ctx.expl.get(f"module:{path}"), mod["measures"], fills,
                              ("mod", path), what=f"module:{path}")
                ev = f"{txt}; {rule[lab]}"
            sec.append(f"| {path} | {MODULE_LABEL[lab]} | {ev} |")
        rest = [m for m in ctx.modules if m not in set(shown)]
        cnt = {g: sum(1 for m in rest if ctx.modules[m]["label"] == g) for g in GROUP_ORDER}
        sec.append(f"\nOther modules: {cnt['StableModule']} stable, {cnt['ActiveModule']} active, "
                   f"{cnt['undetermined']} undetermined.")
    out.append("\n".join(sec) + "\n")

    # -- C5
    out.append("### Notes from the reasoner\n\n" + "\n".join(build_notes(ctx, c1, c2, fills)) + "\n")
    return "\n".join(out), fills


def shown_modules(ctx: Ctx, K: int) -> list[str]:
    """The K largest modules by LOC (ties by path), the same selection in C4 and D2."""
    return sorted(ctx.modules, key=lambda p: (-ctx.modules[p]["measures"]["moduleLoc"], p))[:K]


def build_notes(ctx: Ctx, c1: Optional[str], c2: Optional[str], fills: Fills) -> list[str]:
    """C5: notes N1-N4 in this order, or ``none``."""
    pop, cfg, fmt = ctx.pop, ctx.cfg, ctx.fmt
    pe = pop["inferred"][pop["primary_config"]]
    thr = pop["modules_meta"]["thresholds"]
    notes: list[str] = []
    if pe.get("inconsistent"):  # N1
        raw = (ctx.expl.get("_inconsistent") or {}).get("raw_text") or pe.get("inconsistency_explanation") \
            or pe.get("inconsistency_error") or "no explanation available"
        first = next((ln.strip() for ln in raw.splitlines() if ln.strip()), "no explanation available")
        notes.append(f"- N1 (inconsistent facts): {first}")
        return notes
    # N2: undetermined label families
    fam: list[str] = []
    if c1 is None or c2 is None:
        fam.append(f"lifecycle stage ({_reason_text(cfg, pop)})")
    for roman, _ in LAWS:
        if _law_label(pop, roman) is None:
            req = cfg["law_required"][roman]
            reason = (cfg["law_not_measured"][roman] if not any(r in ctx.measures for r in req)
                      else cfg["law_guard_not_met"])
            fam.append(f"Law {roman} ({reason})")
    n_und = sum(1 for m in ctx.modules.values() if m["label"] == "undetermined")
    if n_und:
        fam.append(f"module stability for {n_und} module(s) without non-blank lines")
    if fam:
        notes.append("- N2 (undetermined label families): " + "; ".join(fam) + ".")
    # N3: C1/C2 combination text
    if c1 and c2 and (C1_KEY[c1], C2_KEY[c2]) in N3_TEXT:
        j1 = justification_facts(first_justification(ctx.expl.get(f"stage:{c1}")))
        j2 = justification_facts(first_justification(ctx.expl.get(f"stage:{c2}")))
        facts = {**ctx.measures, **j1, **j2}

        def f(prop: str) -> str:
            if prop not in facts:
                return "n/a"
            s = fmt(prop, facts[prop])
            fills.tokens.append(("repo", prop, s))
            fills.cited_props.add(prop)
            return s
        p_txt = f("locMKpValue")
        # the dormancy and growth limits are TBox constants, shown as numbers (not facts)
        text = N3_TEXT[(C1_KEY[c1], C2_KEY[c2])].format(
            tau=f("locMKTau"), p=p_txt if p_txt.startswith("<") else "= " + p_txt,
            rel=f("locRelSenSlopeAnnual"), months=f("monthsSinceLastCommit"),
            G=_register(ctx, "rb_min_rel_loc_growth_per_year"), D=_register(ctx, "rb_dormancy_months"))
        notes.append(f"- N3 (stage rules): {text}")
    # N4: stage-module tension
    mods = ctx.modules
    if c2 in ("RBServicingStage", "RBPhaseOutStage"):
        act = sorted((p for p, m in mods.items() if m["label"] == "ActiveModule"),
                     key=lambda p: (-mods[p]["measures"]["moduleLinesChangedInWindow"], p))[:5]
        if act:
            items = "; ".join(f"{p} ({fmt('moduleLinesChangedInWindow', mods[p]['measures']['moduleLinesChangedInWindow'])}"
                              f" lines changed)" for p in act)
            notes.append(f"- N4 (stage and modules): Although the repository-level stage is {STAGE_C2[c2]}, "
                         f"these modules changed often in the last {thr['mod_window_months']} months: {items}.")
    elif c2 == "RBActiveDevelopmentStage":
        stab = sorted((p for p, m in mods.items() if m["label"] == "StableModule"),
                      key=lambda p: (-mods[p]["measures"]["moduleLoc"], p))[:5]
        if stab:
            items = "; ".join(f"{p} ({fmt('moduleLoc', mods[p]['measures']['moduleLoc'])} LOC)" for p in stab)
            notes.append(f"- N4 (stage and modules): Although the repository-level stage is active development, "
                         f"these modules were rarely changed in the last {thr['mod_window_months']} months: "
                         f"{items}.")
    return notes or ["none"]


def _register(ctx: Ctx, tid: str) -> Any:
    """A threshold constant of the TBox register (``thresholds`` of the population JSON or thresholds.yaml)."""
    v = (ctx.pop.get("modules_meta", {}).get("thresholds") or {}).get(tid)
    if v is not None:
        return v
    from ontology.modules.build_ontology import load_thresholds
    return load_thresholds()[tid]["value"]


# ---------------------------------------------------------------------------
# Condition D
# ---------------------------------------------------------------------------

def build_D(ctx: Ctx, K: int, m: int, drop_props: Sequence[str] = (), extra: int = 0) -> str:
    """Condition D: header, D1 measurements, D2 module table (same K as C4), D3 monthly rows (m months).

    ``extra`` appends that many further D2 rows (modules beyond the top K, alphabetical), the last
    length equalizer (deviation 1 of the WP5 deviations log).
    """
    pop, cfg, fmt = ctx.pop, ctx.cfg, ctx.fmt
    out = [shared_header(pop)]
    rows = ["### Repository measurements\n", "| Measurement | Value | Definition |", "|---|---|---|"]
    for r in cfg["phi"]:
        p = r["property"]
        if p in drop_props or p not in ctx.measures:
            continue
        rows.append(f"| {r['display']} | {fmt(p, ctx.measures[p])} | {r['definition']} |")
    out.append("\n".join(rows) + "\n")
    cols = cfg["module_columns"]
    shown = sorted(shown_modules(ctx, K))
    rows = ["### Module measurements\n", "| Module | " + " | ".join(c["header"] for c in cols) + " |",
            "|---|" + "---|" * len(cols)]
    for path in shown:
        meas = ctx.modules[path]["measures"]
        cells = [fmt(c["property"], meas[c["property"]]) if c["property"] in meas else "-" for c in cols]
        rows.append(f"| {path} | " + " | ".join(cells) + " |")
    rest = sorted(set(ctx.modules) - set(shown))
    for path in rest[:extra]:
        meas = ctx.modules[path]["measures"]
        cells = [fmt(c["property"], meas[c["property"]]) if c["property"] in meas else "-" for c in cols]
        rows.append(f"| {path} | " + " | ".join(cells) + " |")
    rows.append(f"\nOther modules: {len(rest) - min(extra, len(rest))} not listed.")
    out.append("\n".join(rows) + "\n")
    if m > 0:
        series = list(reversed(pop["series_months"]))[:m]
        mc = cfg["monthly_columns"]
        rows = ["### Monthly activity\n", "| Month | " + " | ".join(c["header"] for c in mc) + " |",
                "|---|" + "---|" * len(mc)]
        for s in series:
            rows.append(f"| {s['month']} | " + " | ".join(
                "-" if s.get(c["key"]) is None else str(s[c["key"]]) for c in mc) + " |")
        out.append("\n".join(rows) + "\n")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Condition B
# ---------------------------------------------------------------------------

def _match(path: str, pattern: str) -> bool:
    return path.count("/") == pattern.count("/") and fnmatch.fnmatchcase(path, pattern)


def b_sources(tree: Mapping[str, tuple[str, str]]) -> list[str]:
    """Guidance files of a tree (``path -> (mode, blob)``), in plan 3.7 order; symlinks skipped."""
    out: list[str] = []
    for pat in B_PATTERNS:
        for p in sorted(tree):
            if tree[p][0] != "120000" and _match(p, pat) and p not in out:
                out.append(p)
    return out


def build_B_text(files: Sequence[tuple[str, str]], cap: int) -> Optional[str]:
    """B from ``(path, text)`` pairs already in order; None when there is no non-empty file.

    The result is cut at ``cap`` characters at a line boundary (the marker included).
    """
    parts = [f"### {p}\n\n{t.strip(chr(10))}\n" for p, t in files if t.strip()]
    if not parts:
        return None
    text = f"{HEADING}\n\n{B_INTRO}\n\n" + "\n".join(parts)
    if len(text) <= cap:
        return text
    room = cap - len("\n" + TRUNCATED)
    cut = text[:room]
    cut = cut[:cut.rfind("\n")] if "\n" in cut else cut
    return cut + "\n" + TRUNCATED


def build_B(git_dir: Path, base_commit: str, cap: int) -> Optional[str]:
    """Contributor guidance at the base commit (plan 3.7), or None if unavailable."""
    r = subprocess.run(["git", "-C", str(git_dir), "-c", "core.quotepath=false", "ls-tree", "-r", "-z", base_commit],
                       capture_output=True, check=True)
    tree: dict[str, tuple[str, str]] = {}
    for rec in r.stdout.decode("utf-8", "replace").split("\0"):
        meta, _, path = rec.partition("\t")
        f = meta.split()
        if len(f) == 3 and f[1] == "blob":
            tree[path] = (f[0], f[2])
    files = []
    for p in b_sources(tree):
        blob = subprocess.run(["git", "-C", str(git_dir), "cat-file", "blob", tree[p][1]], capture_output=True,
                              check=True).stdout.decode("utf-8", "replace")
        files.append((p, blob))
    return build_B_text(files, cap)


# ---------------------------------------------------------------------------
# Lints, containment, equalization
# ---------------------------------------------------------------------------

def d_lint(text: str, cfg: Mapping[str, Any], identifiers: Sequence[str]) -> list[str]:
    """Forbidden substrings found in D (repository and module names masked)."""
    low = _mask(text, identifiers).lower()
    return [w for w in cfg["d_lint_words"] if w in low]


def c_lint(text: str, cfg: Mapping[str, Any], identifiers: Sequence[str]) -> list[str]:
    """Forbidden imperative and verdict words found in C (names masked; whole-word match)."""
    low = _mask(text, identifiers).lower()
    return [w for w in cfg["c_lint_words"] if re.search(rf"(?<![a-z]){re.escape(w)}", low)]


def containment(ctx: Ctx, fills: Fills, d_text: str, shown: Sequence[str]) -> list[str]:
    """Numbers of C1-C4 (formatted facts) that are not in D1 or D2; empty when contained."""
    miss: list[str] = []
    d1 = d_text.split("### Module measurements")[0]
    d2 = "### Module measurements" + d_text.split("### Module measurements")[1].split("### Monthly activity")[0]
    rows: dict[str, list[str]] = {}
    for ln in d2.splitlines():
        if ln.startswith("| ") and not ln.startswith("| Module"):
            cells = [c.strip() for c in ln.strip("|").split("|")]
            rows[cells[0]] = cells[1:]
    cols = [c["property"] for c in ctx.cfg["module_columns"]]
    shown_set = set(shown)
    for tok in fills.tokens:
        if tok[0] == "repo":
            _, prop, s = tok
            ok = any(ln.startswith("| ") and f"| {s} |" in ln and
                     ln.split("|")[1].strip() == next((r["display"] for r in ctx.cfg["phi"]
                                                       if r["property"] == prop), None)
                     for ln in d1.splitlines())
            if not ok:
                miss.append(f"{prop}={s}")
        else:
            _, path, prop, s = tok
            if path not in shown_set or prop not in cols or rows.get(path, [None] * 9)[cols.index(prop)] != s:
                miss.append(f"{path}:{prop}={s}")
    return miss


@dataclass
class Generated:
    """Result of ``generate_task``."""

    task_id: str
    C: Optional[str] = None
    D: Optional[str] = None
    B: Optional[str] = None
    meta: dict[str, Any] = field(default_factory=dict)


def generate_task(pop: Mapping[str, Any], cfg: Mapping[str, Any], tpl: Mapping[str, Mapping[str, Any]], *,
                  qualifier: bool = True, b_text: Optional[str] = None) -> Generated:
    """C and D of one task from its population JSON (and the given B text): lengths equalized, lints run.

    Args:
        pop: Per-task population JSON of ``populate_v2.py --snapshot-commit``.
        cfg: ``load_config`` result.
        tpl: ``load_templates`` result.
        qualifier: Include the C1 qualifier sentence (plan 3.8).
        b_text: Condition B text or None when unavailable.

    Returns:
        ``Generated`` with texts and a ``meta`` dict (K, m, lengths, lints, flags).
    """
    task = pop.get("task_id") or pop["repo"]
    g = Generated(task_id=task, B=b_text)
    lim = cfg["length"]
    g.meta = {"task_id": task, "repo": pop["repo"], "base_commit": pop.get("base_commit"),
              "b_available": b_text is not None, "b_chars": len(b_text) if b_text else None}
    if pop.get("status") != "ok" or "modules_meta" not in pop:
        g.meta.update(ok=False, problems=["population_unavailable"], status=pop.get("status"),
                      unmineable_reason=pop.get("unmineable_reason"))
        return g
    ctx = Ctx(pop, cfg, tpl, Formatter(cfg), qualifier)
    ids = [pop["repo"], pop["repo"].split("/")[0], pop["repo"].split("/")[-1], *ctx.modules]
    K = lim["k_start"]
    while True:
        c_text, fills = build_C(ctx, K)
        if len(c_text) <= lim["cap"] or K <= lim["k_min"]:
            break
        K -= lim["k_step"]
    lc = len(c_text)
    n_months = len(pop["series_months"])
    m, dropped, extra = 0, [], 0
    d_text = build_D(ctx, K, m)
    while len(d_text) < lim["lower"] * lc and m < n_months:
        m += 1
        d_text = build_D(ctx, K, m)
    n_rest = len(ctx.modules) - min(K, len(ctx.modules))
    while len(d_text) < lim["lower"] * lc and extra < n_rest:  # all months used: more D2 rows
        extra += 1
        d_text = build_D(ctx, K, m, extra=extra)
    if m == 0 and len(d_text) > lim["upper"] * lc:
        for r in reversed(cfg["phi"]):
            if len(d_text) <= lim["upper"] * lc:
                break
            if r["property"] in ctx.measures and r["property"] not in fills.cited_props:
                dropped.append(r["property"])
                d_text = build_D(ctx, K, m, dropped)
    ld = len(d_text)
    shown = shown_modules(ctx, K)
    miss = containment(ctx, fills, d_text, shown)
    forbidden_text = [t for t in (pop.get("settings", {}).get("test_patch_files") or []) if t in c_text or t in d_text]
    problems = []
    dl, cl = d_lint(d_text, cfg, ids), c_lint(c_text, cfg, ids)
    if dl:
        problems.append(f"d_lint:{dl}")
    if cl:
        problems.append(f"c_lint:{cl}")
    if miss:
        problems.append(f"containment:{miss[:5]}")
    if forbidden_text:
        problems.append(f"patch_paths_in_text:{forbidden_text[:3]}")
    if "Development Status" in c_text or "Development Status" in d_text:
        problems.append("declared_status_in_text")
    cap_viol = [x for x, t in (("C", c_text), ("D", d_text), ("B", b_text or "")) if len(t) > lim["cap"]]
    if cap_viol:
        problems.append(f"cap_exceeded:{cap_viol}")
    if shared_header(pop) != c_text[:len(shared_header(pop))] or d_text[:len(shared_header(pop))] != shared_header(pop):
        problems.append("headers_differ")
    g.C, g.D = c_text, d_text
    g.meta.update(
        K=K, m=m, d2_extra_rows=extra, n_modules=len(ctx.modules), n_modules_shown=len(shown), n_months=n_months,
        chars={"C": lc, "D": ld, "B": g.meta["b_chars"]}, d1_rows_dropped=dropped,
        length_ratio_c_over_d=round(lc / ld, 4),
        length_violation=abs(lc - ld) > lim["tolerance"] * lc, lint_d=dl, lint_c=cl, containment_missing=miss,
        explanation_fallbacks=len(fills.fallbacks), explanation_fallback=len(fills.fallbacks),
        L_C=lc, L_D=ld, L_B=g.meta["b_chars"],  # keys read by run_wp5_analysis.py
        explanation_fallback_items=sorted(fills.fallbacks),
        placeholders_from_abox=fills.from_abox, qualifier_included=qualifier, problems=problems,
        ok=not problems, inconsistent=bool(pop["inferred"][pop["primary_config"]].get("inconsistent")),
        labels={"stage": _stage_classes(pop), "modules": {k: sum(1 for v in ctx.modules.values() if v["label"] == k)
                                                          for k in GROUP_ORDER}})
    return g


def sha256(text: str) -> str:
    """SHA-256 of a manifest (UTF-8)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def tbox_hash(tbox_dir: Path) -> str:
    """Hash of the seo-inference and seo-metrics module files the templates come from."""
    h = hashlib.sha256()
    for n in ("seo-metrics", "seo-inference"):
        h.update((tbox_dir / f"{n}.owl").read_bytes())
    return h.hexdigest()


def run(population_dir: Path, out_dir: Path, *, repo_cache: Optional[Path], task_ids: Optional[Sequence[str]],
        rq1_verdict: str, config_path: Path, tbox_dir: Path, write_b: bool = True) -> dict[str, Any]:
    """Generate B, C and D for every task JSON of a directory; check determinism; write files and index."""
    cfg = load_config(config_path)
    tpl = load_templates(tbox_dir)
    qualifier = rq1_verdict != "GO"
    if rq1_verdict == "UNRESOLVED":
        logger.warning("RQ1 verdict not recorded: the C1 qualifier sentence is included (plan 3.8)")
    files = sorted(population_dir.glob("*.json"))
    index: dict[str, Any] = {
        "generator": "manifests/generator/wp5_manifests.py",
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "config_sha256": cfg["_sha256"], "tbox_sha256": tbox_hash(tbox_dir),
        "rq1_verdict": rq1_verdict, "c1_qualifier_included": qualifier, "tasks": {}}
    for f in files:
        pop = json.loads(f.read_text())
        task = pop.get("task_id") or f.stem
        if task_ids and task not in task_ids:
            continue
        b_text = None
        if write_b and repo_cache is not None and pop.get("base_commit"):
            gd = repo_cache / f"{pop['repo'].replace('/', '__')}.git"
            b_text = build_B(gd, pop["base_commit"], cfg["length"]["cap"]) if gd.exists() else None
            if not gd.exists():
                logger.warning("no clone for %s: B not generated", task)
        g1 = generate_task(pop, cfg, tpl, qualifier=qualifier, b_text=b_text)
        g2 = generate_task(pop, cfg, tpl, qualifier=qualifier, b_text=b_text)
        deterministic = (g1.B, g1.C, g1.D, g1.meta) == (g2.B, g2.C, g2.D, g2.meta)
        g1.meta["deterministic"] = deterministic
        if not deterministic:
            g1.meta["ok"] = False
            g1.meta.setdefault("problems", []).append("not_deterministic")
        tdir = out_dir / "manifests" / re.sub(r"[^A-Za-z0-9_.-]", "_", task)
        tdir.mkdir(parents=True, exist_ok=True)
        files_meta = {}
        for cond, text in (("B", g1.B), ("C", g1.C), ("D", g1.D)):
            if text is None:
                (tdir / f"{cond}.md").unlink(missing_ok=True)
                continue
            (tdir / f"{cond}.md").write_text(text, encoding="utf-8")
            files_meta[cond] = {"sha256": sha256(text), "chars": len(text)}
        g1.meta["files"] = files_meta
        index["tasks"][task] = g1.meta
        logger.info("%s: K=%s m=%s chars=%s ok=%s %s", task, g1.meta.get("K"), g1.meta.get("m"),
                    g1.meta.get("chars"), g1.meta["ok"], g1.meta.get("problems") or "")
    index["all_ok"] = all(t["ok"] for t in index["tasks"].values())
    index["counts"] = {"tasks": len(index["tasks"]),
                       "length_violation": sum(1 for t in index["tasks"].values() if t.get("length_violation")),
                       "with_explanation_fallback": sum(1 for t in index["tasks"].values()
                                                        if t.get("explanation_fallbacks")),
                       "b_available": sum(1 for t in index["tasks"].values() if t["b_available"])}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "wp5_manifests_index.json").write_text(json.dumps(index, indent=1, sort_keys=True), encoding="utf-8")
    return index


def main() -> int:
    ap = argparse.ArgumentParser(description="WP5 B, C and D manifests (Paper 1)")
    ap.add_argument("--population-dir", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--repo-cache", type=Path, default=DEFAULT_REPO_CACHE)
    ap.add_argument("--task-ids", nargs="*", default=None)
    ap.add_argument("--rq1-verdict", choices=("GO", "NOGO", "UNRESOLVED"), default="UNRESOLVED",
                    help="recorded RQ1 verdict; the C1 qualifier is included unless GO (plan 3.8)")
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--tbox-dir", type=Path, default=DEFAULT_TBOX)
    ap.add_argument("--skip-b", action="store_true")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    idx = run(a.population_dir, a.out_dir, repo_cache=None if a.skip_b else a.repo_cache,
              task_ids=a.task_ids, rq1_verdict=a.rq1_verdict, config_path=a.config, tbox_dir=a.tbox_dir,
              write_b=not a.skip_b)
    logger.info("index: %s", idx["counts"])
    return 0 if idx["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
