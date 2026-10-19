#!/usr/bin/env python3
"""
Paper 1 — Expand RQ4/RQ5 with 10 architecture-sensitive repos from JCSSE corpus.

Strategy:
  1. Select 10 evolution-positive repos from the JCSSE corpus (not already in experiment)
     Prioritise: high stars (issue/PR hygiene), supported languages, multiple evo dims
  2. For each new repo: populate (Phase 2 data), generate SENSO manifest (Phase 3)
  3. Curate architecture-sensitive tasks: filter to closed issues whose ground-truth
     diff touches files in stabilization-phase modules flagged by the SENSO manifest
  4. Merge with existing 42 tasks → re-run RQ4-5 with the expanded+filtered set
  5. Delete old RQ4-5 cache so run_rq4_rq5.py generates fresh results

Expected outcome: stronger phase_alignment signal, architecture_violation should move.

Paper 1: "From Tribal Knowledge to Machine-Readable Evolution Context"

Usage:
    python experiments/paper1_ontology_manifests/expand_and_rerun_rq4_rq5.py
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Optional

import requests
import yaml
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _THIS_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("expand_rq4_rq5")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
RESULTS_DIR = _THIS_DIR / "results" / "real"
TASKS_PATH = RESULTS_DIR / "phase4_agentic" / "tasks.json"
POPULATION_DIR = RESULTS_DIR / "phase2_population"
MANIFESTS_DIR = RESULTS_DIR / "phase3_manifests"
RQ4_RQ5_DIR = RESULTS_DIR / "rq4_rq5"
JCSSE_DIR = PROJECT_ROOT / "experiments" / "jcsse2026" / "results"
CORPUS_PATH = JCSSE_DIR / "expanded_corpus.json"
EVO_GAP_PATH = JCSSE_DIR / "rq2_evolution_gap.json"

# Target 10 new repos — prefer higher stars + supported languages
SUPPORTED_LANGUAGES = {"python", "javascript", "typescript", "java", "go", "ruby",
                       "rust", "kotlin", "scala", "swift"}
TARGET_NEW_REPOS = 10

LEHMAN_LAW_NAMES = {
    1: "Continuing Change", 2: "Increasing Complexity", 3: "Self Regulation",
    4: "Conservation of Organizational Stability", 5: "Conservation of Familiarity",
    6: "Continuing Growth", 7: "Declining Quality", 8: "Feedback System",
}


# ---------------------------------------------------------------------------
# GitHub API
# ---------------------------------------------------------------------------
class GitHubAPI:
    """Lightweight GitHub API client with rate-limit handling."""

    BASE = "https://api.github.com"

    def __init__(self, token: str):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        })

    def get(self, endpoint: str, params: dict = None) -> Any:
        url = f"{self.BASE}/{endpoint}" if not endpoint.startswith("http") else endpoint
        r = self.session.get(url, params=params, timeout=30)
        remaining = int(r.headers.get("X-RateLimit-Remaining", 999))
        if remaining < 20:
            reset = int(r.headers.get("X-RateLimit-Reset", 0))
            wait = max(reset - time.time(), 0) + 2
            logger.warning("Rate limit low (%d). Sleeping %.0fs", remaining, wait)
            time.sleep(wait)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 403:
            time.sleep(60)
            return self.get(endpoint, params)
        return None

    def get_file_content(self, repo: str, path: str) -> Optional[str]:
        data = self.get(f"repos/{repo}/contents/{path}")
        if data and isinstance(data, dict) and "content" in data:
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return None

    def get_closed_issues_with_prs(self, repo: str, per_page: int = 30) -> list[dict]:
        """Get closed issues that have linked PRs (for task curation)."""
        issues = self.get(f"repos/{repo}/issues", params={
            "state": "closed", "per_page": per_page, "sort": "updated",
            "direction": "desc",
        })
        if not issues:
            return []
        # Filter to issues with pull_request link
        return [i for i in issues if i.get("pull_request")]

    def get_pr_diff(self, repo: str, pr_number: int) -> Optional[str]:
        """Get the diff for a PR."""
        url = f"{self.BASE}/repos/{repo}/pulls/{pr_number}"
        r = self.session.get(url, headers={"Accept": "application/vnd.github.v3.diff"}, timeout=30)
        if r.status_code == 200:
            return r.text
        return None

    def get_pr_details(self, repo: str, pr_number: int) -> Optional[dict]:
        return self.get(f"repos/{repo}/pulls/{pr_number}")

    def get_repo_tree(self, repo: str, sha: str = "HEAD") -> list[dict]:
        """Get the file tree for architecture analysis."""
        data = self.get(f"repos/{repo}/git/trees/{sha}", params={"recursive": "1"})
        if data and "tree" in data:
            return [t for t in data["tree"] if t.get("type") == "blob"]
        return []


# ---------------------------------------------------------------------------
# NIM helpers
# ---------------------------------------------------------------------------
_DEAD_MODELS: set[str] = set()


def _get_nim_client() -> Optional[dict]:
    """Get primary NIM client for manifest generation."""
    from openai import OpenAI
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        return None
    return {
        "model": "meta/llama-3.3-70b-instruct",
        "org": "Meta",
        "client": OpenAI(base_url=NIM_BASE_URL, api_key=api_key,
                         max_retries=1, timeout=120.0),
    }


def _call_nim(client_info: dict, prompt: str, temperature: float = 0,
              max_tokens: int = 2048) -> str:
    model = client_info["model"]
    if model in _DEAD_MODELS:
        return ""
    try:
        resp = client_info["client"].chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""
    except Exception as exc:
        logger.warning("NIM call failed (%s): %s", model, str(exc)[:200])
        return ""


# ---------------------------------------------------------------------------
# Step 1: Select 10 architecture-sensitive repos from JCSSE corpus
# ---------------------------------------------------------------------------

def select_repos() -> list[dict]:
    """Select 10 evolution-positive repos from JCSSE corpus.

    Criteria:
    - evolution_context_present = True in JCSSE classification
    - Not already in current experiment
    - Supported language
    - Prioritise: multiple evolution dimensions > higher evo_frac > higher stars
    """
    # Load JCSSE evolution gap data
    with open(EVO_GAP_PATH) as f:
        gap = json.load(f)

    # Load corpus for metadata
    with open(CORPUS_PATH) as f:
        corpus = json.load(f)
    corpus_map = {r["full_name"]: r for r in corpus}

    # Load current tasks to exclude existing repos
    if TASKS_PATH.exists():
        with open(TASKS_PATH) as f:
            tasks = json.load(f)
        current_repos = {t["repo"] for t in tasks}
    else:
        current_repos = set()

    candidates = []
    for m in gap["per_manifest"]:
        repo = m["repo"]
        if not m["evolution_context_present"]:
            continue
        if repo in current_repos:
            continue

        info = corpus_map.get(repo, {})
        lang = (info.get("language") or "").lower()
        stars = info.get("stars", 0)

        # Filter to supported languages
        if lang not in SUPPORTED_LANGUAGES:
            logger.debug("Skipping %s (language: %s)", repo, lang)
            continue

        dims = sum([
            m.get("dim_phase_mentioned", False),
            m.get("dim_complexity_trend", False),
            m.get("dim_tech_debt", False),
            m.get("dim_refactoring_plans", False),
            m.get("dim_churn_trajectory", False),
        ])

        candidates.append({
            "repo": repo,
            "language": lang,
            "stars": stars,
            "evo_frac": m["evolution_char_frac"],
            "evo_dims": dims,
            "manifest_content": info.get("manifest_content", ""),
        })

    # Sort: most evolution dimensions first, then evo fraction, then stars
    candidates.sort(key=lambda x: (-x["evo_dims"], -x["evo_frac"], -x["stars"]))

    selected = candidates[:TARGET_NEW_REPOS]
    logger.info("Selected %d new repos from JCSSE corpus:", len(selected))
    for r in selected:
        logger.info("  %-45s stars=%-5d lang=%-12s evo=%.1f%% dims=%d",
                    r["repo"], r["stars"], r["language"],
                    r["evo_frac"] * 100, r["evo_dims"])

    return selected


# ---------------------------------------------------------------------------
# Step 2: Populate repos (Phase 2 — lightweight, no Fuseki needed)
# ---------------------------------------------------------------------------

def populate_repo(repo_name: str, language: str, gh: GitHubAPI) -> dict:
    """Lightweight population: mine basic stats from GitHub API.

    Returns population dict compatible with Phase 2 format.
    """
    cache_path = POPULATION_DIR / f"{repo_name.replace('/', '__')}.json"
    if cache_path.exists():
        logger.info("  Population cached for %s", repo_name)
        with open(cache_path) as f:
            return json.load(f)

    logger.info("  Populating %s...", repo_name)

    # Get repo metadata
    repo_data = gh.get(f"repos/{repo_name}")
    if not repo_data:
        logger.warning("  Could not fetch repo data for %s", repo_name)
        return {}

    # Get recent commits for activity analysis
    commits = gh.get(f"repos/{repo_name}/commits", params={
        "per_page": 100, "since": "2024-01-01T00:00:00Z"
    }) or []

    # Get contributors
    contributors = gh.get(f"repos/{repo_name}/contributors", params={"per_page": 30}) or []

    # Detect agent commits
    agent_commits = 0
    for c in commits:
        msg = (c.get("commit", {}).get("message", "") or "").lower()
        author = (c.get("commit", {}).get("author", {}).get("name", "") or "").lower()
        if any(x in msg for x in ["co-authored-by: github-actions", "co-authored-by: dependabot",
                                    "co-authored-by: claude", "generated by"]):
            agent_commits += 1
        if any(x in author for x in ["bot", "dependabot", "github-actions"]):
            agent_commits += 1

    # Get file tree for architecture analysis
    tree = gh.get_repo_tree(repo_name)
    src_files = [t for t in tree if not t["path"].startswith(".") and
                 any(t["path"].endswith(ext) for ext in
                     [".py", ".js", ".ts", ".tsx", ".java", ".go", ".rb", ".rs",
                      ".kt", ".scala", ".swift", ".c", ".cpp", ".h"])]

    # Identify modules (top-level directories)
    modules: dict[str, int] = {}
    for f in src_files:
        parts = f["path"].split("/")
        if len(parts) > 1:
            mod = parts[0]
            modules[mod] = modules.get(mod, 0) + 1

    # Determine phase from commit activity
    total_commits = len(commits)
    if total_commits > 80:
        phase = "growth"
    elif total_commits > 20:
        phase = "stabilization"
    else:
        phase = "decline"

    # Law conformance heuristics
    law_conformance = {
        "law_1": total_commits > 0,
        "law_2": True,  # assume conforming unless we have complexity data
        "law_3": True,
        "law_4": len(contributors) > 1,
        "law_5": True,
        "law_6": total_commits > 10,
        "law_7": True,
        "law_8": agent_commits / max(total_commits, 1) < 0.5,
    }

    pop = {
        "repo": repo_name,
        "language": language,
        "status": "completed",
        "total_commits": total_commits,
        "total_months": 12,
        "total_triples": 0,
        "triples_loaded": 0,
        "phase": phase,
        "law_conformance": law_conformance,
        "stars": repo_data.get("stargazers_count", 0),
        "agent_commits": agent_commits,
        "agent_ratio": round(agent_commits / max(total_commits, 1), 3),
        "modules": [{"name": k, "file_count": v} for k, v in
                    sorted(modules.items(), key=lambda x: -x[1])[:20]],
        "total_files": len(src_files),
        "contributors": len(contributors),
    }

    POPULATION_DIR.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(pop, f, indent=2)

    return pop


# ---------------------------------------------------------------------------
# Step 3: Generate SENSO manifests
# ---------------------------------------------------------------------------

def generate_senso_manifest(repo_name: str, pop: dict, nim_client: dict) -> str:
    """Generate SENSO evolution-aware manifest for a repo.

    Uses population data to create a manifest with phase awareness,
    complexity hotspots, and architectural guidance.
    """
    cache_path = MANIFESTS_DIR / f"{repo_name.replace('/', '__')}_senso.md"
    if cache_path.exists():
        logger.info("  SENSO manifest cached for %s", repo_name)
        return cache_path.read_text()

    logger.info("  Generating SENSO manifest for %s...", repo_name)

    lang = pop.get("language", "unknown")
    phase = pop.get("phase", "unknown")
    total_commits = pop.get("total_commits", 0)
    law_conformance = pop.get("law_conformance", {})
    modules = pop.get("modules", [])
    total_files = pop.get("total_files", 0)
    agent_ratio = pop.get("agent_ratio", 0)
    contributors = pop.get("contributors", 0)

    phase_details = {
        "growth": "Active feature development with increasing commit volume. Focus on maintainability and test coverage.",
        "stabilization": "Mature maintenance phase with steady commit patterns. Focus on refactoring, dependency updates, and architectural hygiene.",
        "decline": "Declining activity with reduced contributor engagement. Minimize scope of changes, focus on critical bug fixes only.",
        "unknown": "Insufficient history to determine evolution phase.",
    }

    # Law conformance section
    law_lines = []
    violations = []
    for i in range(1, 9):
        key = f"law_{i}"
        conforms = law_conformance.get(key, True)
        name = LEHMAN_LAW_NAMES.get(i, f"Law {i}")
        status = "Conforming" if conforms else "**VIOLATION**"
        law_lines.append(f"- Law {i} ({name}): {status}")
        if not conforms:
            violations.append(f"Law {i} ({name})")

    # Recommendations
    recommendations = []
    if phase == "growth":
        recommendations.append("Ensure new features include adequate test coverage before merging.")
    elif phase == "stabilization":
        recommendations.append("Prefer refactoring over new feature additions to maintain stability.")
        recommendations.append("Avoid introducing new cross-module dependencies.")
    elif phase == "decline":
        recommendations.append("Limit changes to critical fixes; avoid introducing new dependencies.")

    if not law_conformance.get("law_8", True):
        recommendations.append("Feedback loop is broken (Law VIII violation). Increase review scrutiny on agent-generated code.")
    if agent_ratio > 0.3:
        recommendations.append(f"Agent contribution is high ({agent_ratio:.0%}). Review for architectural alignment.")

    # Module section
    mod_lines = []
    if modules:
        for mod in modules[:10]:
            pct = mod["file_count"] / max(total_files, 1) * 100
            mod_lines.append(f"- **{mod['name']}/** — {mod['file_count']} files ({pct:.0f}% of codebase)")
        largest = modules[0]
        largest_pct = largest["file_count"] / max(total_files, 1) * 100
        if largest_pct > 60:
            recommendations.append(f"Module `{largest['name']}/` is overly concentrated ({largest_pct:.0f}%). Consider decomposing into sub-modules.")

    manifest = f"""# {repo_name} — Evolution-Aware Manifest (SENSO)

