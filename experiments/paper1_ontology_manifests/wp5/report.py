"""WP5 pilot / run summary: descriptive metrics per model x condition, from the unit JSONs.

Used by Paper 1 (JSEP rebuild), WP5. Descriptive only; the confirmatory analysis follows the committed
analysis plan, not this report.

Usage:
    python experiments/paper1_ontology_manifests/run_wp5.py report --pilot
"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from datetime import datetime
from statistics import mean, median
from typing import Any, Optional

from .common import read_json, rpath, write_json
from .evaluate import units_dir

logger = logging.getLogger("wp5.report")


def _m(xs: list) -> Optional[float]:
    xs = [x for x in xs if x is not None]
    return round(mean(xs), 3) if xs else None


def group_stats(us: list[dict]) -> dict[str, Any]:
    done = [u for u in us if u.get("status") == "done"]
    ev = [u.get("eval") or {} for u in done]
    err: Counter = Counter()
    for u in done:
        err.update(u.get("api_errors") or {})
    mets = [e.get("outcomes") for e in ev if e.get("outcomes")]
    return {
        "n_units": len(us), "n_done": len(done),
        "n_skipped": sum(1 for u in us if u.get("status") == "skipped"),
        "n_env_failed": sum(1 for u in us if u.get("status") == "env_failed"),
        "resolved": sum(1 for e in ev if e.get("resolved")),
        "resolve_rate": round(sum(1 for e in ev if e.get("resolved")) / len(done), 3) if done else None,
        "eval_reasons": dict(Counter(e.get("reason") for e in ev)),
        "exit_status": dict(Counter(u.get("exit_status") for u in done)),
        "steps_mean": _m([u["steps"] for u in done]), "steps_median": median([u["steps"] for u in done]) if done else None,
        "wall_s_mean": _m([u["wall_s"] for u in done]), "wall_s_max": max([u["wall_s"] for u in done], default=None),
        "format_errors_total": sum(u.get("format_errors", 0) for u in done),
        "runs_with_format_error": sum(1 for u in done if u.get("format_errors", 0) > 0),
        "length_cutoffs_total": sum(u.get("length_cutoffs", 0) for u in done),
        "limit_exits": sum(1 for u in done if u.get("exit_status") in ("LimitsExceeded", "TimeExceeded", "WallTimeAbort")),
        "repeated_format_error_exits": sum(1 for u in done if u.get("exit_status") == "RepeatedFormatError"),
        "api_errors": dict(err),
        "n_429": err.get("429", 0), "n_503": err.get("503", 0),
        "prompt_tokens_mean": _m([u["prompt_tokens"] for u in done]),
        "completion_tokens_mean": _m([u["completion_tokens"] for u in done]),
        "prompt_tokens_total": sum(u["prompt_tokens"] for u in done),
        "completion_tokens_total": sum(u["completion_tokens"] for u in done),
        "empty_patches": sum(1 for e in ev if e.get("reason") == "empty_patch"),
        "Y0_patch_rate": _m([m["Y0"] for m in mets]),
        "Y1_delta_ccn_mean": _m([m["Y1"] for m in mets]), "Y2_new_edges_mean": _m([m["Y2"] for m in mets]),
        "Y3_stable_share_mean": _m([m["Y3"] for m in mets]), "Y4_log2_size_ratio_mean": _m([m["Y4"] for m in mets]),
        "Y5_files_mean": _m([m["Y5"] for m in mets]), "Y6_steps_mean": _m([m["Y6"] for m in mets]),
    }


def monitor_report(cfg: dict, units: list[dict]) -> dict[str, Any]:
    """Plan 11.3 monitor: terminal states, infra failures/retries, prompt tokens by condition, evaluation errors.
    Deliberately contains no resolve rate and no outcome, by condition or otherwise."""
    from .evaluate import state_of
    rows = []
    for u in units:
        if u.get("status") in ("done", "env_failed"):
            st, infra = state_of(u)
            rows.append({"cond": u["condition"], "model": u["model"].split("/")[-1], "state": st, "infra": infra,
                         "retries": u.get("retries", 0), "ptok": u.get("prompt_tokens") or 0,
                         "eval_error": (u.get("eval") or {}).get("reason") in ("harness_exception", "env_rebuild_failed")})
    by: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by[f"{r['model']}|{r['cond']}"].append(r)
    return {"kind": "monitor", "n_units": len(rows),
            "by_model_condition": {k: {"n": len(v), "states": dict(Counter(r["state"] for r in v)),
                                       "infra_failures": sum(r["infra"] for r in v),
                                       "retries": sum(r["retries"] for r in v),
                                       "prompt_tokens_mean": _m([r["ptok"] for r in v]),
                                       "eval_errors": sum(r["eval_error"] for r in v)} for k, v in sorted(by.items())}}


def pilot_summary(cfg: dict, units: list[dict]) -> dict[str, Any]:
    """Inputs of the power decision (plan 7.1): p0 from condition-A runs, model log-OR over A and B runs."""
    import math
    from shared.evaluation import statistics as st
    a = [u for u in units if u.get("status") == "done" and u["condition"] == "A"]
    k = sum(1 for u in a if (u.get("eval") or {}).get("resolved"))
    n = len(a)
    ms = sorted({u["model"] for u in units if u.get("status") == "done"})
    tab = {m: [sum(1 for u in units if u.get("status") == "done" and u["model"] == m and u["condition"] in ("A", "B")
                   and (u.get("eval") or {}).get("resolved")),
               sum(1 for u in units if u.get("status") == "done" and u["model"] == m and u["condition"] in ("A", "B"))]
           for m in ms}
    logor = None
    if len(ms) == 2:
        (k1, n1), (k2, n2) = tab[ms[0]], tab[ms[1]]
        logor = math.log(((k1 + .5) / (n1 - k1 + .5)) / ((k2 + .5) / (n2 - k2 + .5)))
    lo, hi = st.jeffreys_interval(k, n, 0.80) if n else (None, None)
    return {"k_A_resolved": k, "n_A_runs": n, "p0_hat": (k / n) if n else None, "p0_jeffreys_80": [lo, hi],
            "model_pair": ms, "model_AB_resolved_over_runs": tab,
            "model_logor_raw": logor, "model_logor": None if logor is None else max(-1.5, min(1.5, logor / 2)),
            "pilot_icc": None, "note": "pilot only; ICC not estimated (10 tasks); never evidence"}


def make_report(cfg: dict, pilot: bool = False) -> dict[str, Any]:
    ud = units_dir(cfg, pilot)
    if not pilot:
        rep = monitor_report(cfg, [u for u in (read_json(f) for f in sorted(ud.glob("*.json"))) if u])
        write_json(ud.parent / "run_monitor.json", rep)
        logger.info("monitor: %s", {k: v["states"] for k, v in rep["by_model_condition"].items()})
        return rep
    base = ud.parent
    units = [u for u in (read_json(f) for f in sorted(ud.glob("*.json"))) if u]
    by: dict[str, list[dict]] = defaultdict(list)
    by_model: dict[str, list[dict]] = defaultdict(list)
    by_stage: dict[str, list[dict]] = defaultdict(list)
    for u in units:
        by[f"{u['model'].split('/')[-1]}|{u['condition']}"].append(u)
        by_model[u["model"].split("/")[-1]].append(u)
        by_stage[u["stage"]].append(u)
    meta = read_json(base / "run_meta.json", {"sessions": []})
    starts = [datetime.fromisoformat(u["started"]) for u in units if u.get("started")]
    ends = [datetime.fromisoformat(u["finished"]) for u in units if u.get("finished")]
    done = [u for u in units if u.get("status") == "done"]
    wall_h = (max(ends) - min(starts)).total_seconds() / 3600 if starts and ends else None
    sess = meta["sessions"][-1] if meta["sessions"] else {}
    env_s = sorted({(u["task_id"], u["env_build_s"]) for u in units if "env_build_s" in u})
    rep = {
        "kind": "pilot" if pilot else "full", "n_units": len(units), "n_tasks": len({u["task_id"] for u in units}),
        "tasks_per_stage": dict(Counter({s: len({u["task_id"] for u in v}) for s, v in by_stage.items()})),
        "temperature": next((u["temperature"] for u in done), None),
        "mini_swe_agent_version": next((u.get("mini_version") for u in done), None),
        "workers": sess.get("workers"),
        "overall": group_stats(units),
        "by_model": {k: group_stats(v) for k, v in sorted(by_model.items())},
        "by_model_condition": {k: group_stats(v) for k, v in sorted(by.items())},
        "by_stage": {k: group_stats(v) for k, v in sorted(by_stage.items())},
        "throughput": {
            "wall_clock_hours": round(wall_h, 2) if wall_h else None,
            "runs_per_hour_overall": round(len(done) / wall_h, 2) if wall_h else None,
            "runs_per_hour_per_worker": round(len(done) / wall_h / sess["workers"], 2) if wall_h and sess.get("workers") else None,
            "env_build_s_per_task_mean": _m([s for _, s in env_s]),
            "agent_wall_s_mean": _m([u["wall_s"] for u in done]),
        },
        "b_unavailable_units": sum(1 for u in units if u.get("reason") == "B_unavailable"),
        "real_agent_manifest_at_base_tasks": sorted({u["task_id"] for u in units if u.get("real_agent_manifest_at_base")}),
    }
    write_json(base / "pilot_summary.json", rep)
    write_json(base / "wp5_pilot_summary.json", pilot_summary(cfg, units))
    o = rep["overall"]
    logger.info("units %d done %d resolved %d; per model/condition resolve rates: %s", len(units), o["n_done"],
                o["resolved"], {k: v["resolve_rate"] for k, v in rep["by_model_condition"].items()})
    return rep
