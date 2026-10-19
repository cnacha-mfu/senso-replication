#!/usr/bin/env python3
"""Regression check of the extended TBox against the rq1-freeze labels (WP5 plan 3.1 item 6).

Paper 1 (WP5). The WP5 generator needs module classes (StableModule, ActiveModule ...) and module
measured properties in the TBox. Plan 3.1 item 6: on the 120 RQ1 repositories the extended TBox must give
project-level labels identical to the ``rq1-freeze`` TBox; any difference blocks ``wp5-generator-freeze``.

For every per-repo population JSON of the RQ1 run (``status == ok``) this script rebuilds the project ABox
from the stored measurements (exactly the ABox ``populate_v2.populate_repo`` wrote: the ``measures`` block
filtered to the declared measured properties, ``AboxWriter.project`` with ``close_months=False``),
reasons over it with HermiT and the TBox in ``--tbox-dir`` (default: the working tree's
``ontology/modules``) and compares the inferred label set of the project individual with the stored
``inferred[<primary config>]["classes"]``. It also compares the number of ABox triples, which proves the
reconstruction is the original ABox. Only the primary configuration is checked (the JSON of a sensitivity
configuration holds no measurements of its own; the variant TBoxes differ from the primary one only in
thresholds that this change does not touch).

Exit status 0 = all labels identical; the JSON report lists every difference.

Usage:
    python ontology/scenario_bank/wp5_regression.py \\
        --population-dir experiments/paper1_ontology_manifests/results/real_v2/rq1_population \\
        --out experiments/paper1_ontology_manifests/results/real_v2/wp5/wp5_tbox_regression.json \\
        [--workers 2] [--limit N]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ontology.reasoning.abox import AboxWriter, property_kinds  # noqa: E402
from ontology.reasoning.reasoner import MODULES_DIR, HermitReasoner  # noqa: E402

logger = logging.getLogger("senso.wp5_regression")
MAX_WORKERS = 4
"""CLAUDE.local.md: at most 4 parallel jobs."""


def check_repo(path: Path, tbox_dir: Optional[Path], jvm_mb: int, temp_dir: Path) -> dict[str, Any]:
    """Re-reason one repository's ABox and compare the project labels with the stored ones."""
    res = json.loads(path.read_text())
    out: dict[str, Any] = {"repo": res.get("repo", path.stem), "file": path.name, "configs": {}}
    if res.get("status") != "ok" or "inferred" not in res:
        out["skipped"] = res.get("status", "no inferred block")
        return out
    kinds = property_kinds()
    meas = {k: v for k, v in res["measures"].items() if k in kinds and k != "commitCount"}  # commitCount: window total of the result block, not asserted
    cid = res["primary_config"]
    wb = AboxWriter()
    iri = wb.project(res["repo"], meas, None, close_months=False)
    rb = HermitReasoner(tbox_dir=tbox_dir or MODULES_DIR, memory_mb=jvm_mb,
                        temp_dir=temp_dir / path.stem).infer(wb.ntriples())
    new = sorted(rb.labels_of(iri))
    old = sorted(res["inferred"][cid]["classes"])
    out["configs"][cid] = {
        "identical": new == old and rb.consistent == (not res["inferred"][cid]["inconsistent"]),
        "only_old": sorted(set(old) - set(new)), "only_new": sorted(set(new) - set(old)),
        "consistent_new": rb.consistent, "abox_triples_same": wb.n_triples == res["inferred"][cid]["abox_triples"],
        "n_labels": len(new)}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--population-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--tbox-dir", type=Path, default=None, help="module directory (default: ontology/modules)")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--jvm-mb", type=int, default=1800)
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    files = sorted(p for p in a.population_dir.glob("*.json") if not p.name.startswith("_"))[:a.limit]
    with tempfile.TemporaryDirectory(prefix="wp5_regr_") as td, ThreadPoolExecutor(
            max_workers=max(1, min(a.workers, MAX_WORKERS))) as ex:
        results = list(ex.map(lambda f: check_repo(f, a.tbox_dir, min(a.jvm_mb, 2000), Path(td)), files))
    checked = [r for r in results if "skipped" not in r]
    bad = [r for r in checked if not all(c["identical"] for c in r["configs"].values())]
    report = {"n_files": len(files), "n_checked": len(checked), "n_identical": len(checked) - len(bad),
              "n_different": len(bad), "all_identical": not bad and bool(checked),
              "abox_reconstruction_ok": all(c["abox_triples_same"] for r in checked for c in r["configs"].values()),
              "tbox_dir": str(a.tbox_dir or MODULES_DIR), "different": bad, "results": results}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=1))
    logger.info("checked %d, identical %d, different %d (abox reconstruction ok: %s)", len(checked),
                len(checked) - len(bad), len(bad), report["abox_reconstruction_ok"])
    return 0 if report["all_identical"] else 1


if __name__ == "__main__":
    sys.exit(main())
