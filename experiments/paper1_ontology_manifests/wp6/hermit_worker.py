"""WP6 instrument 1: HermiT verdicts over the per-task claim ABoxes (project venv; owlready2 + Java).

Used by Paper 1 (JSEP rebuild), WP6; called by wp6/verify.py `run_hermit`.

Reads `<abox-dir>/<task>.items.json` (measured claims), writes the ABox `<task>.nt`, reasons with the frozen WP2 TBox
(`seo-claims.owl`, HermiT, `HermitReasoner(modules=CLAIMS_MODULES)`) and writes `<out-dir>/<task>.json` with the
leaf and verdict label of every claim. At most 2 JVMs at a time (VM rule).

Usage:
    PYTHONPATH=. .venv/bin/python -m experiments.paper1_ontology_manifests.wp6.hermit_worker \
        --abox-dir DIR --out-dir DIR --tbox /home/adtgrade/research/data/wp2_tbox/baseline [--workers 2]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger("wp6.hermit")


def reason_task(task: str, abox_dir: str, out_dir: str, tbox: str, force: bool) -> dict[str, Any]:
    from experiments.paper1_ontology_manifests.wp2 import step_reason as SR
    from ontology.reasoning.reasoner import CLAIMS_MODULES, HermitReasoner

    from experiments.paper1_ontology_manifests.wp2 import step_measure as SM

    out_p = Path(out_dir) / f"{task}.json"
    ab = Path(abox_dir) / f"{task}.nt"
    items_p = Path(abox_dir) / f"{task}.items.json"
    if out_p.exists() and not force and json.loads(out_p.read_text()).get("items_mtime") == items_p.stat().st_mtime:
        return {"task": task, "cached": True}
    it = json.loads(items_p.read_text())
    ab.write_text(SM.build_abox(task, {"S": it["S"], "manifest_path": "wp6/generated"}, it["items"]), encoding="utf-8")
    meas = {"repo": task, "claims": [{"key_str": i["key_str"]} for i in it["items"]]}
    tb = Path(tbox)
    r = HermitReasoner(tb, modules=CLAIMS_MODULES, temp_dir=Path(f"/tmp/wp6_reason_{os.getpid()}"))
    t0 = time.time()
    inf = r.infer(ab)
    rec: dict[str, Any] = {"task": task, "consistent": inf.consistent, "error": inf.error, "items_mtime": items_p.stat().st_mtime,
                           "seconds": round(time.time() - t0, 2), "tbox_sha256": SR.tbox_sha(tb), "n_claims": len(meas["claims"])}
    if inf.consistent:
        rec["claims"] = SR.labels_to_record(inf.labels, SR.iri_key_map(task, meas), SR.leaf_names(tb))
    out_p.write_text(json.dumps(rec, indent=1))
    return {"task": task, "cached": False, "consistent": inf.consistent}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--abox-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--tbox", required=True)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only", nargs="*", default=None)
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    Path(a.out_dir).mkdir(parents=True, exist_ok=True)
    tasks = sorted(p.name[: -len(".items.json")] for p in Path(a.abox_dir).glob("*.items.json"))
    if a.only:
        tasks = [t for t in tasks if t in a.only]
    n = min(a.workers, 2)
    with ProcessPoolExecutor(max_workers=n) as ex:
        res = list(ex.map(reason_task, tasks, [a.abox_dir] * len(tasks), [a.out_dir] * len(tasks), [a.tbox] * len(tasks),
                          [a.force] * len(tasks)))
    bad = [r["task"] for r in res if not r.get("cached") and not r.get("consistent", True)]
    logger.info("HermiT: %d tasks, %d inconsistent", len(res), len(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
