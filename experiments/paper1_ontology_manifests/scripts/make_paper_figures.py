"""Statistical figures for the Paper 1 results section (JSEP rebuild).

Used by: Paper 1 (JSEP rebuild), Section 4 results (RQ1, RQ2, RQ3/RQ4). Reads ONLY
committed result files under
``experiments/paper1_ontology_manifests/results/real_v2/`` and writes vector PDFs to
``papers/paper1/jsep/figures/``. No experiment or analysis pipeline is run and no
result file is written.

Integrity checks (the script exits non-zero if any fails):

1. Every source result file must have the sha256 recorded in
   ``papers/paper1/results-digest.json``, so the figures use the same data as the digest.
2. Every plotted value that the digest traces (``file::json.path``) must equal the
   digest value.
3. Every plotted value that the paper prints must match the paper text: the exact-number
   tables in the supplement (``supp/*.tex``, located by ``\\label``) and key prose
   sentences in the main text (``sections/*.tex``) are searched for the rounded value.

The only computed quantities are the task-level bootstrap intervals for resolve rates
(Figure ``wp5_resolve`` by condition and model; Figure ``wp6_harm`` by condition) and
the Wilson intervals in ``wp6_harm``, which no result file holds. Bootstrap intervals are
percentile intervals over 10,000 resamples of tasks, seeded with the WP5 seed read from
``wp5_primary.json`` (``wp6_harm``: the WP6 seed from ``wp6/runs/run_meta.json``, checked
against ``configs/wp6.yaml``). ``rq2b_persistence`` and ``wp6_harm`` have no paper-text
checks yet (the text is not written). Pre-registered cut-offs come from the analysis configs
(``configs/rq1_analysis.yaml``) and the MDE from ``wp5_power.json``.

Usage:
    .venv/bin/python experiments/paper1_ontology_manifests/scripts/make_paper_figures.py --skip-prose
    .venv/bin/python experiments/paper1_ontology_manifests/scripts/make_paper_figures.py \\
        --png-dir /tmp/previews   # also write PNG previews for visual inspection
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import logging
import math
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import yaml  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

LOG = logging.getLogger("paper_figures")

PROJECT_ROOT = Path(__file__).resolve().parents[3]
EXP = PROJECT_ROOT / "experiments" / "paper1_ontology_manifests"
RES_REL = "experiments/paper1_ontology_manifests/results/real_v2"
RES = PROJECT_ROOT / RES_REL
PAPER = PROJECT_ROOT / "papers" / "paper1"
JSEP = PAPER / "jsep"
OUT_DIR = JSEP / "figures"

# Okabe-Ito palette (colour-blind safe); every series also has a marker or hatch.
OI = {
    "orange": "#E69F00", "sky": "#56B4E9", "green": "#009E73", "yellow": "#F0E442",
    "blue": "#0072B2", "vermillion": "#D55E00", "purple": "#CC79A7", "black": "#000000",
    "grey": "#999999",
}
INK = "#222222"
MUTED = "#666666"
FULL_W = 5.4   # \textwidth of elsarticle preprint 12pt is 390 pt = 5.4 in
HALF_W = 3.5


class CheckError(RuntimeError):
    """Raised when a plotted value does not tie to the digest or the paper."""


# --------------------------------------------------------------------------- data access
class Results:
    """Loads committed result files and checks each read value against the digest."""

    def __init__(self) -> None:
        digest = json.loads((PAPER / "results-digest.json").read_text())
        self.sha = digest["files_sha256"]
        self.trace: dict[str, Any] = {e["source"]: e["value"] for e in digest["values"]}
        self._cache: dict[str, Any] = {}
        self.n_digest_checks = 0
        self.n_reads = 0

    def _load(self, rel: str) -> Any:
        if rel in self._cache:
            return self._cache[rel]
        path = RES / rel
        full = f"{RES_REL}/{rel}"
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if full in self.sha and self.sha[full] != actual:
            raise CheckError(f"{full} changed since the digest was generated")
        if full not in self.sha:
            LOG.warning("%s has no hash in the digest; values read unchecked by hash", full)
        if rel.endswith(".jsonl"):
            data = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        else:
            data = json.loads(path.read_text())
        self._cache[rel] = data
        return data

    @staticmethod
    def source(rel: str, keys: Sequence[str | int]) -> str:
        parts: list[str] = []
        for k in keys:
            if isinstance(k, int):
                parts.append(f"[{k}]")
            elif re.fullmatch(r"[A-Za-z0-9_\-]+", k):
                parts.append(("." if parts else "") + k)
            else:
                parts.append(f'["{k}"]')
        return f"{RES_REL}/{rel}::" + "".join(parts)

    def get(self, rel: str, *keys: str | int) -> Any:
        node = self._load(rel)
        for k in keys:
            node = node[k]
        self.n_reads += 1
        src = self.source(rel, keys)
        if src in self.trace and isinstance(node, (int, float)) and not isinstance(node, bool):
            ref = self.trace[src]
            if not math.isclose(float(node), float(ref), rel_tol=1e-9, abs_tol=1e-12):
                raise CheckError(f"{src}: file {node} != digest {ref}")
            self.n_digest_checks += 1
        return node

    def derived(self, rel: str, tag: str, value: float) -> None:
        """Check a tally computed here against the digest's derived tally."""
        src = f'{RES_REL}/{rel}::["{tag}"]'
        if src not in self.trace:
            raise CheckError(f"no digest tally {src}")
        if not math.isclose(float(value), float(self.trace[src]), rel_tol=1e-9, abs_tol=1e-12):
            raise CheckError(f"{src}: computed {value} != digest {self.trace[src]}")
        self.n_digest_checks += 1

    def ledger(self, rel: str) -> list[dict[str, Any]]:
        return self._load(rel)


# --------------------------------------------------------------------------- paper checks
class PaperText:
    """Asserts that rounded plotted values appear where the paper prints them."""

    def __init__(self, skip: bool = False) -> None:
        # PUBLIC COPY: skip=True turns every paper-text check into a no-op (the manuscript is not
        # distributed with the replication package). Numeric checks against the digest are unaffected.
        self.skip = skip
        self.files = {p.relative_to(JSEP).as_posix(): p.read_text()
                      for p in list((JSEP / "sections").glob("*.tex")) + list((JSEP / "supp").glob("*.tex"))} if not skip else {}
        self.n_checks = 0

    def table_rows(self, label: str) -> list[str]:
        for name, text in self.files.items():
            m = re.search(r"\\label\{" + re.escape(label) + r"\}", text)
            if not m:
                continue
            start = text.rfind(r"\begin{table", 0, m.start())
            end = text.find(r"\end{table}", m.end())
            body = text[start:end]
            return [re.sub(r"\s+", " ", r).strip() for r in body.split(r"\\")]
        raise CheckError(f"table {label} not found in sections/ or supp/")

    def row(self, label: str, row_key: str, *snippets: str) -> None:
        if self.skip:
            return
        rows = [r for r in self.table_rows(label) if re.sub(r"^.*\\midrule ", "", r).startswith(row_key)
                or r.startswith(row_key)]
        if not rows:
            raise CheckError(f"{label}: no row starting with {row_key!r}")
        for s in snippets:
            if not any(s in r for r in rows):
                raise CheckError(f"{label} row {row_key!r}: {s!r} not found in {rows[0]!r}")
            self.n_checks += 1

    def table_has(self, label: str, *snippets: str) -> None:
        if self.skip:
            return
        body = " ".join(self.table_rows(label))
        for s in snippets:
            if s not in body:
                raise CheckError(f"{label}: {s!r} not found")
            self.n_checks += 1

    def prose(self, fname: str, *snippets: str) -> None:
        if self.skip:
            return
        text = re.sub(r"\s+", " ", self.files[fname])
        for s in snippets:
            if s not in text:
                raise CheckError(f"{fname}: {s!r} not found in prose")
            self.n_checks += 1


