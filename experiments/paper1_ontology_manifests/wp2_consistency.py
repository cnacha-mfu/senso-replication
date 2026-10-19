"""WP2 driver: documentation-history consistency checking (Paper 1, RQ2).

Subcommands follow papers/paper1/wp2-design.md section 8. Each step checkpoints
its output under results/real_v2/wp2/ and skips work whose inputs are unchanged.
No LLM is called except in ``extract`` (NIM, via shared/llm_judge/nim_registry).

Usage:
    python experiments/paper1_ontology_manifests/wp2_consistency.py selftest
    python experiments/paper1_ontology_manifests/wp2_consistency.py snapshot
    python experiments/paper1_ontology_manifests/wp2_consistency.py extract --workers nemotron-3-super-120b-a12b=1,gpt-oss-20b=2,diffusiongemma-26b-a4b-it=1
    python experiments/paper1_ontology_manifests/wp2_consistency.py consensus|measure|reason|explain|recheck|triangulate|drift|sensitivity|report
    python experiments/paper1_ontology_manifests/wp2_consistency.py persist --stage verify|fetch|run   # WP2b
    python experiments/paper1_ontology_manifests/wp2_consistency.py persist_report                        # WP2b
"""

from __future__ import annotations

import argparse
import importlib
import logging
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
for p in (str(HERE), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from wp2 import common as C  # noqa: E402

logger = logging.getLogger("wp2")


def _workers(s: str | None) -> dict[str, int]:
    out: dict[str, int] = {}
    for part in (s or "").split(","):
        if "=" in part:
            k, v = part.split("=")
            out[k.strip()] = int(v)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="WP2 consistency checking (Paper 1, RQ2)")
    ap.add_argument("cmd", choices=["selftest", "snapshot", "extract", "consensus", "measure", "reason",
                                    "explain", "recheck", "triangulate", "drift", "sensitivity", "report", "robustness", "persist", "persist_report"])
    ap.add_argument("--config", default=None, help="config YAML (default: configs/wp2_consistency.yaml); "
                    "use scripts/make_check_config.py to build one for your own repository")
    ap.add_argument("--limit-repos", type=int, default=None)
    ap.add_argument("--workers", default=None, help="model-slug=n,... concurrent requests per model")
    ap.add_argument("--only", default=None, help="restrict to one repo (owner/name)")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--engine", default="hermit", choices=["hermit", "pellet"], help="reason: HermiT (primary) or Pellet")
    ap.add_argument("--stage", default="run", choices=["verify", "fetch", "run"], help="persist: WP2b stage")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    C.load_env()
    if a.config:
        C.set_config_path(Path(a.config))
    cfg = C.load_config()
    if a.cmd == "selftest":
        return importlib.import_module("wp2.selftest").run()
    if a.cmd == "snapshot":
        mod = importlib.import_module("wp2.snapshot")
        mod.run_all(cfg, only=a.only)
        return 0
    if a.cmd == "extract":
        mod = importlib.import_module("wp2.extract")
        res = mod.run_extraction(cfg, limit_repos=a.limit_repos, workers=_workers(a.workers))
        logger.info("extraction finished: %s", res["panel"])
        return 0
    mod = importlib.import_module(f"wp2.step_{a.cmd}")
    kw = {"engine": a.engine} if a.cmd == "reason" else {"stage": a.stage} if a.cmd == "persist" else {}
    return int(mod.run(cfg, only=a.only, force=a.force, **kw) or 0)


if __name__ == "__main__":
    sys.exit(main())
