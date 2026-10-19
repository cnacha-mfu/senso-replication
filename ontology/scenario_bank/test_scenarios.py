#!/usr/bin/env python3
"""Scenario bank testing for the Software Evolution Ontology (SEO).

Paper 1 — Phase 1C: Loads evolution scenarios from scenarios.yaml, instantiates
them as OWL individuals in the SEO ontology, runs HermiT reasoning, and checks
inferred phases, law conformance, and evolution patterns against expected values.

Usage:
    cd /tmp && python /home/ubuntu/git/senso-framework/ontology/scenario_bank/test_scenarios.py

Requires:
    - owlready2
    - pyyaml
    - Java runtime (for HermiT reasoner)
"""

import argparse
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# WP1: the label-deciding functions moved to the frozen oracle module. They are
# imported here only so this JSS-era runner keeps working; the ontology is the
# labeller (see differential_test.py).
from ontology.scenario_bank.legacy_oracle import (  # noqa: E402
    check_law_conformance,
    detect_patterns,
    determine_phase_from_snapshot,
)
ONTOLOGY_MODULES_DIR = PROJECT_ROOT / "ontology" / "modules"
SCENARIOS_FILE = Path(__file__).resolve().parent / "scenarios.yaml"

# SEO IRI prefix
SEO_IRI = "http://senso-framework.org/ontology/seo#"


@dataclass
class ScenarioResult:
    """Result of evaluating a single scenario against ontology inferences.

    Paper 1 — tracks per-scenario precision/recall for phases, laws, patterns.
    """

    scenario_id: str
    scenario_name: str
    # Phase
    expected_phase: str
    inferred_phase: str
    phase_correct: bool
    # Law conformance
    law_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    # Pattern detection
    expected_patterns: list[str] = field(default_factory=list)
    inferred_patterns: list[str] = field(default_factory=list)
    pattern_tp: int = 0
    pattern_fp: int = 0
    pattern_fn: int = 0


def load_scenarios(path: Path) -> list[dict[str, Any]]:
    """Load scenario definitions from YAML file.

    Paper 1 — Phase 1C scenario bank loader.

    Args:
        path: Path to scenarios.yaml

    Returns:
        List of scenario dictionaries.
    """
    logger.info("Loading scenarios from %s", path)
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    scenarios = data.get("scenarios", [])
    logger.info("Loaded %d scenarios", len(scenarios))
    return scenarios


def evaluate_scenario(scenario: dict[str, Any]) -> ScenarioResult:
    """Evaluate a single scenario against ontology inference heuristics.

    Paper 1 — Phase 1C scenario evaluation. When OWL ontology files are
    available in ontology/modules/, this function will load them and use
    HermiT for reasoning. Currently uses equivalent Python heuristics
    that mirror the SWRL rules.

    Args:
        scenario: Scenario dict from scenarios.yaml.

    Returns:
        ScenarioResult with comparison details.
    """
    sid = scenario["id"]
    name = scenario["name"]
    months = scenario["repo_snapshot"]["months"]

    expected_phase = scenario["expected_phase"]
    expected_laws = scenario["expected_law_conformance"]
    expected_patterns = scenario.get("expected_patterns", [])

    # Try to use OWL ontology if available
    inferred_phase, inferred_laws, inferred_patterns = _reason_with_owl_or_heuristics(months)

    # Phase comparison
    phase_correct = inferred_phase == expected_phase

    # Law conformance comparison
    law_results: dict[str, dict[str, Any]] = {}
    for law_num in ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]:
        expected = expected_laws.get(law_num, True)
        inferred = inferred_laws.get(law_num, True)
        law_results[law_num] = {
            "expected": expected,
            "inferred": inferred,
            "correct": expected == inferred,
        }

    # Pattern comparison
    expected_set = set(expected_patterns)
    inferred_set = set(inferred_patterns)
    tp = len(expected_set & inferred_set)
    fp = len(inferred_set - expected_set)
    fn = len(expected_set - inferred_set)

    return ScenarioResult(
        scenario_id=sid,
        scenario_name=name,
        expected_phase=expected_phase,
        inferred_phase=inferred_phase,
        phase_correct=phase_correct,
        law_results=law_results,
        expected_patterns=expected_patterns,
        inferred_patterns=inferred_patterns,
        pattern_tp=tp,
        pattern_fp=fp,
        pattern_fn=fn,
    )