def tnum(x: float, nd: int = 2) -> str:
    """Format as the paper's tables print numbers (minus sign in math mode)."""
    s = f"{x:.{nd}f}"
    if s.startswith("-"):
        if float(s) == 0:
            s = s[1:]
        else:
            return f"$-{s[1:]}$"
    return s


def tci(lo: float, hi: float, nd: int = 2) -> str:
    return f"[{tnum(lo, nd)}, {tnum(hi, nd)}]"


def pnum(p: float) -> str:
    return "1" if p >= 0.99995 else f"{p:.4f}"


# --------------------------------------------------------------------------- style
def set_style() -> None:
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["STIXGeneral", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 8,
        "axes.labelsize": 8,
        "axes.titlesize": 8.5,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "legend.fontsize": 7.5,
        "axes.linewidth": 0.6,
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.major.size": 3,
        "ytick.major.size": 3,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
        "pdf.fonttype": 42,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
        "hatch.linewidth": 0.6,
    })


def save(fig: plt.Figure, name: str, png_dir: Path | None) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_DIR / f"{name}.pdf")
    if png_dir is not None:
        png_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(png_dir / f"{name}.png", dpi=220)
    plt.close(fig)
    LOG.info("wrote %s", OUT_DIR / f"{name}.pdf")


def panel_tag(ax: plt.Axes, tag: str) -> None:
    ax.text(-0.02, 1.02, tag, transform=ax.transAxes, ha="right", va="bottom",
            fontsize=8.5, fontweight="bold", color=INK)


# --------------------------------------------------------------------------- RQ1
CLS = ["C1", "C2", "CF"]
CLS_STYLE = {"C1": (OI["orange"], "o"), "C2": (OI["blue"], "s"), "CF": (OI["green"], "^")}
CLS_NAME = {"C1": "C1 trend stages", "C2": "C2 rule set", "CF": "CF commit comparator"}


def fig_rq1_agreement(r: Results, t: PaperText, png: Path | None) -> None:
    cfg = yaml.safe_load((EXP / "configs" / "rq1_analysis.yaml").read_text())["verdict"]
    kappa_pass, lb_pass, recall_pass = cfg["kappa_pass"], cfg["lb_pass"], cfg["recall_pass"]
    n = r.get("rq1/rq1_primary.json", "n")
    k = {c: r.get("rq1/rq1_primary.json", "classifiers", c, "metrics", "kappa") for c in CLS}
    pw = {c: r.get("rq1/rq1_secondary.json", "population_weighted_exploratory", "metrics", c, "kappa") for c in CLS}
    verdict = {c: r.get("rq1/rq1_primary.json", "classifiers", c, "verdict", "verdict") for c in CLS}
    rec = {c: {cl: r.get("rq1/rq1_primary.json", "classifiers", c, "metrics", f"recall_{cl}") for cl in "ASP"}
           for c in CLS}

    # paper ties
    for c in CLS:
        kk = k[c]
        t.row("tab:rq1-metrics", r"$\kappa$ [95\% CI]", f"{tnum(kk['point'])} {tci(*kk['ci95'])}")
        t.row("tab:rq1-metrics", r"$\kappa$ 97.5\% CI", tci(*kk["ci975"]))
        for cl, nm in zip("ASP", ["ACTIVE", "SERVICING", r"PHASE\_OUT"]):
            rr = rec[c][cl]
            t.row("tab:rq1-metrics", f"Recall {nm}", f"{tnum(rr['point'])} {tci(*rr['ci95'])}")
    t.prose("supp/S2-rq1.tex", f"C2 drops to $\\kappa = {pw['C2']:.2f}$ against {pw['CF']:.2f} for CF")
    t.prose("sections/05-rq1.tex", f"($\\kappa = {k['C1']['point']:.2f}$, 97.5\\% CI {tci(*k['C1']['ci975'])})",
            f"($\\kappa = {k['C2']['point']:.2f}$, 97.5\\% CI {tci(*k['C2']['ci975'])})")
    t.row("tab:rq1-metrics", "Pre-registered decision", verdict["C1"], verdict["C2"])

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(FULL_W, 2.35), gridspec_kw={"width_ratios": [1.2, 1]})
    # (a) kappa forest with verdict zones on the 97.5% lower bound
    xmin, xmax = -0.2, 0.8
    zones = [(xmin, 0.0, "#E6E6E6", "FAIL"), (0.0, lb_pass, "#F3F3F3", "WEAK"), (lb_pass, xmax, "#FFFFFF", "")]
    for lo, hi, col, lab in zones:
        ax.axvspan(lo, hi, color=col, zorder=0, lw=0)
        if lab:
            ax.text((lo + hi) / 2, 3.62, lab, ha="center", va="center", fontsize=7, color=MUTED)
    ax.text(lb_pass + 0.02, 3.62, "PASS possible", ha="left", va="center", fontsize=7, color=MUTED,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.5}, zorder=2)
    ax.axvline(0, color=INK, lw=0.6, zorder=1)
    ax.axvline(kappa_pass, color=MUTED, lw=0.8, ls=(0, (4, 2)), zorder=1)
    ax.text(kappa_pass + 0.015, 2.5, rf"$\hat\kappa \geq$ {kappa_pass:.2f}", fontsize=6.5, color=MUTED, va="center")
    ys = {"C1": 3, "C2": 2, "CF": 1}
    for c in CLS:
        col, mk = CLS_STYLE[c]
        y = ys[c]
        lo975, hi975 = k[c]["ci975"]
        lo95, hi95 = k[c]["ci95"]
        ax.plot([lo975, hi975], [y, y], color=col, lw=1.0, zorder=3, solid_capstyle="butt")
        ax.plot([lo975, lo975], [y - 0.12, y + 0.12], color=col, lw=1.0, zorder=3)
        ax.plot([hi975, hi975], [y - 0.12, y + 0.12], color=col, lw=1.0, zorder=3)
        ax.plot([lo95, hi95], [y, y], color=col, lw=3.0, zorder=3, solid_capstyle="butt", alpha=0.55)
        ax.plot(k[c]["point"], y, marker=mk, color=col, ms=5.5, mec="white", mew=0.7, zorder=4, ls="none")
        ax.plot(pw[c], y - 0.3, marker="D", ms=3.8, mfc="white", mec=col, mew=0.9, zorder=4, ls="none")
        vtxt = {"FAIL": "FAIL", "WEAK": "WEAK"}.get(verdict[c], "comparator")
        ax.text(xmax + 0.02, y, vtxt, va="center", ha="left", fontsize=7, color=INK, clip_on=False)
    ax.set_yticks([3, 2, 1], [CLS_NAME[c] for c in ["C1", "C2", "CF"]])
    ax.set_ylim(0.35, 3.85)
    ax.set_xlim(xmin, xmax)
    ax.set_xlabel(r"Cohen's $\kappa$ vs. declared status")
    ax.tick_params(axis="y", length=0)
    handles = [
        plt.Line2D([], [], color=INK, lw=1.0, label="97.5% CI (decision)"),
        plt.Line2D([], [], color=INK, lw=3.0, alpha=0.55, label="95% CI"),
        plt.Line2D([], [], marker="D", ms=3.8, mfc="white", mec=INK, ls="none", label="population-weighted"),
    ]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.25), ncol=3,
              handlelength=1.6, columnspacing=1.0, fontsize=6.8)
    panel_tag(ax, "(a)")

    # (b) per-class recall with 95% CI
    classes = ["A", "S", "P"]
    support = {cl: r.get("rq1/rq1_primary.json", "classifiers", "C2", "per_class_check", "per_class", cl, "support")
               for cl in classes}
    cls_lab = [f"{nm}\n(n = {support[cl]})" for cl, nm in zip(classes, ["Active", "Servicing", "Phase-out"])]
    bx.axhline(recall_pass, color=MUTED, lw=0.8, ls=(0, (4, 2)), zorder=1)
    bx.text(2.48, recall_pass + 0.02, f"{recall_pass:.2f}", fontsize=6.5, color=MUTED, ha="right", va="bottom")
    for i, c in enumerate(CLS):
        col, mk = CLS_STYLE[c]
        off = (i - 1) * 0.22
        for j, cl in enumerate(classes):
            rr = rec[c][cl]
            bx.errorbar(j + off, rr["point"], yerr=[[rr["point"] - rr["ci95"][0]], [rr["ci95"][1] - rr["point"]]],
                        fmt=mk, color=col, ms=4.5, mec="white", mew=0.6, elinewidth=1.0, capsize=1.8,
                        capthick=0.8, zorder=3, label=c if j == 0 else None)
    bx.set_xticks(range(3), cls_lab)
    bx.set_xlim(-0.55, 2.55)
    bx.set_ylim(0, 1.02)
    bx.set_ylabel("Recall (95% CI)")
    bx.tick_params(axis="x", length=0, labelsize=7.5)
    bx.legend(loc="upper center", bbox_to_anchor=(0.5, -0.25), ncol=3, handletextpad=0.3, columnspacing=1.2)
    panel_tag(bx, "(b)")
    fig.tight_layout(w_pad=2.2)
    save(fig, "rq1_agreement", png)
    LOG.info("RQ1 agreement: n=%s, kappa C1/C2/CF = %.3f/%.3f/%.3f", n, *(k[c]["point"] for c in CLS))


