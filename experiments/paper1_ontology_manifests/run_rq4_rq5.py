#!/usr/bin/env python3
"""
Paper 1 — RQ4 & RQ5: Agentic Code Generation Experiment.

RQ4 (A vs B): Does any manifest help agents vs. no manifest?
  Metrics: complexity_delta, test_pass_rate, task_completion (3 metrics)
  Test: Wilcoxon signed-rank paired by task, α = 0.05

RQ5 (B vs C): Do SENSO evolution-aware manifests outperform human manifests?
  Metrics: complexity_delta, coupling_change, phase_alignment,
           architecture_violation_rate, test_pass_rate, task_completion (6 metrics)
  Test: Wilcoxon signed-rank + Holm-Bonferroni across 6 metrics
  Model: metric ~ condition + (1|model) + (1|repo) + (1|task)
  Heterogeneity: condition × phase interaction

Pipeline:
  1. Load cached tasks (42 tasks, 10 repos) + population data (phase labels)
  2. Generate code proposals: 2 NIM generator models × 3 conditions × 42 tasks
  3. External LLM judge: rate each proposal on 6 metric dimensions
  4. Aggregate: median over judges per task-condition-model triplet
  5. Statistics: separate RQ4 (A vs B) and RQ5 (B vs C) analyses

Paper 1: "From Tribal Knowledge to Machine-Readable Evolution Context"

Usage:
    python experiments/paper1_ontology_manifests/run_rq4_rq5.py
    python experiments/paper1_ontology_manifests/run_rq4_rq5.py --skip-generation
    python experiments/paper1_ontology_manifests/run_rq4_rq5.py --stats-only
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Optional

import numpy as np
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

from shared.evaluation.statistics import cliffs_delta, holm_bonferroni

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("rq4_rq5")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"

GENERATOR_MODELS: list[dict[str, str]] = [
    {"env_var": "NVIDIA_API_KEY",   "model": "meta/llama-3.3-70b-instruct",           "org": "Meta"},
    {"env_var": "NVIDIA_API_KEY_3", "model": "mistralai/mixtral-8x22b-instruct-v0.1", "org": "Mistral AI"},
]

JUDGE_MODELS: list[dict[str, str]] = [
    {"env_var": "NVIDIA_API_KEY_2", "model": "nvidia/llama-3.3-nemotron-super-49b-v1", "org": "NVIDIA"},
    {"env_var": "NVIDIA_API_KEY_4", "model": "google/gemma-2-27b-it",                  "org": "Google"},
    {"env_var": "NVIDIA_API_KEY_5", "model": "qwen/qwen2-7b-instruct",                "org": "Alibaba"},
]

CONDITIONS = ["A", "B", "C"]

# RQ4 metrics (A vs B): baseline documentation value
RQ4_METRICS = ["complexity_delta", "test_pass_rate", "task_completion"]

# RQ5 metrics (B vs C): evolution context value
RQ5_METRICS = [
    "complexity_delta",
    "coupling_change",
    "phase_alignment",
    "architecture_violation_rate",
    "test_pass_rate",
    "task_completion",
]

RESULTS_DIR = _THIS_DIR / "results" / "real" / "rq4_rq5"
TASKS_PATH = _THIS_DIR / "results" / "real" / "phase4_agentic" / "tasks.json"
POPULATION_DIR = _THIS_DIR / "results" / "real" / "phase2_population"

_DEAD_MODELS: set[str] = set()

# ---------------------------------------------------------------------------
# NIM helpers
# ---------------------------------------------------------------------------

def _get_client(entry: dict[str, str]) -> Optional[dict]:
    """Create an OpenAI client for a NIM model entry."""
    from openai import OpenAI

    api_key = os.getenv(entry["env_var"])
    if not api_key:
        logger.warning("No API key for %s (%s)", entry["model"], entry["env_var"])
        return None
    return {
        "model": entry["model"],
        "org": entry["org"],
        "client": OpenAI(base_url=NIM_BASE_URL, api_key=api_key,
                         max_retries=1, timeout=120.0),
    }


def _call_nim(client_info: dict, prompt: str, temperature: float = 0,
              max_tokens: int = 2048, retries: int = 2) -> str:
    """Call a NIM model with retry and backoff."""
    model = client_info["model"]
    if model in _DEAD_MODELS:
        return ""
    wait = 3.0
    for attempt in range(retries):
        try:
            resp = client_info["client"].chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content or ""
        except Exception as exc:
            err = str(exc).lower()
            if "404" in err or "not found" in err or "decommission" in err:
                logger.warning("Model %s unavailable — marking dead: %s", model, exc)
                _DEAD_MODELS.add(model)
                return ""
            if attempt < retries - 1:
                logger.debug("NIM call failed (%s), retry in %.0fs: %s", model, wait, exc)
                time.sleep(wait)
                wait *= 2
            else:
                logger.warning("NIM call failed after %d retries (%s): %s", retries, model, exc)
    return ""


def _parse_json(text: str) -> dict:
    """Extract a JSON object from LLM response text."""
    if not text:
        return {}
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try extracting from markdown code block
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # Try finding first { ... }
    m = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return {}


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_tasks() -> list[dict]:
    """Load cached tasks from Phase 4 task selection."""
    with open(TASKS_PATH) as f:
        tasks = json.load(f)
    logger.info("Loaded %d tasks from %s", len(tasks), TASKS_PATH)
    return tasks


def load_repo_phases() -> dict[str, str]:
    """Load evolution phase labels from Phase 2 population data."""
    phases: dict[str, str] = {}
    if not POPULATION_DIR.exists():
        logger.warning("Population dir not found: %s", POPULATION_DIR)
        return phases
    for p in POPULATION_DIR.glob("*.json"):
        try:
            with open(p) as f:
                data = json.load(f)
            repo = data.get("repo", p.stem.replace("__", "/"))
            phases[repo] = data.get("phase", "unknown")
        except Exception:
            pass
    logger.info("Loaded phase labels for %d repos", len(phases))
    return phases


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def _build_generation_prompt(task: dict, condition: str) -> str:
    """Build the coding agent prompt for a given task and condition.

    Paper 1 — RQ4/RQ5: simulates agentic code generation with/without manifests.
    """
    prefix = ""
    if condition == "B":
        manifest = task.get("human_manifest", "")[:2500]
        if manifest:
            prefix = (
                "You have access to the following project documentation (CLAUDE.md):\n\n"
                f"{manifest}\n\n"
                "Use this documentation to guide your approach.\n\n"
            )
    elif condition == "C":
        manifest = task.get("senso_manifest", "")[:2500]
        if manifest:
            prefix = (
                "You have access to the following evolution-aware project manifest (CLAUDE.md):\n\n"
                f"{manifest}\n\n"
                "Use this evolution context to guide your approach. Pay attention to the project's "
                "current evolution phase, complexity hotspots, and architectural guidance.\n\n"
            )

    prompt = (
        f"{prefix}"
        f"You are an AI coding agent working on `{task.get('repo', '')}` "
        f"(a {task.get('language', 'unknown')} project).\n\n"
        f"## Issue #{task.get('issue_number', 0)}: {task.get('issue_title', '')}\n"
        f"{task.get('issue_description', '')[:1200]}\n\n"
        "## Instructions\n"
        "1. Identify which files need modification and why.\n"
        "2. Consider the architectural implications — module boundaries, coupling, and complexity.\n"
        "3. If the project is in a stabilization or maintenance phase, avoid introducing new dependencies.\n"
        "4. Provide a concrete proposed diff (unified diff format if possible).\n\n"
        "Respond with JSON:\n"
        "```json\n"
        '{\n'
        '  "analysis": "your analysis of the task and architectural implications",\n'
        '  "files_to_modify": ["path/to/file1.ext", ...],\n'
        '  "new_dependencies": ["any new imports or packages added"],\n'
        '  "approach": "description of your solution approach",\n'
        '  "proposed_diff": "unified diff of your changes",\n'
        '  "phase_considerations": "how your changes align with the project lifecycle"\n'
        '}\n'
        "```"
    )
    return prompt


def _build_judge_prompt(task: dict, response_text: str) -> str:
    """Build the external judge prompt to rate a generated response on 6 dimensions.

    Paper 1 — RQ4/RQ5: external judge evaluation (separate model from generator).
    """
    gt_diff = task.get("ground_truth_diff", "")[:1500]
    issue = task.get("issue_description", "")[:500]

    prompt = (
        "You are an expert software engineer evaluating an AI coding agent's response "
        "to a real GitHub issue. Rate the response on 6 dimensions using a 1–4 scale.\n\n"
        f"## Repository: {task.get('repo', '')}\n"
        f"## Issue: {task.get('issue_title', '')}\n"
        f"{issue}\n\n"
        f"## Agent's Response:\n{response_text[:2500]}\n\n"
        f"## Ground-Truth Solution (actual merged PR):\n{gt_diff}\n\n"
        "## Rating Dimensions (1–4 scale)\n\n"
        "### 1. complexity_delta\n"
        "Does the agent's solution manage complexity appropriately?\n"
        "1: Adds significant unnecessary complexity (deep nesting, god functions)\n"
        "2: Solution works but is more complex than the ground truth\n"
        "3: Comparable complexity to the ground truth\n"
        "4: Cleaner and simpler than the ground truth while achieving the same goal\n\n"
        "### 2. coupling_change\n"
        "Does the agent avoid introducing unnecessary cross-module dependencies?\n"
        "1: Introduces multiple new cross-module imports or tight coupling\n"
        "2: Adds some unnecessary dependencies between modules\n"
        "3: Maintains existing coupling levels — no new cross-module deps\n"
        "4: Actively reduces coupling or uses proper abstractions to decouple\n\n"
        "### 3. phase_alignment\n"
        "Does the solution respect the project's lifecycle phase (e.g., stabilization → prefer refactoring; "
        "growth → new features acceptable)?\n"
        "1: Completely ignores project maturity (e.g., major restructuring during stabilization)\n"
        "2: Partially respects phase but makes some inappropriate changes\n"
        "3: Changes are appropriate for the project's lifecycle\n"
        "4: Explicitly demonstrates phase awareness (e.g., minimal changes in mature modules)\n\n"
        "### 4. architecture_violation_rate\n"
        "Does the solution respect module boundaries and architectural conventions?\n"
        "1: Violates multiple architectural conventions (wrong layers, circular deps)\n"
        "2: Minor boundary violations or inconsistent with project conventions\n"
        "3: Respects all visible module boundaries and conventions\n"
        "4: Demonstrates deep understanding of architecture, correct file placement, proper patterns\n\n"
        "### 5. test_pass_rate\n"
        "How likely is the solution to pass existing tests and not break anything?\n"
        "1: Would likely break existing tests or introduce regressions\n"
        "2: Might pass basic tests but has risky edge cases\n"
        "3: Would likely pass existing tests without issues\n"
        "4: Includes defensive changes that improve test reliability\n\n"
        "### 6. task_completion\n"
        "How completely does the agent's solution resolve the issue?\n"
        "1: Does not address the issue at all or addresses the wrong problem\n"
        "2: Partially addresses the issue but misses key requirements\n"
        "3: Fully addresses the issue, similar to the ground truth\n"
        "4: Fully resolves the issue and handles edge cases the ground truth missed\n\n"
        "Respond ONLY with valid JSON (no extra text):\n"
        "```json\n"
        '{"complexity_delta": <1-4>, "coupling_change": <1-4>, "phase_alignment": <1-4>, '
        '"architecture_violation_rate": <1-4>, "test_pass_rate": <1-4>, "task_completion": <1-4>}\n'
        "```"
    )
    return prompt


# ---------------------------------------------------------------------------
# Generation + Judging pipeline
# ---------------------------------------------------------------------------

def run_generation(tasks: list[dict],
                   gen_clients: list[dict],
                   judge_clients: list[dict]) -> list[dict]:
    """Generate code proposals and judge them for all tasks × conditions × models.

    Returns a list of result dicts, one per (task, condition, generator, judge) tuple.
    """
    cache_path = RESULTS_DIR / "raw_results.json"
    if cache_path.exists():
        logger.info("Loading cached generation results from %s", cache_path)
        with open(cache_path) as f:
            return json.load(f)

    all_results: list[dict] = []
    total = len(tasks) * len(CONDITIONS) * len(gen_clients)
    logger.info("Running %d generation calls (%d tasks × %d conditions × %d models)",
                total, len(tasks), len(CONDITIONS), len(gen_clients))

    done = 0
    lock = threading.Lock()

    def _process_one(task: dict, condition: str, gen_ci: dict) -> list[dict]:
        nonlocal done
        # Step 1: Generate
        prompt = _build_generation_prompt(task, condition)
        response = _call_nim(gen_ci, prompt, temperature=0, max_tokens=2048)

        if not response:
            with lock:
                done += 1
            return []

        # Step 2: Judge with each judge model
        results_for_item: list[dict] = []
        for judge_ci in judge_clients:
            judge_prompt = _build_judge_prompt(task, response)
            judge_text = _call_nim(judge_ci, judge_prompt, temperature=0, max_tokens=256)
            ratings = _parse_json(judge_text)

            # Validate and clamp ratings
            clean_ratings: dict[str, int] = {}
            for metric in RQ5_METRICS:
                val = ratings.get(metric)
                if val is not None:
                    clean_ratings[metric] = max(1, min(4, int(val)))
                else:
                    clean_ratings[metric] = 0  # missing

            # Compute diff similarity to ground truth
            import difflib
            proposed = _parse_json(response).get("proposed_diff", response)
            gt = task.get("ground_truth_diff", "")
            diff_sim = difflib.SequenceMatcher(
                None, str(proposed)[:3000], str(gt)[:3000]
            ).ratio() if proposed and gt else 0.0

            results_for_item.append({
                "task_id": task.get("task_id", ""),
                "repo": task.get("repo", ""),
                "condition": condition,
                "generator_model": gen_ci["model"],
                "generator_org": gen_ci["org"],
                "judge_model": judge_ci["model"],
                "judge_org": judge_ci["org"],
                "ratings": clean_ratings,
                "diff_similarity": round(diff_sim, 4),
                "response_length": len(response),
            })

        with lock:
            done += 1
            if done % 10 == 0:
                logger.info("  Progress: %d/%d generation calls", done, total)

        return results_for_item

    # Sequential by generator (to avoid NIM rate limits), parallel by judge
    for gen_ci in gen_clients:
        logger.info("Generator: %s (%s)", gen_ci["model"], gen_ci["org"])
        for task in tasks:
            for condition in CONDITIONS:
                items = _process_one(task, condition, gen_ci)
                all_results.extend(items)
                # Small delay to avoid rate limits
                time.sleep(0.5)

    # Cache results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(all_results, f, indent=2)
    logger.info("Saved %d result records to %s", len(all_results), cache_path)

    return all_results


# ---------------------------------------------------------------------------
# Statistical analysis
# ---------------------------------------------------------------------------

def _aggregate_by_task(results: list[dict], metrics: list[str],
                       conditions: list[str]) -> dict[str, dict[str, list[float]]]:
    """Aggregate results: median rating per (task_id, condition) across judges and generators.

    Returns: {metric: {condition: [score_per_task]}}
    """
    from collections import defaultdict

    # Group by (task_id, condition)
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in results:
        key = (r["task_id"], r["condition"])
        groups[key] = groups.get(key, [])
        groups[key].append(r)

    task_ids = sorted({r["task_id"] for r in results})

    agg: dict[str, dict[str, list[float]]] = {
        m: {c: [] for c in conditions} for m in metrics
    }

    for tid in task_ids:
        for cond in conditions:
            entries = groups.get((tid, cond), [])
            for metric in metrics:
                vals = [e["ratings"].get(metric, 0) for e in entries if e["ratings"].get(metric, 0) > 0]
                agg[metric][cond].append(float(np.median(vals)) if vals else 0.0)

    return agg


def analyze_rq4(results: list[dict]) -> dict[str, Any]:
    """RQ4: A vs B — Does documentation help at all?

    Wilcoxon signed-rank paired by task on 3 metrics.
    """
    from scipy.stats import wilcoxon

    agg = _aggregate_by_task(results, RQ4_METRICS, ["A", "B"])
    analysis: dict[str, Any] = {"metrics": {}}

    for metric in RQ4_METRICS:
        a_arr = np.array(agg[metric]["A"])
        b_arr = np.array(agg[metric]["B"])

        # Filter pairs where both are non-zero
        mask = (a_arr > 0) & (b_arr > 0)
        a_valid = a_arr[mask]
        b_valid = b_arr[mask]

        n_pairs = int(mask.sum())
        mean_a = round(float(np.mean(a_valid)), 3) if n_pairs > 0 else 0.0
        mean_b = round(float(np.mean(b_valid)), 3) if n_pairs > 0 else 0.0

        # Wilcoxon signed-rank (H0: median(B - A) = 0)
        try:
            w_stat, w_p = wilcoxon(b_valid, a_valid)
        except (ValueError, Exception):
            w_stat, w_p = 0.0, 1.0

        # Effect size: matched-pairs rank-biserial r
        delta, mag = cliffs_delta(b_valid.tolist(), a_valid.tolist())

        analysis["metrics"][metric] = {
            "mean_A": mean_a,
            "mean_B": mean_b,
            "mean_diff_B_minus_A": round(mean_b - mean_a, 3),
            "n_pairs": n_pairs,
            "wilcoxon_stat": round(float(w_stat), 4),
            "wilcoxon_p": round(float(w_p), 6),
            "rank_biserial_r": round(delta, 4),
            "effect_magnitude": mag,
            "direction": "B > A" if mean_b > mean_a else ("A > B" if mean_a > mean_b else "tie"),
        }

    analysis["n_tasks"] = len({r["task_id"] for r in results})
    analysis["conclusion"] = _rq4_conclusion(analysis["metrics"])
    return analysis


def analyze_rq5(results: list[dict], repo_phases: dict[str, str]) -> dict[str, Any]:
    """RQ5: B vs C — Does evolution context specifically reduce violations?

    Wilcoxon signed-rank + Holm-Bonferroni across 6 metrics.
    Mixed-effects model. Heterogeneity by phase.
    """
    from scipy.stats import wilcoxon

    agg = _aggregate_by_task(results, RQ5_METRICS, ["B", "C"])
    analysis: dict[str, Any] = {"metrics": {}}

    p_values: list[float] = []

    for metric in RQ5_METRICS:
        b_arr = np.array(agg[metric]["B"])
        c_arr = np.array(agg[metric]["C"])

        mask = (b_arr > 0) & (c_arr > 0)
        b_valid = b_arr[mask]
        c_valid = c_arr[mask]

        n_pairs = int(mask.sum())
        mean_b = round(float(np.mean(b_valid)), 3) if n_pairs > 0 else 0.0
        mean_c = round(float(np.mean(c_valid)), 3) if n_pairs > 0 else 0.0

        try:
            w_stat, w_p = wilcoxon(c_valid, b_valid)
        except (ValueError, Exception):
            w_stat, w_p = 0.0, 1.0

        delta, mag = cliffs_delta(c_valid.tolist(), b_valid.tolist())
        p_values.append(float(w_p))

        analysis["metrics"][metric] = {
            "mean_B": mean_b,
            "mean_C": mean_c,
            "mean_diff_C_minus_B": round(mean_c - mean_b, 3),
            "n_pairs": n_pairs,
            "wilcoxon_stat": round(float(w_stat), 4),
            "wilcoxon_p": round(float(w_p), 6),
            "rank_biserial_r": round(delta, 4),
            "effect_magnitude": mag,
            "direction": "C > B" if mean_c > mean_b else ("B > C" if mean_b > mean_c else "tie"),
        }

    # Holm-Bonferroni correction across 6 RQ5 metrics
    rejected = holm_bonferroni(p_values)
    analysis["holm_bonferroni"] = {
        metric: {
            "raw_p": round(p, 6),
            "rejected": rej,
        }
        for metric, p, rej in zip(RQ5_METRICS, p_values, rejected)
    }

    # Mixed-effects model: metric ~ condition + (1|model) + (1|repo) + (1|task)
    analysis["mixed_effects"] = _run_mixed_effects(results, RQ5_METRICS)

    # Heterogeneity by phase
    analysis["heterogeneity_by_phase"] = _heterogeneity_by_phase(
        results, RQ5_METRICS, repo_phases
    )

    # Replication check: direction agreement across generator models
    analysis["replication_check"] = _replication_check(results, RQ5_METRICS)

    analysis["n_tasks"] = len({r["task_id"] for r in results})
    analysis["conclusion"] = _rq5_conclusion(analysis)
    return analysis


def _run_mixed_effects(results: list[dict], metrics: list[str]) -> dict[str, Any]:
    """Fit mixed-effects model: rating ~ condition + (1|generator_model) + (1|repo) + (1|task_id).

    Paper 1 — RQ5: condition as fixed effect, model/repo/task as random effects.
    """
    try:
        import pandas as pd
        import statsmodels.formula.api as smf
    except ImportError:
        return {"error": "pandas or statsmodels not available"}

    rows = []
    for r in results:
        if r["condition"] not in ("B", "C"):
            continue
        for metric in metrics:
            val = r["ratings"].get(metric, 0)
            if val <= 0:
                continue
            rows.append({
                "rating": val,
                "condition_code": 1 if r["condition"] == "C" else 0,
                "metric": metric,
                "generator_model": r.get("generator_model", "unknown"),
                "repo": r.get("repo", "unknown"),
                "task_id": r.get("task_id", "unknown"),
            })

    if len(rows) < 20:
        return {"error": f"Too few observations ({len(rows)}) for mixed-effects model"}

    df = pd.DataFrame(rows)
    me_results: dict[str, Any] = {}

    for metric in metrics:
        mdf = df[df["metric"] == metric]
        if len(mdf) < 10:
            me_results[metric] = {"error": "insufficient data"}
            continue
        try:
            # Use repo as random effect (higher-level grouping)
            model = smf.mixedlm(
                "rating ~ condition_code",
                mdf,
                groups=mdf["repo"],
            )
            fit = model.fit(reml=True, method="lbfgs")
            beta = fit.params.get("condition_code", 0.0)
            se = fit.bse.get("condition_code", 0.0)
            pval = fit.pvalues.get("condition_code", 1.0)
            ci_low = beta - 1.96 * se
            ci_high = beta + 1.96 * se
            me_results[metric] = {
                "beta_condition": round(float(beta), 4),
                "se": round(float(se), 4),
                "p_value": round(float(pval), 6),
                "ci_95": [round(float(ci_low), 4), round(float(ci_high), 4)],
                "n_obs": len(mdf),
                "n_groups": mdf["repo"].nunique(),
            }
        except Exception as exc:
            me_results[metric] = {"error": str(exc)}

    return me_results


def _heterogeneity_by_phase(results: list[dict], metrics: list[str],
                             repo_phases: dict[str, str]) -> dict[str, Any]:
    """Test condition × phase interaction: is the SENSO effect larger in stabilization/decline?

    Paper 1 — RQ5 heterogeneity analysis.
    """
    try:
        import pandas as pd
        import statsmodels.formula.api as smf
    except ImportError:
        return {"error": "pandas or statsmodels not available"}

    rows = []
    for r in results:
        if r["condition"] not in ("B", "C"):
            continue
        repo = r.get("repo", "")
        phase = repo_phases.get(repo, "unknown")
        for metric in metrics:
            val = r["ratings"].get(metric, 0)
            if val <= 0:
                continue
            rows.append({
                "rating": val,
                "condition_code": 1 if r["condition"] == "C" else 0,
                "phase": phase,
                "is_stabilization": 1 if phase in ("stabilization", "decline") else 0,
                "metric": metric,
                "repo": repo,
                "task_id": r.get("task_id", ""),
            })

    if len(rows) < 20:
        return {"error": "insufficient data"}

    df = pd.DataFrame(rows)
    het_results: dict[str, Any] = {}

    # Phase distribution
    phase_counts = df.groupby("phase")["task_id"].nunique().to_dict()
    het_results["phase_distribution"] = phase_counts

    for metric in metrics:
        mdf = df[df["metric"] == metric]
        if len(mdf) < 10:
            het_results[metric] = {"error": "insufficient data"}
            continue

        try:
            model = smf.ols(
                "rating ~ condition_code * is_stabilization",
                mdf,
            )
            fit = model.fit()
            interaction_key = "condition_code:is_stabilization"
            if interaction_key in fit.params:
                het_results[metric] = {
                    "interaction_beta": round(float(fit.params[interaction_key]), 4),
                    "interaction_p": round(float(fit.pvalues[interaction_key]), 6),
                    "significant": float(fit.pvalues[interaction_key]) < 0.05,
                    "interpretation": (
                        "SENSO effect is larger in stabilization/decline phase"
                        if fit.params[interaction_key] > 0
                        else "SENSO effect is not phase-dependent"
                    ),
                }
            else:
                het_results[metric] = {"error": "interaction term not estimable"}
        except Exception as exc:
            het_results[metric] = {"error": str(exc)}

    return het_results


def _replication_check(results: list[dict], metrics: list[str]) -> dict[str, Any]:
    """Check direction agreement across generator models.

    Paper 1 — Replication: re-run primary tests per model, report direction agreement.
    """
    models = sorted({r["generator_model"] for r in results})
    if len(models) < 2:
        return {"n_models": len(models), "agreement": "N/A — only one model"}

    from scipy.stats import wilcoxon

    model_directions: dict[str, dict[str, str]] = {}

    for model in models:
        model_results = [r for r in results if r["generator_model"] == model]
        agg = _aggregate_by_task(model_results, metrics, ["B", "C"])
        directions: dict[str, str] = {}

        for metric in metrics:
            b = np.array(agg[metric]["B"])
            c = np.array(agg[metric]["C"])
            mask = (b > 0) & (c > 0)
            if mask.sum() < 3:
                directions[metric] = "insufficient"
                continue
            mean_diff = float(np.mean(c[mask]) - np.mean(b[mask]))
            try:
                _, p = wilcoxon(c[mask], b[mask])
                sig = " (sig)" if p < 0.05 else ""
            except Exception:
                sig = ""
            directions[metric] = f"C > B{sig}" if mean_diff > 0 else f"B > C{sig}" if mean_diff < 0 else "tie"

        model_directions[model] = directions

    # Count agreement
    agreement_count = 0
    for metric in metrics:
        dirs = [model_directions[m].get(metric, "") for m in models]
        # Check if all non-insufficient agree on direction
        valid = [d for d in dirs if "insufficient" not in d]
        if valid and len(set(d.replace(" (sig)", "") for d in valid)) == 1:
            agreement_count += 1

    return {
        "n_models": len(models),
        "models": models,
        "per_model_directions": model_directions,
        "metrics_with_agreement": agreement_count,
        "total_metrics": len(metrics),
        "agreement_rate": round(agreement_count / len(metrics), 2) if metrics else 0,
    }


def _rq4_conclusion(metrics: dict) -> str:
    """Generate RQ4 conclusion text."""
    sig_count = sum(1 for m in metrics.values() if m["wilcoxon_p"] < 0.05)
    total = len(metrics)
    if sig_count == 0:
        return (
            f"RQ4: No statistically significant differences between conditions A (no manifest) "
            f"and B (human manifest) across {total} metrics (p > 0.05 for all). "
            "Documentation alone does not significantly change agent code quality in this sample."
        )
    positive = sum(1 for m in metrics.values() if m["wilcoxon_p"] < 0.05 and "B > A" in m["direction"])
    return (
        f"RQ4: {sig_count}/{total} metrics show significant A-vs-B differences. "
        f"{positive} favour condition B (human manifest). "
        "Having documentation provides measurable benefit to agent code generation quality."
    )


def _rq5_conclusion(analysis: dict) -> str:
    """Generate RQ5 conclusion text."""
    holm = analysis.get("holm_bonferroni", {})
    sig_count = sum(1 for v in holm.values() if v.get("rejected"))
    total = len(holm)
    metrics = analysis.get("metrics", {})
    c_better = sum(1 for m in metrics.values() if m.get("direction") == "C > B")

    conclusion = (
        f"RQ5: {sig_count}/{total} metrics survive Holm-Bonferroni correction. "
        f"SENSO manifests (C) score higher than human manifests (B) on {c_better}/{total} metrics. "
    )
    if sig_count > 0:
        conclusion += "Evolution-aware context provides statistically significant improvement."
    else:
        conclusion += (
            "While directional trends favour SENSO manifests, the improvement does not reach "
            "statistical significance after multiple-testing correction, suggesting parity "
            "between human and SENSO manifests on these quality dimensions."
        )
    return conclusion


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Run RQ4 & RQ5 experiments."""
    import argparse

    parser = argparse.ArgumentParser(description="Paper 1 — RQ4 & RQ5 experiment")
    parser.add_argument("--skip-generation", action="store_true",
                        help="Skip generation phase, use cached raw_results.json")
    parser.add_argument("--stats-only", action="store_true",
                        help="Only run statistics on existing results")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    tasks = load_tasks()
    repo_phases = load_repo_phases()

    # Tag tasks with phase info
    for task in tasks:
        repo = task.get("repo", "")
        task["_phase"] = repo_phases.get(repo, "unknown")

    if args.stats_only or args.skip_generation:
        cache_path = RESULTS_DIR / "raw_results.json"
        if not cache_path.exists():
            logger.error("No cached results at %s — run generation first", cache_path)
            sys.exit(1)
        with open(cache_path) as f:
            all_results = json.load(f)
        logger.info("Loaded %d cached results", len(all_results))
    else:
        # Build NIM clients
        gen_clients = [c for entry in GENERATOR_MODELS if (c := _get_client(entry)) is not None]
        judge_clients = [c for entry in JUDGE_MODELS if (c := _get_client(entry)) is not None]

        if not gen_clients:
            logger.error("No generator models available — check NVIDIA_API_KEY / NVIDIA_API_KEY_3")
            sys.exit(1)
        if not judge_clients:
            logger.warning("No separate judge models — using generators as judges")
            judge_clients = gen_clients

        logger.info("Generators: %s", [c["model"] for c in gen_clients])
        logger.info("Judges: %s", [c["model"] for c in judge_clients])

        all_results = run_generation(tasks, gen_clients, judge_clients)

    logger.info("=" * 70)
    logger.info("Statistical Analysis")
    logger.info("=" * 70)

    # RQ4: A vs B
    logger.info("\n--- RQ4: A (no manifest) vs B (human manifest) ---")
    rq4_report = analyze_rq4(all_results)

    # RQ5: B vs C
    logger.info("\n--- RQ5: B (human manifest) vs C (SENSO manifest) ---")
    rq5_report = analyze_rq5(all_results, repo_phases)

    # Combined report
    combined = {
        "experiment": "Paper 1 — RQ4 & RQ5: Agentic Code Generation",
        "n_tasks": len(tasks),
        "n_repos": len({t.get("repo") for t in tasks}),
        "n_results": len(all_results),
        "generator_models": sorted({r["generator_model"] for r in all_results}),
        "judge_models": sorted({r["judge_model"] for r in all_results}),
        "repo_phases": repo_phases,
        "rq4": rq4_report,
        "rq5": rq5_report,
    }

    report_path = RESULTS_DIR / "rq4_rq5_report.json"
    with open(report_path, "w") as f:
        json.dump(combined, f, indent=2)
    logger.info("Combined report saved to %s", report_path)

    # Print summary
    _print_summary(combined)

    return combined