def _reason_with_owl_or_heuristics(
    months: list[dict[str, Any]],
) -> tuple[str, dict[str, bool], list[str]]:
    """Attempt OWL reasoning; fall back to heuristics if ontology not available.

    Paper 1 — Phase 1C. When the OWL ontology modules are built (Phase 1A),
    this function will:
    1. Load the SEO ontology via Owlready2
    2. Create OWL individuals from the snapshot data
    3. Run HermiT reasoner
    4. Extract inferred classes and property values

    Until then, uses equivalent Python heuristics.

    Args:
        months: Monthly snapshot data.

    Returns:
        Tuple of (phase, law_conformance, patterns).
    """
    owl_files = list(ONTOLOGY_MODULES_DIR.glob("*.owl")) + list(ONTOLOGY_MODULES_DIR.glob("*.rdf"))

    if owl_files:
        try:
            return _reason_with_owl(months, owl_files)
        except Exception as e:
            logger.warning("OWL reasoning failed, falling back to heuristics: %s", e)

    # Fallback to heuristics
    phase = determine_phase_from_snapshot(months)
    laws = check_law_conformance(months)
    patterns = detect_patterns(months)
    return phase, laws, patterns


def _reason_with_owl(
    months: list[dict[str, Any]], owl_files: list[Path]
) -> tuple[str, dict[str, bool], list[str]]:
    """Perform OWL-based reasoning using Owlready2 and HermiT.

    Paper 1 — Phase 1C OWL reasoning path. Creates temporary OWL
    individuals from scenario data, runs HermiT, and extracts inferred
    classifications.

    Args:
        months: Monthly snapshot data.
        owl_files: List of OWL ontology file paths.

    Returns:
        Tuple of (phase, law_conformance, patterns).

    Raises:
        ImportError: If owlready2 is not installed.
        Exception: If reasoning fails.
    """
    import owlready2  # type: ignore[import-untyped]

    onto = owlready2.get_ontology(str(owl_files[0])).load()

    # Load additional modules
    for owl_file in owl_files[1:]:
        owlready2.get_ontology(str(owl_file)).load()

    # Create individuals from snapshot data
    with onto:
        # Create a project individual
        project_cls = onto.search_one(iri=f"{SEO_IRI}SoftwareProject")
        if project_cls is None:
            logger.warning("SoftwareProject class not found in ontology")
            raise ValueError("SoftwareProject class not found")

        project = project_cls("test_project_scenario")

        # Create version/metric individuals for each month
        for i, month_data in enumerate(months):
            version_cls = onto.search_one(iri=f"{SEO_IRI}Version")
            if version_cls:
                version = version_cls(f"version_{i}")
                # Set properties if they exist
                for prop_name, value_key in [
                    ("hasLOC", "loc"),
                    ("hasCommitCount", "commits"),
                    ("hasComplexityAvg", "complexity_avg"),
                    ("hasDependencyCount", "dependency_count"),
                    ("hasAgentCommitRatio", "agent_commit_ratio"),
                ]:
                    prop = onto.search_one(iri=f"{SEO_IRI}{prop_name}")
                    if prop and value_key in month_data:
                        try:
                            setattr(version, prop_name, [month_data[value_key]])
                        except Exception:
                            pass

    # Run HermiT reasoner
    try:
        with onto:
            owlready2.sync_reasoner_hermit(infer_property_values=True)
    except Exception as e:
        logger.warning("HermiT reasoning error: %s", e)

    # Extract inferred phase
    phase = determine_phase_from_snapshot(months)  # Fallback
    growth_cls = onto.search_one(iri=f"{SEO_IRI}GrowthPhase")
    stab_cls = onto.search_one(iri=f"{SEO_IRI}StabilizationPhase")
    decline_cls = onto.search_one(iri=f"{SEO_IRI}DeclinePhase")

    if growth_cls and project in growth_cls.instances():
        phase = "growth"
    elif stab_cls and project in stab_cls.instances():
        phase = "stabilization"
    elif decline_cls and project in decline_cls.instances():
        phase = "decline"

    # For laws and patterns, use heuristics as fallback
    # (full OWL encoding of all 8 laws as SWRL rules is in Phase 1A)
    laws = check_law_conformance(months)
    patterns = detect_patterns(months)

    # Clean up the ontology world to avoid cross-scenario contamination
    owlready2.default_world.close()

    return phase, laws, patterns


def compute_aggregate_metrics(
    results: list[ScenarioResult],
) -> dict[str, Any]:
    """Compute aggregate precision/recall across all scenarios.

    Paper 1 — Phase 1C aggregate evaluation metrics.

    Args:
        results: List of per-scenario results.

    Returns:
        Dict with phase_accuracy, law_accuracy (per law and overall),
        pattern_precision, pattern_recall, pattern_f1.
    """
    # Phase accuracy
    phase_correct = sum(1 for r in results if r.phase_correct)
    phase_accuracy = phase_correct / max(len(results), 1)

    # Law accuracy per law and overall
    law_accuracies: dict[str, float] = {}
    total_law_correct = 0
    total_law_count = 0
    for law_num in ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]:
        correct = sum(1 for r in results if r.law_results.get(law_num, {}).get("correct", False))
        law_accuracies[law_num] = correct / max(len(results), 1)
        total_law_correct += correct
        total_law_count += len(results)

    overall_law_accuracy = total_law_correct / max(total_law_count, 1)

    # Pattern precision/recall
    total_tp = sum(r.pattern_tp for r in results)
    total_fp = sum(r.pattern_fp for r in results)
    total_fn = sum(r.pattern_fn for r in results)

    pattern_precision = total_tp / max(total_tp + total_fp, 1)
    pattern_recall = total_tp / max(total_tp + total_fn, 1)
    pattern_f1 = (
        2 * pattern_precision * pattern_recall / max(pattern_precision + pattern_recall, 1e-9)
    )

    return {
        "phase_accuracy": phase_accuracy,
        "law_accuracies": law_accuracies,
        "overall_law_accuracy": overall_law_accuracy,
        "pattern_precision": pattern_precision,
        "pattern_recall": pattern_recall,
        "pattern_f1": pattern_f1,
        "total_scenarios": len(results),
    }


