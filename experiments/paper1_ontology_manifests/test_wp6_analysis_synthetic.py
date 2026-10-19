"""Test of run_wp6_analysis.py on simulated ledgers with a planted effect (Paper 1, WP6; design section 8, step 2).

Used by Paper 1 (JSEP rebuild), WP6. Simulates 40 tasks in 20 repositories x 4 conditions x 2 models x 2 replicates: F_R runs
take false-lead actions at a raised rate and waste more steps, F_I and T at a low background rate, resolve rates are equal. The
analysis must reject H1 and H2, not reject H4, and write all four output files. Output goes to a temporary directory.

Usage:
    python experiments/paper1_ontology_manifests/test_wp6_analysis_synthetic.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from experiments.paper1_ontology_manifests import run_wp6_analysis as an  # noqa: E402

MODELS = ["nvidia/nemotron-3-super-120b-a12b", "google/diffusiongemma-26b-a4b-it"]


def simulate(d: Path, seed: int = 1) -> tuple[Path, Path]:
    rng = np.random.default_rng(seed)
    tasks = [{"instance_id": f"org{i // 2}__proj-{i}", "repo": f"org{i // 2}/proj", "stage": ["servicing", "evolution"][i % 2]}
             for i in range(40)]
    runs, outs = [], []
    for t in tasks:
        task_eff = rng.normal(0, 0.3)
        for c in ("A", "T", "F_R", "F_I"):
            for m in MODELS:
                for r in (1, 2):
                    rid = f"{t['instance_id']}__{c}__{m.split('/')[-1]}__r{r}"
                    rate_r = 0.04 if c != "F_R" else 0.5          # planted: false-lead actions in F_R only
                    rate_i = 0.04 if c != "F_I" else 0.05
                    y1r, y1i = rng.poisson(rate_r * np.exp(task_eff)), rng.poisson(rate_i * np.exp(task_eff))
                    wasted = lambda y: y + rng.poisson(0.3)       # noqa: E731
                    sets = {"F_R": {"Y1": int(y1r), "Y2": int(wasted(y1r)), "Y3": int(y1r > 0), "Y4_by_kind": {"1": int(y1r)},
                                    "Y5": 3 if y1r else None, "Y8": int(rng.poisson(0.05))},
                            "F_I": {"Y1": int(y1i), "Y2": int(wasted(y1i)), "Y3": int(y1i > 0), "Y4_by_kind": {"3": int(y1i)},
                                    "Y5": 4 if y1i else None, "Y8": int(rng.poisson(0.05))}}
                    runs.append({"run_id": rid, "instance_id": t["instance_id"], "condition": c, "model": m, "rep": r,
                                 "state": "Submitted", "infra_failure": False, "steps": int(rng.integers(5, 41)), "wall_s": 100.0,
                                 "prompt_tokens": 1000})
                    outs.append({"run_id": rid, "resolved": int(rng.random() < 0.2), "hit_step_limit": 0, "Y7": 0,
                                 "sets": sets, "sets_sa6": sets, "sets_sa7": sets,
                                 "Y6_sets": {"F_R": {"Y6": 0}, "F_I": {"Y6": 0}}})
    d.mkdir(parents=True, exist_ok=True)
    (d / "wp6_runs.jsonl").write_text("".join(json.dumps(x) + "\n" for x in runs))
    (d / "wp6_outcomes.jsonl").write_text("".join(json.dumps(x) + "\n" for x in outs))
    idx = {t["instance_id"]: {"false_claims": [{"cond": c, "key": "k", "kind": k, "mode": m} for c in ("F_R", "F_I")
                                               for k, m in ((1, "replace"), (3, "add"))],
                              "modes": {c: {"1": "replace", "3": "add"} for c in ("F_R", "F_I")}, "flags": [], "fallbacks": {}}
           for t in tasks}
    (d / "index.json").write_text(json.dumps({"tasks": idx}))
    tf = d / "tasks.json"
    tf.write_text(json.dumps({"tasks": tasks}))
    return d, tf


class Synthetic(unittest.TestCase):
    def test_planted_effect(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_p = Path(tmp)
            d, tf = simulate(tmp_p / "res")
            res = an.analyze(d, tf, d / "index.json", tmp_p / "out", None, None, n_boot=200, synthetic=True)
            h = {r["id"]: r for r in res["confirmatory"]["hypotheses"]}
            self.assertTrue(h["H1"]["reject"], h["H1"])
            self.assertGreater(h["H1"]["ratio"], 3)
            self.assertTrue(h["H3"]["reject"], h["H3"])
            self.assertFalse(h["H4"]["reject"], h["H4"])
            self.assertFalse(h["H1"]["estimator_sensitive"], h["H1"])
            for f in ("wp6_primary.json", "wp6_secondary.json", "wp6_sensitivity.json", "wp6_exploratory.json"):
                self.assertTrue((tmp_p / "out" / f).exists())
            self.assertIn("SA8_negative_binomial_instead_of_Poisson", res["sensitivity"])
            self.assertIn("SA10_replace_mode_claims_only", res["sensitivity"])
            self.assertEqual(res["n_runs"], 40 * 4 * 2 * 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
