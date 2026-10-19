"""RQ4/RQ5 confirmatory estimators (H1-H3, Holm) on the Claude Code study (exploratory; WP5 deviation 18).

Used by Paper 1 (JSEP rebuild). Builds one row per Claude Code run from ``results/real_v2/claude_rq45/units`` with the task
attributes of ``results/real_v2/wp5_rep/wp5_tasks.json`` and applies the same functions as ``run_wp5_analysis.py``
(``confirmatory``, ``holm3``: GEE, exchangeable, clustered by repository, one model). Infra failures count as unresolved
(intention to treat), as in the main analysis. Writes ``results/real_v2/claude_rq45/claude_analysis.json``.

Usage:
    /home/adtgrade/research/wp5_feasibility/.venv/bin/python \\
        experiments/paper1_ontology_manifests/scripts/claude_rq45_analysis.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from experiments.paper1_ontology_manifests import run_wp5_analysis as W  # noqa: E402

RES = PROJECT_ROOT / "experiments/paper1_ontology_manifests/results/real_v2"
CFG = PROJECT_ROOT / "experiments/paper1_ontology_manifests/configs/wp5_analysis.yaml"
logger = logging.getLogger("claude_rq45_analysis")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    cfg = W.load_config(CFG)
    tmap = {t["instance_id"]: t for t in W.load_tasks(RES / "wp5_rep/wp5_tasks.json")}
    rows = []
    for f in sorted((RES / "claude_rq45/units").glob("*.json")):
        u = json.loads(f.read_text())
        t = tmap[u["task_id"]]
        e = u.get("eval") or {}
        rows.append({"task": u["task_id"], "repo": t["repo"], "condition": u["condition"], "model": "claude-code/sonnet",
                     "stage": t["declared_stage"], "stage_H3": W.collapse_stage(t["declared_stage"]),
                     "resolved": 0.0 if e.get("reason") == "infra_failure" else float(bool(e.get("resolved")))})
    d = pd.DataFrame(rows)
    d = d[d["condition"].isin(cfg["conditions_confirmatory"])]
    po3 = W.po_is_h3_level(d.drop_duplicates("task"), cfg)
    res = W.confirmatory(d, cfg, model=False, po_h3=po3)
    out = {"label": "exploratory (WP5 deviation 18); same estimators as wp5_primary, one model",
           "n_tasks": int(d["task"].nunique()), "n_runs": int(len(d)), "po_is_h3_level": po3,
           "M1_M2": W.compact(res), "holm": W.holm3(res, cfg["alpha_familywise"])}
    W.write_json(RES / "claude_rq45/claude_analysis.json", W.jsonable(out))
    logger.info("wrote claude_analysis.json: %s", out["holm"])


if __name__ == "__main__":
    main()
