"""WP5 task-list freeze (plan sections 2.1 and 7.4 rule 1).

Used by Paper 1 (JSEP rebuild), WP5.

N = min(supply, cap). All phase_out tasks are kept; the remaining slots are split equally over ID, EVO and SERV.
If the remainder is not divisible by 3 the extra slots go to SERV, then ID, then EVO. Each stratum is ordered by
numpy `default_rng(seed).permutation` over its lexicographically sorted task ids. Development tasks are excluded.

Usage:
    python experiments/paper1_ontology_manifests/run_wp5.py freeze-tasks
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any

import numpy as np

from .common import PROJECT_ROOT, read_json, rpath, write_json
from .ledgers import write_tasks

logger = logging.getLogger("wp5.freeze")
STAGES = ("initial_development", "evolution", "servicing", "phase_out")


def pilot_ids() -> set[str]:
    ids: set[str] = set()
    for sub in ("wp5_pilot", "wp5_pilot2"):
        f = PROJECT_ROOT / "experiments/paper1_ontology_manifests/results/real_v2" / sub / "pilot_tasks.json"
        ids |= set(read_json(f, {"task_ids": []})["task_ids"])
    return ids


def freeze_tasks(cfg: dict, cap: int = 80, replace: dict[str, str] | None = None) -> dict[str, Any]:
    from .runner import load_valid
    valid = load_valid(cfg)
    dev_ids = {t["instance_id"] for t in read_json(rpath(cfg, "output_dir") / "dev_pool.json", {"tasks": []})["tasks"]}
    sample = {t: v for t, v in valid.items() if t not in dev_ids}
    by = {s: sorted(t for t, v in sample.items() if v["stage"] == s) for s in STAGES}
    order = {s: [ids[i] for i in np.random.default_rng(cfg["seed"]).permutation(len(ids))] for s, ids in by.items()}
    supply = {s: len(v) for s, v in by.items()}
    n_total = min(sum(supply.values()), cap)
    chosen = list(order["phase_out"])[:n_total]
    rest = n_total - len(chosen)
    base, extra = divmod(rest, 3)
    quota = {"servicing": base, "initial_development": base, "evolution": base}
    for s in ("servicing", "initial_development", "evolution")[:extra]:
        quota[s] += 1
    for s, q in quota.items():
        chosen += order[s][:min(q, supply[s])]
    replace = replace or {}  # plan 5: a task whose population fails is replaced before any run (old -> new)
    chosen = [replace.get(t, t) for t in chosen]
    chosen_set = set(chosen)
    excl = [{"instance_id": t, "stage": sample[t]["stage"], "repo": sample[t]["repo"],
             "reason": f"not_selected: stratum quota under N={n_total} (seeded order)"}
            for s in STAGES for t in order[s] if t not in chosen_set]
    for old, new in replace.items():
        excl.append({"instance_id": old, "stage": sample[old]["stage"], "repo": sample[old]["repo"],
                     "reason": f"replaced_by:{new}: population unmineable (no_commits_up_to_snapshot)"})
        excl = [e for e in excl if e["instance_id"] != new]
    p = write_tasks(cfg, sorted(chosen))
    d = read_json(p)
    ts = d["tasks"]
    pil = pilot_ids()
    d.update(
        n_tasks=len(ts), supply_by_stage=supply, quota_by_stage=quota,
        allocation_rule=f"N=min(supply,{cap}); all phase_out; remaining {rest} split equally over ID, EVO, SERV; "
                        "extra slots in the order SERV, ID, EVO; stratum order = numpy default_rng(seed).permutation of sorted ids",
        counts_by_stage=dict(Counter(t["stage"] for t in ts)),
        counts_by_repo=dict(sorted(Counter(t["repo"] for t in ts).items())),
        n_repos=len({t["repo"] for t in ts}), max_tasks_per_repo=max(Counter(t["repo"] for t in ts).values()),
        b_available=sum(1 for t in ts if t["b_available"]), exclusions=excl,
        replacements=replace, dev_tasks_excluded=sorted(dev_ids & set(valid)),
        pilot_tasks_included=sorted(t["instance_id"] for t in ts if t["instance_id"] in pil))
    write_json(p, d)
    logger.info("frozen %d tasks: %s", len(ts), d["counts_by_stage"])
    return d