def fig_rq1_confusion(r: Results, t: PaperText, png: Path | None) -> None:
    cm = r.get("rq1/rq1_primary.json", "classifiers", "C2", "confusion_strata_x_pred")
    rows, cols = cm["rows_true"], cm["cols_pred"]
    counts = np.array([[r.get("rq1/rq1_primary.json", "classifiers", "C2", "confusion_strata_x_pred", "counts", i, j)
                        for j in range(len(cols))] for i in range(len(rows))])
    row_name = {"initial_development": "Initial development", "evolution": "Evolution",
                "servicing": "Servicing", "phase_out": "Phase-out"}
    col_name = {"A": "ACTIVE", "S": "SERVICING", "P": "PHASE_OUT", "U": "Undet."}
    for i, rn in enumerate(rows):
        t.row("tab:rq1-confusion-all", row_name[rn], " & ".join(str(v) for v in counts[i]))
    expected = {"initial_development": "A", "evolution": "A", "servicing": "S", "phase_out": "P"}

    fig, ax = plt.subplots(figsize=(HALF_W, 2.05))
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("seqblue", ["#FFFFFF", "#9ECAE1", "#08519C"])
    vmax = counts.max()
    ax.imshow(counts, cmap=cmap, vmin=0, vmax=vmax, aspect="auto")
    for i in range(counts.shape[0]):
        for j in range(counts.shape[1]):
            v = counts[i, j]
            ax.text(j, i, str(v), ha="center", va="center", fontsize=8,
                    color="white" if v > 0.6 * vmax else INK)
        jj = cols.index(expected[rows[i]])
        ax.add_patch(Rectangle((jj - 0.47, i - 0.45), 0.94, 0.9, fill=False, ec=INK, lw=1.2, zorder=6))
    ax.set_xticks(range(len(cols)), [col_name[c] for c in cols])
    ax.set_yticks(range(len(rows)), [f"{row_name[x]} (n = {counts[i].sum()})" for i, x in enumerate(rows)])
    ax.set_xlabel("Label predicted by C2")
    ax.set_ylabel("Declared stratum")
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks(np.arange(-0.5, len(cols)), minor=True)
    ax.set_yticks(np.arange(-0.5, len(rows)), minor=True)
    ax.grid(which="minor", color="white", lw=1.5)
    ax.tick_params(which="minor", length=0)
    save(fig, "rq1_confusion_c2", png)


# --------------------------------------------------------------------------- RQ2
TYPES = ["T1", "T2", "T3", "T4", "T5", "T6"]
TYPE_NAME = {"T1": "T1 path", "T2": "T2 status", "T3": "T3 tool", "T4": "T4 dependency",
             "T5": "T5 command", "T6": "T6 version", "all_types": "All types"}
RESULTS = ["SupportedClaim", "ContradictedClaim", "UnverifiableClaim", "IndeterminateClaim", "ConflictedClaim"]
RES_STYLE = {
    "SupportedClaim": ("Supported", "#D9D9D9", ""),
    "ContradictedClaim": ("Contradicted", OI["vermillion"], ""),
    "UnverifiableClaim": ("Unverifiable", OI["sky"], "////"),
    "IndeterminateClaim": ("Indeterminate", OI["yellow"], "...."),
    "ConflictedClaim": ("Conflicted", OI["purple"], "xxxx"),
}


