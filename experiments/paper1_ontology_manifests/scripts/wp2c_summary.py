"""Summarise the WP2c fresh check (Paper 1, JSEP; design papers/paper1/wp2c-fresh-check-design.md).

Reads the per-repository outputs of scripts/wp2c_run.py under /home/adtgrade/research/data/wp2c/<slug>/ (check.json,
results/ with verdicts, measurements, triangulation.json, recheck_rows.jsonl) and computes outcomes 1-5 of the design:
claims with a result per manifest, contradicted claims by type and leaf class, triangulation confirmation (T6: the
independent re-parse of recheck.py), the quote-context check of contradicted T1/T2 claims, and the headline share
of contradicted claims confirmed and passing the context check, with Wilson 95% intervals. No LLM, no human rater.
Quote-context check: the subject must occur in its raw quote (a) not preceded by a wildcard, (b) not inside a URL,
(c) not followed by a placeholder such as <name>, {name} or "...". It is not applicable to T3-T6, which count as passed.

Usage:
    python experiments/paper1_ontology_manifests/scripts/wp2c_summary.py [--data /home/adtgrade/research/data/wp2c]
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
HERE = PROJECT_ROOT / "experiments" / "paper1_ontology_manifests"
sys.path.insert(0, str(HERE))
from wp2.normalize import quote_shows_wildcard  # noqa: E402

logger = logging.getLogger("wp2c_summary")
OUT = HERE / "results/real_v2/wp2c"
URL = re.compile(r"(?:https?://|ftp://|www\.)\S*", re.I)
PLACEHOLDER_AFTER = re.compile(r"^\s{0,1}(?:<[^>\n]*>|\{[^}\n]*\}|\$\{|\.\.\.|…|\[[^\]\n]*\]|\*\*?\.)")


def wilson(k: int, n: int, z: float = 1.96) -> dict:
    if n == 0:
        return {"k": k, "n": n, "p": None, "lo": None, "hi": None}
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return {"k": k, "n": n, "p": round(p, 4), "lo": round(max(0, c - h), 4), "hi": round(min(1, c + h), 4)}


def quote_context(typ: str, subj: str, quote: str, tree: bool = False) -> tuple[str, str]:
    """('passed'|'failed'|'not_applicable', reason).

    Backticks are ignored when locating the subject (the normalised subject has none). A claim expanded from a tree
    diagram has a composed path (parents plus leaf) while its quote is the leaf line, so the leaf name is searched.
    """
    if typ not in ("T1", "T2"):
        return "not_applicable", ""
    quote = quote.replace("`", "")
    t = subj.strip().strip("'\"").rstrip("/")
    if tree:
        t = t.rsplit("/", 1)[-1]
    i = quote.find(t)
    if not t or i < 0:
        return "failed", "subject_not_in_raw_quote"
    if quote_shows_wildcard(t, quote):
        return "failed", "preceded_by_wildcard"
    for m in URL.finditer(quote):
        if m.start() <= i < m.end():
            return "failed", "inside_url"
    if PLACEHOLDER_AFTER.search(quote[i + len(t):]):
        return "failed", "followed_by_placeholder"
    return "passed", ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="/home/adtgrade/research/data/wp2c")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    data = Path(a.data)
    status = [json.loads(x) for x in (data / "wp2c_run_status.jsonl").read_text().splitlines() if x.strip()]
    elig = {e["full_name"]: e for e in json.loads((OUT / "wp2c_eligible_shuffled.json").read_text())["eligible"]}
    done = [s for s in status if s["status"] == "completed"]
    per_repo, contra = [], []
    for st in done:
        slug, name = st["slug"], st["repo"]
        res = data / slug / "results"
        chk = json.loads((data / slug / "check.json").read_text())
        ver = json.loads((res / "verdicts" / f"{slug}.json").read_text())
        meas = {c["key_str"]: c for c in json.loads((res / "measurements" / f"{slug}.json").read_text())["claims"]}
        tri = {}
        tp = res / "triangulation.json"
        if tp.exists():
            for r in json.loads(tp.read_text())["rows"]:
                tri[r["key"]] = r
        rck = {}
        rp = res / "recheck_rows.jsonl"
        if rp.exists():
            for ln in rp.read_text().splitlines():
                if ln.strip():
                    r = json.loads(ln)
                    rck[r["key"]] = r
        counts, n_contra = Counter(), 0
        for key, v in ver["claims"].items():
            vd = (v.get("verdicts") or [None])[0]
            if not vd or key not in meas or not meas[key].get("headline"):
                continue
            counts[vd] += 1
            if vd != "ContradictedClaim":
                continue
            n_contra += 1
            c = meas[key]
            typ = c["tcode"]
            if typ == "T6":
                r = rck.get(key)
                tres = "not_checkable" if r is None else ("confirmed" if r.get("recheck_verdict") == "ContradictedClaim" else "not_confirmed")
                tinst = "reparse"
            else:
                r = tri.get(key)
                tinst = r.get("instrument") if r else None
                cor = r.get("corroborates") if r else None
                tres = "not_checkable" if cor is None else ("confirmed" if cor else "not_confirmed")
            qc, qwhy = quote_context(typ, c["subject"], c["quote"], bool(c["attrs"].get("tree")))
            contra.append({"repo": name, "line": c["line"], "type": typ, "subject": c["subject"],
                           "leaf": (v.get("leaves") or [None])[0], "triangulation": tres, "triangulation_instrument": tinst,
                           "quote_context": qc, "quote_context_reason": qwhy, "quote": " ".join(c["quote"].split())[:160]})
        e = elig.get(name, {})
        per_repo.append({"repo": name, "stars": e.get("stars"), "manifest_path": st["manifest_path"], "manifest_chars": e.get("manifest_chars"),
                         "snapshot": chk.get("snapshot"), "claims_with_result": sum(counts.values()), "by_result": dict(counts),
                         "contradicted": n_contra, "any_contradicted": n_contra > 0, "timings_s": chk.get("timings_s"),
                         "check_total_s": chk.get("total_s"), "triangulate_s": st.get("triangulate_seconds"), "wall_s": st.get("seconds")})
    (OUT / "wp2c_per_repo.jsonl").write_text("".join(json.dumps(r) + "\n" for r in per_repo))
    (OUT / "wp2c_contradicted.jsonl").write_text("".join(json.dumps(r) + "\n" for r in contra))

    def good(r: dict) -> bool:
        return r["triangulation"] == "confirmed" and r["quote_context"] in ("passed", "not_applicable")

    by_type: dict = {}
    for t in sorted({r["type"] for r in contra}):
        rr = [r for r in contra if r["type"] == t]
        by_type[t] = {"contradicted": len(rr), "triangulation": dict(Counter(r["triangulation"] for r in rr)),
                      "quote_context": dict(Counter(r["quote_context"] for r in rr)),
                      "confirmed_and_context_ok": wilson(sum(good(r) for r in rr), len(rr))}
    repos_good = {r["repo"] for r in contra if good(r)}
    tot = Counter()
    for r in per_repo:
        tot.update(r["by_result"])
    secs = [r["wall_s"] for r in per_repo if r["wall_s"]]
    summary = {
        "n_attempted": len(status), "n_completed": len(done),
        "failures": [{"repo": s["repo"], "reason": s.get("reason")} for s in status if s["status"] != "completed"],
        "outcome1": {"claims_with_result_total": sum(r["claims_with_result"] for r in per_repo), "by_result_total": dict(tot),
                     "claims_with_result_per_manifest": {"median": sorted(r["claims_with_result"] for r in per_repo)[len(per_repo) // 2] if per_repo else None,
                                                          "min": min((r["claims_with_result"] for r in per_repo), default=None),
                                                          "max": max((r["claims_with_result"] for r in per_repo), default=None)},
                     "manifests_with_contradicted": wilson(sum(r["any_contradicted"] for r in per_repo), len(per_repo)),
                     "mean_wall_seconds_per_repo": round(sum(secs) / len(secs), 1) if secs else None,
                     "max_wall_seconds": max(secs, default=None)},
        "outcome2": {"contradicted_total": len(contra), "by_type": dict(Counter(r["type"] for r in contra)),
                     "by_leaf": dict(Counter(r["leaf"] for r in contra)),
                     "by_type_leaf": dict(Counter(f"{r['type']}:{r['leaf']}" for r in contra))},
        "outcome3": {"overall": dict(Counter(r["triangulation"] for r in contra)),
                     "by_type": {t: v["triangulation"] for t, v in by_type.items()}},
        "outcome4": {"overall": dict(Counter(r["quote_context"] for r in contra)),
                     "failed_reasons": dict(Counter(r["quote_context_reason"] for r in contra if r["quote_context"] == "failed")),
                     "by_type": {t: v["quote_context"] for t, v in by_type.items()}},
        "outcome5": {"claims_confirmed_and_context_ok": wilson(sum(good(r) for r in contra), len(contra)), "by_type": {t: v["confirmed_and_context_ok"] for t, v in by_type.items()},
                     "manifests_with_confirmed_contradiction": wilson(len(repos_good), len(per_repo))},
    }
    (OUT / "wp2c_summary.json").write_text(json.dumps(summary, indent=1))
    logger.info("completed %d, contradicted claims %d, headline %s", len(done), len(contra), summary["outcome5"]["claims_confirmed_and_context_ok"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
