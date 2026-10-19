"""Tallies for the exploratory stronger-model replication (nemotron-3-ultra) of RQ4-RQ6.

Used by Paper 1 (JSEP rebuild); WP6 deviations 21-24, WP5 deviations 15-16. Reads the Ultra ledgers only:
``results/real_v2/wp6_rep/ultra/wp6_outcomes.jsonl`` (RQ6, the GLM rows of the shared ledger filtered out) and
``results/real_v2/wp5_rep/wp5_{runs,outcomes}.jsonl`` (RQ4/RQ5). RQ4/RQ5 counts are on the tasks not marked ``excluded``
in ``wp5_rep/wp5_tasks.json`` (all 80 since the rerun of 2026-10-18). The same tasks are tallied for the original two-model
study, for comparison. Writes ``results/real_v2/rep_summary.json``. When the Claude Code study (WP5 deviation 18) has units,
also writes ``results/real_v2/claude_rq45/claude_summary.json``: Claude Code by condition, and Ultra and the original models
on the same tasks. The results digest renders both.

Usage:
    python experiments/paper1_ontology_manifests/scripts/rep_summary.py
"""
from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RES = PROJECT_ROOT / "experiments/paper1_ontology_manifests/results/real_v2"
KINDS = {"1": "folder", "2": "file", "3": "test_command", "4": "dependency"}   # wp6 manifest generator item kinds

logger = logging.getLogger("rep_summary")


def jl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


def rq6(ledger: str = "wp6_rep/ultra/wp6_outcomes.jsonl") -> dict:
    out: dict = defaultdict(lambda: defaultdict(int))
    for r in jl(RES / ledger):
        c = r["condition"]
        s = r["sets"]["F_I" if c == "F_I" else "F_R"]   # A and T are scored against the F_R items, as in the analysis
        o = out[c]
        o["runs"] += 1
        o["runs_with_false_lead"] += s["Y3"]
        o["false_lead_actions"] += s["Y1"]
        o["wasted_steps"] += s["Y2"]
        o["resolved"] += r["resolved"] or 0
        for k, v in s["Y4_by_kind"].items():
            o["actions_" + KINDS[k]] += v
    return {c: dict(v) for c, v in sorted(out.items())}


def rq45(d: str, keep: set[str]) -> dict:
    runs = {r["run_id"]: r for r in jl(RES / d / "wp5_runs.jsonl")}
    out: dict = defaultdict(lambda: defaultdict(int))
    for o in jl(RES / d / "wp5_outcomes.jsonl"):
        r = runs[o["run_id"]]
        if r["instance_id"] not in keep:
            continue
        x = out[r["condition"]]
        x["runs"] += 1
        x["resolved"] += o["resolved"]
        x["step_limit"] += r["state"] == "LimitsExceeded"
        x["steps_total"] += o.get("Y6") or 0
        x["label_term_uptake"] += bool((o.get("uptake") or {}).get("label_term"))
    res = {}
    for c, v in sorted(out.items()):
        v = dict(v)
        v["resolve_rate"] = round(v["resolved"] / v["runs"], 4)
        v["mean_steps"] = round(v.pop("steps_total") / v["runs"], 2)
        res[c] = v
    return res


def claude(units: Path) -> dict:
    out: dict = defaultdict(lambda: defaultdict(float))
    tasks = set()
    for f in sorted(units.glob("*.json")):
        u = json.loads(f.read_text())
        e = u.get("eval") or {}
        x = out[u["condition"]]
        tasks.add(u["task_id"])
        x["runs"] += 1
        x["infra_failure"] += e.get("reason") == "infra_failure"
        x["resolved"] += bool(e.get("resolved"))
        x["turns_total"] += u.get("steps") or 0
        x["label_term_uptake"] += bool((u.get("uptake") or {}).get("label_term"))
        x["api_equivalent_usd"] += u.get("cost_estimate_usd") or 0
    res = {}
    for c, v in sorted(out.items()):
        v = {k: (round(n, 2) if k == "api_equivalent_usd" else int(n)) for k, n in v.items()}
        v["resolve_rate"] = round(v["resolved"] / v["runs"], 4)
        v["mean_turns"] = round(v.pop("turns_total") / v["runs"], 2)
        res[c] = v
    return {"tasks": sorted(tasks), "by_condition": res}


def main() -> None:
    tasks = json.loads((RES / "wp5_rep/wp5_tasks.json").read_text())["tasks"]
    keep = {t["instance_id"] for t in tasks if not t.get("excluded")}
    summary = {
        "model": "nvidia/nemotron-3-ultra-550b-a55b",
        "rq6_by_condition": rq6(),
        "rq6_original_by_condition": rq6("wp6/runs/wp6_outcomes.jsonl"),   # both original models pooled
        "rq45_tasks_complete": len(keep),
        "rq45_tasks_excluded": sorted(t["instance_id"] for t in tasks if t.get("excluded") and t.get("excluded_reason")),
        "rq45_ultra_by_condition": rq45("wp5_rep", keep),
        "rq45_original_same_tasks_by_condition": rq45("wp5", keep),
    }
    (RES / "rep_summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    logger.info("wrote %s", RES / "rep_summary.json")
    units = RES / "claude_rq45/units"
    if units.is_dir() and any(units.glob("*.json")):
        cl = claude(units)
        keep_c = set(cl["tasks"])
        cs = {"model": "claude-code/sonnet (Sonnet 5.5)", "n_tasks": len(keep_c), "claude_by_condition": cl["by_condition"],
              "ultra_same_tasks_by_condition": rq45("wp5_rep", keep_c),
              "original_same_tasks_by_condition": rq45("wp5", keep_c)}
        (RES / "claude_rq45/claude_summary.json").write_text(json.dumps(cs, indent=1) + "\n")
        logger.info("wrote %s", RES / "claude_rq45/claude_summary.json")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    main()