def fig_rq2_results(r: Results, t: PaperText, png: Path | None) -> None:
    rep = "wp2/report.json"
    dist = {ty: {v: r.get(rep, "verdict_distribution_by_type", ty, "verdicts").get(v, 0) for v in RESULTS}
            for ty in TYPES}
    ntype = {ty: r.get(rep, "verdict_distribution_by_type", ty, "n") for ty in TYPES}
    overall = {v: r.get(rep, "verdict_distribution_overall", v) for v in RESULTS}
    rate = {ty: {
        "pooled": r.get(rep, "contradiction_rate", ty, "pooled_rate"),
        "pooled_ci": [r.get(rep, "contradiction_rate", ty, "pooled_rate_ci95", i) for i in (0, 1)],
        "share": r.get(rep, "contradiction_rate", ty, "share_manifests_with_any_contradiction"),
        "share_ci": [r.get(rep, "contradiction_rate", ty, "share_ci95", i) for i in (0, 1)],
        "n_man": r.get(rep, "contradiction_rate", ty, "n_manifests_evaluable"),
    } for ty in TYPES + ["all_types"]}
    for ty in TYPES:
        if sum(dist[ty].values()) != ntype[ty]:
            raise CheckError(f"{ty}: check results do not sum to n")
        d = dist[ty]
        t.row("tab:rq2-verdicts", TYPE_NAME[ty], f"& {ntype[ty]} & {d['SupportedClaim']} & {d['ContradictedClaim']} & "
              f"{d['UnverifiableClaim']} & {d['IndeterminateClaim']}/{d['ConflictedClaim']} &")
        rr = rate[ty]
        if rr["pooled"] > 0:
            t.row("tab:rq2-verdicts", TYPE_NAME[ty],
                  f"{100 * rr['pooled']:.1f} [{100 * rr['pooled_ci'][0]:.1f}, {100 * rr['pooled_ci'][1]:.1f}]",
                  f"{100 * rr['share']:.1f} [{100 * rr['share_ci'][0]:.1f}, {100 * rr['share_ci'][1]:.1f}] ({rr['n_man']})")
    ra = rate["all_types"]
    t.row("tab:rq2-verdicts", "All types", f"{100 * ra['pooled']:.1f} [{100 * ra['pooled_ci'][0]:.1f}, "
          f"{100 * ra['pooled_ci'][1]:.1f}]", f"({ra['n_man']})")
    t.prose("sections/06-rq2.tex", f"Of the {sum(overall.values()):,} claims, {overall['SupportedClaim']:,} are supported, "
            f"{overall['ContradictedClaim']} contradicted",
            f"{100 * ra['share']:.1f}\\% [{100 * ra['share_ci'][0]:.1f}, {100 * ra['share_ci'][1]:.1f}]")

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(FULL_W, 2.45), sharey=True,
                                 gridspec_kw={"width_ratios": [1.15, 1]})
    order = TYPES + ["all_types"]
    ys = {ty: len(order) - 1 - i + (0 if ty != "all_types" else -0.3) for i, ty in enumerate(order)}
    for ty in order:
        d = overall if ty == "all_types" else dist[ty]
        tot = sum(d.values())
        left = 0.0
        for v in RESULTS:
            w = 100 * d[v] / tot
            if w <= 0:
                continue
            lab, col, hatch = RES_STYLE[v]
            ax.barh(ys[ty], w, left=left, height=0.62, color=col, hatch=hatch, edgecolor="white", lw=0.5, zorder=2)
            left += w
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of claims (%)")
    ylabels = [f"{TYPE_NAME[ty]} (n = {ntype[ty] if ty != 'all_types' else sum(overall.values()):,})" for ty in order]
    ax.set_yticks([ys[ty] for ty in order], ylabels)
    ax.tick_params(axis="y", length=0)
    ax.axhline(ys["all_types"] + 0.65, color=MUTED, lw=0.5)
    handles = [Patch(facecolor=RES_STYLE[v][1], hatch=RES_STYLE[v][2], edgecolor="white", label=RES_STYLE[v][0])
               for v in RESULTS]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=3, handlelength=1.2,
              columnspacing=0.9, handletextpad=0.4, fontsize=6.8)
    panel_tag(ax, "(a)")

    for ty in order:
        rr = rate[ty]
        y = ys[ty]
        p, plo, phi = (100 * rr["pooled"], 100 * rr["pooled_ci"][0], 100 * rr["pooled_ci"][1])
        s, slo, shi = (100 * rr["share"], 100 * rr["share_ci"][0], 100 * rr["share_ci"][1])
        bx.errorbar(p, y + 0.14, xerr=[[p - plo], [phi - p]], fmt="o", color=OI["vermillion"], ms=4,
                    mec="white", mew=0.5, elinewidth=1.0, capsize=1.6, zorder=3)
        bx.errorbar(s, y - 0.14, xerr=[[s - slo], [shi - s]], fmt="s", color=OI["blue"], ms=3.8,
                    mec="white", mew=0.5, elinewidth=1.0, capsize=1.6, zorder=3)
        bx.text(101, y, f"{rr['n_man']}", va="center", ha="left", fontsize=6.8, color=MUTED, clip_on=False)
    bx.text(101, len(order) - 0.35, "manifests", va="bottom", ha="left", fontsize=6.5, color=MUTED, clip_on=False)
    bx.axhline(ys["all_types"] + 0.65, color=MUTED, lw=0.5)
    bx.set_xlim(-2, 100)
    bx.set_xticks(range(0, 101, 20))
    bx.set_xlabel("Contradicted (%, 95% CI)")
    bx.tick_params(axis="y", length=0)
    hb = [plt.Line2D([], [], marker="o", color=OI["vermillion"], ms=4, lw=1.0, label="of decidable claims"),
          plt.Line2D([], [], marker="s", color=OI["blue"], ms=3.8, lw=1.0, label="manifests with at least one")]
    bx.legend(handles=hb, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=1, fontsize=6.8)
    panel_tag(bx, "(b)")
    fig.tight_layout(w_pad=1.0)
    save(fig, "rq2_check_results", png)


KIND_NAME = {
    "PathNeverExisted": "Path never existed (T1)",
    "PathRemoved": "Path removed (T1)",
    "DependencyUndeclared": "Dependency undeclared (T4)",
    "ScriptUndefined": "Script undefined (T5)",
    "VersionContradicted": "Version contradicted (T6)",
    "ToolAbsentInEcosystem": "Tool absent from ecosystem (T3)",
    "ToolAbsentCompetitorPresent": "Competing tool present (T3)",
    "DependencyMajorTooOld": "Declared major version too old (T4)",
}