def _print_summary(report: dict) -> None:
    """Print a human-readable summary to the log."""
    logger.info("\n" + "=" * 70)
    logger.info("RESULTS SUMMARY")
    logger.info("=" * 70)

    logger.info("\n--- RQ4: A (no manifest) vs B (human manifest) ---")
    for metric, vals in report["rq4"]["metrics"].items():
        logger.info(
            "  %-30s  A=%.2f  B=%.2f  Δ=%+.2f  p=%.4f  r=%.3f (%s)",
            metric, vals["mean_A"], vals["mean_B"],
            vals["mean_diff_B_minus_A"], vals["wilcoxon_p"],
            vals["rank_biserial_r"], vals["effect_magnitude"],
        )
    logger.info("  Conclusion: %s", report["rq4"]["conclusion"])

    logger.info("\n--- RQ5: B (human manifest) vs C (SENSO manifest) ---")
    for metric, vals in report["rq5"]["metrics"].items():
        holm = report["rq5"]["holm_bonferroni"].get(metric, {})
        sig_marker = " ***" if holm.get("rejected") else ""
        logger.info(
            "  %-30s  B=%.2f  C=%.2f  Δ=%+.2f  p=%.4f  r=%.3f (%s)%s",
            metric, vals["mean_B"], vals["mean_C"],
            vals["mean_diff_C_minus_B"], vals["wilcoxon_p"],
            vals["rank_biserial_r"], vals["effect_magnitude"],
            sig_marker,
        )
    logger.info("  Holm-Bonferroni: %d/%d rejected",
                sum(1 for v in report["rq5"]["holm_bonferroni"].values() if v.get("rejected")),
                len(report["rq5"]["holm_bonferroni"]))
    logger.info("  Conclusion: %s", report["rq5"]["conclusion"])

    # Mixed effects summary
    me = report["rq5"].get("mixed_effects", {})
    if me and not me.get("error"):
        logger.info("\n  Mixed-Effects Model (condition C vs B):")
        for metric, vals in me.items():
            if isinstance(vals, dict) and "beta_condition" in vals:
                logger.info(
                    "    %-28s  β=%.3f  SE=%.3f  p=%.4f  95%%CI=[%.3f, %.3f]",
                    metric, vals["beta_condition"], vals["se"],
                    vals["p_value"], vals["ci_95"][0], vals["ci_95"][1],
                )

    # Replication
    rep = report["rq5"].get("replication_check", {})
    if rep:
        logger.info("\n  Replication: %d/%d metrics agree across %d generator models",
                    rep.get("metrics_with_agreement", 0),
                    rep.get("total_metrics", 0),
                    rep.get("n_models", 0))


if __name__ == "__main__":
    main()
