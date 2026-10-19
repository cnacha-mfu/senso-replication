"""Re-evaluate RQ4/RQ5 replication patches tested while the shared /tmp was running out of inodes (WP5 deviation 17).

Used by Paper 1 (JSEP rebuild). /tmp's inode table filled by about 2026-10-16 03:20 UTC with test-suite leftovers, so a test
run that needed a temp file could fail regardless of the patch. Every Ultra unit of wp5_rep that finished at or after
2026-10-15T21:00 and has a real evaluation (not an infra failure) is tested again from its saved patch in a fresh environment.
The earlier verdict is kept in the unit as `eval_before_tmp_fix`. Selection is by finish time only, not by outcome.
Writes wp5_rep/reeval_tmp_fix.json (old vs new verdict per unit) and rewrites the ledgers.

Usage:
    PY=/home/adtgrade/research/wp5_feasibility/.venv/bin/python
    systemd-run --user --scope -p MemoryMax=6G -p TasksMax=300 $PY experiments/paper1_ontology_manifests/scripts/reeval_after_tmp_full.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from experiments.paper1_ontology_manifests.wp5 import evaluate  # noqa: E402
from experiments.paper1_ontology_manifests.wp5.common import read_json, write_json  # noqa: E402
from experiments.paper1_ontology_manifests.wp6 import common as C  # noqa: E402

CUTOFF = "2026-10-15T21:00"
logger = logging.getLogger("reeval_tmp")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    cfg = C.load_config(PROJECT_ROOT / "experiments/paper1_ontology_manifests/configs/wp5_rep.yaml")
    ud = evaluate.units_dir(cfg, False)
    picked = []
    for f in sorted(ud.glob("*ultra*.json")):
        u = read_json(f)
        e = u.get("eval") or {}
        if u.get("status") != "done" or (u.get("finished") or "") < CUTOFF or e.get("reason") == "infra_failure":
            continue
        u.setdefault("eval_before_tmp_fix", e)
        u["eval"] = None
        write_json(f, u)
        picked.append(f)
    logger.info("re-evaluating %d units", len(picked))
    evaluate.evaluate_all(cfg, pilot=False)
    rows = []
    for f in picked:
        u = read_json(f)
        rows.append({"unit_id": u["unit_id"], "before": u["eval_before_tmp_fix"].get("reason"),
                     "after": (u.get("eval") or {}).get("reason"),
                     "resolved_before": bool(u["eval_before_tmp_fix"].get("resolved")),
                     "resolved_after": bool((u.get("eval") or {}).get("resolved"))})
    out = {"cutoff": CUTOFF, "n": len(rows), "n_changed": sum(r["resolved_before"] != r["resolved_after"] for r in rows),
           "units": rows}
    (PROJECT_ROOT / cfg["output_dir"] / "reeval_tmp_fix.json").write_text(json.dumps(out, indent=1) + "\n")
    logger.info("done: %d re-evaluated, %d verdicts changed", out["n"], out["n_changed"])


if __name__ == "__main__":
    main()
