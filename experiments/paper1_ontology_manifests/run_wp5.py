"""WP5 execution-based agent evaluation CLI (Paper 1 JSEP rebuild).

Used by Paper 1 (WP5). Subcommands, each checkpointed and re-runnable:
    build-pool  SWE-rebench Python tasks -> PyPI package -> declared stage at base date -> pool.json
    validate    per-task env + FAIL_TO_PASS / PASS_TO_PASS check (human-free validator)
    dev-pool    development tasks that can never be in the sample (plan 2.1)
    populate    per-task population JSON (populate_v2.py --snapshot-commit ... --no-fuseki)
    manifests   B, C, D manifests (manifests/generator/wp5_manifests.py, deterministic, no LLM)
    tasks       wp5_tasks.json from the validated pool;   manifest: wp5_run_manifest.json
    run         task x condition x model x run, checkpoint per unit, ledgers wp5_runs.jsonl / wp5_outcomes.jsonl
    evaluate    measured outcomes (no LLM judging)
    report      pilot summary

Run with a Python that has datasets, mini-swe-agent, litellm, lizard (the wp5 venv):

Usage:
    PY=/home/adtgrade/research/wp5_feasibility/.venv/bin/python
    $PY experiments/paper1_ontology_manifests/run_wp5.py build-pool
    $PY experiments/paper1_ontology_manifests/run_wp5.py validate [--limit N] [--stage S]
    $PY experiments/paper1_ontology_manifests/run_wp5.py run --pilot
    $PY experiments/paper1_ontology_manifests/run_wp5.py evaluate --pilot
    $PY experiments/paper1_ontology_manifests/run_wp5.py report --pilot
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from experiments.paper1_ontology_manifests.wp5 import common  # noqa: E402

logger = logging.getLogger("wp5")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(common.DEFAULT_CONFIG))
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("build-pool")
    p.add_argument("--limit-repos", type=int, default=None, help="debug: first N repos only")

    p = sub.add_parser("validate")
    p.add_argument("--limit", type=int, default=None, help="max tasks to validate in this call")
    p.add_argument("--stage", default=None, help="only this stage")
    p.add_argument("--workers", type=int, default=None)
    p.add_argument("--keep-env", action="store_true", help="keep venv/workdir after validation")
    p.add_argument("--ids", nargs="*", default=None, help="validate exactly these instance ids")
    p.add_argument("--dev", action="store_true", help="validate the development set (dev_pool.json)")

    sub.add_parser("dev-pool", help="select the development tasks (never in the sample)")
    p = sub.add_parser("populate", help="per-task population (populate_v2.py --snapshot-commit)")
    p.add_argument("--ids", nargs="+", required=True)
    p = sub.add_parser("manifests", help="B, C, D manifests via manifests/generator/wp5_manifests.py")
    p.add_argument("--ids", nargs="*", default=None, help="default: every task in wp5_tasks.json")
    p = sub.add_parser("tasks", help="write wp5_tasks.json from the validation checkpoints")
    p.add_argument("--ids", nargs="*", default=None)
    p = sub.add_parser("freeze-tasks", help="freeze wp5_tasks.json (plan 7.4 rule 1)")
    p.add_argument("--replace", nargs="*", default=[], metavar="OLD=NEW", help="replace tasks whose population failed")
    p = sub.add_parser("drift", help="gold-patch drift check after all runs (plan 5; SA5)")
    p.add_argument("--workers", type=int, default=None)
    p.add_argument("--ids", nargs="*", default=None, help="re-check only these tasks (merged into the earlier result)")
    sub.add_parser("sa9", help="Y3 under module-threshold variants -> wp5_outcomes_sa9.jsonl (plan 9, SA9)")
    sub.add_parser("manifest", help="write wp5_run_manifest.json (hashes, versions)")

    p = sub.add_parser("run")
    p.add_argument("--pilot", action="store_true", help="use the pilot task selection and pilot_dir")
    p.add_argument("--tasks", default=None, help="JSON list of task ids (default: validated pool)")
    p.add_argument("--conditions", nargs="*", default=None)
    p.add_argument("--runs", type=int, default=None)
    p.add_argument("--models", nargs="*", default=None, help="substring filter on model names")
    p.add_argument("--workers", type=int, default=None)
    p.add_argument("--select-only", action="store_true", help="only write the pilot task selection")
    p.add_argument("--max-tokens", type=int, default=None, help="override agent max_tokens (supplementary pilots)")
    p.add_argument("--tag", default=None, help="write to wp5_pilot_<tag> instead of wp5_pilot (supplementary pilots)")

    p = sub.add_parser("evaluate")
    p.add_argument("--pilot", action="store_true")
    p.add_argument("--tag", default=None)
    p.add_argument("--workers", type=int, default=None)

    p = sub.add_parser("report")
    p.add_argument("--pilot", action="store_true")
    p.add_argument("--tag", default=None)

    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    for noisy in ("LiteLLM", "litellm", "httpx", "httpcore", "agent", "litellm_model", "urllib3", "datasets"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    cfg = common.load_config(args.config)
    if getattr(args, "tag", None):
        cfg["pilot_dir"] = cfg["pilot_dir"] + ("" if args.tag.isdigit() else "_") + args.tag
    if getattr(args, "max_tokens", None):
        cfg["agent"]["max_tokens"] = args.max_tokens

    if args.cmd == "build-pool":
        from experiments.paper1_ontology_manifests.wp5 import pool
        pool.build_pool(cfg, args.limit_repos)
    elif args.cmd == "validate":
        from experiments.paper1_ontology_manifests.wp5 import validate
        validate.validate_pool(cfg, limit=args.limit, stage=args.stage, workers=args.workers,
                               keep_env=args.keep_env, ids=args.ids, dev=args.dev)
    elif args.cmd == "freeze-tasks":
        from experiments.paper1_ontology_manifests.wp5 import freeze
        freeze.freeze_tasks(cfg, replace=dict(x.split('=', 1) for x in args.replace))
    elif args.cmd in ("dev-pool", "populate", "manifests", "tasks", "manifest"):
        from experiments.paper1_ontology_manifests.wp5 import ledgers
        if args.cmd == "dev-pool":
            ledgers.build_dev_pool(cfg)
        elif args.cmd == "populate":
            ledgers.populate_tasks(cfg, args.ids)
        elif args.cmd == "manifests":
            ledgers.generate_manifests(cfg, args.ids)
        elif args.cmd == "tasks":
            ledgers.write_tasks(cfg, args.ids)
        else:
            ledgers.write_run_manifest(cfg)
    elif args.cmd == "run":
        from experiments.paper1_ontology_manifests.wp5 import runner
        runner.run_all(cfg, pilot=args.pilot, tasks_file=args.tasks, conditions_=args.conditions,
                       runs=args.runs, models=args.models, workers=args.workers,
                       select_only=args.select_only)
    elif args.cmd == "evaluate":
        from experiments.paper1_ontology_manifests.wp5 import evaluate
        evaluate.evaluate_all(cfg, pilot=args.pilot, workers=args.workers)
    elif args.cmd == "drift":
        from experiments.paper1_ontology_manifests.wp5 import evaluate
        evaluate.gold_drift(cfg, workers=args.workers, ids=args.ids)
    elif args.cmd == "sa9":
        from experiments.paper1_ontology_manifests.wp5 import sa9
        sa9.run_sa9(cfg)
    elif args.cmd == "report":
        from experiments.paper1_ontology_manifests.wp5 import report
        report.make_report(cfg, pilot=args.pilot)
    return 0


if __name__ == "__main__":
    sys.exit(main())
