"""Inspection of every contradicted claim of the WP2c fresh check (Paper 1, JSEP; design deviation of 2026-10-19).

Used by Paper 1 (JSEP rebuild). The design's automatic checks (triangulation and the quote-context check) confirm 40 of
the 41 contradicted claims, but they test whether the named path or version is absent, not whether the claim was read
correctly. As in RQ2's first pass, the authors read each contradicted claim next to the repository at its snapshot. The
label of each claim and the evidence for it are written out below, so that the classification can be checked claim by
claim. ``real`` means the manifest names a file, folder or version that the repository contradicts; the other kinds are
false alarms, named by their cause. Writes ``results/real_v2/wp2c/wp2c_inspection.json``.

Usage:
    python experiments/paper1_ontology_manifests/scripts/wp2c_inspection.py
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT = PROJECT_ROOT / "experiments/paper1_ontology_manifests/results/real_v2/wp2c"
logger = logging.getLogger("wp2c_inspection")

# kind -> (real error?, plain description)
KINDS = {
    "real_missing": (True, "file or folder never in the repository"),
    "real_removed": (True, "file or folder removed from the repository"),
    "real_version": (True, "version contradicted by the version file"),
    "false_slash_alternation": (False, "two files written as one (src/elf.c/h)"),
    "false_go_package": (False, "Go import or package path read as a file path"),
    "false_outside_repo": (False, "path outside the repository"),
    "false_placeholder": (False, "naming template (NNNN-short-name.md)"),
    "false_build_output": (False, "file produced by the build"),
    "false_tree_root": (False, "name of the repository itself, as the root of a tree diagram"),
    "false_other_version": (False, "version of another tool read as the project's"),
}

# (repo, manifest line) -> (kind, evidence at the snapshot); every line of wp2c_contradicted.jsonl must appear.
LABELS: dict[tuple[str, int], tuple[str, str]] = {
    ("pro-vi/cc-stretch", 31): ("false_other_version", "'Claude Code 2.1.302' is the version of Claude Code, not of the project"),
    ("URML-MARS/URML", 139): ("false_placeholder", "docs/rfcs/ holds 0000-template.md, 0001-rfc-process.md, ...; NNNN is a template"),
    ("obot-platform/obot", 158): ("false_go_package", "Go import path; the manifest maps it to ./apiclient"),
    ("obot-platform/obot", 159): ("false_go_package", "Go import path; the manifest maps it to ./logger"),
    ("FastEndpoints/Documentation", 32): ("real_missing", "no OKF/ folder; the file is .okf/conventions.md"),
    ("Johnny520/wcx", 21): ("real_missing", "libs/common holds annotation-scanner, bsh, reflekt, stubs; no submodule libxposed-api"),
    ("ckotzbauer/vulnerability-operator", 36): ("false_tree_root", "tree diagram root 'vulnerability-operator/' is the repository"),
    ("ckotzbauer/vulnerability-operator", 86): ("real_removed", "stale.yml deleted in f61b264 (2026-03-13)"),
    ("ckotzbauer/vulnerability-operator", 87): ("real_removed", "update-snyk.yml replaced by scan-grype.yml in bd5cc68"),
    ("ckotzbauer/vulnerability-operator", 88): ("real_removed", "label-issues.yml deleted in f61b264"),
    ("ckotzbauer/vulnerability-operator", 89): ("real_removed", "size-label.yml deleted in f61b264"),
    ("ckotzbauer/vulnerability-operator", 42): ("real_missing", "no config.yaml anywhere in the tree"),
    ("ckotzbauer/vulnerability-operator", 44): ("real_missing", "no run.sh anywhere in the tree"),
    ("ckotzbauer/vulnerability-operator", 49): ("real_missing", "no reports/ folder"),
    ("ckotzbauer/vulnerability-operator", 50): ("real_missing", "no reports/report.json"),
    ("ckotzbauer/vulnerability-operator", 15): ("real_version", "go.mod says go 1.26.8, the manifest 1.25.0"),
    ("ckotzbauer/vulnerability-operator", 150): ("real_version", "go.mod says go 1.26.8, the manifest Go 1.25+"),
    ("zw3rk/hyper-linux", 236): ("false_outside_repo", "macOS system path /Library/Apple/..., not a repository path"),
    ("Weaverse/.agents", 8): ("real_removed", "agents/ emptied by 78cab76 (deprecated agent docs removed)"),
    ("qoli/localclash-luci", 39): ("real_missing", "no file named istoreos-test-features.md in history"),
    ("gogpu/gg", 16): ("false_go_package", "Go package gg/gpu of module github.com/gogpu/gg is the folder gpu/"),
    ("gogpu/gg", 37): ("false_go_package", "Go package path; the folder is integration/ggcanvas"),
    ("gogpu/gg", 65): ("false_go_package", "Go package path; the folder is scene/"),
    ("northword/zotero-format-metadata", 44): ("false_build_output", "'bundled script' written by the build, not tracked"),
}
for _line in (10, 11, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 26, 27, 28, 29, 31):
    LABELS[("zw3rk/hyper-linux", _line)] = ("false_slash_alternation", "src/x.c and src/x.h exist; 'src/x.c/h' names both")


def main() -> None:
    rows = [json.loads(x) for x in (OUT / "wp2c_contradicted.jsonl").read_text().splitlines() if x.strip()]
    out_rows, missing = [], []
    for r in rows:
        key = (r["repo"], int(r["line"]))
        if key not in LABELS:
            missing.append(key)
            continue
        kind, ev = LABELS[key]
        out_rows.append({"repo": r["repo"], "line": r["line"], "type": r["type"], "leaf": r["leaf"], "subject": r["subject"],
                         "automatic_confirmed": r["triangulation"] == "confirmed", "kind": kind,
                         "real": KINDS[kind][0], "evidence": ev})
    if missing or len(out_rows) != len(LABELS):
        raise SystemExit(f"labels and contradicted claims differ: missing {missing}")
    real = [r for r in out_rows if r["real"]]
    summary = {
        "label": "authors' inspection of all contradicted claims (WP2c deviation 2026-10-19); descriptive",
        "kinds": {k: {"real": v[0], "description": v[1]} for k, v in KINDS.items()},
        "n_contradicted": len(out_rows),
        "n_real": len(real),
        "n_false_alarm": len(out_rows) - len(real),
        "by_kind": dict(Counter(r["kind"] for r in out_rows).most_common()),
        "real_by_type": dict(Counter(r["type"] for r in real)),
        "automatic_confirmed_but_false": sum(r["automatic_confirmed"] and not r["real"] for r in out_rows),
        "manifests_with_real_error": sorted({r["repo"] for r in real}),
        "manifests_with_false_alarm_only": sorted({r["repo"] for r in out_rows} - {r["repo"] for r in real}),
        "claims": out_rows,
    }
    (OUT / "wp2c_inspection.json").write_text(json.dumps(summary, indent=1) + "\n")
    logger.info("real %d of %d; manifests with a real error: %d", len(real), len(out_rows),
                len(summary["manifests_with_real_error"]))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    main()
