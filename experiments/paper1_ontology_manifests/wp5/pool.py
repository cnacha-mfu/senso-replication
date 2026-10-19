"""WP5 task pool: SWE-rebench Python tasks stratified by the declared lifecycle stage at the base commit.

Used by Paper 1 (JSEP rebuild), WP5. Reuses the WP3 ground-truth functions and cache
(experiments/paper1_ontology_manifests/wp3_ground_truth.py): PyPI Development Status classifier of the
latest release on or before the task's base-commit date, mapped by the frozen stage mapping in
configs/wp3_ground_truth.yaml. phase_out is classifier 7, or a README at the base commit that says the
project is unmaintained (GitHub 'archived' cannot be dated, so it is not used here).

Usage:
    python experiments/paper1_ontology_manifests/run_wp5.py build-pool [--config ...] [--limit-repos N]
"""

from __future__ import annotations

import logging
import random
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

from .common import PROJECT_ROOT, hf_dataset, read_json, rpath, write_json

sys.path.insert(0, str(PROJECT_ROOT))
from experiments.paper1_ontology_manifests import wp3_ground_truth as wp3  # noqa: E402

logger = logging.getLogger("wp5.pool")


# ----------------------------------------------------------------------------
# Repo -> PyPI package
# ----------------------------------------------------------------------------
def reverse_package_map(cache_dir: Path) -> dict[str, list[str]]:
    """github repo (lower) -> PyPI package names, from every project already in the WP3 cache."""
    out: dict[str, list[str]] = defaultdict(list)
    for f in (cache_dir / "pypi_project").glob("*.json"):
        d = read_json(f, {}).get("data")
        if not d or not d.get("name"):
            continue
        gh = wp3.resolve_github(d)
        if gh:
            out[gh.lower()].append(d["name"])
    return out


def name_candidates(repo: str) -> list[str]:
    base = repo.split("/")[1]
    c = [base, base.replace("_", "-"), base.replace("-", "_"), base.lower()]
    for pre in ("python-", "py-", "py", "python_"):
        if base.lower().startswith(pre) and len(base) > len(pre) + 1:
            c.append(base[len(pre):])
    for suf in ("-python", "-py", ".py", "_py"):
        if base.lower().endswith(suf):
            c.append(base[: -len(suf)])
    seen, out = set(), []
    for x in c:
        if x.lower() not in seen:
            seen.add(x.lower())
            out.append(x)
    return out


def map_repo_to_package(repo: str, rev: dict[str, list[str]], http: "wp3.Http") -> Optional[str]:
    cands = rev.get(repo.lower())
    if cands:
        base = norm = wp3.norm_name(repo.split("/")[1])
        exact = [c for c in cands if wp3.norm_name(c) == norm]
        return exact[0] if exact else sorted(cands, key=len)[0]
    for name in name_candidates(repo):
        proj = wp3.pypi_project(http, name)
        if proj:
            gh = wp3.resolve_github(proj)
            if gh and gh.lower() == repo.lower():
                return proj["name"]
    return None


# ----------------------------------------------------------------------------
# Declared stage at a date
# ----------------------------------------------------------------------------
def gh_commit_date(http: "wp3.Http", repo: str, sha: str) -> Optional[datetime]:
    key = f"{repo.lower()}@{sha}"
    c = http.cached("gh_commit", key)
    if c is not None:
        return wp3.parse_ts(c.get("date"))
    status, body, _ = http.get(f"{wp3.GH_API}/repos/{repo}/git/commits/{sha}", github=True)
    if status == 200 and isinstance(body, dict):
        date = (body.get("committer") or {}).get("date") or (body.get("author") or {}).get("date")
        http.store("gh_commit", key, {"date": date})
        return wp3.parse_ts(date)
    if status in (404, 409, 422):
        http.store("gh_commit", key, {"date": None, "status": status})
    return None


def gh_readme_at(http: "wp3.Http", repo: str, sha: str) -> Optional[str]:
    key = f"{repo.lower()}@{sha}"
    c = http.cached("gh_readme_at", key)
    if c is not None:
        return c.get("text")
    status, body, _ = http.get(f"{wp3.GH_API}/repos/{repo}/readme", github=True, params={"ref": sha},
                               accept="application/vnd.github.raw+json")
    if status == 404:
        http.store("gh_readme_at", key, {"text": None})
        return None
    if status != 200:
        return None
    text = (body if isinstance(body, str) else str(body))[:60000]
    http.store("gh_readme_at", key, {"text": text})
    return text


def classifier_stage_at(http: "wp3.Http", pkg: str, when: datetime, mapping: dict) -> dict[str, Any]:
    """Classifier-only declared stage in effect at ``when`` (no README)."""
    proj = wp3.pypi_project(http, pkg)
    if not proj:
        return {"stage": None, "reason": "pypi_unavailable"}
    ver = wp3.snapshot_release(proj, when)
    if not ver:
        return {"stage": None, "reason": "no_release_before_date"}
    rel = wp3.pypi_release_classifier(http, pkg, ver)
    if not rel.get("fetched"):
        return {"stage": None, "reason": "release_metadata_unavailable", "release": ver}
    v = rel["dev_status"]["value"]
    if v is None:
        return {"stage": None, "reason": "no_classifier_at_date", "release": ver}
    return {"stage": mapping["classifier"][str(v)], "classifier": v, "release": ver,
            "ambiguous": rel["dev_status"]["ambiguous"]}