def fig_rq2_kinds(r: Results, t: PaperText, png: Path | None) -> None:
    rows = r.ledger("wp2/drift.json")["rows"]
    tally: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    for row in rows:
        if row["verdict_at_S"] != "ContradictedClaim":
            continue
        kind = "drifted" if row["drifted"] else ("born_wrong" if row["born_wrong"] else "unresolved")
        tally[row["leaf_at_S"]][kind] += 1
    # tie to the report's leaf counts and to the drift summary
    leaves_rep: dict[str, int] = {}
    for ty in TYPES:
        for leaf, nleaf in r.get("wp2/report.json", "verdict_distribution_by_type", ty, "leaves").items():
            leaves_rep[leaf] = nleaf
    for leaf, c in tally.items():
        if c["unresolved"]:
            raise CheckError(f"{leaf}: unresolved introduction commits")
        if sum(c.values()) != leaves_rep[leaf]:
            raise CheckError(f"{leaf}: drift rows {sum(c.values())} != report leaves {leaves_rep[leaf]}")
    drifted = sum(c["drifted"] for c in tally.values())
    born = sum(c["born_wrong"] for c in tally.values())
    if drifted != r.get("wp2/drift.json", "overall", "drifted") or born != r.get("wp2/drift.json", "overall", "born_wrong"):
        raise CheckError("drift totals do not match drift.json overall")
    for ty in ("T1", "T3", "T4", "T5", "T6"):
        bt = r.get("wp2/drift.json", "by_type", ty)
        leaves = [lf for lf in tally if lf in r.get("wp2/report.json", "verdict_distribution_by_type", ty, "leaves")]
        if sum(tally[lf]["drifted"] for lf in leaves) != bt["drifted"]:
            raise CheckError(f"{ty}: drifted mismatch")
    t.prose("sections/06-rq2.tex", f"Of the {drifted + born} contradicted claims, {born} (",
            f"and {drifted} (", f"(22 claims)" if tally["PathNeverExisted"].total() == 22 else "__fail__",
            f"({tally['PathRemoved'].total()})", f"({tally['ScriptUndefined'].total()})",
            f"({tally['DependencyUndeclared'].total()})", f"({tally['VersionContradicted'].total()})")
    t.table_has("tab:rq2-validation", f"& {drifted} / {born} (")

    kinds = sorted(tally, key=lambda lf: (-tally[lf].total(), KIND_NAME[lf]))
    fig, ax = plt.subplots(figsize=(HALF_W + 0.4, 2.15))
    y = np.arange(len(kinds))[::-1]
    bw = np.array([tally[k]["born_wrong"] for k in kinds])
    dr = np.array([tally[k]["drifted"] for k in kinds])
    ax.barh(y, bw, height=0.62, color=OI["vermillion"], edgecolor="white", lw=0.5, label="Born wrong", zorder=2)
    ax.barh(y, dr, left=bw, height=0.62, color=OI["sky"], hatch="////", edgecolor="white", lw=0.5,
            label="Drifted", zorder=2)
    for yi, b, d in zip(y, bw, dr):
        ax.text(b + d + 0.4, yi, f"{b + d}", va="center", ha="left", fontsize=7, color=INK)
    ax.set_yticks(y, [KIND_NAME[k] for k in kinds])
    ax.set_xlabel("Contradicted claims (count)")
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, max(bw + dr) * 1.12)
    ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(5))
    ax.legend(loc="lower right", handlelength=1.2)
    save(fig, "rq2_contradiction_kinds", png)


# --------------------------------------------------------------------------- RQ3/RQ4
MODELS = ["nvidia/nemotron-3-super-120b-a12b", "google/diffusiongemma-26b-a4b-it"]
MODEL_SHORT = {MODELS[0]: "nemotron", MODELS[1]: "diffusiongemma"}
MODEL_STYLE = {MODELS[0]: (OI["blue"], "s"), MODELS[1]: (OI["orange"], "^")}
STATES = ["Submitted", "LimitsExceeded", "RepeatedFormatError", "WallTimeExceeded"]
STATE_STYLE = {"Submitted": ("Submitted", "#D9D9D9", ""), "LimitsExceeded": ("Step limit", OI["blue"], ""),
               "RepeatedFormatError": ("Format error", OI["yellow"], "...."),
               "WallTimeExceeded": ("Wall time", OI["vermillion"], "xxxx")}


def task_bootstrap(per_task: dict[str, list[int]], n_boot: int, rng: np.random.Generator) -> tuple[float, float]:
    tasks = sorted(per_task)
    res = np.array([sum(per_task[k]) for k in tasks], dtype=float)
    runs = np.array([len(per_task[k]) for k in tasks], dtype=float)
    idx = rng.integers(0, len(tasks), size=(n_boot, len(tasks)))
    rates = res[idx].sum(axis=1) / runs[idx].sum(axis=1)
    lo, hi = np.percentile(rates, [2.5, 97.5])
    return float(lo), float(hi)


def fig_wp5_resolve(r: Results, t: PaperText, png: Path | None) -> None:
    runs = r.ledger("wp5/wp5_runs.jsonl")
    outs = {o["run_id"]: o for o in r.ledger("wp5/wp5_outcomes.jsonl")}
    seed = r.get("wp5/wp5_primary.json", "seed")
    rng = np.random.default_rng(seed)
    n_boot = 10_000
    conds = ["A", "C", "D", "B"]
    stats: dict[tuple[str, str | None], dict[str, Any]] = {}
    for c in conds:
        for m in [None] + MODELS:
            sel = [x for x in runs if x["condition"] == c and (m is None or x["model"] == m)]
            per_task: dict[str, list[int]] = collections.defaultdict(list)
            for x in sel:
                per_task[x["instance_id"]].append(int(outs[x["run_id"]]["resolved"]))
            nres = sum(sum(v) for v in per_task.values())
            tag = f"condition={c}" + (f",model={m}" if m else "")
            r.derived("wp5/wp5_outcomes.jsonl", f"sum(resolved where {tag})", nres)
            r.derived("wp5/wp5_outcomes.jsonl", f"n(runs where {tag})", len(sel))
            lo, hi = task_bootstrap(per_task, n_boot, rng)
            stats[(c, m)] = {"res": nres, "n": len(sel), "rate": nres / len(sel), "ci": (lo, hi),
                             "tasks": len(per_task)}
    state_n = {c: {s: sum(1 for x in runs if x["condition"] == c and x["state"] == s) for s in STATES} for c in conds}
    for c in conds:
        for s in STATES:
            r.derived("wp5/wp5_runs.jsonl", f"count(condition={c},state={s})", state_n[c][s])
        a = stats[(c, None)]
        t.row("tab:wp5-resolve", c + (r"\textsuperscript" if c == "B" else " &"), f"& {a['n']} & {a['res']} ({a['rate']:.3f})",
              *(f"{stats[(c, m)]['res']}/{stats[(c, m)]['n']} ({stats[(c, m)]['rate']:.3f})" for m in MODELS),
              " & ".join(str(state_n[c][s]) for s in STATES))
    t.prose("sections/07-rq3-rq4.tex", f"({100 * stats[('D', None)]['rate']:.1f}\\%)", f"({100 * stats[('A', None)]['rate']:.1f}\\%)")
    LOG.info("resolve-rate bootstrap: %d task resamples, seed %s", n_boot, seed)

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(FULL_W, 2.4), gridspec_kw={"width_ratios": [1.35, 1]})
    xs = {c: i for i, c in enumerate(conds)}
    ax.axvspan(2.5, 3.5, color="#F0F0F0", lw=0, zorder=0)
    ax.text(3.0, 0.445, "exploratory\n(37 tasks)", ha="center", va="top", fontsize=6.5, color=MUTED)
    for c in conds:
        x0 = xs[c]
        a = stats[(c, None)]
        ax.errorbar(x0, a["rate"], yerr=[[a["rate"] - a["ci"][0]], [a["ci"][1] - a["rate"]]], fmt="o", color=INK,
                    ms=4.8, mec="white", mew=0.6, elinewidth=1.2, capsize=2, zorder=4,
                    label="both models" if c == "A" else None)
        for k, m in enumerate(MODELS):
            col, mk = MODEL_STYLE[m]
            s = stats[(c, m)]
            off = -0.27 if k == 0 else 0.27
            ax.errorbar(x0 + off, s["rate"], yerr=[[s["rate"] - s["ci"][0]], [s["ci"][1] - s["rate"]]], fmt=mk,
                        color=col, ms=4.2, mec="white", mew=0.5, elinewidth=1.0, capsize=1.6, zorder=3,
                        label=MODEL_SHORT[m] if c == "A" else None)
    labels = {"A": "A\nno manifest", "C": "C\nhistory-based", "D": "D\nflat facts", "B": "B\nhuman"}
    ax.set_xticks(range(len(conds)), [labels[c] for c in conds])
    ax.set_xlim(-0.55, 3.55)
    ax.set_ylim(0, 0.45)
    ax.set_ylabel("Resolve rate (95% CI)")
    ax.tick_params(axis="x", length=0)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.27), ncol=3, handletextpad=0.3, columnspacing=1.0)
    panel_tag(ax, "(a)")

    for c in conds:
        tot = sum(state_n[c].values())
        left = 0.0
        for s in STATES:
            w = 100 * state_n[c][s] / tot
            if w <= 0:
                continue
            lab, col, hatch = STATE_STYLE[s]
            bx.barh(len(conds) - 1 - xs[c], w, left=left, height=0.6, color=col, hatch=hatch, edgecolor="white",
                    lw=0.5, zorder=2)
            left += w
    bx.set_yticks([len(conds) - 1 - xs[c] for c in conds],
                  [f"{c} (n = {sum(state_n[c].values())})" for c in conds])
    bx.set_xlim(0, 100)
    bx.set_xlabel("Share of runs (%)")
    bx.tick_params(axis="y", length=0)
    handles = [Patch(facecolor=STATE_STYLE[s][1], hatch=STATE_STYLE[s][2], edgecolor="white", label=STATE_STYLE[s][0])
               for s in STATES]
    bx.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.45, -0.27), ncol=2, handlelength=1.2,
              columnspacing=0.9, handletextpad=0.4)
    panel_tag(bx, "(b)")
    fig.tight_layout(w_pad=1.5)
    save(fig, "wp5_resolve", png)


