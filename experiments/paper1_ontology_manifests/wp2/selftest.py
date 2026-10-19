"""WP2 self-test of seo-claims.owl (Paper 1, RQ2; design section 4 "Self-test").

Builds one synthetic claim per leaf class, with exact boundary values under the default
thresholds (T2 commits 1/2/4/5, lines 99/100, consensus votes 1/2), reasons with HermiT and
asserts the expected leaf and verdict, that the ABox is consistent, and that each claim is in
exactly one verdict class. A second check loads the TBox WITHOUT seo-claims and asserts that
zero verdict triples appear (the WP1 "done" test).

Usage:
    python experiments/paper1_ontology_manifests/wp2_consistency.py selftest
"""

from __future__ import annotations

import json
import logging
import sys
import tempfile
from pathlib import Path
from typing import Any

from . import common as C

logger = logging.getLogger("wp2.selftest")

T1, T2, T3, T4, T5, T6, T7 = ("PathExistenceClaim", "PathStatusClaim", "ToolUsageClaim", "DependencyClaim",
                              "CommandClaim", "VersionClaim", "ImportConstraintClaim")
S, K_, U, I, K = "SupportedClaim", "ContradictedClaim", "UnverifiableClaim", "IndeterminateClaim", "ConflictedClaim"


def cases() -> list[dict[str, Any]]:
    """The synthetic claims: name, types, props, optional evidences, expected leaf (None = unmeasured)."""
    def c(name, types, props, leaf, verdict, evs=None, votes=2):
        return {"name": name, "types": types, "props": props, "leaf": leaf, "verdict": verdict,
                "evs": evs or [], "votes": votes}
    out = [
        # T1
        c("t1_exact", [T1], {"pathExactMatchCount": 1, "pathSuffixMatchCount": 0, "pathIgnoredCount": 0, "pathSubmoduleCount": 0, "pathEverTrackedCount": 3}, "PathFoundExact", S),
        c("t1_suffix", [T1], {"pathExactMatchCount": 0, "pathSuffixMatchCount": 1, "pathIgnoredCount": 0, "pathSubmoduleCount": 0, "pathEverTrackedCount": 0}, "PathFoundBySuffix", S),
        c("t1_ignored", [T1], {"pathExactMatchCount": 0, "pathSuffixMatchCount": 0, "pathIgnoredCount": 1, "pathSubmoduleCount": 0, "pathEverTrackedCount": 0}, "PathUntrackedByDesign", U),
        c("t1_submodule", [T1], {"pathExactMatchCount": 0, "pathSuffixMatchCount": 0, "pathIgnoredCount": 0, "pathSubmoduleCount": 1, "pathEverTrackedCount": 0}, "PathInSubmodule", U),
        c("t1_removed_boundary1", [T1], {"pathExactMatchCount": 0, "pathSuffixMatchCount": 0, "pathIgnoredCount": 0, "pathSubmoduleCount": 0, "pathEverTrackedCount": 1}, "PathRemoved", K_),
        c("t1_never_boundary0", [T1], {"pathExactMatchCount": 0, "pathSuffixMatchCount": 0, "pathIgnoredCount": 0, "pathSubmoduleCount": 0, "pathEverTrackedCount": 0}, "PathNeverExisted", K_),
        c("t1_unmeasured", [T1], {}, None, None),
        c("t1_one_vote_only", [T1], {"pathExactMatchCount": 1, "pathSuffixMatchCount": 0, "pathIgnoredCount": 0, "pathSubmoduleCount": 0, "pathEverTrackedCount": 1}, None, None, votes=1),
        # T2 (window 180, support_max 1, min_commits 5, min_lines 100)
        c("t2_commits0", ["InactiveStatusClaim"], {"pathCommitsIn180d": 0, "pathLinesChangedIn180d": 0}, "InactivePathQuiet", S),
        c("t2_commits1_boundary", ["InactiveStatusClaim"], {"pathCommitsIn180d": 1, "pathLinesChangedIn180d": 5000}, "InactivePathQuiet", S),
        c("t2_commits2_moderate", ["InactiveStatusClaim"], {"pathCommitsIn180d": 2, "pathLinesChangedIn180d": 5000}, "InactivePathModerate", I),
        c("t2_commits4_moderate", ["InactiveStatusClaim"], {"pathCommitsIn180d": 4, "pathLinesChangedIn180d": 5000}, "InactivePathModerate", I),
        c("t2_commits5_lines99_moderate", ["InactiveStatusClaim"], {"pathCommitsIn180d": 5, "pathLinesChangedIn180d": 99}, "InactivePathModerate", I),
        c("t2_commits5_lines100_active", ["InactiveStatusClaim"], {"pathCommitsIn180d": 5, "pathLinesChangedIn180d": 100}, "InactivePathActive", K_),
        c("t2_unresolved", ["InactiveStatusClaim"], {"pathExactMatchCount": 0, "pathSuffixMatchCount": 0}, "StatusPathUnresolved", U),
        c("t2_ambiguous", ["InactiveStatusClaim"], {"pathExactMatchCount": 0, "pathSuffixMatchCount": 2}, "StatusPathAmbiguous", U),
        # T3
        c("t3_found", [T3, "NonPackageManagerToolClaim"], {"toolSignatureHitCount": 1, "toolEcosystemAnchorCount": 1, "competingToolSignatureCount": 0}, "ToolSignatureFound", S),
        c("t3_competitor", [T3, "PackageManagerClaim"], {"toolSignatureHitCount": 0, "toolEcosystemAnchorCount": 1, "competingToolSignatureCount": 1}, "ToolAbsentCompetitorPresent", K_),
        c("t3_pkgmgr_absent_no_competitor", [T3, "PackageManagerClaim"], {"toolSignatureHitCount": 0, "toolEcosystemAnchorCount": 1, "competingToolSignatureCount": 0}, "ToolAbsentInEcosystem", K_),
        c("t3_test_absent_with_competing", [T3, "NonPackageManagerToolClaim"], {"toolSignatureHitCount": 0, "toolEcosystemAnchorCount": 2, "competingToolSignatureCount": 1}, "ToolAbsentInEcosystem", K_),
        c("t3_ecosystem_absent", [T3, "NonPackageManagerToolClaim"], {"toolSignatureHitCount": 0, "toolEcosystemAnchorCount": 0, "competingToolSignatureCount": 0}, "ToolEcosystemAbsent", U),
        # T4
        c("t4_confirmed", [T4, "UnversionedDependencyClaim"], {"dependencyExactMatchCount": 1, "dependencySuffixMatchCount": 1, "dependencyManifestParsedCount": 2}, "DependencyConfirmed", S),
        c("t4_confirmed_suffix", [T4, "UnversionedDependencyClaim"], {"dependencyExactMatchCount": 0, "dependencySuffixMatchCount": 1, "dependencyManifestParsedCount": 2}, "DependencyConfirmed", S),
        c("t4_undeclared", [T4, "UnversionedDependencyClaim"], {"dependencyExactMatchCount": 0, "dependencySuffixMatchCount": 0, "dependencyManifestParsedCount": 1}, "DependencyUndeclared", K_),
        c("t4_nomanifest", [T4, "UnversionedDependencyClaim"], {"dependencyExactMatchCount": 0, "dependencySuffixMatchCount": 0, "dependencyManifestParsedCount": 0}, "DependencyNoManifest", U),
        c("t4_too_old", [T4, "VersionedDependencyClaim"], {"dependencyExactMatchCount": 1, "dependencySuffixMatchCount": 1, "dependencyManifestParsedCount": 1, "claimedMajor": 4, "declaredLowerMajorDelta": 1, "declaredUpperMajorDelta": 1, "declaredUpperUnboundedCount": 0}, "DependencyMajorTooOld", K_),
        c("t4_too_new", [T4, "VersionedDependencyClaim"], {"dependencyExactMatchCount": 1, "dependencySuffixMatchCount": 1, "dependencyManifestParsedCount": 1, "claimedMajor": 4, "declaredLowerMajorDelta": -2, "declaredUpperMajorDelta": -1, "declaredUpperUnboundedCount": 0}, "DependencyMajorTooNew", K_),
        c("t4_in_range_pinned", [T4, "VersionedDependencyClaim"], {"dependencyExactMatchCount": 1, "dependencySuffixMatchCount": 1, "dependencyManifestParsedCount": 1, "claimedMajor": 4, "declaredLowerMajorDelta": 0, "declaredUpperMajorDelta": 0, "declaredUpperUnboundedCount": 0}, "DependencyMajorInRange", S),
        c("t4_in_range_unbounded", [T4, "VersionedDependencyClaim"], {"dependencyExactMatchCount": 1, "dependencySuffixMatchCount": 1, "dependencyManifestParsedCount": 1, "claimedMajor": 4, "declaredLowerMajorDelta": -1, "declaredUpperUnboundedCount": 1}, "DependencyMajorInRange", S),
        c("t4_versioned_undeclared", [T4, "VersionedDependencyClaim"], {"dependencyExactMatchCount": 0, "dependencySuffixMatchCount": 0, "dependencyManifestParsedCount": 3, "claimedMajor": 4}, "DependencyUndeclared", K_),
        # T5
        c("t5_root", [T5], {"scriptDefinedRootCount": 1, "scriptDefinedAnyCount": 2, "scriptHostFileCount": 3, "dynamicTargetRuleCount": 0}, "ScriptDefinedRoot", S),
        c("t5_nested", [T5], {"scriptDefinedRootCount": 0, "scriptDefinedAnyCount": 1, "scriptHostFileCount": 3, "dynamicTargetRuleCount": 0}, "ScriptDefinedNested", S),
        c("t5_undefined", [T5], {"scriptDefinedRootCount": 0, "scriptDefinedAnyCount": 0, "scriptHostFileCount": 1, "dynamicTargetRuleCount": 0}, "ScriptUndefined", K_),
        c("t5_host_missing", [T5], {"scriptDefinedRootCount": 0, "scriptDefinedAnyCount": 0, "scriptHostFileCount": 0, "dynamicTargetRuleCount": 0}, "ScriptHostMissing", K_),
        c("t5_dynamic", [T5], {"scriptDefinedRootCount": 0, "scriptDefinedAnyCount": 0, "scriptHostFileCount": 1, "dynamicTargetRuleCount": 2}, "ScriptPossiblyDynamic", U),
        # T6
        c("t6_min_confirmed", [T6, "MinVersionClaim"], {"versionSourceCount": 1}, "VersionConfirmed", S, evs=[{"versionLowerDelta": 0, "versionUpperUnboundedCount": 1}]),
        c("t6_min_contradicted_below", [T6, "MinVersionClaim"], {"versionSourceCount": 1}, "VersionContradicted", K_, evs=[{"versionLowerDelta": -2, "versionUpperUnboundedCount": 1}]),
        c("t6_min_contradicted_above", [T6, "MinVersionClaim"], {"versionSourceCount": 1}, "VersionContradicted", K_, evs=[{"versionLowerDelta": 1, "versionUpperUnboundedCount": 1}]),
        c("t6_min_conflict", [T6, "MinVersionClaim"], {"versionSourceCount": 2}, "VersionSourcesConflict", K, evs=[{"versionLowerDelta": 0, "versionUpperUnboundedCount": 1}, {"versionLowerDelta": 1, "versionUpperUnboundedCount": 1}]),
        c("t6_exact_confirmed", [T6, "ExactVersionClaim"], {"versionSourceCount": 1}, "VersionConfirmed", S, evs=[{"versionLowerDelta": -2, "versionUpperUnboundedCount": 1}]),
        c("t6_exact_confirmed_bounded", [T6, "ExactVersionClaim"], {"versionSourceCount": 1}, "VersionConfirmed", S, evs=[{"versionLowerDelta": 0, "versionUpperDelta": 0, "versionUpperUnboundedCount": 0}]),
        c("t6_exact_below_range", [T6, "ExactVersionClaim"], {"versionSourceCount": 1}, "VersionContradicted", K_, evs=[{"versionLowerDelta": 2, "versionUpperUnboundedCount": 1}]),
        c("t6_exact_above_range", [T6, "ExactVersionClaim"], {"versionSourceCount": 1}, "VersionContradicted", K_, evs=[{"versionLowerDelta": -3, "versionUpperDelta": -1, "versionUpperUnboundedCount": 0}]),
        c("t6_no_source", [T6, "ExactVersionClaim"], {"versionSourceCount": 0}, "NoVersionSource", U),
        # T7
        c("t7_violated_boundary1", [T7], {"importFilesScanned": 10, "forbiddenImportEdgeCount": 1}, "ImportRuleViolated", K_),
        c("t7_held", [T7], {"importFilesScanned": 10, "forbiddenImportEdgeCount": 0}, "ImportRuleHeld", S),
        c("t7_scope_empty", [T7], {"importFilesScanned": 0, "forbiddenImportEdgeCount": 0}, "ImportScopeEmpty", U),
    ]
    return out