def declared_stage_at(http: "wp3.Http", wcfg: dict, pkg: str, repo: str, sha: str, when: datetime) -> dict[str, Any]:
    """Frozen WP3 mapping applied at the base-commit date (classifier + README at base commit)."""
    base = classifier_stage_at(http, pkg, when, wcfg["stage_mapping"])
    if base["stage"] is None:
        return base
    text = gh_readme_at(http, repo, sha)
    rd = wp3.readme_signals(text, wcfg["readme"])
    sig = {
        "classifier_at_snapshot": {"value": base["classifier"], "ambiguous": base.get("ambiguous", False)},
        "archived": False, "archived_valid": False, "dormant_24m_at_snapshot": False,
        "readme": rd,
    }
    m = wp3.map_stage(sig, wcfg["stage_mapping"])
    return {"stage": m["mapped_stage"], "basis": m["mapped_basis"], "classifier": base["classifier"],
            "release": base["release"], "conflicts": m["conflicts"], "conflict": m["conflict"],
            "readme_available": rd["available"],
            "readme_signal": (rd.get("unmaintained") or {}).get("snippet") if rd.get("unmaintained") else None}


# ----------------------------------------------------------------------------
# Pool
# ----------------------------------------------------------------------------
def base_filter(cfg: dict) -> tuple[list[dict], Counter]:
    """Slim candidate records from SWE-rebench after cheap feasibility filters."""
    pc = cfg["pool"]
    ds, _ = hf_dataset(cfg)
    cols = ds.select_columns(["instance_id", "repo", "base_commit", "created_at", "install_config",
                              "FAIL_TO_PASS", "PASS_TO_PASS", "requirements", "patch", "test_patch"])
    excl: Counter = Counter()
    out = []
    heavy = [h.lower() for h in pc["heavy_packages"]]
    file_re = re.compile(r"^diff --git a/(\S+)", re.M)
    for r in cols:
        ic = r["install_config"] or {}
        py = str(ic.get("python") or "")
        pyv = ".".join(py.split(".")[:2])
        if pyv not in pc["python_versions"]:
            excl["python_version_unsupported"] += 1
            continue
        if "pytest" not in (ic.get("test_cmd") or "") and "py.test" not in (ic.get("test_cmd") or ""):
            excl["non_pytest"] += 1
            continue
        if ic.get("env_yml_path") or ic.get("packages") == "environment.yml":
            excl["conda_environment"] += 1
            continue
        f2p, p2p = r["FAIL_TO_PASS"] or [], r["PASS_TO_PASS"] or []
        if not f2p:
            excl["no_f2p"] += 1
            continue
        if len(f2p) > pc["max_f2p"] or len(p2p) > pc["max_p2p"]:
            excl["too_many_tests"] += 1
            continue
        npf = len(set(file_re.findall(r["patch"] or "")))
        if npf > pc["max_patch_files"]:
            excl["gold_patch_too_wide"] += 1
            continue
        blob = ((r["requirements"] or "") + " " + " ".join(ic.get("pip_packages") or [])).lower()
        if any(h in blob for h in heavy):
            excl["heavy_dependencies"] += 1
            continue
        out.append({"instance_id": r["instance_id"], "repo": r["repo"], "base_commit": r["base_commit"],
                    "created_at": r["created_at"], "python": pyv, "n_f2p": len(f2p), "n_p2p": len(p2p),
                    "gold_patch_files": npf})
    return out, excl