def fig_wp5_confirmatory(r: Results, t: PaperText, png: Path | None) -> None:
    pr = "wp5/wp5_primary.json"
    mde = r.get("wp5/wp5_power.json", "mde_or_c")
    raw = {h: r.get(pr, "holm", "raw_p", h) for h in ("H1", "H2", "H3")}
    holm = {h: r.get(pr, "holm", "holm_p", h) for h in ("H1", "H2", "H3")}
    test_res = {h: r.get(pr, "verdicts", h) for h in ("H1", "H2", "H3")}
    h1 = {"or": r.get(pr, "M1_M2", "H1", "ratio"), "ci": [r.get(pr, "M1_M2", "H1", "ratio_ci", i) for i in (0, 1)]}
    h2 = {"or": r.get(pr, "M1_M2", "H2", "ratio"), "ci": [r.get(pr, "M1_M2", "H2", "ratio_ci", i) for i in (0, 1)]}
    h3 = {k: r.get(pr, "M1_M2", "H3", k) for k in ("stat", "df_num", "df_denom")}
    stages = r.get(pr, "M1_M2", "H3", "levels")
    stage = {s: {"or": r.get(pr, "M1_M2", "stage_specific", s, "C-A", "ratio"),
                 "ci": [r.get(pr, "M1_M2", "stage_specific", s, "C-A", "ratio_ci", i) for i in (0, 1)],
                 "p": r.get(pr, "M1_M2", "stage_specific", s, "C-A", "p"),
                 "tasks": r.get(pr, "M1_M2", "stage_specific", s, "n_tasks")} for s in stages}
    da = {"or": r.get("wp5/wp5_exploratory.json", "D_vs_A", "ratio"),
          "ci": [r.get("wp5/wp5_exploratory.json", "D_vs_A", "ratio_ci", i) for i in (0, 1)],
          "p": r.get("wp5/wp5_exploratory.json", "D_vs_A", "p")}
    t.row("tab:wp5-confirmatory", "H1", f"OR {h1['or']:.2f} {tci(*h1['ci'])} & {pnum(raw['H1'])} & {pnum(holm['H1'])}",
          test_res["H1"])
    t.row("tab:wp5-confirmatory", "H2", f"OR {h2['or']:.2f} {tci(*h2['ci'])} & {pnum(raw['H2'])} & {pnum(holm['H2'])}",
          test_res["H2"])
    t.row("tab:wp5-confirmatory", "H3", f"$F({h3['df_num']}, {h3['df_denom']}) = {h3['stat']:.2f}$ & "
          f"{pnum(raw['H3'])} & {pnum(holm['H3'])}", test_res["H3"])
    t.prose("sections/07-rq3-rq4.tex", f"odds ratio is {h1['or']:.2f} (95\\% CI {h1['ci'][0]:.2f} to {h1['ci'][1]:.2f})",
            f"odds ratio {da['or']:.2f}, 95\\% CI {da['ci'][0]:.2f} to {da['ci'][1]:.2f}",
            f"Holm-adjusted p-value of {holm['H2']:.4f}")
    t.prose("supp/S4-rq3-rq4.tex", f"The raw p-value of the C versus D contrast is {raw['H2']:.4f}")
    t.prose("supp/S4-rq3-rq4.tex", f"at an odds ratio of {mde:.1f}")
    for s in stages:
        key = {"ACTIVE": "ACTIVE", "PO": r"PHASE\_OUT", "SERVICING": "SERVICING"}[s]
        t.row("tab:wp5-stage", key, f"({stage[s]['tasks']} tasks)",
              f"{stage[s]['or']:.2f} {tci(*stage[s]['ci'])}")

    stage_name = {"ACTIVE": "ACTIVE", "PO": "phase-out", "SERVICING": "SERVICING"}
    rows: list[dict[str, Any]] = [
        {"lab": "H1  C vs A", "or": h1["or"], "ci": h1["ci"], "p": raw["H1"], "ph": holm["H1"], "kind": "conf"},
        {"lab": "H2  C vs D", "or": h2["or"], "ci": h2["ci"], "p": raw["H2"], "ph": holm["H2"], "kind": "conf"},
        {"lab": f"H3  C vs A $\\times$ stage, $F({h3['df_num']},{h3['df_denom']}) = {h3['stat']:.2f}$", "or": None,
         "p": raw["H3"], "ph": holm["H3"], "kind": "head"},
    ]
    for s in stages:
        rows.append({"lab": f"      C vs A, {stage_name[s]} ({stage[s]['tasks']} tasks)", "or": stage[s]["or"],
                     "ci": stage[s]["ci"], "p": stage[s]["p"], "ph": None, "kind": "stage"})
    rows.append({"lab": "Expl.  D vs A", "or": da["or"], "ci": da["ci"], "p": da["p"], "ph": None, "kind": "expl"})

    fig = plt.figure(figsize=(FULL_W, 2.35))
    ax = fig.add_axes([0.385, 0.22, 0.40, 0.68])
    n = len(rows)
    ys = list(range(n))[::-1]
    xlo, xhi = 0.4, 4.0
    ax.set_xscale("log")
    ax.set_xlim(xlo, xhi)
    ax.set_ylim(-0.6, n - 0.4)
    tr = matplotlib.transforms.blended_transform_factory(fig.transFigure, ax.transData)
    ax.axvline(1.0, color=INK, lw=0.7, zorder=1)
    ax.axvline(mde, color=MUTED, lw=0.8, ls=(0, (4, 2)), zorder=1)
    ax.text(mde, n - 0.45, f"MDE {mde:.1f}", ha="center", va="bottom", fontsize=6.5, color=MUTED)
    style = {"conf": (OI["blue"], "s", 5), "stage": (OI["green"], "o", 4), "expl": (OI["grey"], "D", 3.8)}
    for row, y in zip(rows, ys):
        fig.text(0.01, y, row["lab"], transform=tr, ha="left", va="center", fontsize=7.3,
                 color=INK if row["kind"] != "expl" else MUTED)
        if row["or"] is not None:
            col, mk, ms = style[row["kind"]]
            ax.plot(row["ci"], [y, y], color=col, lw=1.1, zorder=3)
            for xe in row["ci"]:
                ax.plot([xe, xe], [y - 0.13, y + 0.13], color=col, lw=0.9, zorder=3)
            ax.plot(row["or"], y, marker=mk, color=col, ms=ms, mec="white", mew=0.6, zorder=4, ls="none")
            txt = f"{row['or']:.2f} [{row['ci'][0]:.2f}, {row['ci'][1]:.2f}]"
            fig.text(0.795, y, txt, transform=tr, ha="left", va="center", fontsize=7, color=INK)
        htxt = pnum(row["ph"]) if row["ph"] is not None else "n/a"
        fig.text(0.925, y, pnum(row["p"]), transform=tr, ha="left", va="center", fontsize=7, color=INK)
        fig.text(0.99, y, htxt, transform=tr, ha="left", va="center", fontsize=7, color=INK)
    for x, h in ((0.01, "Contrast"), (0.795, "OR [95% CI]"), (0.925, "raw $p$"), (0.99, "Holm $p$")):
        fig.text(x, n - 0.1, h, transform=tr, ha="left", va="bottom", fontsize=7, color=INK, fontweight="bold")
    ax.set_xticks([0.5, 1, 2, 3], ["0.5", "1", "2", "3"])
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("Marginal odds ratio (log scale, 95% CI)", labelpad=11)
    ax.text(1.0, -0.15, "favours C $\\rightarrow$", transform=ax.transAxes, ha="right", va="top", fontsize=6.5,
            color=MUTED)
    ax.text(0.0, -0.15, "$\\leftarrow$ favours comparison", transform=ax.transAxes, ha="left", va="top",
            fontsize=6.5, color=MUTED)
    save(fig, "wp5_confirmatory", png)


