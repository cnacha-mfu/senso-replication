"""WP2 optional step: do the two slow NIM models change the consensus? (Paper 1, RQ2; design section 5.1).

Runs the two slow panel models (meta/llama-3.2-90b-vision-instruct, z-ai/glm-5.3; 98-217 s per call) on 20
random chunks (seeded), validates their claims with the same mechanical pipeline, and compares the
3-model consensus (>= 2 of 3) on those chunks with a 5-model consensus (>= 3 of 5): Jaccard overlap of the
claim-key sets and per-model F1 against the 3-model consensus. NIM only; 40 calls.

Usage:
    python experiments/paper1_ontology_manifests/wp2_consistency.py robustness
"""

from __future__ import annotations

import logging
import random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Optional

from . import common as C
from . import extract as X
from . import normalize as N
from .consensus import final_panel

logger = logging.getLogger("wp2.robustness")
SLOW = ["meta/llama-3.2-90b-vision-instruct", "z-ai/glm-5.3"]


def _keys(cfg: dict[str, Any], res: Path, repo_entry: dict[str, Any], ch: dict[str, Any], model: str, raw_dir: Path) -> set[str]:
    p = raw_dir / repo_entry["slug"] / f"{ch['idx']:03d}.{C.model_slug(model)}.json"
    if not p.exists():
        return set()
    rec = C.read_json(p)
    if not rec.get("parse_ok"):
        return set()
    items, _ = X.parse_response(rec["text"])
    good, _bad = X.validate_claims(items or [])
    out = set()
    for raw in good:
        acc, _ = N.process_claim(raw, ch, repo_entry.get("manifest_path") or "CLAUDE.md", cfg, repair=True,
                                 repo_name=repo_entry["full_name"].split("/")[-1])
        out |= {a["key_str"] for a in acc if a["mode"] == "asserts_existing"}
    return out


def run(cfg: dict[str, Any], only: Optional[str] = None, force: bool = False) -> int:
    res = C.results_dir(cfg)
    panel = final_panel(cfg, res)
    ex = cfg["extraction"]
    system = (C.PROJECT_ROOT / ex["prompt_file"]).read_text(encoding="utf-8")
    prompt_sha = C.sha256_text(system)
    jobs = X.build_jobs(cfg)
    rng = random.Random(cfg["seeds"]["sample"] + 1)
    chosen = rng.sample(jobs, 20)
    rcfg = {**cfg, "extraction": {**ex, "timeout_s": 420, "attempts": 2, "max_parse_retries": 1}}
    callers = X.make_callers(rcfg, SLOW)
    raw_dir = res / "extraction" / "robustness" / "raw"

    def do(caller: X.ModelCaller, job: dict[str, Any]) -> None:
        p = raw_dir / job["slug"] / f"{job['chunk']['idx']:03d}.{C.model_slug(caller.model)}.json"
        if p.exists() and not force:
            return
        r = caller.extract(system, job["user"])
        last = r["attempts"][-1]
        C.write_json(p, {"repo": job["repo"], "chunk": job["chunk"]["idx"], "model": caller.model, "prompt_sha256": prompt_sha,
                         "text": last["text"], "parse_ok": r["parse_ok"], "parse_error": r["parse_error"],
                         "latency_s": sum(a["latency_s"] for a in r["attempts"]), "usage": last.get("usage"),
                         "error": last.get("error")})
        logger.info("%s chunk %s/%d done (parse_ok=%s)", caller.model, job["repo"], job["chunk"]["idx"], r["parse_ok"])

    pools = {m: ThreadPoolExecutor(max_workers=1) for m in SLOW}
    futs = [pools[m].submit(do, callers[m], j) for j in chosen for m in SLOW]
    for f in futs:
        f.result()
    for p in pools.values():
        p.shutdown()

    corpus = {e["full_name"]: e for e in C.load_corpus(cfg)}
    set3: set[tuple[str, int, str]] = set()
    set5: set[tuple[str, int, str]] = set()
    per_model: dict[str, set[tuple[str, int, str]]] = {m: set() for m in panel + SLOW}
    for j in chosen:
        e, ch = corpus[j["repo"]], j["chunk"]
        snap = res / "snapshots" / f"{e['slug']}.json"
        if snap.exists() and C.read_json(snap).get("manifest_path"):
            e = {**e, "manifest_path": C.read_json(snap)["manifest_path"]}
        ks: dict[str, set[str]] = {}
        for m in panel:
            ks[m] = _keys(cfg, res, e, ch, m, res / "extraction" / "raw")
        for m in SLOW:
            ks[m] = _keys(cfg, res, e, ch, m, raw_dir)
        from collections import Counter
        c3 = Counter(k for m in panel for k in ks[m])
        c5 = Counter(k for m in panel + SLOW for k in ks[m])
        for k, n in c3.items():
            if n >= 2:
                set3.add((j["repo"], ch["idx"], k))
        for k, n in c5.items():
            if n >= 3:
                set5.add((j["repo"], ch["idx"], k))
        for m in panel + SLOW:
            per_model[m] |= {(j["repo"], ch["idx"], k) for k in ks[m]}
    inter = len(set3 & set5)
    union = len(set3 | set5)

    def f1(a: set, b: set) -> float:
        return 2 * len(a & b) / (len(a) + len(b)) if (a or b) else float("nan")

    out = {"n_chunks": len(chosen), "models_added": SLOW, "consensus_3_ge2": len(set3), "consensus_5_ge3": len(set5),
           "intersection": inter, "jaccard": inter / union if union else float("nan"),
           "only_in_3model": len(set3 - set5), "only_in_5model": len(set5 - set3),
           "f1_vs_3model_consensus": {m: f1(per_model[m], set3) for m in panel + SLOW},
           "claims_per_model": {m: len(per_model[m]) for m in panel + SLOW},
           "note": "Optional robustness run (design 5.1): the slow models were not part of the panel because of 98-217 s latency."}
    C.write_json(res / "robustness.json", out)
    logger.info("robustness: %s", out)
    return 0
