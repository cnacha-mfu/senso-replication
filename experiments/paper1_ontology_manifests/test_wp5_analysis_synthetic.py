#!/usr/bin/env python3
"""End-to-end test of run_wp5_analysis.py on synthetic data (Paper 1, WP5; plan section 11.3).

Committed before any non-pilot run, as the plan requires. The data come from the power
simulator's generator (``simulate_glmm_binary``): 66 tasks in 22 repositories (declared
stages ID/EVO/SERV/PO cycling by repository), 3 conditions x 2 models x 2 replicates plus B
on half of the tasks, a true conditional OR of 2.5 for C versus A in SERVICING tasks only.
Everything is written to a scratch directory, never to ``results/``.

Checks: the section 0 refusals (missing freeze tag, hash mismatch, non-terminal run,
synthetic output under real_v2, bootstrap overrides outside synthetic mode) all exit 2 and
write nothing; a frozen run (temporary git repository with the tag ``wp5-run-freeze``,
matching hashes) and a ``--synthetic`` run exit 0 and write the five section 12 files with
the expected structure; the estimated effect has the simulated sign (C vs A in SERVICING);
outputs are deterministic across two runs (byte-identical JSON); the ``power`` subcommand
runs on a tiny grid and writes ``wp5_power.json`` with a label and an MDE.

Usage:
    nice -n 10 python experiments/paper1_ontology_manifests/test_wp5_analysis_synthetic.py [--scratch DIR]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_wp5_analysis as RA  # noqa: E402
from shared.evaluation import statistics as st  # noqa: E402

logger = logging.getLogger("test_wp5_analysis_synthetic")
RESULTS: list[tuple[str, bool, str]] = []
CFG_PATH = Path(RA.DEFAULT_CONFIG)


def check(name: str, cond: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(cond), detail))
    logger.info("%s  %s %s", "PASS" if cond else "FAIL", name, detail)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def make_inputs(d: Path, seed: int = 11, break_terminal: bool = False) -> None:
    """Write wp5_tasks.json, wp5_runs.jsonl, wp5_outcomes.jsonl, wp5_manifests_index.json."""
    cfg = RA.load_config(CFG_PATH)
    models = cfg["models"]
    rng = np.random.default_rng(seed)
    stages = ["ID", "EVO", "SERV", "PO"]
    tasks = []
    for r in range(22):
        for t in range(3):
            tasks.append({"instance_id": f"o{r}__repo{r}-{t}", "repo": f"o{r}/repo{r}",
                          "declared_stage": stages[r % 4], "b_available": (r + t) % 2 == 0,
                          "agent_manifest_in_tree": r % 7 == 0, "gold_drift_fail": r == 3 and t == 0,
                          "inferred_stage": ["A", "S", "P"][(r + t) % 3]})
    rows = []
    for t in tasks:
        for cond in "ABCD":
            if cond == "B" and not t["b_available"]:
                continue
            for mi, m in enumerate(models):
                for k in range(2):
                    sh = RA.collapse_stage(t["declared_stage"])
                    rows.append({"repo": t["repo"], "task": t["instance_id"], "condition": cond, "model": m,
                                 "model_is_second": mi, "rep": k, "is_C": int(cond == "C"),
                                 "is_C_SERV": int(cond == "C" and sh == "SERVICING")})
    df = pd.DataFrame(rows)
    s2 = 0.5 * (np.pi ** 2 / 3) / 0.5
    alpha = st.calibrate_marginal_intercept(0.3, s2)
    y = st.simulate_glmm_binary(df, alpha, {"is_C_SERV": np.log(2.5), "model_is_second": -0.3},
                                0.2 * s2, 0.8 * s2, rng)
    ledger, outs = [], []
    for i, r in df.iterrows():
        rid = f"{r['task']}|{r['condition']}|{r['model']}|{r['rep']}"
        infra = rng.random() < 0.02
        lim = rng.random() < 0.3
        ledger.append({"run_id": rid, "instance_id": r["task"], "condition": r["condition"], "model": r["model"],
                       "rep": int(r["rep"]), "state": "infra_failure" if infra else
                       ("LimitsExceeded" if lim else "Submitted"), "retries": 0})
        patch = rng.random() < 0.8
        outs.append({"run_id": rid, "resolved": int(y[i]), "Y0": int(patch),
                     "Y1": float(rng.normal(1, 3)) if patch else None,
                     "Y2": int(rng.poisson(0.5)) if patch else None,
                     "Y3": float(rng.beta(2, 5)) if patch else None,
                     "Y3_excess": float(rng.normal(0, .2)) if patch else None,
                     "Y3w": float(rng.beta(3, 3)) if patch else None,
                     "Y4": float(rng.normal(0, 1)) if patch else None, "Y5": int(rng.poisson(2)),
                     "Y6": int(rng.integers(5, 41)), "hit_step_limit": int(lim),
                     "uptake": {"repo_context": int(r["condition"] != "A" and rng.random() < .5),
                                "label_term": int(r["condition"] == "C" and rng.random() < .4),
                                "d1_name": int(r["condition"] == "D" and rng.random() < .2)}})
    if break_terminal:
        ledger[5]["state"] = "running"
    index = {"tasks": {t["instance_id"]: {"length_violation": bool(rng.random() < 0.1),
                                          "explanation_fallback": int(rng.random() < 0.1),
                                          "C": {"chars": 6000 + int(rng.integers(0, 1500))},
                                          "D": {"chars": 6000 + int(rng.integers(0, 1500))},
                                          "B": {"chars": int(rng.integers(500, 8000))}} for t in tasks}}
    d.mkdir(parents=True, exist_ok=True)
    (d / "wp5_tasks.json").write_text(json.dumps({"tasks": tasks}))
    (d / "wp5_runs.jsonl").write_text("\n".join(json.dumps(x) for x in ledger) + "\n")
    (d / "wp5_outcomes.jsonl").write_text("\n".join(json.dumps(x) for x in outs) + "\n")
    (d / "wp5_manifests_index.json").write_text(json.dumps(index))


def write_run_manifest(d: Path) -> None:
    (d / "wp5_run_manifest.json").write_text(json.dumps({"hashes": {
        "tasks": sha(d / "wp5_tasks.json"), "manifests_index": sha(d / "wp5_manifests_index.json"),
        "analysis_config": sha(CFG_PATH)}}))


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                   check=True, capture_output=True)


def run(args: list[str]) -> int:
    return RA.main(args)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--scratch", type=Path, default=None)
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    root = Path(a.scratch) if a.scratch else Path(tempfile.mkdtemp(prefix="wp5_synth_"))
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    RA.logger.setLevel(logging.CRITICAL)  # refusals log errors on purpose
    inp = root / "in"
    make_inputs(inp)
    write_run_manifest(inp)
    base = ["analyze", "--results-dir", str(inp), "--n-boot", "300", "--n-boot-clogit", "15"]

    # --- refusals -----------------------------------------------------------------
    repo = root / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    (repo / "f").write_text("1")
    git(repo, "add", "f")
    git(repo, "commit", "-q", "-m", "plan")
    out_r = root / "out_refused"
    check("refuse: freeze tag missing, nothing written",
          RA.main(["analyze", "--results-dir", str(inp), "--out-dir", str(out_r),
                   "--repo-root", str(repo)]) == 2 and not out_r.exists())
    main_branch = subprocess.run(["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"],
                                 capture_output=True, text=True).stdout.strip()
    git(repo, "checkout", "-q", "-b", "side")
    (repo / "g").write_text("x")
    git(repo, "add", "g")
    git(repo, "commit", "-q", "-m", "side")
    git(repo, "tag", "wp5-run-freeze")
    git(repo, "checkout", "-q", main_branch)
    (repo / "f").write_text("1b")
    git(repo, "commit", "-q", "-am", "main moves on")
    check("refuse: freeze tag exists but is not an ancestor of HEAD",
          RA.main(["analyze", "--results-dir", str(inp), "--out-dir", str(root / "o1"),
                   "--repo-root", str(repo)]) == 2)
    git(repo, "tag", "-d", "wp5-run-freeze")
    git(repo, "tag", "wp5-run-freeze")
    (repo / "f").write_text("2")
    git(repo, "commit", "-q", "-am", "later")
    bad = root / "in_bad_hash"
    shutil.copytree(inp, bad)
    (bad / "wp5_tasks.json").write_text((bad / "wp5_tasks.json").read_text() + " ")
    check("refuse: task-list sha256 mismatch", RA.main(["analyze", "--results-dir", str(bad), "--out-dir",
                                                        str(root / "o2"), "--repo-root", str(repo)]) == 2)
    bad2 = root / "in_bad_cfg"
    shutil.copytree(inp, bad2)
    m = json.loads((bad2 / "wp5_run_manifest.json").read_text())
    m["hashes"]["analysis_config"] = "0" * 64
    (bad2 / "wp5_run_manifest.json").write_text(json.dumps(m))
    check("refuse: analysis config differs from frozen hash",
          RA.main(["analyze", "--results-dir", str(bad2), "--out-dir", str(root / "o3"),
                   "--repo-root", str(repo)]) == 2)
    nt = root / "in_nonterminal"
    make_inputs(nt, break_terminal=True)
    write_run_manifest(nt)
    check("refuse: run not in a terminal state (also with --synthetic)",
          RA.main(["analyze", "--results-dir", str(nt), "--out-dir", str(root / "o4"), "--repo-root", str(repo)]) == 2
          and RA.main(["analyze", "--synthetic", "--results-dir", str(nt), "--out-dir", str(root / "o5")]) == 2)
    check("refuse: --synthetic with output under real_v2",
          RA.main(["analyze", "--synthetic", "--results-dir", str(inp), "--out-dir",
                   str(root / "real_v2" / "wp5")]) == 2)
    check("refuse: --n-boot outside synthetic mode",
          RA.main(["analyze", "--results-dir", str(inp), "--out-dir", str(root / "o6"), "--n-boot", "10",
                   "--repo-root", str(repo)]) == 2)

    # --- positive path ---------------------------------------------------------------
    # Frozen runs forbid --n-boot overrides (the config is frozen), so the git + hash checks are
    # exercised through check_refusals and the full analysis through --synthetic.
    RA.logger.setLevel(logging.INFO)
    cfg = RA.load_config(CFG_PATH)
    ledger = {RA.run_key(r): r for r in RA.read_jsonl(inp / "wp5_runs.jsonl")}
    probs = RA.check_refusals(inp, CFG_PATH, cfg, repo, False, list(ledger.values()))
    check("frozen checks pass on a clean synthetic set (tag ancestor, hashes, terminal)", probs == [], str(probs))

    outs = []
    for i in (1, 2):
        o = root / f"out_syn{i}"
        rc = RA.main([*base, "--synthetic", "--out-dir", str(o)])
        check(f"synthetic analysis {i} exits 0", rc == 0)
        outs.append(o)
    names = ["wp5_primary.json", "wp5_secondary.json", "wp5_sensitivity.json", "wp5_exploratory.json",
             "wp5_deviations.json"]
    check("all five outputs written", all((outs[0] / n).exists() for n in names))
    check("outputs byte-identical across two runs", all((outs[0] / n).read_bytes() == (outs[1] / n).read_bytes()
                                                       for n in names))
    prim = json.loads((outs[0] / "wp5_primary.json").read_text())
    sec = json.loads((outs[0] / "wp5_secondary.json").read_text())
    sen = json.loads((outs[0] / "wp5_sensitivity.json").read_text())
    exp = json.loads((outs[0] / "wp5_exploratory.json").read_text())
    check("outputs stamped synthetic", prim["synthetic"] is True and sec["synthetic"] is True)
    check("primary has H1-H3, Holm, verdicts, risk differences",
          set(prim["holm"]["holm_p"]) == {"H1", "H2", "H3"} and prim["verdicts"] is not None
          and "C-A" in prim["risk_difference"], str(prim["holm"]["raw_p"]))
    check("PO became a third H3 level (>= 10 tasks, >= 4 repos)", prim["po_is_h3_level"] is True,
          str(prim["M1_M2"]["H3"]["levels"]))
    ss = prim["M1_M2"]["stage_specific"]
    check("C vs A in SERVICING estimated positive (true OR 2.5)", ss["SERVICING"]["C-A"]["est"] > 0,
          f"OR {ss['SERVICING']['C-A'].get('ratio')}")
    check("C vs A in ACTIVE near null (|log OR| < 0.8)", abs(ss["ACTIVE"]["C-A"]["est"]) < 0.8,
          f"est {ss['ACTIVE']['C-A']['est']}")
    check("estimator-agreement block present", "estimator_sensitive" in prim)
    check("secondary: Y0..Y6 models, bootstrap, within-stage, condition B present",
          all(y in sec["outcome_models"] for y in ["Y0", "Y1", "Y2", "Y3", "Y4", "Y5", "Y6"])
          and "resolved" in sec["bootstrap"] and sec["within_stage"] and sec["condition_B"].get("B-A"))
    check("secondary: Holm descriptive guard over 14 tests", len(sec["holm_descriptive_guard"]) == 14)
    check("sensitivity: SA1-SA8 present, SA9 reports not provided",
          all(any(k.startswith(f"SA{i}_") for k in sen) for i in range(1, 9))
          and sen["SA9_Y3_thresholds"].get("status") == "not provided")
    check("exploratory: condition x model, D vs A, step curves present",
          "condition_x_model" in exp and exp["D_vs_A"] and "step_efficiency_curves" in exp)
    # exploratory-only rule and small-PO rule
    check("po_is_h3_level false for a 9-task PO stratum",
          RA.po_is_h3_level(pd.DataFrame({"task": [f"t{i}" for i in range(9)], "repo": ["r"] * 4 + ["q"] * 5,
                                          "stage": ["PO"] * 9}), cfg) is False)

    # --- power subcommand -----------------------------------------------------------
    (root / "pilot.json").write_text(json.dumps({"p0_hat": 0.3, "model_logor": -0.5}))
    rc = RA.main(["power", "--pilot-summary", str(root / "pilot.json"), "--tasks", str(inp / "wp5_tasks.json"),
                  "--out", str(root / "wp5_power.json"), "--n-rep", "12", "--icc-grid", "0.5",
                  "--or-grid", "2.0,3.0", "--p0-only"])
    pw = json.loads((root / "wp5_power.json").read_text()) if (root / "wp5_power.json").exists() else {}
    check("power subcommand writes wp5_power.json with label and N decision",
          rc == 0 and pw.get("label") in ("POWERED", "UNDER-POWERED", "UNINFORMATIVE")
          and pw["n_decision"]["N"] == 66, str(pw.get("label")))
    check("select_design caps at 80 keeping all PO",
          len(RA.select_design([{"instance_id": f"t{i}", "repo": f"r{i}", "declared_stage":
                                 ["ID", "EVO", "SERV", "PO"][i % 4]} for i in range(120)], 80, 1)) == 80)
    failed = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed (scratch {root})")
    for name, _, detail in failed:
        print(f"FAILED: {name} {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
