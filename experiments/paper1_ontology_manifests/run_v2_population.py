#!/usr/bin/env python3
"""Batch runner for the v2 population pipeline (Paper 1, RQ1/WP3).

Paper 1 rebuild. Runs ``ontology/population/populate_v2.py`` over many
repositories and writes the population JSONs that
``experiments/paper1_ontology_manifests/run_rq1_v2.py`` reads (schema:
``run_rq1_v2.adapt_population_json``): per repo ``measures`` (primary
configuration plus the 48-month left-truncated ``monthly_series``), ``inferred``
keyed by ``a{alpha:g}_L{L}_D{D}_G{G:g}_{orig|hr}`` for the primary and the 11
one-at-a-time sensitivity configurations (S1 alpha 0.01/0.1, S2 L 24/48, S3 D
6/18/24, S4 G 0/0.02/0.1, S5 Hamed-Rao), and ``unmineable`` / ``replaces``.

* Mining and stage A run once per repo (cached under ``~/research/data/rq1_mining``);
  L and the MK variant re-measure from that cache; alpha, D and G need another TBox,
  so each distinct variant TBox is built ONCE per batch (``<output-dir>/_tboxes/``) and
  the ABox is left unchanged. Explanations, Fuseki write-back and the detailed
  record cover the primary configuration only.
* Checkpointing: a repo whose output JSON exists is skipped (delete it to re-run).
  Unmineable repos get a JSON with ``unmineable: true`` and are listed at the end for
  the replacement procedure of the pre-registration (section 4).
* ``<output-dir>/_run_meta.json``: Pellet/HermiT jar hashes, TBox sha256 per
  configuration, LOC instrument description, library versions, git state.
* One process per repo; each reasoner JVM is capped at 2 GB, so keep ``--workers``
  at 2-4. Logs go to ``<output-dir>/run.log``.

Input (``--repos``): the WP3 sample file (JSON object with ``records`` carrying
``repo``), a JSON list of ``owner/name`` strings or of objects with ``repo`` (and
optionally ``replaces``), or a text file with one ``owner/name`` per line. The
snapshot date is ``--snapshot-date`` or the ``snapshot_date`` of
``configs/wp3_ground_truth.yaml`` (2025-06-30).

Usage:
    python experiments/paper1_ontology_manifests/run_v2_population.py \\
        --repos experiments/paper1_ontology_manifests/results/real_v2/wp3/ground_truth_sample.json \\
        --output-dir experiments/paper1_ontology_manifests/results/real_v2/population --workers 2
    python experiments/paper1_ontology_manifests/run_v2_population.py --repo owner/name \\
        --output-dir /tmp/out --no-fuseki --no-explain --no-sensitivity
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ontology.population import populate_v2 as P  # noqa: E402

logger = logging.getLogger("senso.run_v2_population")
WP3_CONFIG = PROJECT_ROOT / "experiments" / "paper1_ontology_manifests" / "configs" / "wp3_ground_truth.yaml"
MAX_WORKERS = 4


def config_snapshot_date() -> str:
    """``snapshot_date`` from the WP3 config (fallback 2025-06-30)."""
    try:
        import yaml

        return str(yaml.safe_load(WP3_CONFIG.read_text())["snapshot_date"])
    except Exception:
        return "2025-06-30"


def load_repos(path: Path) -> tuple[list[str], Optional[str], dict[str, str]]:
    """Read repo names, an embedded snapshot date (if any) and ``replaces`` links from a repo list file."""
    text = path.read_text()
    try:
        d: Any = json.loads(text)
    except json.JSONDecodeError:
        return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("#")], None, {}
    snap = None
    if isinstance(d, dict):
        snap = d.get("snapshot_date")
        d = d.get("records", d.get("repos", []))
    repos, replaces = [], {}
    for x in d:
        r = x if isinstance(x, str) else x.get("repo")
        if r:
            repos.append(r)
            if not isinstance(x, str) and x.get("replaces"):
                replaces[r] = x["replaces"]
    return list(dict.fromkeys(repos)), snap, replaces


def _work(repo: str, snapshot: str, out_dir: str, opts: dict[str, Any]) -> dict[str, Any]:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        res = P.populate_repo(repo, P.parse_snapshot(snapshot), Path(out_dir), **opts)
    except Exception as exc:
        logger.exception("repo %s failed", repo)
        res = {"repo": repo, "status": "error", "error": f"{type(exc).__name__}: {exc}"[:800]}
        P._write(Path(out_dir) / f"_error_{P.safe_name(repo)}.json", res)
    return res


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_meta(snapshot: str, configs: list[dict[str, Any]], tboxes: dict[str, Optional[Path]],
             opts: dict[str, Any]) -> dict[str, Any]:
    """Provenance for ``_run_meta.json``: jar hashes, TBox sha256 per configuration, LOC tool, git state."""
    import owlready2

    from ontology.reasoning.reasoner import MODULES_DIR, STAGE_A_MODULES, STAGE_B_MODULES

    base = Path(owlready2.__file__).parent
    jars = {f"{sub}/{j.name}": _sha256(j) for sub in ("pellet", "hermit")
            for j in sorted((base / sub).glob("*.jar"))}

    def tbox_sha(d: Optional[Path], modules: list[str]) -> str:
        h = hashlib.sha256()
        for m in modules:
            h.update(((d or MODULES_DIR) / f"{m}.owl").read_bytes())
        return h.hexdigest()

    def git(*a: str) -> str:
        return subprocess.run(["git", *a], cwd=PROJECT_ROOT, capture_output=True, text=True).stdout.strip()

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "snapshot_date": snapshot,
        "primary_config": P.cfg_id(**P.PRIMARY),
        "configs": [P.cfg_id(**c) for c in configs],
        "tbox_sha256_by_config": {P.cfg_id(**c): tbox_sha(tboxes[P.tbox_key(c)], STAGE_B_MODULES)
                                  for c in configs},
        "tbox_sha256_stage_a": tbox_sha(None, STAGE_A_MODULES),
        "jar_sha256": jars,
        "reasoners": {"stage_a": "Pellet 2.3.1 (Owlready2 bundle)", "stage_b": "HermiT (Owlready2 bundle)"},
        "loc_tool": {"instrument": P.LOC_INSTRUMENT, "first_parent": True, "max_blob_bytes": P.MAX_BLOB_BYTES,
                     "extensions": sorted(P.SOURCE_EXTENSIONS), "excluded_dirs": list(P.EXCLUDED_DIRS),
                     "git": P.git_version(), "complexity": opts["complexity"]},
        "mining_months": P.MINING_MONTHS,
        "versions": P._lib_versions(),
        "git_commit": git("rev-parse", "HEAD"),
        "git_dirty_ontology_experiments": bool(git("status", "--porcelain", "--", "ontology",
                                                   "experiments/paper1_ontology_manifests")),
        "options": {k: str(v) for k, v in opts.items()},
    }


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description="Batch v2 population (Paper 1)")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--repos", type=Path, help="WP3 sample JSON, JSON list or text file")
    src.add_argument("--repo", action="append", help="owner/name (repeatable)")
    ap.add_argument("--snapshot-date", default=None, help="default: WP3 config snapshot_date")
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=2, help=f"parallel repos (max {MAX_WORKERS})")
    ap.add_argument("--limit", type=int, default=None, help="only the first N repos")
    ap.add_argument("--log-file", type=Path, default=None, help="default: <output-dir>/run.log")
    P.add_common_args(ap)
    a = ap.parse_args()

    out_dir: Path = a.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    log_file = a.log_file or out_dir / "run.log"
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                        handlers=[logging.FileHandler(log_file), logging.StreamHandler()])
    repos, embedded, replaces = (load_repos(a.repos) if a.repos else (list(dict.fromkeys(a.repo)), None, {}))
    snapshot = a.snapshot_date or config_snapshot_date()
    if embedded and embedded != snapshot:
        logger.warning("input file snapshot_date %s differs from the date in use %s", embedded, snapshot)
    if a.limit:
        repos = repos[: a.limit]
    opts = P.options_from_args(a)
    workers = max(1, min(a.workers, MAX_WORKERS))
    todo = [r for r in repos if not P.result_path(out_dir, r).exists()]
    logger.info("%d repos, %d to do (%d checkpointed), snapshot %s, workers %d, dataset %s, %s",
                len(repos), len(todo), len(repos) - len(todo), snapshot, workers,
                opts["dataset"] if opts["fuseki_url"] else "none",
                "12 configs" if opts["sensitivity"] else "primary config only")
    P.check_primary_matches_register()
    configs = P.config_list(opts["sensitivity"])
    tboxes = P.build_tboxes(out_dir / "_tboxes", configs)  # once per batch, before the workers start
    meta = run_meta(snapshot, configs, tboxes, opts)
    (out_dir / "_run_meta.json").write_text(json.dumps(meta, indent=1))
    opts["tboxes"] = tboxes
    if opts["fuseki_url"] and todo:
        P.ensure_dataset(opts["fuseki_url"], opts["dataset"])  # once, before workers race to create it
    t0 = time.perf_counter()
    done = failed = 0
    unmineable: list[str] = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_work, r, snapshot, str(out_dir), {**opts, "replaces": replaces.get(r)}): r
                for r in todo}
        for f in as_completed(futs):
            r = futs[f]
            res = f.result()
            done += 1
            failed += res.get("status") not in ("ok", "unmineable")
            if res.get("status") == "unmineable":
                unmineable.append(f"{r} ({res.get('unmineable_reason')})")
            s = res.get("summary") or {}
            logger.info("[%d/%d] %s status=%s C1=%s C2=%s CF=%s t_total=%s", done, len(todo), r,
                        res.get("status"), s.get("c1"), s.get("c2"), s.get("cf"),
                        (res.get("timings") or {}).get("t_total"))
    if unmineable:
        logger.warning("UNMINEABLE (replace per pre-registration section 4): %s", "; ".join(unmineable))
    logger.info("finished %d repos (%d failed) in %.0f s", done, failed, time.perf_counter() - t0)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
