#!/usr/bin/env python3
"""Check that the RQ1 (snapshot-date) mode of populate_v2.py is unchanged by the WP5 extension.

Paper 1 (WP5, wp5-analysis-plan.md 3.1; RQ1 outputs must not move). Runs
``populate_repo`` in the RQ1 mode for one repository into a scratch directory with a FRESH
mining cache, then compares

  * the per-repo JSON against a golden JSON made with the pre-WP5 code, and
  * the decompressed mining-cache entry against the golden one,

after dropping the keys that legitimately differ between runs or TBoxes: timings, library
versions, TBox hashes (the extended TBox has other module files; the labels must not
change), the explanation graph IRI (it contains the TBox hash) and per-call explain seconds.
Everything else (measures, series, ABox triple counts, inferred classes, stage and law
labels, explanations' justifications, cache keys) must be equal.

Usage:
    python ontology/population/check_rq1_mode_unchanged.py --repo jazzband/tablib \\
        --snapshot-date 2023-06-30 --golden-dir <dir with <repo>.json> --golden-cache <mining dir> \\
        --cache-dir <clone cache> --work-dir <scratch> [--no-explain]
"""

from __future__ import annotations

import argparse
import gzip
import json
import logging
import shutil
import sys
from datetime import date
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ontology.population import populate_v2 as P  # noqa: E402

logger = logging.getLogger("senso.check_rq1_mode")

VOLATILE = frozenset({
    "timings", "versions", "tbox_sha256", "tbox_sha256_stage_a", "tbox_sha256_stage_b", "explanation_graph",
    "seconds", "chunk_timings", "cached", "dataset", "blobs_fetched", "blobs_fetched_churn"})
"""Keys that differ between runs (clone-cache state, timings, TBox hashes); ``t_*`` keys are timings too."""


def _canon_explanations(expl: dict) -> dict:
    """Pellet prints the axioms of a justification in a run-dependent order: compare them as sorted sets."""
    out = {}
    for tag, e in expl.items():
        if isinstance(e, dict) and "justifications" in e:
            js = [{"axioms": sorted(a["text"] for a in j["axioms"]), "facts": sorted(f["raw"] for f in j["facts"]),
                   "closures": sorted(j["closures"])} for j in e["justifications"]]
            out[tag] = {**normalise({k: v for k, v in e.items() if k not in ("justifications", "raw_text")}),
                        "justifications": js}
        else:
            out[tag] = normalise(e)
    return out


def normalise(x: Any) -> Any:
    """Drop volatile keys recursively."""
    if isinstance(x, dict):
        return {k: (_canon_explanations(v) if k == "explanations" and isinstance(v, dict) else normalise(v))
                for k, v in x.items() if k not in VOLATILE and not k.startswith("t_")}
    if isinstance(x, list):
        return [normalise(v) for v in x]
    return x


def diff(a: Any, b: Any, path: str = "") -> list[str]:
    """Paths at which two normalised JSON values differ."""
    if type(a) is not type(b):
        return [f"{path}: type {type(a).__name__} != {type(b).__name__}"]
    if isinstance(a, dict):
        out = [f"{path}/{k}: only in golden" for k in a.keys() - b.keys()]
        out += [f"{path}/{k}: only in new" for k in b.keys() - a.keys()]
        for k in sorted(a.keys() & b.keys()):
            out += diff(a[k], b[k], f"{path}/{k}")
        return out
    if isinstance(a, list):
        if len(a) != len(b):
            return [f"{path}: length {len(a)} != {len(b)}"]
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in diff(x, y, f"{path}[{i}]")]
    return [] if a == b else [f"{path}: {a!r} != {b!r}"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", required=True)
    ap.add_argument("--snapshot-date", required=True)
    ap.add_argument("--golden-dir", type=Path, required=True)
    ap.add_argument("--golden-cache", type=Path, required=True)
    ap.add_argument("--cache-dir", type=Path, required=True)
    ap.add_argument("--work-dir", type=Path, required=True)
    ap.add_argument("--no-explain", action="store_true")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    shutil.rmtree(a.work_dir, ignore_errors=True)
    P.populate_repo(a.repo, date.fromisoformat(a.snapshot_date), a.work_dir / "out", sensitivity=False,
                    cache_dir=a.cache_dir, mining_cache=a.work_dir / "mining", fuseki_url=None,
                    explain=not a.no_explain)
    name = f"{P.safe_name(a.repo)}.json"
    new = normalise(json.loads((a.work_dir / "out" / name).read_text()))
    gold = normalise(json.loads((a.golden_dir / name).read_text()))
    problems = diff(gold, new)
    for f in sorted((a.work_dir / "mining").glob("*.json.gz")):
        g = a.golden_cache / f.name
        if not g.exists():
            problems.append(f"mining cache file name {f.name} not in golden cache (key changed)")
            continue
        problems += diff(normalise(json.loads(gzip.decompress(g.read_bytes()))),
                         normalise(json.loads(gzip.decompress(f.read_bytes()))), f"cache:{f.name}")
    for p in problems[:50]:
        logger.error("DIFF %s", p)
    print("RQ1 mode unchanged" if not problems else f"{len(problems)} difference(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