## Evolution Phase: {phase.title()}
{phase_details.get(phase, '')}

## Project Overview
- **Language**: {lang}
- **Commits analyzed**: {total_commits} (recent 12 months)
- **Contributors**: {contributors}

## Agent Contribution
- Agent-authored commits: {pop.get('agent_commits', 0)} ({agent_ratio:.0%} of recent commits)
{'- Agent contribution within safe range' if agent_ratio <= 0.3 else '- **WARNING**: High agent contribution — review for hidden tech debt'}

## Lehman's Law Conformance
{chr(10).join(law_lines)}

{'**Active violations**: ' + ', '.join(violations) if violations else 'All laws conforming.'}

## Recommendations
{chr(10).join('- ' + r for r in recommendations)}

## Architectural Guidance
### Module Structure ({len(modules)} source modules, {total_files} files)
{chr(10).join(mod_lines) if mod_lines else '- Architecture data not available'}

### Development Guidelines
- When modifying large modules, check for downstream dependencies
- Prefer extending existing modules over creating new top-level directories
- In stabilization phase: decompose before extending, avoid new cross-module imports
"""

    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(manifest)
    return manifest


# ---------------------------------------------------------------------------
# Step 4: Curate architecture-sensitive tasks
# ---------------------------------------------------------------------------

def curate_arch_sensitive_tasks(repo: dict, pop: dict, senso_manifest: str,
                                 gh: GitHubAPI, max_tasks: int = 5) -> list[dict]:
    """Curate architecture-sensitive tasks from closed issues.

    Filter criteria (from study design):
    1. Ground-truth diff modifies a file with coupling fan-out > project p75, OR
    2. Ground-truth diff introduces or removes a cross-module dependency, OR
    3. Ground-truth diff touches a file in a module the SENSO ontology labels
       as in stabilization/decline phase.

    Simplified for API-only approach: select issues whose PRs modify files in the
    largest modules (highest coupling risk) flagged in the SENSO manifest.
    """
    repo_name = repo["repo"]
    language = repo.get("language", "unknown")

    # Extract flagged modules from SENSO manifest
    flagged_modules = set()
    for line in senso_manifest.split("\n"):
        m = re.search(r"\*\*(\S+?)/\*\*", line)
        if m:
            flagged_modules.add(m.group(1))

    # Also use population module data — focus on top modules (highest concentration)
    top_modules = [m["name"] for m in pop.get("modules", [])[:5]]
    flagged_modules.update(top_modules)

    logger.info("  Flagged modules for %s: %s", repo_name, flagged_modules)

    # Get closed issues with PRs
    issues = gh.get_closed_issues_with_prs(repo_name, per_page=50)
    if not issues:
        logger.warning("  No closed issues with PRs for %s", repo_name)
        return []

    tasks = []
    for issue in issues:
        if len(tasks) >= max_tasks:
            break

        # Get the linked PR
        pr_url = issue.get("pull_request", {}).get("url", "")
        if not pr_url:
            continue

        pr_number = int(pr_url.rstrip("/").split("/")[-1])

        # Get PR diff
        diff = gh.get_pr_diff(repo_name, pr_number)
        if not diff:
            continue

        # Check diff size (skip very large or very small diffs)
        diff_lines = len(diff.split("\n"))
        if diff_lines < 5 or diff_lines > 1500:
            continue

        # Extract changed files
        changed_files = re.findall(r"^diff --git a/(.+?) b/", diff, re.MULTILINE)
        if not changed_files:
            continue

        # Architecture-sensitivity check: does the diff touch flagged modules?
        touches_flagged = False
        for f in changed_files:
            parts = f.split("/")
            if parts and parts[0] in flagged_modules:
                touches_flagged = True
                break

        if not touches_flagged:
            continue

        # Get PR details for pre-fix commit
        pr_details = gh.get_pr_details(repo_name, pr_number)
        pre_fix_commit = ""
        if pr_details:
            pre_fix_commit = pr_details.get("base", {}).get("sha", "")

        # Build task
        task = {
            "task_id": f"{repo_name.replace('/', '_')}_issue_{issue['number']}",
            "repo": repo_name,
            "language": language,
            "issue_number": issue["number"],
            "issue_title": issue.get("title", ""),
            "issue_description": issue.get("body", "") or "",
            "pre_fix_commit": pre_fix_commit,
            "ground_truth_diff": diff[:10000],
            "test_commands": [],
            "ground_truth_files_changed": changed_files,
            "human_manifest": repo.get("manifest_content", ""),
            "senso_manifest": senso_manifest,
            "arch_sensitive": True,
            "touches_flagged_modules": [f.split("/")[0] for f in changed_files
                                        if f.split("/")[0] in flagged_modules],
        }
        tasks.append(task)
        logger.info("    Task: #%d %s (%d files, touches: %s)",
                    issue["number"], issue.get("title", "")[:50],
                    len(changed_files),
                    task["touches_flagged_modules"])

    return tasks


# ---------------------------------------------------------------------------
# Step 5: Filter existing tasks for architecture sensitivity
# ---------------------------------------------------------------------------

def filter_existing_tasks(tasks: list[dict], repo_phases: dict[str, str]) -> list[dict]:
    """Re-filter existing tasks: only keep those touching stabilization-phase modules.

    For existing tasks, check if the ground_truth_files_changed touch modules
    that appear in the SENSO manifest for their repo.
    """
    filtered = []
    for task in tasks:
        repo = task.get("repo", "")
        phase = repo_phases.get(repo, "unknown")
        senso = task.get("senso_manifest", "")

        # Extract flagged modules from SENSO manifest
        flagged = set()
        for line in senso.split("\n"):
            m = re.search(r"\*\*(\S+?)/\*\*", line)
            if m:
                flagged.add(m.group(1))

        # Check if changed files touch flagged modules
        changed = task.get("ground_truth_files_changed", [])
        touches_flagged = any(
            f.split("/")[0] in flagged
            for f in changed if "/" in f
        )

        if touches_flagged or phase == "stabilization":
            task["arch_sensitive"] = True
            filtered.append(task)

    return filtered


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Expand and re-run RQ4/RQ5 with architecture-sensitive repos."""

    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        logger.error("GITHUB_TOKEN not set")
        sys.exit(1)

    gh = GitHubAPI(token)
    nim_client = _get_nim_client()

    # Step 1: Select 10 new repos
    logger.info("=" * 70)
    logger.info("Step 1: Select architecture-sensitive repos from JCSSE corpus")
    logger.info("=" * 70)
    new_repos = select_repos()

    if not new_repos:
        logger.error("No new repos selected — check JCSSE corpus and language filter")
        sys.exit(1)

    # Step 2: Populate and generate SENSO manifests
    logger.info("\n" + "=" * 70)
    logger.info("Step 2: Populate + generate SENSO manifests")
    logger.info("=" * 70)

    for repo in new_repos:
        repo_name = repo["repo"]
        language = repo["language"]

        # Populate
        pop = populate_repo(repo_name, language, gh)
        if not pop:
            continue

        # Generate SENSO manifest
        if nim_client:
            senso = generate_senso_manifest(repo_name, pop, nim_client)
            repo["senso_manifest"] = senso
            repo["population"] = pop
        else:
            logger.warning("No NIM client — cannot generate SENSO manifest for %s", repo_name)

    # Step 3: Curate architecture-sensitive tasks from new repos
    logger.info("\n" + "=" * 70)
    logger.info("Step 3: Curate architecture-sensitive tasks")
    logger.info("=" * 70)

    new_tasks: list[dict] = []
    for repo in new_repos:
        repo_name = repo["repo"]
        pop = repo.get("population", {})
        senso = repo.get("senso_manifest", "")

        if not pop or not senso:
            logger.warning("  Skipping %s (no population or manifest)", repo_name)
            continue

        tasks = curate_arch_sensitive_tasks(repo, pop, senso, gh, max_tasks=5)
        new_tasks.extend(tasks)
        logger.info("  %s: %d architecture-sensitive tasks", repo_name, len(tasks))

    logger.info("Total new tasks curated: %d", len(new_tasks))

    # Step 4: Filter existing tasks for architecture sensitivity
    logger.info("\n" + "=" * 70)
    logger.info("Step 4: Filter existing tasks for architecture sensitivity")
    logger.info("=" * 70)

    # Load existing tasks
    if TASKS_PATH.exists():
        with open(TASKS_PATH) as f:
            existing_tasks = json.load(f)
        logger.info("Loaded %d existing tasks", len(existing_tasks))
    else:
        existing_tasks = []

    # Load repo phases
    repo_phases: dict[str, str] = {}
    if POPULATION_DIR.exists():
        for p in POPULATION_DIR.glob("*.json"):
            try:
                with open(p) as f:
                    data = json.load(f)
                repo_phases[data.get("repo", p.stem.replace("__", "/"))] = data.get("phase", "unknown")
            except Exception:
                pass

    filtered_existing = filter_existing_tasks(existing_tasks, repo_phases)
    logger.info("Existing tasks after arch-sensitivity filter: %d/%d",
                len(filtered_existing), len(existing_tasks))

    # Merge
    all_tasks = filtered_existing + new_tasks
    logger.info("\nCombined task set: %d tasks (%d filtered existing + %d new)",
                len(all_tasks), len(filtered_existing), len(new_tasks))

    repos_in_set = sorted({t["repo"] for t in all_tasks})
    logger.info("Repos in expanded set (%d):", len(repos_in_set))
    for r in repos_in_set:
        n = sum(1 for t in all_tasks if t["repo"] == r)
        phase = repo_phases.get(r, "unknown")
        logger.info("  %-45s %d tasks  phase=%s", r, n, phase)

    # Save expanded task set
    expanded_tasks_path = RESULTS_DIR / "phase4_agentic" / "tasks_expanded.json"
    expanded_tasks_path.parent.mkdir(parents=True, exist_ok=True)
    with open(expanded_tasks_path, "w") as f:
        json.dump(all_tasks, f, indent=2, default=str)
    logger.info("\nSaved expanded tasks to %s", expanded_tasks_path)

    # Step 5: Clear old RQ4-5 cache and re-run
    logger.info("\n" + "=" * 70)
    logger.info("Step 5: Clear old cache and prepare for re-run")
    logger.info("=" * 70)

    # Update the main tasks.json to point to the expanded set
    with open(TASKS_PATH, "w") as f:
        json.dump(all_tasks, f, indent=2, default=str)
    logger.info("Updated %s with %d tasks", TASKS_PATH, len(all_tasks))

    # Clear old RQ4-5 cache
    raw_cache = RQ4_RQ5_DIR / "raw_results.json"
    report_cache = RQ4_RQ5_DIR / "rq4_rq5_report.json"
    for cache_file in [raw_cache, report_cache]:
        if cache_file.exists():
            cache_file.unlink()
            logger.info("Deleted cache: %s", cache_file)

    logger.info("\n" + "=" * 70)
    logger.info("READY — Run the experiment:")
    logger.info("  python experiments/paper1_ontology_manifests/run_rq4_rq5.py")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
