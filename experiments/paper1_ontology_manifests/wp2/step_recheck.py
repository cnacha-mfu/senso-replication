"""WP2 step: compare reasoner verdicts with the independent deterministic re-check (Paper 1, RQ2; design 6.1).

Reads ``measurements/`` (claim content only) and ``verdicts/`` (HermiT), runs ``wp2/recheck.py`` (which
measures the repository again and applies the rules with plain ``if`` logic), and writes ``recheck.json``:
verdict confusion matrix, per-type agreement, Cohen's kappa, precision of ContradictedClaim and the list
of every disagreement. This is encoding fidelity, not construct validity.

Usage:
    python experiments/paper1_ontology_manifests/wp2_consistency.py recheck [--only owner/name]
"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Optional

import yaml

from . import common as C
from . import recheck as R

logger = logging.getLogger("wp2.step_recheck")

CATS = ["SupportedClaim", "ContradictedClaim", "UnverifiableClaim", "IndeterminateClaim", "ConflictedClaim", "none"]


def cohen_kappa(pairs: list[tuple[str, str]]) -> float:
    n = len(pairs)
    if n == 0:
        return float("nan")
    po = sum(1 for a, b in pairs if a == b) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def recheck_repo(cfg: dict[str, Any], slug: str, thr: dict[str, Any], sigs: dict[str, Any], vsrc: dict[str, Any]
                 ) -> list[dict[str, Any]]:
    res = C.results_dir(cfg)
    mp, vp = res / "measurements" / f"{slug}.json", res / "verdicts" / f"{slug}.json"
    if not mp.exists() or not vp.exists():
        return []
    meas, ver = C.read_json(mp), C.read_json(vp)
    if not ver.get("consistent"):
        return []
    g = R.Git(Path(cfg["clone_dir"]) / slug, meas["S"])
    g.prefetch_interesting()
    cache: dict[str, Any] = {}
    tool_cache: dict[str, int] = {}
    rows = []
    for c in meas["claims"]:
        if int(c["votes"]) < int(thr["wp2_consensus_min_votes"]) or c["tcode"] == "T7":
            continue  # T7 (stretch, case studies) has no independent re-implementation
        rv = ver["claims"].get(c["key_str"], {})
        rs_verdict = (rv.get("verdicts") or ["none"])[0]
        rs_leaf = (rv.get("leaves") or [None])[0]
        ch_verdict, ch_leaf = R.recheck_claim(g, {"tcode": c["tcode"], "attrs": c["attrs"], "votes": c["votes"]}, thr, sigs,
                                              vsrc, cache, tool_cache)
        rows.append({"repo": meas["repo"], "key": c["key_str"], "tcode": c["tcode"], "headline": c["headline"],
                     "reasoner_verdict": rs_verdict, "reasoner_leaf": rs_leaf,
                     "recheck_verdict": ch_verdict or "none", "recheck_leaf": ch_leaf,
                     "agree_verdict": rs_verdict == (ch_verdict or "none"), "agree_leaf": rs_leaf == ch_leaf,
                     "props": c["m"]["props"], "n_evidences": len(c["m"]["evidences"]), "quote": c["quote"][:160]})
    logger.info("%s: rechecked %d claims", meas["repo"], len(rows))
    return rows


def run(cfg: dict[str, Any], only: Optional[str] = None, force: bool = False) -> int:
    bad = R.check_independence()
    if bad:
        raise RuntimeError(f"recheck.py imports forbidden modules: {bad}")
    res = C.results_dir(cfg)
    thr = R.load_thr()
    sigs = yaml.safe_load((C.EXP_DIR / "configs" / "wp2_tool_signatures.yaml").read_text(encoding="utf-8"))
    vsrc = yaml.safe_load((C.EXP_DIR / "configs" / "wp2_version_sources.yaml").read_text(encoding="utf-8"))["subjects"]
    slugs = [e["slug"] for e in C.load_corpus(cfg) if not only or e["full_name"] == only]
    with ThreadPoolExecutor(max_workers=3) as ex:
        parts = list(ex.map(lambda s: recheck_repo(cfg, s, thr, sigs, vsrc), slugs))
    rows = [r for p in parts for r in p]
    conf: dict[str, dict[str, int]] = {a: {b: 0 for b in CATS} for a in CATS}
    for r in rows:
        conf[r["reasoner_verdict"]][r["recheck_verdict"]] += 1
    by_type: dict[str, dict[str, Any]] = {}
    for t in sorted({r["tcode"] for r in rows}):
        rt = [r for r in rows if r["tcode"] == t]
        by_type[t] = {"n": len(rt), "agree_verdict": sum(r["agree_verdict"] for r in rt) / len(rt),
                      "agree_leaf": sum(r["agree_leaf"] for r in rt) / len(rt),
                      "kappa": cohen_kappa([(r["reasoner_verdict"], r["recheck_verdict"]) for r in rt])}
    rc = [r for r in rows if r["reasoner_verdict"] == "ContradictedClaim"]
    kc = [r for r in rows if r["recheck_verdict"] == "ContradictedClaim"]
    out = {
        "independence_check": {"forbidden_imports_found": bad},
        "n_claims": len(rows), "confusion_matrix_rows_reasoner_cols_recheck": conf,
        "agree_verdict": sum(r["agree_verdict"] for r in rows) / max(1, len(rows)),
        "agree_leaf": sum(r["agree_leaf"] for r in rows) / max(1, len(rows)),
        "kappa_verdict": cohen_kappa([(r["reasoner_verdict"], r["recheck_verdict"]) for r in rows]),
        "precision_contradicted": (sum(1 for r in rc if r["recheck_verdict"] == "ContradictedClaim") / len(rc)) if rc else None,
        "recall_contradicted": (sum(1 for r in kc if r["reasoner_verdict"] == "ContradictedClaim") / len(kc)) if kc else None,
        "n_reasoner_contradicted": len(rc), "n_recheck_contradicted": len(kc),
        "by_type": by_type,
        "disagreements": [r for r in rows if not r["agree_verdict"]],
        "leaf_only_disagreements": [r for r in rows if r["agree_verdict"] and not r["agree_leaf"]],
        "note": ("Encoding fidelity: does the reasoner decide exactly what the rules state? Not construct validity. "
                 "Both sides read the same git objects through different code."),
    }
    C.write_json(res / "recheck.json", out)
    C.write_jsonl(res / "recheck_rows.jsonl", rows)
    logger.info("recheck: %d claims, verdict agreement %.3f, kappa %.3f, precision(Contradicted)=%s", len(rows),
                out["agree_verdict"], out["kappa_verdict"], out["precision_contradicted"])
    return 0
