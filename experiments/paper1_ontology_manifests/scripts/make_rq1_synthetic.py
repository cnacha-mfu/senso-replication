"""Generate a SYNTHETIC input for run_rq1_v2.py (pipeline test only).

Used by: Paper 1 (RQ1 analysis-code test). Fake repositories ("synth-org/repoNNN")
with random series and a synthetic ground-truth file in the schema of
ground_truth_sample.json. Reasoner labels are produced with the Python oracle of
run_rq1_v2.py (so the differential check passes), optionally corrupted with
--corrupt to test the failure path. The real ground-truth labels are not used.

Usage:
    python experiments/paper1_ontology_manifests/scripts/make_rq1_synthetic.py \\
        --out <dir> [--seed 1] [--corrupt 0] [--no-series]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "experiments" / "paper1_ontology_manifests"))

import run_rq1_v2 as rq  # noqa: E402

logger = logging.getLogger("make_rq1_synthetic")
STRATA = ["initial_development", "evolution", "servicing", "phase_out"]
STAGE_OF = {1: "initial_development", 2: "initial_development", 3: "initial_development",
            4: "initial_development", 5: "evolution", 6: "servicing", 7: "phase_out"}


def months_48() -> list[str]:
    out, y, m = [], 2022, 7
    for _ in range(48):
        out.append(f"{y}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def gen_repo(rng: np.random.Generator, stratum: str) -> dict:
    n = 48
    trunc = int(rng.integers(0, 14)) if rng.random() < 0.2 else 0
    if stratum == "phase_out":
        dormant = rng.random() < 0.6
        rate = np.concatenate([rng.uniform(0.5, 4) * np.ones(n - 14), np.zeros(14) if dormant else rng.uniform(0, 1) * np.ones(14)])
    elif stratum == "servicing":
        rate = rng.uniform(0.5, 3) * np.ones(n)
    elif stratum == "evolution":
        rate = np.linspace(rng.uniform(2, 6), rng.uniform(2, 10), n)
    else:
        rate = np.linspace(rng.uniform(1, 4), rng.uniform(3, 15), n)
    commits = rng.poisson(rate).astype(float)
    base = rng.integers(2000, 20000)
    scale = {"initial_development": 60, "evolution": 40, "servicing": 6, "phase_out": 3}[stratum]
    loc = base + np.cumsum(np.maximum(0, rng.normal(commits * scale * 0.3, scale)))
    months = months_48()[trunc:]
    commits, loc = commits[trunc:], loc[trunc:]
    nz = np.flatnonzero(commits > 0)
    msl = int(len(commits) - 1 - nz[-1]) if len(nz) else int(len(commits))
    if len(nz) and msl == len(commits):
        msl = len(commits)
    return {"months": months, "commits": commits.tolist(), "loc": [round(float(x)) for x in loc],
            "msl": msl}


def population_json(repo: str, g: dict, rng: np.random.Generator, corrupt: bool, no_series: bool,
                    cfg: dict) -> dict:
    rec = rq.RepoRecord(repo=repo, measures={"monthssincelastcommit": g["msl"]},
                        months=g["months"], commits=g["commits"], loc=g["loc"])
    pm = rq._mk(rq._tail(g["loc"], 36), "orig")
    cm = rq._mk(rq._tail(g["commits"], 36), "orig")
    c = g["commits"][-36:]
    measures = {
        "locMKTau": pm["tau"], "locMKpValue": pm["p"], "locSenSlope": pm["slope"],
        "locRelSenSlopeAnnual": pm["rel"], "monthsSinceLastCommit": g["msl"],
        "commitMKTau": cm["tau"], "commitMKpValue": cm["p"],
        "meanMonthlyCommits": float(np.mean(c)), "activeMonthRatio": float(np.mean(np.array(c) > 0)),
        "distinctAuthorsInWindow": int(rng.integers(1, 30)),
        "multiAuthorMonthRatio": float(rng.random()),
        "commitCount": float(sum(c)), "featCommitCount": int(rng.integers(0, 40)) if rng.random() < .7 else 0,
        "bugFixCommitCount": int(rng.integers(0, 40)),
    }
    if not no_series:
        measures["monthly_series"] = {"months": g["months"], "commits": g["commits"], "loc": g["loc"]}
    grid = cfg["grid"]
    cfgs = {rq.primary_cfg_id(cfg)}
    p = cfg["primary"]
    for a in grid["alpha"]:
        cfgs.add(rq.cfg_id(a, 36, 12, 0.05, "orig"))
    for Lm in grid["lookback_months"]:
        cfgs.add(rq.cfg_id(0.05, Lm, 12, 0.05, "orig"))
    for D in grid["dormancy_months"]:
        cfgs.add(rq.cfg_id(0.05, 36, D, 0.05, "orig"))
    for G in grid["min_rel_loc_growth_per_year"]:
        cfgs.add(rq.cfg_id(0.05, 36, 12, G, "orig"))
    cfgs.add(rq.cfg_id(0.05, 36, 12, 0.05, "hr"))
    inferred = {}
    import re
    for cid in sorted(cfgs):
        m = re.fullmatch(r"a([0-9.]+)_L(\d+)_D(\d+)_G([0-9.]+)_(orig|hr)", cid)
        a, Lm, D, G, mk = float(m[1]), int(m[2]), int(m[3]), float(m[4]), m[5]
        r1 = rq.oracle_c1(rec, a, Lm, mk) if True else "U"
        r2 = rq.oracle_c2(rec, a, Lm, D, G, mk)
        rec.loc = g["loc"]
        c1 = {"Growth": "GrowthStage", "Stabilization": "StabilizationStage",
              "Decline": "DeclineStage"}.get(r1)
        c2 = {"A": "RBActiveDevelopmentStage", "S": "RBServicingStage",
              "P": "RBPhaseOutStage"}.get(r2)
        classes = [x for x in (c1, c2) if x]
        # C1 is independent of dormancy: oracle_c1 ignores D, matching the real TBox
        entry = {"classes": classes, "inconsistent": False, "inconsistency_explanation": None,
                 "undetermined_reason": None,
                 "explanation_graph": {"C1": f"urn:synthetic:expl/{repo}/{cid}/c1",
                                       "C2": f"urn:synthetic:expl/{repo}/{cid}/c2"}}
        if corrupt and cid == rq.primary_cfg_id(cfg):
            entry["classes"] = ["RBPhaseOutStage" if c2 != "RBPhaseOutStage" else "RBServicingStage"]
        inferred[cid] = entry
    return {"schema": "rq1_population_v1", "repo": repo, "unmineable": False, "replaces": None,
            "measures": measures, "inferred": inferred}


def gt_record(repo: str, stratum: str, rng: np.random.Generator) -> dict:
    basis = {"initial_development": "classifier", "evolution": "classifier",
             "servicing": "classifier" if rng.random() < .8 else "readme",
             "phase_out": "archived_valid" if rng.random() < .9 else "readme"}[stratum]
    code = {"initial_development": 3, "evolution": 5, "servicing": 6, "phase_out": 7}[stratum]
    rels = []
    for i, t in enumerate(["2023-01-10T00:00:00Z", "2024-03-01T00:00:00+00:00",
                           "2024-09-15T12:00:00Z", "2025-02-01T00:00:00Z"]):
        ds = code if rng.random() < .85 else (code + 1 if code < 7 else 6)
        rels.append({"version": f"1.{i}", "time": t, "fetched": bool(rng.random() < .93),
                     "has_classifier_field": True, "dev_status": ds if rng.random() < .9 else None})
    return {"package": repo.split("/")[1], "repo": repo, "stratum": stratum,
            "github": {"archived": stratum == "phase_out"},
            "signals": {"classifier_stale_vs_latest": bool(rng.random() < .08),
                        "close_down_candidate": bool(stratum == "phase_out" and rng.random() < .3),
                        "readme": {"available": True}},
            "mapping": {"mapped_stage": stratum, "mapped_basis": basis, "conflict": False,
                        "conflicts": []},
            "snapshot_release": {"version": "1.3", "dev_status": {"value": code}},
            "history": {"n_releases_total": 4 + (3 if rng.random() < .2 else 0), "n_releases_fetched": 4,
                        "truncated": bool(rng.random() < .2), "releases": rels}}


def main() -> int:
    ap = argparse.ArgumentParser(description="synthetic RQ1 input generator")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--corrupt", type=int, default=0, help="number of repos with a wrong reasoner label")
    ap.add_argument("--no-series", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    import yaml
    cfg = yaml.safe_load(open(rq.CONFIG_PATH))
    rng = np.random.default_rng(args.seed)
    out = Path(args.out)
    (out / "pop").mkdir(parents=True, exist_ok=True)
    gts, i = [], 0
    for s in STRATA:
        for _ in range(30):
            repo = f"synth-org/repo{i:03d}"
            i += 1
            gts.append(gt_record(repo, s, rng))
    extra = []
    unmineable_idx = {5: "synth-org/repl-a", 70: "synth-org/repl-b"}
    corrupt_idx = set(rng.choice([k for k in range(120) if k not in unmineable_idx],
                                 size=args.corrupt, replace=False).tolist()) if args.corrupt else set()
    for k, gt in enumerate(gts):
        if k in unmineable_idx:
            json.dump({"repo": gt["repo"], "unmineable": True, "unmineable_reason": "clone failed"},
                      open(out / "pop" / f"{k:03d}.json", "w"))
            rname = unmineable_idx[k]
            g = gen_repo(rng, gt["stratum"])
            pj = population_json(rname, g, rng, False, args.no_series, cfg)
            pj["replaces"] = gt["repo"]
            json.dump(pj, open(out / "pop" / f"{k:03d}_repl.json", "w"))
            extra.append(gt_record(rname, gt["stratum"], rng))
            continue
        g = gen_repo(rng, gt["stratum"])
        json.dump(population_json(gt["repo"], g, rng, k in corrupt_idx, args.no_series, cfg),
                  open(out / "pop" / f"{k:03d}.json", "w"))
    json.dump({"snapshot_date": "2025-06-30", "records": gts}, open(out / "gt_synthetic.json", "w"))
    json.dump({"records": extra}, open(out / "gt_extra_synthetic.json", "w"))
    logger.info("wrote synthetic input to %s", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
