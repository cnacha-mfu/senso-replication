"""WP3 external, maintainer-declared lifecycle ground truth (no human raters).

Used by Paper 1 (RQ1, convergent validity of lifecycle-stage labels). Collects
labels that maintainers already published (PyPI ``Development Status``
classifier and its per-release history, GitHub ``archived`` flag, README
"unmaintained" phrases), maps them provisionally onto Rajlich & Bennett stages,
and draws a stratified sample with quotas fixed in the config beforehand.

No LLM or paid API is used. Only the PyPI JSON API, the GitHub REST API and the
hugovk top-pypi-packages file are called; every response is cached on disk so
reruns do not hit the network.

Usage:
    python experiments/paper1_ontology_manifests/wp3_ground_truth.py \\
        --config experiments/paper1_ontology_manifests/configs/wp3_ground_truth.yaml \\
        [--env-file /path/to/.env] [--cache-dir /path/to/cache] [--limit N]

Outputs (all under results/real_v2/wp3/): candidates_raw.json,
ground_truth_sample.json, summary.json.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import re
import sys
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests
import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger("wp3")

GH_API = "https://api.github.com"
PYPI = "https://pypi.org/pypi"
DEV_STATUS_RE = re.compile(r"^Development Status :: (\d)")
GH_URL_RE = re.compile(r"github\.com[/:]([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", re.I)
STAGES = ["initial_development", "evolution", "servicing", "phase_out"]


# ----------------------------------------------------------------------------
# HTTP + cache
# ----------------------------------------------------------------------------
class Http:
    """Cached, retrying, rate-limit-aware HTTP client (thread safe)."""

    def __init__(self, cache_dir: Path, token: Optional[str], timeout: int, retries: int):
        self.cache_dir = cache_dir
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "senso-wp3-ground-truth/1.0 (research)"
        self.token = token
        self._gh_lock = threading.Lock()
        self._gh_pause_until = 0.0
        self.net_calls = 0
        self.cache_hits = 0

    def _path(self, kind: str, key: str) -> Path:
        safe = re.sub(r"[^A-Za-z0-9_.=-]", "_", key)[:150]
        h = format(abs(hash_str(key)) % (10**8), "08d")
        return self.cache_dir / kind / f"{safe}.{h}.json"

    def cached(self, kind: str, key: str) -> Optional[dict]:
        p = self._path(kind, key)
        if p.exists():
            self.cache_hits += 1
            return json.loads(p.read_text())
        return None

    def store(self, kind: str, key: str, value: dict) -> None:
        p = self._path(kind, key)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp%d" % threading.get_ident())
        tmp.write_text(json.dumps(value))
        tmp.replace(p)

    def get(self, url: str, *, github: bool = False, params: Optional[dict] = None,
            accept: Optional[str] = None) -> tuple[int, Any, dict]:
        """Return (status, body, headers). body is JSON or text. Retries on 429/5xx."""
        headers = {}
        if github:
            headers["Accept"] = accept or "application/vnd.github+json"
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
        for attempt in range(self.retries):
            if github:
                wait = self._gh_pause_until - time.time()
                if wait > 0:
                    time.sleep(wait)
            try:
                self.net_calls += 1
                r = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
            except requests.RequestException as exc:
                logger.warning("network error %s (%s), retry %d", url, exc, attempt + 1)
                time.sleep(2 ** attempt)
                continue
            if github:
                rem = r.headers.get("X-RateLimit-Remaining")
                if rem is not None and int(rem) <= 2:
                    reset = int(r.headers.get("X-RateLimit-Reset", "0"))
                    with self._gh_lock:
                        self._gh_pause_until = max(self._gh_pause_until, reset + 2)
                    logger.info("GitHub rate limit low, pausing until reset")
                if r.status_code in (403, 429) and "rate limit" in r.text.lower():
                    reset = int(r.headers.get("X-RateLimit-Reset", str(int(time.time()) + 60)))
                    with self._gh_lock:
                        self._gh_pause_until = max(self._gh_pause_until, reset + 2)
                    continue
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(min(60, 2 ** attempt * 2))
                continue
            if r.status_code == 200:
                try:
                    body: Any = r.json()
                except ValueError:
                    body = r.text
            else:
                body = None
            return r.status_code, body, dict(r.headers)
        return 0, None, {}


def hash_str(s: str) -> int:
    """Stable (process independent) string hash for cache file names."""
    h = 5381
    for ch in s:
        h = (h * 33 + ord(ch)) & 0xFFFFFFFF
    return h


def norm_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_ts(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    s = s.replace("Z", "+00:00")
    try:
        d = datetime.fromisoformat(s)
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def months_between(a: datetime, b: datetime) -> float:
    return (b - a).days / 30.4375


# ----------------------------------------------------------------------------
# PyPI
# ----------------------------------------------------------------------------
def dev_status_of(classifiers: Optional[list[str]]) -> dict:
    vals = sorted({int(m.group(1)) for c in (classifiers or []) if (m := DEV_STATUS_RE.match(c))})
    return {"value": vals[0] if vals else None, "all": vals, "ambiguous": len(vals) > 1}


def pypi_project(http: Http, pkg: str) -> Optional[dict]:
    """Slim project record: info subset + release upload times. None if 404."""
    key = norm_name(pkg)
    c = http.cached("pypi_project", key)
    if c is not None:
        return c.get("data")
    status, body, _ = http.get(f"{PYPI}/{pkg}/json")
    if status == 404:
        http.store("pypi_project", key, {"data": None})
        return None
    if status != 200 or not isinstance(body, dict):
        logger.warning("pypi project %s -> %s (not cached)", pkg, status)
        return None
    info = body.get("info", {})
    rel: dict[str, dict] = {}
    for ver, files in (body.get("releases") or {}).items():
        times = [f.get("upload_time_iso_8601") for f in files if f.get("upload_time_iso_8601")]
        rel[ver] = {"t": min(times) if times else None,
                    "yanked": bool(files) and all(f.get("yanked") for f in files)}
    data = {
        "name": info.get("name"),
        "version": info.get("version"),
        "classifiers": info.get("classifiers") or [],
        "project_urls": info.get("project_urls") or {},
        "home_page": info.get("home_page"),
        "releases": rel,
    }
    http.store("pypi_project", key, {"data": data})
    return data


def pypi_release_classifier(http: Http, pkg: str, ver: str) -> dict:
    """Classifier record for one release. 'fetched' False means the call failed."""
    key = f"{norm_name(pkg)}@{ver}"
    c = http.cached("pypi_release", key)
    if c is not None:
        return c
    status, body, _ = http.get(f"{PYPI}/{pkg}/{ver}/json")
    if status == 200 and isinstance(body, dict):
        cls = body.get("info", {}).get("classifiers")
        rec = {"fetched": True, "has_classifier_field": cls is not None and len(cls) > 0,
               "dev_status": dev_status_of(cls)}
    elif status == 404:
        rec = {"fetched": False, "reason": "404", "has_classifier_field": False,
               "dev_status": dev_status_of([])}
    else:
        logger.warning("pypi release %s %s -> %s (not cached)", pkg, ver, status)
        return {"fetched": False, "reason": f"http_{status}", "has_classifier_field": False,
                "dev_status": dev_status_of([])}
    http.store("pypi_release", key, rec)
    return rec


def resolve_github(proj: dict) -> Optional[str]:
    """owner/repo most referenced in project_urls/home_page, preferring Source-like keys."""
    urls: list[tuple[int, str]] = []
    for k, v in (proj.get("project_urls") or {}).items():
        pri = 0 if re.search(r"source|repo|code|github", k, re.I) else 1
        urls.append((pri, v or ""))
    urls.append((2, proj.get("home_page") or ""))
    cands: list[tuple[int, str]] = []
    for pri, u in urls:
        m = GH_URL_RE.search(u)
        if m:
            repo = m.group(2)
            repo = re.sub(r"\.git$", "", repo)
            if m.group(1).lower() in ("sponsors", "orgs", "apps", "marketplace"):
                continue
            cands.append((pri, f"{m.group(1)}/{repo}"))
    if not cands:
        return None
    counts = Counter(r.lower() for _, r in cands)
    cands.sort(key=lambda t: (t[0], -counts[t[1].lower()]))
    return cands[0][1]


def snapshot_release(proj: dict, snapshot: datetime) -> Optional[str]:
    best: Optional[tuple[datetime, str]] = None
    for ver, r in proj["releases"].items():
        t = parse_ts(r["t"])
        if t and t <= snapshot and not r["yanked"] and (best is None or t > best[0]):
            best = (t, ver)
    return best[1] if best else None


def first_release_time(proj: dict) -> Optional[datetime]:
    ts = [parse_ts(r["t"]) for r in proj["releases"].values() if r["t"]]
    ts = [t for t in ts if t]
    return min(ts) if ts else None


# ----------------------------------------------------------------------------
# GitHub
# ----------------------------------------------------------------------------
def gh_repo(http: Http, full: str) -> Optional[dict]:
    c = http.cached("gh_repo", full.lower())
    if c is not None:
        return c.get("data")
    status, body, _ = http.get(f"{GH_API}/repos/{full}", github=True)
    if status in (404, 410, 451):
        http.store("gh_repo", full.lower(), {"data": None, "status": status})
        return None
    if status != 200 or not isinstance(body, dict):
        logger.warning("gh repo %s -> %s (not cached)", full, status)
        return None
    data = {k: body.get(k) for k in ("full_name", "archived", "pushed_at", "created_at",
                                     "stargazers_count", "language", "fork", "disabled",
                                     "default_branch", "html_url")}
    http.store("gh_repo", full.lower(), {"data": data})
    return data


def gh_readme(http: Http, full: str) -> Optional[str]:
    c = http.cached("gh_readme", full.lower())
    if c is not None:
        return c.get("text")
    status, body, _ = http.get(f"{GH_API}/repos/{full}/readme", github=True,
                               accept="application/vnd.github.raw+json")
    if status == 404:
        http.store("gh_readme", full.lower(), {"text": None})
        return None
    if status != 200:
        logger.warning("gh readme %s -> %s (not cached)", full, status)
        return None
    text = body if isinstance(body, str) else json.dumps(body)
    text = text[:60000]
    http.store("gh_readme", full.lower(), {"text": text})
    return text


def gh_search_archived(http: Http, cfg: dict) -> list[dict]:
    lang = cfg["language"]
    out: dict[str, dict] = {}
    for lo, hi in cfg["star_bands"]:
        q = f"archived:true language:{lang} stars:{lo}..{hi}"
        for page in range(1, cfg["max_pages_per_band"] + 1):
            key = f"{q}|{page}"
            c = http.cached("gh_search", key)
            if c is None:
                status, body, _ = http.get(f"{GH_API}/search/repositories", github=True,
                                           params={"q": q, "per_page": 100, "page": page,
                                                   "sort": "stars"})
                if status != 200 or not isinstance(body, dict):
                    logger.warning("search %s page %d -> %s", q, page, status)
                    break
                c = {"items": [{"full_name": i["full_name"], "stars": i["stargazers_count"]}
                               for i in body.get("items", [])],
                     "total": body.get("total_count")}
                http.store("gh_search", key, c)
                time.sleep(2.2)  # search API: 30 req/min
            for i in c["items"]:
                out[i["full_name"].lower()] = i
            if len(c["items"]) < 100:
                break
        logger.info("archived search band %s..%s -> total %d repos", lo, hi, len(out))
    return list(out.values())


# ----------------------------------------------------------------------------
# README signals
# ----------------------------------------------------------------------------
def readme_signals(text: Optional[str], rcfg: dict) -> dict:
    res: dict[str, Any] = {"available": text is not None, "unmaintained": None,
                           "maintenance_mode": None}
    if not text:
        return res
    head = text[: rcfg["head_chars"]]

    def find(patterns: list[str], hay: str, offset_ok: bool = True) -> Optional[dict]:
        for p in patterns:
            m = re.search(p, hay, re.I)
            if m:
                s = max(0, m.start() - 80)
                snippet = re.sub(r"\s+", " ", hay[s: m.end() + 80]).strip()
                return {"pattern": p, "snippet": snippet, "pos": m.start()}
        return None

    res["unmaintained"] = (find(rcfg["unmaintained"], text)
                           or find(rcfg["unmaintained_head_only"], head))
    res["maintenance_mode"] = find(rcfg["maintenance_mode"], text)
    return res


# ----------------------------------------------------------------------------
# Mapping
# ----------------------------------------------------------------------------
def map_stage(sig: dict, mapping: dict) -> dict:
    """Provisional stage mapping + conflict flags. Never resolves silently."""
    cls = sig["classifier_at_snapshot"]["value"]
    implied: dict[str, str] = {}
    if cls is not None:
        implied["classifier"] = mapping["classifier"][str(cls)]
    if sig["archived_valid"]:
        implied["archived_valid"] = mapping["archived_valid"]
    rd = sig["readme"]
    if rd.get("unmaintained"):
        implied["readme"] = mapping["readme_unmaintained"]
    elif rd.get("maintenance_mode"):
        implied["readme"] = mapping["readme_maintenance_mode"]

    stage = None
    basis = None
    if "archived_valid" in implied:
        stage, basis = implied["archived_valid"], "archived_valid"
    elif cls == 7:
        stage, basis = "phase_out", "classifier_7"
    elif "readme" in implied:
        stage, basis = implied["readme"], "readme"
    elif "classifier" in implied:
        stage, basis = implied["classifier"], "classifier"

    conflicts: list[str] = []
    if len(set(implied.values())) > 1:
        conflicts.append("signals_disagree:" + ",".join(f"{k}={v}" for k, v in sorted(implied.items())))
    if sig["archived"] and not sig["archived_valid"]:
        conflicts.append("archived_but_pushed_after_snapshot")
    if cls is not None and cls <= 6 and sig["dormant_24m_at_snapshot"]:
        conflicts.append(f"classifier_{cls}_but_no_push_24m_at_snapshot")
    if sig["classifier_at_snapshot"]["ambiguous"]:
        conflicts.append("multiple_dev_status_classifiers")
    if cls is None:
        conflicts.append("no_classifier_at_snapshot")
    return {"mapped_stage": stage, "mapped_basis": basis, "implied_by_signal": implied,
            "conflicts": conflicts,
            "conflict": any(c.startswith(("signals_disagree", "archived_but", "classifier_"))
                            and not c.startswith("classifier_at") for c in conflicts)}


# ----------------------------------------------------------------------------
# Pipeline
# ----------------------------------------------------------------------------
def build_pool(cfg: dict, http: Http, limit: Optional[int]) -> dict[str, dict]:
    """norm package name -> {package, sources, rank}"""
    pool: dict[str, dict] = {}
    pcfg = cfg["pool"]
    c = http.cached("misc", "top_pypi")
    if c is None:
        status, body, _ = http.get(pcfg["top_pypi_url"])
        if status != 200 or not isinstance(body, dict):
            raise RuntimeError(f"cannot fetch top pypi list ({status})")
        c = {"last_update": body.get("last_update"),
             "projects": [r["project"] for r in body["rows"]]}
        http.store("misc", "top_pypi", c)
    logger.info("top-pypi list last_update=%s size=%d", c["last_update"], len(c["projects"]))
    for rank, name in enumerate(c["projects"][: pcfg["top_n"]], 1):
        pool[norm_name(name)] = {"package": name, "sources": ["top_pypi"], "rank": rank}

    if pcfg["archived_search"]["enabled"]:
        repos = gh_search_archived(http, pcfg["archived_search"])
        logger.info("archived GitHub repos found: %d; mapping to PyPI by name", len(repos))

        def map_one(item: dict) -> Optional[tuple[str, str, str]]:
            owner, repo = item["full_name"].split("/")
            seen = set()
            for cand in (repo, repo.replace("_", "-"), repo.lower(), re.sub(r"^(py|python-)", "", repo.lower())):
                n = norm_name(cand)
                if n in seen or not n:
                    continue
                seen.add(n)
                proj = pypi_project(http, cand)
                if proj and (g := resolve_github(proj)) and g.lower() == item["full_name"].lower():
                    return n, proj["name"] or cand, item["full_name"]
            return None

        with ThreadPoolExecutor(cfg["network"]["workers"]) as ex:
            for res in ex.map(map_one, repos):
                if res:
                    n, nm, _ = res
                    if n in pool:
                        pool[n]["sources"].append("github_archived_search")
                    else:
                        pool[n] = {"package": nm, "sources": ["github_archived_search"], "rank": None}
        logger.info("pool size after archived mapping: %d", len(pool))
    if limit:
        pool = dict(list(pool.items())[:limit])
    return pool


def process_package(entry: dict, cfg: dict, http: Http, snapshot: datetime) -> dict:
    pkg = entry["package"]
    rec: dict[str, Any] = {"package": pkg, "sources": entry["sources"], "rank": entry["rank"],
                           "excluded": None}
    proj = pypi_project(http, pkg)
    if not proj:
        rec["excluded"] = "pypi_unavailable"
        return rec
    gh = resolve_github(proj)
    rec["github_url_resolved"] = gh
    if not gh:
        rec["excluded"] = "no_github_url"
        return rec
    repo = gh_repo(http, gh)
    if not repo:
        rec["excluded"] = "github_repo_unavailable"
        return rec
    rec["repo"] = repo["full_name"]
    created = parse_ts(repo["created_at"])
    pushed = parse_ts(repo["pushed_at"])
    first_rel = first_release_time(proj)
    rec["github"] = {k: repo[k] for k in ("archived", "pushed_at", "created_at",
                                          "stargazers_count", "language", "fork", "disabled")}
    rec["pypi"] = {"latest_version": proj["version"], "n_releases": len(proj["releases"]),
                   "first_release": first_rel.isoformat() if first_rel else None,
                   "classifier_latest": dev_status_of(proj["classifiers"])}
    if repo.get("fork"):
        rec["excluded"] = "fork"
        return rec
    if not created or months_between(created, snapshot) < cfg["min_history_months"]:
        rec["excluded"] = "history_lt_min_months"
        return rec
    ver = snapshot_release(proj, snapshot)
    if not ver:
        rec["excluded"] = "no_pypi_release_before_snapshot"
        return rec
    rel = pypi_release_classifier(http, pkg, ver)
    rec["snapshot_release"] = {"version": ver, "time": proj["releases"][ver]["t"], **rel}
    if not rel["fetched"]:
        rec["excluded"] = "snapshot_release_metadata_unavailable"
        return rec
    text = gh_readme(http, repo["full_name"])
    rd = readme_signals(text, cfg["readme"])
    archived = bool(repo["archived"])
    archived_valid = bool(archived and pushed and pushed <= snapshot)
    dormant_m = months_between(pushed, snapshot) if pushed and pushed <= snapshot else None
    close_m = cfg["close_down_dormant_months"]
    sig = {
        "classifier_at_snapshot": rel["dev_status"],
        "classifier_latest": rec["pypi"]["classifier_latest"],
        "classifier_stale_vs_latest": (rel["dev_status"]["value"] != rec["pypi"]["classifier_latest"]["value"]),
        "archived": archived,
        "archived_valid": archived_valid,
        "dormant_24m_at_snapshot": bool(dormant_m is not None and dormant_m >= 24),
        "months_since_last_push_at_snapshot": round(dormant_m, 1) if dormant_m is not None else None,
        "close_down_candidate": bool(archived_valid and dormant_m is not None and dormant_m >= close_m),
        "readme": rd,
    }
    rec["signals"] = sig
    rec["mapping"] = map_stage(sig, cfg["stage_mapping"])
    return rec


def sample_ground_truth(cands: list[dict], cfg: dict) -> tuple[list[dict], dict]:
    scfg = cfg["sampling"]
    rng = random.Random(scfg["seed"])
    elig: dict[str, list[dict]] = defaultdict(list)
    for r in cands:
        stage = r.get("mapping", {}).get("mapped_stage")
        if r.get("excluded") or stage not in scfg["quotas"]:
            continue
        if (r["github"]["stargazers_count"] or 0) < scfg["min_stars"]:
            continue
        elig[stage].append(r)
    sampled: list[dict] = []
    report: dict[str, dict] = {}
    for stage, quota in scfg["quotas"].items():
        pool = sorted(elig[stage], key=lambda r: r["repo"].lower())
        clean = [r for r in pool if not r["mapping"]["conflict"]]
        dirty = [r for r in pool if r["mapping"]["conflict"]]
        rng.shuffle(clean)
        rng.shuffle(dirty)
        order = (clean + dirty) if scfg["prefer_unconflicted"] else rng.sample(pool, len(pool))
        take = order[:quota]
        for r in take:
            r["stratum"] = stage
        sampled.extend(take)
        report[stage] = {"quota": quota, "eligible": len(pool), "eligible_clean": len(clean),
                         "eligible_conflicted": len(dirty), "sampled": len(take),
                         "sampled_conflicted": sum(1 for r in take if r["mapping"]["conflict"]),
                         "shortfall": max(0, quota - len(take))}
    return sampled, report


def release_history(rec: dict, cfg: dict, http: Http) -> dict:
    """Per-release classifiers for a sampled repo (capped, evenly spaced)."""
    pkg = rec["package"]
    proj = pypi_project(http, pkg)
    items = sorted(((parse_ts(v["t"]), ver) for ver, v in proj["releases"].items()
                    if v["t"] and not v["yanked"]), key=lambda t: t[0])
    cap = cfg["history"]["max_releases_per_package"]
    vers = [v for _, v in items]
    must = {vers[0], vers[-1], rec["snapshot_release"]["version"]} if vers else set()
    if len(vers) > cap:
        step = (len(vers) - 1) / (cap - 1)
        chosen = {vers[round(i * step)] for i in range(cap)} | must
    else:
        chosen = set(vers)
    rows = []
    for t, ver in items:
        if ver in chosen:
            r = pypi_release_classifier(http, pkg, ver)
            rows.append({"version": ver, "time": t.isoformat(), "fetched": r["fetched"],
                         "dev_status": r["dev_status"]["value"],
                         "has_classifier_field": r["has_classifier_field"]})
    ok = [r for r in rows if r["fetched"]]
    seq = [r["dev_status"] for r in ok]
    changes = sum(1 for a, b in zip(seq, seq[1:]) if a != b)
    return {"n_releases_total": len(items), "n_releases_fetched": len(ok),
            "truncated": len(items) > cap,
            "n_missing_classifier": sum(1 for r in ok if r["dev_status"] is None),
            "n_fetch_failed": len(rows) - len(ok),
            "n_changes": changes, "distinct_values": sorted({s for s in seq if s is not None}),
            "releases": rows}


def pct(a: int, b: int) -> Optional[float]:
    return round(100 * a / b, 1) if b else None


def summarize(cfg: dict, pool_n: int, cands: list[dict], sampled: list[dict],
              sample_report: dict, snapshot: datetime) -> dict:
    ok = [r for r in cands if not r.get("excluded")]
    excl = Counter(r["excluded"] for r in cands if r.get("excluded"))
    stage_counts = Counter(r["mapping"]["mapped_stage"] or "unlabelled" for r in ok)
    conflict_types: Counter = Counter()
    for r in ok:
        for c in r["mapping"]["conflicts"]:
            conflict_types[c.split(":")[0] if c.startswith("signals_disagree") else c] += 1
        if r["mapping"]["conflicts"]:
            for c in r["mapping"]["conflicts"]:
                if c.startswith("signals_disagree"):
                    conflict_types["pair:" + c.split(":", 1)[1]] += 1
    cls_dist = Counter(str(r["signals"]["classifier_at_snapshot"]["value"]) for r in ok)
    hist = [r["history"] for r in sampled]
    n_h = len(hist)
    tot_fetched = sum(h["n_releases_fetched"] for h in hist)
    tot_missing = sum(h["n_missing_classifier"] for h in hist)
    stale = [r for r in ok if r["signals"]["classifier_at_snapshot"]["value"] is not None
             and r["signals"]["classifier_latest"]["value"] is not None]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "snapshot_date": snapshot.date().isoformat(),
        "pool_size": pool_n,
        "pool_sources": dict(Counter(s for r in cands for s in r["sources"])),
        "exclusions": dict(excl),
        "candidates_passing_filters": len(ok),
        "candidates_per_mapped_stage": dict(stage_counts),
        "classifier_at_snapshot_distribution": dict(cls_dist),
        "stratum_sampling": sample_report,
        "sampled_total": len(sampled),
        "conflicts_all_candidates": {
            "n_with_any_conflict": sum(1 for r in ok if r["mapping"]["conflict"]),
            "by_type": dict(conflict_types)},
        "conflicts_sampled": {
            "n_with_any_conflict": sum(1 for r in sampled if r["mapping"]["conflict"]),
            "by_stratum": {s: sum(1 for r in sampled if r["stratum"] == s and r["mapping"]["conflict"])
                           for s in STAGES}},
        "flags_all_candidates": {
            "archived": sum(1 for r in ok if r["signals"]["archived"]),
            "archived_valid": sum(1 for r in ok if r["signals"]["archived_valid"]),
            "close_down_candidate": sum(1 for r in ok if r["signals"]["close_down_candidate"]),
            "readme_unmaintained": sum(1 for r in ok if r["signals"]["readme"].get("unmaintained")),
            "readme_maintenance_mode": sum(1 for r in ok if r["signals"]["readme"].get("maintenance_mode")),
            "no_classifier_at_snapshot": sum(1 for r in ok if r["signals"]["classifier_at_snapshot"]["value"] is None),
        },
        "noise": {
            "classifier_at_snapshot_differs_from_latest": {
                "n": sum(1 for r in stale if r["signals"]["classifier_stale_vs_latest"]),
                "of": len(stale),
                "pct": pct(sum(1 for r in stale if r["signals"]["classifier_stale_vs_latest"]), len(stale))},
            "sampled_repos_with_history": n_h,
            "sampled_repos_with_any_classifier_change": sum(1 for h in hist if h["n_changes"] > 0),
            "sampled_pct_with_change": pct(sum(1 for h in hist if h["n_changes"] > 0), n_h),
            "mean_changes_per_repo": round(sum(h["n_changes"] for h in hist) / n_h, 2) if n_h else None,
            "releases_fetched": tot_fetched,
            "releases_missing_classifier": tot_missing,
            "pct_releases_missing_classifier": pct(tot_missing, tot_fetched),
            "sampled_repos_lacking_any_per_release_classifier":
                sum(1 for h in hist if h["n_releases_fetched"] > 0 and h["n_missing_classifier"] == h["n_releases_fetched"]),
            "sampled_repos_with_some_missing_release_classifier":
                sum(1 for h in hist if h["n_missing_classifier"] > 0),
            "sampled_repos_with_failed_release_fetch": sum(1 for h in hist if h["n_fetch_failed"] > 0),
            "sampled_repos_history_truncated": sum(1 for h in hist if h["truncated"]),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(PROJECT_ROOT / "experiments/paper1_ontology_manifests/configs/wp3_ground_truth.yaml"))
    ap.add_argument("--env-file", default=str(PROJECT_ROOT / ".env"))
    ap.add_argument("--cache-dir", default=None, help="default: <output_dir>/cache")
    ap.add_argument("--limit", type=int, default=None, help="debug: cap pool size")
    ap.add_argument("--out-suffix", default="", help="debug: suffix for output file names")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    cfg = yaml.safe_load(Path(args.config).read_text())
    if Path(args.env_file).exists():
        load_dotenv(args.env_file)
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        logger.warning("GITHUB_TOKEN missing: GitHub calls will be heavily rate limited")
    out_dir = PROJECT_ROOT / cfg["output_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = Path(args.cache_dir) if args.cache_dir else out_dir / "cache"
    net = cfg["network"]
    http = Http(cache_dir, token, net["timeout_s"], net["max_retries"])
    snapshot = datetime.fromisoformat(cfg["snapshot_date"]).replace(tzinfo=timezone.utc)
    workers = min(4, net["workers"])  # VM rule: at most 4 workers

    pool = build_pool(cfg, http, args.limit)
    logger.info("pool: %d packages", len(pool))

    done = 0
    lock = threading.Lock()

    def work(entry: dict) -> dict:
        nonlocal done
        try:
            r = process_package(entry, cfg, http, snapshot)
        except Exception as exc:  # keep going; record the failure
            logger.exception("package %s failed", entry["package"])
            r = {"package": entry["package"], "sources": entry["sources"], "rank": entry["rank"],
                 "excluded": f"error:{type(exc).__name__}"}
        with lock:
            done += 1
            if done % 250 == 0:
                logger.info("processed %d/%d (net calls %d, cache hits %d)", done, len(pool),
                            http.net_calls, http.cache_hits)
        return r

    with ThreadPoolExecutor(workers) as ex:
        cands = list(ex.map(work, list(pool.values())))

    # Deduplicate monorepos: several packages may point to one repo. Keep best-ranked.
    best: dict[str, dict] = {}
    for r in sorted((c for c in cands if not c.get("excluded")),
                    key=lambda c: (c["rank"] is None, c["rank"] or 0, c["package"])):
        key = r["repo"].lower()
        if key in best:
            r["excluded"] = f"duplicate_repo_of:{best[key]['package']}"
            best[key].setdefault("other_packages_same_repo", []).append(r["package"])
        else:
            best[key] = r

    sfx = args.out_suffix
    (out_dir / f"candidates_raw{sfx}.json").write_text(json.dumps(
        {"snapshot_date": cfg["snapshot_date"], "pool_size": len(pool), "candidates": cands}, indent=1))
    logger.info("wrote candidates_raw (%d records)", len(cands))

    sampled, sample_report = sample_ground_truth(cands, cfg)
    logger.info("sampled %d repos; fetching release histories", len(sampled))

    def hist(r: dict) -> None:
        r["history"] = release_history(r, cfg, http)

    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(hist, sampled))

    gt = {"snapshot_date": cfg["snapshot_date"], "seed": cfg["sampling"]["seed"],
          "quotas": cfg["sampling"]["quotas"],
          "mapping_status": "PROVISIONAL (see configs/wp3_ground_truth.yaml)",
          "records": sampled}
    (out_dir / f"ground_truth_sample{sfx}.json").write_text(json.dumps(gt, indent=1))
    summary = summarize(cfg, len(pool), cands, sampled, sample_report, snapshot)
    (out_dir / f"summary{sfx}.json").write_text(json.dumps(summary, indent=2))
    logger.info("done. summary:\n%s", json.dumps(summary["stratum_sampling"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
