"""WP5 SA9: Y3 recomputed under module-stability threshold variants (plan 9, SA9).

Used by Paper 1 (JSEP rebuild), WP5. Output: wp5_outcomes_sa9.jsonl (run_id, variant, Y3) for run_wp5_analysis.py.

The module classes of the TBox (build_ontology.py) are datatype-restriction definitions:
  StableModule = relChurn < Rs AND changeMonths <= Ms;  ActiveModule = relChurn >= Rs OR changeMonths > Ms;
  a module without relChurn (LOC 0) is undetermined (its other rule input is withheld).
This script applies these definitions directly to the module measures instead of re-running the reasoner for
every variant (equivalent for datatype restrictions). The equivalence is checked on the primary configuration:
the recomputed labels must equal the stored reasoner labels of every module, and the recomputed primary Y3 must
equal the ledger Y3 of every run (reported in the `check` block of wp5_sa9_check.json; the script aborts on a
mismatch). W variants re-cut the cached raw module history (`mine_modules` cache, window up to 24 months) with
`measures.module_measurements`.

Usage:
    python experiments/paper1_ontology_manifests/run_wp5.py sa9
"""

from __future__ import annotations

import gzip
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from . import metrics
from .common import load_task, read_json, rpath, safe_id

logger = logging.getLogger("wp5.sa9")
PRIMARY = {"W": 12, "Rs": 0.10, "Ms": 2}
VARIANTS = {"primary": {}, "Rs0.05": {"Rs": 0.05}, "Rs0.20": {"Rs": 0.20}, "Ms0": {"Ms": 0}, "Ms1": {"Ms": 1},
            "Ms4": {"Ms": 4}, "W6": {"W": 6}, "W24": {"W": 24}}


def label_of(row: dict, Rs: float, Ms: int) -> str:
    rc = row.get("moduleRelChurnInWindow")
    if rc is None or row.get("moduleLoc", 0) <= 0:
        return "undetermined"
    cm = row["moduleChangeMonthsInWindow"]
    if rc < Rs and cm <= Ms:
        return "StableModule"
    if rc >= Rs or cm > Ms:
        return "ActiveModule"
    return "undetermined"


def _load_mod_cache(cfg: dict, repo: str, sha: str, tp_files: list[str]) -> dict:
    import hashlib
    th = hashlib.sha256("\n".join(sorted(tp_files)).encode()).hexdigest()[:10]
    name = f"{repo.replace('/', '__')}.{sha}.modules-v1.{th}.json.gz"
    for d in (Path(cfg.get("work_dir", "")) / "mining", Path.home() / "research/data/wp5/mining",
              Path.home() / "research/data/rq1_mining"):
        p = d / name
        if p.exists():
            doc = json.loads(gzip.decompress(p.read_bytes()))
            for c in doc["commits"]:
                c["author_date"] = datetime.fromisoformat(c["author_date"])
            return doc
    raise FileNotFoundError(name)


def run_sa9(cfg: dict) -> dict[str, Any]:
    M = metrics.measures()
    base = rpath(cfg, "output_dir")
    tasks = read_json(base / "wp5_tasks.json")["tasks"]
    runs = [json.loads(line) for line in (base / "wp5_runs.jsonl").read_text().splitlines()]
    outs = {r["run_id"]: r for r in (json.loads(line) for line in (base / "wp5_outcomes.jsonl").read_text().splitlines())}
    by_task: dict[str, list[dict]] = {}
    for r in runs:
        by_task.setdefault(r["instance_id"], []).append(r)
    rows: list[dict] = []
    check = {"labels_checked": 0, "label_mismatch": [], "runs_checked": 0, "y3_mismatch": []}
    for t in tasks:
        tid = t["instance_id"]
        task = load_task(cfg, tid)
        tp_files = list(metrics.split_diff(task["test_patch"]))
        tp = set(tp_files)
        pop = metrics.load_population(cfg, tid)
        S = datetime.fromisoformat(pop["modules_meta"]["anchor_S"])
        roots = frozenset(pop["modules_meta"]["package_roots"])
        doc = _load_mod_cache(cfg, t["repo"], t["base_commit"], tp_files)
        mk = lambda p: M.module_of(p, roots, tp)  # noqa: E731
        # per-W measurements
        meas = {W: M.module_measurements(doc["commits"], doc["module_loc"], S, W, mk, doc["last_change_month"])
                for W in (6, 12, 24)}
        for m, info in pop["modules"].items():  # equivalence check on the primary configuration
            lab = label_of(meas[12][m], PRIMARY["Rs"], PRIMARY["Ms"])
            check["labels_checked"] += 1
            if lab != info["label"]:
                check["label_mismatch"].append([tid, m, lab, info["label"]])
        pop_by_var: dict[str, dict] = {}
        for var, ch in VARIANTS.items():
            v = {**PRIMARY, **ch}
            mods = {m: {"label": label_of(meas[v["W"]][m], v["Rs"], v["Ms"]), "measures": meas[v["W"]][m]}
                    for m in pop["modules"]}
            pop_by_var[var] = mods
        for r in by_task.get(tid, []):
            rid = r["run_id"]
            p = base / "runs" / "patches" / f"{rid}.diff.gz"
            diff = metrics.filter_diff(gzip.open(p, "rt").read(), tp) if p.exists() else ""
            changed = sum(metrics.lines_by_file(diff, tp).values()) if diff.strip() else 0
            for var, mods in pop_by_var.items():
                y3 = metrics._stability(diff, tp, roots, mods)["Y3"] if changed else None
                rows.append({"run_id": rid, "variant": var, "Y3": y3})
                if var == "primary":
                    led = outs[rid].get("Y3")
                    check["runs_checked"] += 1
                    if (led is None) != (y3 is None) or (led is not None and abs(led - y3) > 1e-9):
                        check["y3_mismatch"].append([rid, led, y3])
    ok = not check["label_mismatch"] and not check["y3_mismatch"]
    (base / "wp5_sa9_check.json").write_text(json.dumps({**check, "ok": ok, "variants": VARIANTS, "primary": PRIMARY}, indent=1))
    if not ok:
        raise RuntimeError(f"SA9 equivalence check failed: {len(check['label_mismatch'])} labels, {len(check['y3_mismatch'])} Y3")
    (base / "wp5_outcomes_sa9.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows if r["variant"] != "primary"))
    logger.info("SA9: %d rows, checks ok (%d labels, %d runs)", len(rows), check["labels_checked"], check["runs_checked"])
    return check