def run() -> int:
    """Run the self-test; returns 0 on success."""
    from ontology.modules.build_ontology import build_all
    from ontology.modules.claims_module import LEAF_VERDICT, VERDICTS
    from ontology.reasoning.claims_abox import ClaimsAboxWriter
    from ontology.reasoning.reasoner import CLAIMS_MODULES, HermitReasoner

    cfg = C.load_config()
    res_dir = C.results_dir(cfg)
    tmp = Path(tempfile.mkdtemp(prefix="wp2_selftest_"))
    build_all(out_dir=tmp)
    cs = cases()
    w = ClaimsAboxWriter()
    doc_ok = w.manifest("selftest/ok", {"snapshotCommit": "0" * 40, "manifestPath": "CLAUDE.md"})
    doc_bad = w.manifest("selftest/bad", {"snapshotCommit": "0" * 40, "manifestPath": "CLAUDE.md"})
    doc_empty = w.manifest("selftest/empty", {"snapshotCommit": "0" * 40, "manifestPath": "CLAUDE.md"})
    iris: dict[str, str] = {}
    for cs_ in cs:
        key = f"selftest|{cs_['name']}"
        props = {"claimQuote": cs_["name"], "claimSubject": cs_["name"], "claimKey": key, "claimLine": 1,
                 "extractionVotes": cs_["votes"], **cs_["props"]}
        doc = doc_bad if cs_["verdict"] == K_ else doc_ok
        iri = w.claim("selftest", key, cs_["types"], props, doc=doc)
        iris[cs_["name"]] = iri
        eis = [w.evidence(iri, i, {**e, "versionSourcePath": "x", "versionSourceRaw": "x"}) for i, e in enumerate(cs_["evs"])]
        w.close_evidence(iri, eis)
    # drift: claim contradicted now, supported at introduction / contradicted at introduction
    def drift_pair(name: str, now: dict, then: dict) -> tuple[str, str]:
        key = f"selftest|{name}"
        base = {"claimQuote": name, "claimSubject": name, "claimKey": key, "claimLine": 1, "extractionVotes": 2}
        a = w.claim("selftest", key, [T1], {**base, **now}, doc=doc_bad)
        b = w.claim("selftest", key, [T1], {**base, **then}, suffix="/intro")
        w.introduced_as(a, b)
        return a, b
    removed = {"pathExactMatchCount": 0, "pathSuffixMatchCount": 0, "pathIgnoredCount": 0, "pathSubmoduleCount": 0, "pathEverTrackedCount": 2}
    found = {"pathExactMatchCount": 1, "pathSuffixMatchCount": 0, "pathIgnoredCount": 0, "pathSubmoduleCount": 0, "pathEverTrackedCount": 2}
    drifted, drifted_intro = drift_pair("drift_a", removed, found)
    born, born_intro = drift_pair("drift_b", removed, removed)
    nt = w.ntriples()

    reasoner = HermitReasoner(tmp, modules=CLAIMS_MODULES)
    r = reasoner.infer(nt)
    failures: list[str] = []
    results: list[dict[str, Any]] = []
    if not r.consistent:
        failures.append(f"ABox inconsistent: {r.error}")
    else:
        for cs_ in cs:
            labels = r.labels_of(iris[cs_["name"]])
            vs = sorted(labels & set(VERDICTS))
            leaves = sorted(labels & set(LEAF_VERDICT))
            ok = (vs == [cs_["verdict"]] and leaves == [cs_["leaf"]]) if cs_["leaf"] else (not vs and not leaves)
            if not ok:
                failures.append(f"{cs_['name']}: expected {cs_['leaf']}/{cs_['verdict']}, got {leaves}/{vs}")
            results.append({"case": cs_["name"], "expected_leaf": cs_["leaf"], "expected_verdict": cs_["verdict"],
                            "got_leaves": leaves, "got_verdicts": vs, "pass": ok})
        for iri, nm, exp in ((doc_bad, "doc_bad", True), (doc_ok, "doc_ok", False), (doc_empty, "doc_empty", False)):
            has = "ManifestWithContradiction" in r.labels_of(iri)
            if has != exp:
                failures.append(f"{nm}: ManifestWithContradiction={has}, expected {exp}")
        for iri, nm, exp in ((drifted, "drifted", "DriftedClaim"), (born, "born_wrong", "BornWrongClaim")):
            labs = r.labels_of(iri)
            other = "BornWrongClaim" if exp == "DriftedClaim" else "DriftedClaim"
            if exp not in labs or other in labs:
                failures.append(f"{nm}: labels {sorted(labs & set(['DriftedClaim', 'BornWrongClaim']))}, expected {exp}")
        # leaf coverage
        covered = {x for rr in results for x in rr["got_leaves"]}
        missing = sorted(set(LEAF_VERDICT) - covered - {"ImportRuleModerate"})
        if missing:
            failures.append(f"leaf classes without a test case: {missing}")
    # removing seo-claims -> zero verdicts
    r0 = HermitReasoner(tmp, modules=["seo-entities"]).infer(nt)
    verdict_hits = [n for ns in r0.labels.values() for n in ns if n in set(VERDICTS) | set(LEAF_VERDICT)]
    leak = any(("senso-framework.org/ontology/seo#" + v) in r0.inferred_ntriples for v in VERDICTS)
    if verdict_hits or leak:
        failures.append(f"verdicts appear without seo-claims: {verdict_hits[:5]}")
    out = {"n_cases": len(cs), "n_failures": len(failures), "failures": failures, "cases": results,
           "consistent": r.consistent, "tbox_sha256": r.tbox_sha256, "timings": r.timings,
           "verdicts_without_claims_module": len(verdict_hits), "leaf_classes": len(LEAF_VERDICT)}
    C.write_json(res_dir / "selftest.json", out)
    for f in failures:
        logger.error("FAIL %s", f)
    logger.info("selftest: %d cases, %d failures, consistent=%s, reason_s=%.1f", len(cs), len(failures),
                r.consistent, r.timings.get("reason_s", -1))
    return 1 if failures else 0