def print_report(results: list[ScenarioResult], metrics: dict[str, Any]) -> None:
    """Print a formatted evaluation report.

    Paper 1 — Phase 1C scenario bank test report.

    Args:
        results: Per-scenario results.
        metrics: Aggregate metrics dict.
    """
    logger.info("=" * 80)
    logger.info("SCENARIO BANK EVALUATION REPORT — Paper 1, Phase 1C")
    logger.info("=" * 80)

    # Per-scenario details
    for r in results:
        phase_mark = "PASS" if r.phase_correct else "FAIL"
        logger.info(
            "\n[%s] %s (%s)",
            r.scenario_id,
            r.scenario_name,
            phase_mark,
        )
        logger.info(
            "  Phase: expected=%s, inferred=%s [%s]",
            r.expected_phase,
            r.inferred_phase,
            phase_mark,
        )

        # Laws
        law_pass = sum(1 for v in r.law_results.values() if v["correct"])
        law_total = len(r.law_results)
        logger.info("  Laws: %d/%d correct", law_pass, law_total)
        for law_num in ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]:
            lr = r.law_results.get(law_num, {})
            mark = "PASS" if lr.get("correct", False) else "FAIL"
            logger.info(
                "    Law %s: expected=%s, inferred=%s [%s]",
                law_num,
                lr.get("expected"),
                lr.get("inferred"),
                mark,
            )

        # Patterns
        logger.info(
            "  Patterns: expected=%s, inferred=%s (TP=%d, FP=%d, FN=%d)",
            r.expected_patterns,
            r.inferred_patterns,
            r.pattern_tp,
            r.pattern_fp,
            r.pattern_fn,
        )

    # Aggregate summary
    logger.info("\n" + "=" * 80)
    logger.info("AGGREGATE METRICS")
    logger.info("=" * 80)
    logger.info("Phase accuracy: %.1f%% (%d/%d)",
                metrics["phase_accuracy"] * 100,
                int(metrics["phase_accuracy"] * metrics["total_scenarios"]),
                metrics["total_scenarios"])

    logger.info("Law conformance accuracy (per law):")
    for law_num, acc in metrics["law_accuracies"].items():
        logger.info("  Law %s: %.1f%%", law_num, acc * 100)
    logger.info("Overall law accuracy: %.1f%%", metrics["overall_law_accuracy"] * 100)

    logger.info("Pattern detection:")
    logger.info("  Precision: %.1f%%", metrics["pattern_precision"] * 100)
    logger.info("  Recall:    %.1f%%", metrics["pattern_recall"] * 100)
    logger.info("  F1:        %.1f%%", metrics["pattern_f1"] * 100)


def main() -> None:
    """Run scenario bank evaluation.

    Paper 1 — Phase 1C entry point. Loads scenarios, evaluates each
    against ontology inferences, and reports results.
    """
    parser = argparse.ArgumentParser(
        description="Paper 1 Phase 1C: Scenario bank testing for SEO ontology"
    )
    parser.add_argument(
        "--scenarios",
        type=str,
        default=str(SCENARIOS_FILE),
        help="Path to scenarios.yaml (default: ontology/scenario_bank/scenarios.yaml)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    scenarios_path = Path(args.scenarios)
    if not scenarios_path.exists():
        logger.error("Scenarios file not found: %s", scenarios_path)
        sys.exit(1)

    scenarios = load_scenarios(scenarios_path)

    results: list[ScenarioResult] = []
    for scenario in scenarios:
        result = evaluate_scenario(scenario)
        results.append(result)

    metrics = compute_aggregate_metrics(results)
    print_report(results, metrics)

    # Exit with non-zero if accuracy is below threshold
    if metrics["phase_accuracy"] < 0.7:
        logger.warning("Phase accuracy below 70%% threshold")
        sys.exit(1)
    if metrics["overall_law_accuracy"] < 0.6:
        logger.warning("Overall law accuracy below 60%% threshold")
        sys.exit(1)

    logger.info("\nAll scenario bank tests completed successfully.")


if __name__ == "__main__":
    main()