# --------------------------------------------------------------------------- RQ2b
def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    p = k / n
    den = 1 + z * z / n
    cen = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return cen - half, cen + half


def fig_rq2b_persistence(r: Results, t: PaperText, png: Path | None) -> None:
    rep = "wp2b/report.json"
    out = {"ContradictedClaim": {o: r.get(rep, "population", "outcomes_contradicted", o) for o in ("U", "G", "R", "P-C", "P-S", "P-O")},
           "SupportedClaim": {o: r.get(rep, "population", "outcomes_supported", o) for o in ("U", "G", "R", "P-C", "P-S", "P-O")}}
    for v, d in out.items():
        for o, n in d.items():
            r.derived("wp2b/claims.jsonl", f"count(verdict_S={v},outcome={o})", n)
        if d["U"] or d["P-O"]:
            raise CheckError(f"{v}: unexpected U/P-O outcomes {d}")
    if sum(out["ContradictedClaim"].values()) != r.get(rep, "population", "n_contradicted") or \
            sum(out["SupportedClaim"].values()) != r.get(rep, "population", "n_supported"):
        raise CheckError("WP2b outcome counts do not sum to the population")
    # categories (codes from wp2b-persistence-design.md section 3)
    same = {"ContradictedClaim": "P-C", "SupportedClaim": "P-S"}
    flip = {"ContradictedClaim": "P-S", "SupportedClaim": "P-C"}
    cats = [("same", "Kept, same check result", OI["vermillion"], ""),
            ("flip", "Kept, check result changed", OI["sky"], "////"),
            ("R", "Claim removed", OI["orange"], ""),
            ("G", "Manifest deleted", "#BBBBBB", "....")]

    def count(v: str, c: str) -> int:
        d = out[v]
        return d[same[v]] if c == "same" else d[flip[v]] if c == "flip" else d[c]

    groups = [("ContradictedClaim", "Contradicted at snapshot"), ("SupportedClaim", "Supported at snapshot")]
    fig, ax = plt.subplots(figsize=(FULL_W, 1.95))
    for gi, (v, name) in enumerate(groups):
        y = len(groups) - 1 - gi
        tot = sum(out[v].values())
        left = 0.0
        for ci, (c, lab, col, hatch) in enumerate(cats):
            n = count(v, c)
            if n == 0:
                continue
            w = 100 * n / tot
            ax.barh(y, w, left=left, height=0.52, color=col, hatch=hatch, edgecolor="white", lw=0.5, zorder=2)
            if w >= 8:
                ax.text(left + w / 2, y, f"{n}", ha="center", va="center", fontsize=7.5, color="white" if col == OI["vermillion"] else INK)
            else:
                # narrow segment: count above the bar with a short leader line, staggered to avoid overlap
                xc = left + w / 2
                ty = y + 0.26 + 0.2 * (ci % 2) + 0.1
                ax.plot([xc, xc], [y + 0.26, ty], color=MUTED, lw=0.5, zorder=1)
                ax.text(xc + (1.2 if ci == 3 else -0.2 if ci == 1 else 0.0), ty, f"{n}", ha="center", va="bottom", fontsize=7, color=INK)
            left += w
    ax.set_yticks([1, 0], [f"{n}\n(n = {sum(out[v].values()):,})" for v, n in groups])
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.45, 1.55)
    ax.set_xlabel("Share of claims at the latest commit (%)")
    ax.tick_params(axis="y", length=0)
    handles = [Patch(facecolor=c[2], hatch=c[3], edgecolor="white", label=c[1]) for c in cats]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.45, -0.3), ncol=2, handlelength=1.2,
              columnspacing=1.2, handletextpad=0.4)
    save(fig, "rq2b_persistence", png)


