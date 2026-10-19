"""WP6 (Study B: do wrong manifests hurt agents?) CLI (Paper 1 JSEP rebuild).

Used by Paper 1 (WP6); design papers/paper1/wp6-harm-design.md, deviations papers/paper1/wp6-deviations-log.md.
Subcommands, each checkpointed and re-runnable. Run with the WP5 run venv (datasets, mini-swe-agent, litellm) except
`verify-hermit`, which starts the project venv itself (owlready2 + Java).

    generate               mechanical manifests T / F_R / F_I per task + pre-HermiT gate (re-check, runtime probes)
    verify-hermit          instrument 1 (RQ2 checker, HermiT) over the generated ABoxes
    finalize-verification  join the three instruments: wp6_verification.json, wp6_manifests_index.json
    pip-carryover          count WP5 runs that installed packages (WP5 deviation 14) -> wp5_pip_carryover.json
    run                    task x condition x model x replicate with a venv reset before every run
    outcomes               trajectory parser (Y1..Y8) + ledgers

Usage:
    PY=/home/adtgrade/research/wp5_feasibility/.venv/bin/python
    $PY experiments/paper1_ontology_manifests/run_wp6.py generate [--ids ID ...] [--dev] [--pilot]
    $PY experiments/paper1_ontology_manifests/run_wp6.py verify-hermit [--pilot]
    $PY experiments/paper1_ontology_manifests/run_wp6.py finalize-verification [--pilot]
    $PY experiments/paper1_ontology_manifests/run_wp6.py pip-carryover
    $PY experiments/paper1_ontology_manifests/run_wp6.py run --pilot --ids ID ID --replicates 1
    $PY experiments/paper1_ontology_manifests/run_wp6.py outcomes --pilot
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from experiments.paper1_ontology_manifests.wp6 import common  # noqa: E402

logger = logging.getLogger("wp6")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(common.DEFAULT_CONFIG))
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("generate")
    p.add_argument("--ids", nargs="*", default=None)
    p.add_argument("--dev", action="store_true", help="the WP5 development tasks (never in the sample)")
    p.add_argument("--pilot", action="store_true", help="write under the pilot directory")
    p.add_argument("--workers", type=int, default=None)
    p.add_argument("--force", action="store_true")
    for name in ("verify-hermit", "finalize-verification"):
        p = sub.add_parser(name)
        p.add_argument("--pilot", action="store_true")
        if name == "finalize-verification":
            p.add_argument("--reject-failures", action="store_true",
                           help="record failing candidates in wp6_rejects.json; then rerun `generate --force --ids ...` for them")
    sub.add_parser("pip-carryover")

    p = sub.add_parser("run")
    p.add_argument("--pilot", action="store_true", help="use the pilot directory (manifests, units, trajectories)")
    p.add_argument("--ids", nargs="*", default=None, help="task ids (default: the 80 WP5 tasks)")
    p.add_argument("--conditions", nargs="*", default=None)
    p.add_argument("--replicates", type=int, default=None)
    p.add_argument("--models", nargs="*", default=None, help="substring filter on model names")
    p.add_argument("--workers", type=int, default=None)

    p = sub.add_parser("outcomes")
    p.add_argument("--pilot", action="store_true")

    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    for noisy in ("LiteLLM", "litellm", "httpx", "httpcore", "agent", "litellm_model", "urllib3", "datasets"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    cfg = common.load_config(args.config)

    if args.cmd == "generate":
        from experiments.paper1_ontology_manifests.wp6 import generate
        generate.generate(cfg, ids=args.ids, pilot=args.pilot, dev=args.dev, workers=args.workers, force=args.force)
    elif args.cmd == "verify-hermit":
        from experiments.paper1_ontology_manifests.wp6 import verify
        out = common.out_dir(cfg, args.pilot)
        p = verify.run_hermit(cfg, out / "verification" / "abox", out / "verification" / "hermit")
        sys.stderr.write(p.stderr[-3000:])
        return p.returncode
    elif args.cmd == "finalize-verification":
        from experiments.paper1_ontology_manifests.wp6 import generate
        s = generate.finalize(cfg, pilot=args.pilot, reject_failures=args.reject_failures)
        if s.get('rejected_and_to_regenerate'):
            logger.warning('regenerate with --force --ids: %s', ' '.join(s['rejected_and_to_regenerate']))
        return 0 if s["n_claims_failing"] == 0 else 1
    elif args.cmd == "pip-carryover":
        from experiments.paper1_ontology_manifests.wp6 import outcomes
        outcomes.pip_carryover(cfg)
    elif args.cmd == "run":
        from experiments.paper1_ontology_manifests.wp6 import runner
        runner.run_all(cfg, pilot=args.pilot, ids=args.ids, conditions_=args.conditions, replicates=args.replicates,
                       models=args.models, workers=args.workers)
    elif args.cmd == "outcomes":
        from experiments.paper1_ontology_manifests.wp6 import outcomes
        outcomes.write_outcomes(cfg, pilot=args.pilot)
    return 0


if __name__ == "__main__":
    sys.exit(main())