def build_pool(cfg: dict, limit_repos: Optional[int] = None) -> dict[str, Any]:
    pc = cfg["pool"]
    wcfg = yaml.safe_load((PROJECT_ROOT / cfg["wp3_config"]).read_text())
    cache_dir = Path(cfg["wp3_cache"])
    import os
    http = wp3.Http(cache_dir, os.environ.get("GITHUB_TOKEN"), wcfg["network"]["timeout_s"],
                    wcfg["network"]["max_retries"])
    rng = random.Random(cfg["seed"])
    workers = min(2, cfg["limits"]["max_workers"])
    out_dir = rpath(cfg, "output_dir")

    tasks, excl = base_filter(cfg)
    logger.info("after base filters: %d tasks, %d repos; excluded %s", len(tasks),
                len({t["repo"] for t in tasks}), dict(excl))
    repos = sorted({t["repo"] for t in tasks})
    if limit_repos:
        repos = repos[:limit_repos]
        tasks = [t for t in tasks if t["repo"] in set(repos)]

    rev = reverse_package_map(cache_dir)
    logger.info("reverse package map: %d github repos from WP3 cache", len(rev))
    with ThreadPoolExecutor(workers) as ex:
        pkgs = dict(zip(repos, ex.map(lambda r: map_repo_to_package(r, rev, http), repos)))
    mapped = {r for r, p in pkgs.items() if p}
    logger.info("repos mapped to a PyPI package: %d / %d", len(mapped), len(repos))
    excl["repo_not_on_pypi"] = sum(1 for t in tasks if t["repo"] not in mapped)
    tasks = [t for t in tasks if t["repo"] in mapped]
    for t in tasks:
        t["package"] = pkgs[t["repo"]]

    # current README 'unmaintained' signal per repo (cached by WP3 for its pool) -> priority hint
    def cur_unmaintained(repo: str) -> bool:
        txt = wp3.gh_readme(http, repo)
        return bool(wp3.readme_signals(txt, wcfg["readme"]).get("unmaintained"))
    with ThreadPoolExecutor(workers) as ex:
        unm = dict(zip(sorted(mapped), ex.map(cur_unmaintained, sorted(mapped))))

    # preliminary stage (classifier at PR-creation date) used only to balance the per-repo cap
    def prelim(t: dict) -> str:
        when = wp3.parse_ts(t["created_at"].replace(" ", "T") + "+00:00") or datetime.now(timezone.utc)
        s = classifier_stage_at(http, t["package"], when, wcfg["stage_mapping"])
        t["created_dt"] = when.isoformat()
        return s["stage"] or "none"
    with ThreadPoolExecutor(workers) as ex:
        for t, s in zip(tasks, ex.map(prelim, tasks)):
            t["prelim_stage"] = "phase_out" if (unm.get(t["repo"]) and s != "none") else s
    pre_counts = Counter(t["prelim_stage"] for t in tasks)
    logger.info("preliminary stage counts (before cap): %s", dict(pre_counts))
    rank = {s: i for i, (s, _) in enumerate(sorted(pre_counts.items(), key=lambda kv: kv[1]))}

    # cap per repo: round-robin over stages, rarest stage first, seeded
    by_repo: dict[str, list[dict]] = defaultdict(list)
    for t in tasks:
        if t["prelim_stage"] != "none":
            by_repo[t["repo"]].append(t)
        else:
            excl["no_classifier_at_pr_date"] += 1
    sampled: list[dict] = []
    for repo in sorted(by_repo):
        buckets: dict[str, list[dict]] = defaultdict(list)
        for t in by_repo[repo]:
            buckets[t["prelim_stage"]].append(t)
        for b in buckets.values():
            rng.shuffle(b)
        order = sorted(buckets, key=lambda s: rank[s])
        picked: list[dict] = []
        while len(picked) < pc["cap_per_repo"] and any(buckets.values()):
            for s in order:
                if buckets[s] and len(picked) < pc["cap_per_repo"]:
                    picked.append(buckets[s].pop())
        sampled.extend(picked)
    excl["dropped_by_repo_cap"] = sum(len(v) for v in by_repo.values()) - len(sampled)
    logger.info("after cap (<=%d per repo): %d tasks over %d repos", pc["cap_per_repo"], len(sampled), len(by_repo))

    # final stage: base-commit date (GitHub) + README at base commit
    def finalize(t: dict) -> dict:
        d = gh_commit_date(http, t["repo"], t["base_commit"])
        t["base_date_source"] = "base_commit_committer_date"
        if d is None:
            d = wp3.parse_ts(t["created_dt"])
            t["base_date_source"] = "pr_created_at_fallback"
        t["base_date"] = d.isoformat()
        st = declared_stage_at(http, wcfg, t["package"], t["repo"], t["base_commit"], d)
        t["stage"] = st.get("stage")
        t["stage_detail"] = {k: v for k, v in st.items() if k != "stage"}
        return t
    with ThreadPoolExecutor(workers) as ex:
        final = list(ex.map(finalize, sampled))
    for t in final:
        t.pop("created_dt", None)
    kept = [t for t in final if t["stage"]]
    excl["no_declared_stage_at_base"] = len(final) - len(kept)
    counts = Counter(t["stage"] for t in kept)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": cfg["seed"], "cap_per_repo": pc["cap_per_repo"],
        "n_dataset": len(hf_dataset(cfg)[0]), "n_after_base_filters": len(tasks) + excl["repo_not_on_pypi"],
        "n_repos_mapped": len(mapped), "n_repos_total": len(repos),
        "exclusions": dict(excl),
        "preliminary_stage_counts_before_cap": dict(pre_counts),
        "pool_size": len(kept),
        "pool_stage_counts": {s: counts.get(s, 0) for s in pc["stages"]},
        "pool_repos_per_stage": {s: len({t["repo"] for t in kept if t["stage"] == s}) for s in pc["stages"]},
        "stage_basis": dict(Counter(t["stage_detail"].get("basis") for t in kept)),
        "stage_conflicts": sum(1 for t in kept if t["stage_detail"].get("conflict")),
        "base_date_source": dict(Counter(t["base_date_source"] for t in kept)),
        "network": {"calls": http.net_calls, "cache_hits": http.cache_hits},
    }
    write_json(out_dir / "pool.json", {"summary": summary, "tasks": kept})
    write_json(out_dir / "pool_summary.json", summary)
    logger.info("pool: %d tasks; per stage %s", len(kept), summary["pool_stage_counts"])
    return summary
