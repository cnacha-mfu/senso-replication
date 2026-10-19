"""Build the WP2c sample of fresh repositories (Paper 1, JSEP; design papers/paper1/wp2c-fresh-check-design.md).

GitHub code search (filename CLAUDE.md / AGENTS.md at the repository root), then the design's eligibility filter,
ordered by full name and shuffled with seed 20261019. Writes raw candidates and the eligible list.

Usage:
    python experiments/paper1_ontology_manifests/scripts/wp2c_sample.py [--out results/real_v2/wp2c]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
HERE = PROJECT_ROOT / "experiments" / "paper1_ontology_manifests"
logger = logging.getLogger("wp2c_sample")
GH = "https://api.github.com"
SEED = 20261019
PUSHED_MIN = "2026-07-01T00:00:00Z"


def get(s: requests.Session, url: str, params: dict | None = None):
    for _ in range(6):
        r = s.get(url, params=params, timeout=60)
        if r.status_code in (403, 429):
            wait = int(r.headers.get("Retry-After") or max(5, int(r.headers.get("X-RateLimit-Reset", time.time() + 60)) - time.time() + 2))
            logger.info("rate limited, sleeping %ss", min(wait, 120))
            time.sleep(min(wait, 120))
            continue
        if r.status_code >= 500:
            time.sleep(5)
            continue
        return r
    return r


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "results/real_v2/wp2c"))
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    load_dotenv(PROJECT_ROOT / ".env")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}", "Accept": "application/vnd.github+json", "User-Agent": "senso-wp2c"})
    cands: dict[str, dict] = {}
    for fn in ("CLAUDE.md", "AGENTS.md"):
        for page in range(1, 11):
            r = get(s, f"{GH}/search/code", {"q": f"filename:{fn} path:/", "per_page": 100, "page": page})
            if r.status_code != 200:
                logger.warning("search %s page %d: %s %s", fn, page, r.status_code, r.text[:100])
                break
            items = r.json().get("items", [])
            for it in items:
                if it["path"] != fn:
                    continue
                c = cands.setdefault(it["repository"]["full_name"], {"full_name": it["repository"]["full_name"], "files": []})
                if fn not in c["files"]:
                    c["files"].append(fn)
            logger.info("%s page %d: %d items, %d repos", fn, page, len(items), len(cands))
            if len(items) < 100:
                break
            time.sleep(7)
    excl = {p.stem.replace("__", "/", 1) for p in (HERE / "results/real_v2/wp2/snapshots").glob("*.json")}
    excl |= {p.name.replace("__", "/", 1) for p in Path("/home/adtgrade/research/data/senso_check").iterdir() if p.is_dir() and "__" in p.name}
    excl |= {"stefanbschneider/mobile-env", "jvkersch/tmtools", "kantord/headson", "HassanZahirnia/laravel-package-ocean"}
    exl = {e.lower() for e in excl}
    rows, elig = [], []
    for name in sorted(cands):
        c = cands[name]
        c["excluded_rq2_or_dev"] = name.lower() in exl
        r = get(s, f"{GH}/repos/{name}")
        if r.status_code != 200:
            c["why_not"] = f"repo_api_{r.status_code}"
            rows.append(c)
            continue
        m = r.json()
        c.update(private=m["private"], fork=m["fork"], archived=m["archived"], stars=m["stargazers_count"], pushed_at=m["pushed_at"],
                 size_kb=m["size"], default_branch=m["default_branch"])
        why = None
        if c["excluded_rq2_or_dev"]:
            why = "rq2_or_dev"
        elif m["private"] or m["fork"] or m["archived"]:
            why = "private_fork_or_archived"
        elif m["stargazers_count"] < 20:
            why = "stars_lt_20"
        elif m["pushed_at"] < PUSHED_MIN:
            why = "pushed_before_2026-07-01"
        else:
            mf = "CLAUDE.md" if "CLAUDE.md" in c["files"] else "AGENTS.md"
            rr = get(s, f"{GH}/repos/{name}/contents/{mf}", None)
            if rr.status_code != 200 or rr.json().get("encoding") != "base64":
                why = "manifest_unreadable"
            else:
                import base64
                n = len(base64.b64decode(rr.json()["content"]).decode("utf-8", "replace"))
                c["manifest"], c["manifest_chars"] = mf, n
                if n < 500:
                    why = "manifest_lt_500_chars"
        c["why_not"] = why
        rows.append(c)
        if why is None:
            elig.append(c)
    elig.sort(key=lambda c: c["full_name"])
    random.Random(SEED).shuffle(elig)
    (out / "wp2c_candidates_raw.json").write_text(json.dumps({"collected": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "n": len(rows), "candidates": rows}, indent=1))
    (out / "wp2c_eligible_shuffled.json").write_text(json.dumps({"seed": SEED, "n": len(elig), "eligible": elig}, indent=1))
    logger.info("candidates %d, eligible %d", len(rows), len(elig))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
