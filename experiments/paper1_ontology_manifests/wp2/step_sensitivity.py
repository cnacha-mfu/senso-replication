"""WP2 step: one-at-a-time threshold sensitivity by TBox rebuild (Paper 1, RQ2; design sections 6.4, 8, 10).

Five thresholds (``wp2_status_window_days``, ``wp2_inactive_contradict_min_commits``,
``wp2_inactive_contradict_min_lines``, ``wp2_inactive_support_max_commits``, ``wp2_consensus_min_votes``),
each at the two values listed in thresholds.yaml, plus the baseline = 11 TBox builds. For each build the
unchanged ABoxes (abox/*.nt) are re-reasoned with HermiT; only the TBox differs. The result is a table of
verdict and leaf counts per variant.

Usage:
    python experiments/paper1_ontology_manifests/wp2_consistency.py sensitivity
"""

from __future__ import annotations

import logging
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Optional

import yaml

from . import common as C
from .step_reason import ensure_tbox, reason_one

logger = logging.getLogger("wp2.step_sensitivity")
PARAMS = ["wp2_status_window_days", "wp2_inactive_contradict_min_commits", "wp2_inactive_contradict_min_lines",
          "wp2_inactive_support_max_commits", "wp2_consensus_min_votes"]


def variant_thresholds(param: str, value: Any) -> Path:
    base = yaml.safe_load((C.PROJECT_ROOT / "ontology" / "modules" / "thresholds.yaml").read_text(encoding="utf-8"))
    for t in base["thresholds"]:
        if t["id"] == param:
            t["value"] = value
    p = Path("/home/adtgrade/research/data/wp2_tbox") / f"thresholds_{param}_{value}.yaml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(base, sort_keys=False), encoding="utf-8")
    return p


def tally(recs: list[dict[str, Any]], meas: dict[str, Any]) -> dict[str, Any]:
    leaves: Counter = Counter()
    verdicts: Counter = Counter()
    by_type: dict[str, Counter] = {}
    n_doc = n_docs = 0
    rates = []
    for r in recs:
        if not r.get("consistent"):
            continue
        m = meas[r["slug"]]
        head = {c["key_str"]: c for c in m["claims"] if c["headline"]}
        s = c_ = k = 0
        for key, rec in r["claims"].items():
            if key not in head or not rec["verdicts"]:
                continue
            v = rec["verdicts"][0]
            verdicts[v] += 1
            t = head[key]["tcode"]
            by_type.setdefault(t, Counter())[v] += 1
            for lf in rec["leaves"]:
                leaves[lf] += 1
            s += v == "SupportedClaim"
            c_ += v == "ContradictedClaim"
            k += v == "ConflictedClaim"
        n_docs += 1
        n_doc += bool(r.get("document"))
        if s + c_ + k:
            rates.append(c_ / (s + c_ + k))
    return {"verdicts": dict(verdicts), "leaves": dict(leaves), "by_type": {t: dict(c) for t, c in by_type.items()},
            "manifests": n_docs, "manifests_with_contradiction": n_doc,
            "mean_manifest_contradiction_rate": sum(rates) / len(rates) if rates else None, "n_manifests_with_rate": len(rates)}


def run(cfg: dict[str, Any], only: Optional[str] = None, force: bool = False) -> int:
    res = C.results_dir(cfg)
    thr = {t["id"]: t for t in yaml.safe_load((C.PROJECT_ROOT / "ontology" / "modules" / "thresholds.yaml").read_text(encoding="utf-8"))["thresholds"]}
    corpus = C.load_corpus(cfg)
    slugs = [e["slug"] for e in corpus if (res / "abox" / f"{e['slug']}.nt").exists()]
    meas = {s: C.read_json(res / "measurements" / f"{s}.json") for s in slugs}
    variants: list[tuple[str, Optional[tuple[str, Any]]]] = [("baseline", None)]
    for p in PARAMS:
        for v in thr[p]["sensitivity"]:
            variants.append((f"{p}={v}", (p, v)))
    out: dict[str, Any] = {"mode": "one_at_a_time", "n_builds": len(variants), "variants": {}}
    for name, pv in variants:
        t0 = time.time()
        if pv is None:
            tbox = ensure_tbox("baseline")
        else:
            tbox = ensure_tbox(name.replace("=", "_"), variant_thresholds(*pv))
        tag = "sens_" + name.replace("=", "_").replace("/", "_")
        with ProcessPoolExecutor(max_workers=2) as ex:
            recs = [x for x in ex.map(reason_one, [cfg] * len(slugs), slugs, [tbox] * len(slugs), ["hermit"] * len(slugs),
                                      [force] * len(slugs), [f"sensitivity_verdicts/{tag}"] * len(slugs)) if x]
        out["variants"][name] = {"param": pv[0] if pv else None, "value": pv[1] if pv else None, **tally(recs, meas),
                                 "seconds": round(time.time() - t0, 1)}
        logger.info("%s: %s", name, {k: out["variants"][name][k] for k in ("verdicts", "manifests_with_contradiction")})
        C.write_json(res / "sensitivity.json", out)
    return 0