# --------------------------------------------------------------------------- WP6
def fig_wp6_harm(r: Results, t: PaperText, png: Path | None) -> None:
    runs = r.ledger("wp6/runs/wp6_runs.jsonl")
    outs = {o["run_id"]: o for o in r.ledger("wp6/runs/wp6_outcomes.jsonl")}
    seed = r.get("wp6/runs/run_meta.json", "sessions", 0, "seed")
    cfg_seed = yaml.safe_load((EXP / "configs" / "wp6.yaml").read_text())["seed"]
    if seed != cfg_seed:
        raise CheckError(f"run_meta seed {seed} != configs/wp6.yaml seed {cfg_seed}")
    rng = np.random.default_rng(seed)
    n_boot = 10_000
    conds = ["A", "T", "F_R", "F_I"]
    stats: dict[str, dict[str, Any]] = {}
    for c in conds:
        sel = [x for x in runs if x["condition"] == c]
        per_task: dict[str, list[int]] = collections.defaultdict(list)
        hits = 0
        for x in sel:
            o = outs[x["run_id"]]
            per_task[x["instance_id"]].append(int(o["resolved"]))
            hits += 1 if o["sets"]["F_I" if c == "F_I" else "F_R"]["Y1"] > 0 else 0
        nres = sum(sum(v) for v in per_task.values())
        tag = f"condition={c}"
        r.derived("wp6/runs/wp6_outcomes.jsonl", f"sum(resolved where {tag})", nres)
        r.derived("wp6/runs/wp6_outcomes.jsonl", f"n(runs where {tag})", len(sel))
        r.derived("wp6/runs/wp6_outcomes.jsonl", f"count(Y1>0 where {tag})", hits)
        lo, hi = task_bootstrap(per_task, n_boot, rng)
        stats[c] = {"n": len(sel), "hits": hits, "hit_ci": wilson(hits, len(sel)), "res": nres,
                    "rate": nres / len(sel), "ci": (lo, hi)}
    prim = "wp6/analysis/wp6_primary.json"
    hyp = {}
    for i in range(4):
        hid = r.get(prim, "hypotheses", i, "id")
        hyp[hid] = {"ratio": r.get(prim, "hypotheses", i, "ratio"),
                    "ci": [r.get(prim, "hypotheses", i, "ratio_ci", j) for j in (0, 1)],
                    "p_holm": r.get(prim, "hypotheses", i, "p_holm")}
    LOG.info("WP6 resolve bootstrap: %d task resamples, seed %s", n_boot, seed)

    names = {"A": "No\nmanifest", "T": "All-true\nmanifest", "F_R": "False\nnear\ntask (F$_R$)", "F_I": "False\nelsewhere\n(F$_I$)"}
    cols = {"A": "#BBBBBB", "T": OI["green"], "F_R": OI["vermillion"], "F_I": OI["orange"]}
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(FULL_W, 2.6), gridspec_kw={"width_ratios": [1.0, 1.1]})
    xs = np.arange(len(conds))
    for i, c in enumerate(conds):
        s = stats[c]
        p = s["hits"] / s["n"]
        ax.bar(i, p, width=0.6, color=cols[c], edgecolor="white", lw=0.5, zorder=2)
        ax.errorbar(i, p, yerr=[[p - s["hit_ci"][0]], [s["hit_ci"][1] - p]], fmt="none", ecolor=INK, elinewidth=1.1,
                    capsize=2, zorder=3)
        ax.text(i, s["hit_ci"][1] + 0.008, f"{s['hits']}/{s['n']}", ha="center", va="bottom", fontsize=7, color=INK)
    ax.set_xticks(xs, [names[c] for c in conds])
    ax.tick_params(axis="x", length=0)
    ax.set_ylim(0, 0.40)
    ax.set_ylabel("Runs with a false-lead\naction (95% CI)")
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))

    def rr(h: str) -> str:
        d = hyp[h]
        return f"{d['ratio']:.1f} [{d['ci'][0]:.1f}, {d['ci'][1]:.{0 if d['ci'][1] >= 100 else 1}f}], Holm $p$ = {pnum(d['p_holm'])}"
    ax.text(0.02, 0.985, f"H1 F$_R$ vs all-true: rate ratio {rr('H1')}\nH3 F$_R$ vs F$_I$: rate ratio {rr('H3')}",
            transform=ax.transAxes, ha="left", va="top", fontsize=6.5, color=INK, linespacing=1.5)
    panel_tag(ax, "(a)")

    for i, c in enumerate(conds):
        s = stats[c]
        bx.errorbar(i, s["rate"], yerr=[[s["rate"] - s["ci"][0]], [s["ci"][1] - s["rate"]]], fmt="o", color=cols[c] if c != "A" else MUTED,
                    ms=5, mec=INK, mew=0.6, elinewidth=1.2, capsize=2, zorder=3)
        bx.text(i, s["ci"][1] + 0.006, f"{s['res']}/{s['n']}", ha="center", va="bottom", fontsize=6.5, color=INK)
    bx.set_xticks(xs, [names[c] for c in conds])
    bx.set_xlim(-0.5, 3.5)
    bx.tick_params(axis="x", length=0)
    bx.set_ylim(0, 0.26)
    bx.set_ylabel("Resolve rate (95% CI)")
    panel_tag(bx, "(b)")
    for a in (ax, bx):
        for lab in a.get_xticklabels():
            lab.set_fontsize(7)
    fig.tight_layout(w_pad=1.5)
    save(fig, "wp6_harm", png)


# --------------------------------------------------------------------------- main
def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--png-dir", type=Path, default=None, help="also write PNG previews here")
    ap.add_argument("--skip-prose", action="store_true",
                    help="public copy: skip the checks against the manuscript text (not distributed); "
                         "digest and file-hash checks still run")
    ap.add_argument("--out-dir", type=Path, default=None,
                    help="public copy: where to write the PDFs (default: papers/paper1/jsep/figures if the "
                         "manuscript folder exists, else ./figures_out)")
    args = ap.parse_args(list(argv) if argv is not None else None)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("fontTools").setLevel(logging.WARNING)
    set_style()
    global OUT_DIR
    if args.out_dir is not None:
        OUT_DIR = args.out_dir
    elif not JSEP.exists():
        OUT_DIR = PROJECT_ROOT / "figures_out"
    if not JSEP.exists() and not args.skip_prose:
        LOG.error("manuscript sources not found under %s; rerun with --skip-prose", JSEP)
        return 2
    r, t = Results(), PaperText(skip=args.skip_prose)
    try:
        fig_rq1_agreement(r, t, args.png_dir)
        fig_rq1_confusion(r, t, args.png_dir)
        fig_rq2_results(r, t, args.png_dir)
        fig_rq2_kinds(r, t, args.png_dir)
        fig_wp5_resolve(r, t, args.png_dir)
        fig_wp5_confirmatory(r, t, args.png_dir)
        fig_rq2b_persistence(r, t, args.png_dir)
        fig_wp6_harm(r, t, args.png_dir)
    except CheckError as exc:
        LOG.error("integrity check failed: %s", exc)
        return 1
    LOG.info("all checks passed: %d values read, %d tied to the digest, %d tied to the paper text",
             r.n_reads, r.n_digest_checks, t.n_checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
