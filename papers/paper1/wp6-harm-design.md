# WP6 (Study B): Do wrong manifests hurt agents? Design and pre-registration

`papers/paper1/wp6-harm-design.md`. Status: **DRAFT, not yet pre-registered**. It becomes binding when committed. That commit must come before any WP6 manifest is generated for a sample task and before any non-development agent run.

> When this was written (2026-10-09), WP5 was complete and analysed (`results/real_v2/wp5/`). No WP6 manifest, run or outcome existed. The sizing figures below come from WP5 ledgers and trajectories only.

## 1. Question and hypotheses

RQ2 found that 29 of 79 real manifests make at least one claim that their own repository contradicts. Most of these are paths that never existed or were removed, undefined scripts, and undeclared dependencies, and 68 % were wrong from the start (`06-rq2.tex`). WP6 asks whether such claims change what an agent does. Errors of the RQ2 kinds are injected into short manifests that are otherwise correct, on the 80 WP5 tasks, with the two WP5 agent models.

| ID | Hypothesis (two-sided) | Outcome | Contrast |
|---|---|---|---|
| H1 | Agents act on false claims | Y1 false-lead actions | F_R vs T |
| H2 | False task-relevant claims waste steps | Y2 wasted steps | F_R vs T |
| H3 | Relevance matters: false claims about the task's area draw more actions than false claims about unrelated areas | Y1 | F_R vs F_I |
| H4 | False task-relevant claims change the resolve rate | `resolved` | F_R vs T |

These four form the confirmatory family: Holm at a familywise α of 0.05, using the existing `holm_adjusted_p`. Everything else is secondary or exploratory and is labelled as such.

## 2. Conditions (within task; 4 conditions × 2 models × 2 replicates = 16 runs per task)

| Cond. | Appended section (`## Repository context`, injected exactly as in WP5 §2.5) |
|---|---|
| A | nothing (run fresh, see §5) |
| T | the true manifest: every claim is supported at the base commit |
| F_R | T with k = 4 claims replaced by false ones placed in the **task-relevant** area |
| F_I | T with the same 4 slots replaced by false ones placed in an **unrelated** area |

### 2.1 True manifest T (deterministic, no LLM; inputs: the base tree, the cache clone and the task record)

Claims are bare facts. They carry no descriptions, counts or imperatives, so a false entry cannot be given away by a missing annotation.

- **Layout (T1 path claims, directories, 8 entries).**
  - The task's own directory is always listed: the directory of each gold-touched non-test file, truncated to depth 2.
  - The remaining entries are package directories at depth ≤ 2 with the most `.py` files (test directories excluded, WP5 §3.2 regex), plus the test root.
  - Entries are sorted alphabetically. The last non-gold, non-test entry in this order is the **filler slot P1**.
- **Key files (T1, 3 entries).** The largest non-test `.py` file (by bytes) in each of the three largest listed directories. The third entry is the **filler slot P2**.
- **Commands (2 entries).**
  - `Run the tests: python -m pytest <test root>`. This is the **relevant command slot C_R**. It is checked as T3 (pytest signature) plus T1 (test root).
  - `Install for development: pip install -e .`. This is the **peripheral command slot C_I**. It is checked as T1 on `pyproject.toml` or `setup.py`.
- **Dependencies (T4, up to 5).** Declared runtime dependencies from the WP2 `depparse` census, ranked by the number of non-test files at base that import them. Each is written with its declared specifier, verbatim. The lowest-ranked dependency that no gold-touched file imports is the **filler slot D**.
- **Python (T6, 1 line).** The declared `requires-python` / `python_requires`. The line is omitted if no version source exists. It is never falsified.

About 19 claims in all, at roughly 1.0 to 1.6 k characters.

**Localisation information.** The layout names the task's directory, and it does so in T, F_R and F_I alike. A-vs-T contrasts therefore include this weak pointer. A covariate `pointer_in_issue` records whether the problem statement already names that directory or file.

### 2.2 Falsification (fixed slots; relevance is the *location* of the false item)

The four RQ2 kinds that account for 56 of the 65 RQ2 contradictions (86 %) are injected once each. F_R and F_I replace the **same** slots, except for the command slot. All true information outside the replaced slots is identical across T, F_R and F_I.

| # | RQ2 kind (target verdict leaf) | Slot replaced | F_R content | F_I content |
|---|---|---|---|---|
| 1 | Path never existed (`PathNeverExisted`) | P1 | `<gold dir>/<name>/` | `<unrelated listed dir>/<name>/` |
| 2 | Path removed (`PathRemoved`) | P2 | a `.py` file deleted before base under the gold directory (else under its top package) | a `.py` file deleted before base outside the gold package |
| 3 | Undefined command (`ScriptUndefined` / `ScriptHostMissing`) | C_R in F_R, C_I in F_I | `Run the tests: make <t>` | `Install for development: make <t>` |
| 4 | Undeclared dependency (`DependencyUndeclared`) | D | competitor of a dependency that a gold-touched file imports | competitor of a dependency that no gold-touched file imports |

Each false item is the first candidate, in a fixed order, that passes every constraint:

- `<name>` comes from a fixed vocabulary (`core internal engine backends handlers services common impl`).
- `<t>` comes from `test tests check` for the C_R slot and `install dev develop` for the C_I slot.
- Competitors come from `configs/wp6_competitors.yaml`, for example requests→httpx, click→typer, pyyaml→ruamel.yaml, attrs→pydantic, with a fixed generic fallback list.

**Uniqueness constraints**, which make the trajectory parsing in §3 exact:

- The false token (the final path component, the make target with `make`, the distribution and import name) occurs nowhere among the base-tree path components (for paths, except the removed path's own history).
- It does not occur in the problem statement.
- For dependencies, it gets zero `git grep` hits at base, and `import <name>` fails in the task venv.

**Fallbacks**, flagged and excluded in SA3:

- If a removed-file candidate does not exist in the required area, a never-existed `.py` file name is used instead. At base, 75 of the 80 tasks have at least one deleted `.py` file in their history (48 have five or more), so this fallback should be rare; how often it applies within the required area is reported. 15 of the 80 have a root Makefile, so the fake `make` target is mostly `ScriptHostMissing`.
- If no gold-touched file imports a declared dependency, F_R uses the I competitor.

**Length.** |L_F − L_T| ≤ 0.05 · L_T. Otherwise the task is flagged `length_violation` and a covariate is added in SA4.

**Dose.** 4 of about 19 claims (about 21 %) are false. That is far above the RQ2 per-claim rate of 5.5 %, but close to the 2.2 contradictions per contradicted manifest. The design tests whether wrong claims of these kinds hurt when present, not the prevalence-weighted harm.

### 2.3 Verification that every T claim is true and every F claim false (gate before `wp6-run-freeze`)

Every claim of every manifest is converted directly into a WP2 claim record (`tcode`, `attrs`, `votes = 3`; no LLM extraction). Three instruments then check it at `base_commit`:

1. **The RQ2 checker.** The record goes through `wp2/measure.py` (with `RepoAt(cache clone, base_commit)`) into the ABox, and HermiT gives a verdict with the frozen `seo-claims.owl`.
2. **The independent re-check.** `wp2/recheck.py` recomputes the verdict.
3. **A runtime probe** in the task workspace, which tests what the agent would actually experience:

   | Claim | Probe |
   |---|---|
   | true path | `test -e` |
   | false path | `! test -e`, and `git log -- p` count = 0 or ≥ 1 according to the subtype |
   | true test command | `python -m pytest --collect-only -q <root>` returns rc 0 |
   | fake make target | `make -n <t>` returns rc ≠ 0 |
   | true dependency | `python -c "import <mod>"` returns rc 0 |
   | fake dependency | the same command returns rc ≠ 0 |

**Acceptance criteria:**

- Every T claim, and every unchanged F claim, is `Supported` by instruments 1 and 2 and passes its probe.
- Every injected claim gets its target contradicted leaf from both 1 and 2 and passes its probe.

During generation, a candidate that fails moves the generator to the next candidate. A slot that cannot be filled is dropped from **all** of the task's manifests, so the task stays paired. Tasks are never dropped after freeze.

The result is `wp6_verification.json`, which records per-claim verdicts and the agreement between instruments 1 and 2. That agreement is reported as a second application of the RQ2 checker, on claims whose truth is known by construction. Its expected rate of disagreement is 0.

## 3. Outcomes and exact trajectory parsing rules

**Actions.** An action is the single fenced `mswea_bash_command` block of an assistant message that the harness executed. Messages followed by a format-error or output-limit message are not actions. The observation is the next user message: `rc` comes from `<returncode>(-?\d+)</returncode>`, and `out` is the text inside `<output>`, truncated to 4,000 characters.

**False tokens per task.** Fixed at generation and stored in the manifest index:

- paths: the full relative path and its final component;
- command: the regex `\bmake\b[^|;&\n]*\b<t>\b`;
- dependency: the distribution name and the import name, compared case-insensitively.

The same token set is applied to the T and A runs of the task, as a counterfactual baseline: agents can reach the same names unprompted.

**Hits.** `hit(a) = 1` if the command text of action a matches any false token as a whole word (`(?<![\w.-])tok(?![\w-])`; the path token may carry a leading `./` or a trailing `/`). The uniqueness constraints make every match attributable to the manifest.

| ID | Outcome | Definition |
|---|---|---|
| Y1 | false-lead actions (primary, H1 and H3) | Σ hit(a) |
| Y2 | wasted steps (primary, H2) | \|{a : hit(a)} ∪ {a : rc ≠ 0 ∧ NF(out)}\|, where NF is `No such file or directory\|command not found\|No rule to make target\|No module named\|ModuleNotFoundError\|ERROR: file or directory not found\|can't open file\|cannot access\|No matching distribution` |
| resolved | primary (H4) | WP5 §4.2, unchanged (`wp5/evaluate.py`) |
| Y3 | any hit | Y1 > 0 |
| Y4 | hits by kind and by false item | per-kind Y1 |
| Y5 | first-hit step | index of the first hit action; undefined if none |
| Y6 | fake materialised | the final diff creates a file under a false path, or adds `import <fake>` |
| Y7 | venv mutated | `uv pip freeze` hash differs after the run (for example, the fake dependency was installed) |
| Y8 | verbal uptake | THOUGHT text names a false token (not an action) |
| Y9 | steps, `hit_step_limit`, prompt and completion tokens, wall time | as in WP5 ledgers |

Steps are secondary because 58 % of WP5 runs (643 of 1,108) ended at the 40-step limit. Total steps are therefore censored and insensitive (task-level paired MDE about 2 steps). The parser is unit-tested on hand-written trajectories and on 20 WP5 trajectories with expected counts committed before the run freeze.

## 4. Analysis

**Model.**
- **Estimator.** GEE clustered by repository (61 clusters), exchangeable working correlation, bias-reduced sandwich covariance, t(G − 1). This is `shared/evaluation/statistics.gee_fit` and `wald_contrast`, as in WP5 §6.2.
- **Formula.** `y ~ C(condition, Treatment('T')) + C(model)`, fitted on all four conditions.
- **Families.** Y1 and Y2 are Poisson with a log link (rate ratio); `resolved` and Y3 are binomial (OR).
- **Fallbacks.** Independence working correlation if convergence fails; then a task-stratified permutation test.

**Companion test.** A paired Wilcoxon signed-rank test (Pratt zeros) on task-level means over the 4 runs per condition, for each confirmatory contrast. If its sign differs from the GEE estimate, or it falls on the other side of the Holm threshold, the result is reported as "estimator-sensitive". The GEE p-value stays decisive.

**Effect sizes.** Rate ratio or OR with 95 % CI, plus a paired task-level bootstrap difference (`paired_task_bootstrap`, B = 10,000, seed 20261009).

**Secondary contrasts (Holm across them as a descriptive guard only):**
- F_I vs T, and F_R vs A ("wrong manifest vs none") on Y1, Y2, `resolved` and Y9;
- T vs A (does a short true manifest change behaviour, including the pointer);
- Y3 to Y8 for F_R vs T and F_R vs F_I.

**Sensitivity analyses (never change a verdict):**

| ID | Variant |
|---|---|
| SA1 | exclude final infra failures |
| SA2 | each model alone |
| SA3 | exclude tasks with any fallback |
| SA4 | exclude `length_violation` tasks |
| SA5 | cluster by task |
| SA6 | hits on the full path only (no final-component rule) |
| SA7 | narrow NF (the first four strings only) |
| SA8 | negative binomial instead of Poisson |
| SA9 | exclude tasks whose gold patch fails at a post-run drift check |

**Exploratory:** recovery after the first hit (does the agent later use the true item?); per-kind and per-model tables; the fresh A runs against the WP5 A runs on resolve rate (endpoint drift).

## 5. Sample, run budget, power

**Sample.** The 80 frozen WP5 tasks, which are already validated, and their 2 models: `nvidia/nemotron-3-super-120b-a12b` and `google/diffusiongemma-26b-a4b-it`. The settings are the final WP5 settings: step limit 40, temperature 0.7, top_p 0.95, `max_tokens` 4096, nemotron thinking off, wall time 1800 s. Calls rotate over the 4-key pool, with 4 workers (VM cap).

**Runs.** 80 × 4 × 2 × 2 = **1,280 runs**.

- **Throughput.** WP5 measured 66 runs/h after key rotation (1,081 runs in 16.4 h). Manifest conditions ran up to 17 % longer than A (diffusiongemma median wall time), so the estimate is **about 20 h** of wall time.
- **Pilot.** A non-analysed pilot of about 40 runs on the 3 WP5 development tasks adds about 1 h.
- **Dropping A.** 960 runs, about 15 h. A is kept because it is concurrent: NIM endpoints may have changed since WP5. A also gives the practically relevant F_R vs A and T vs A contrasts.
- **Execution.** In a `senso-run-wp6` tmux session.

**Power and MDE.** From WP5 data, at 80 tasks × 4 runs per condition, α/4 = 0.0125 (first Holm step) and power 0.80:

| Hypothesis | Basis | MDE |
|---|---|---|
| H2 (wasted steps) | WP5 not-found failures average 0.24 to 0.49 per run; the SD of task-level paired differences is 0.64 to 0.74 (A/C/D pairs) | **about +0.28 wasted steps per run**, about +75 % over the baseline of about 0.37 |
| H1 (any hit) | simulated, T counterfactual rate 0.01, latent ICC 0.3 to 0.5 | **F_R hit rate of about 0.08** (power 0.87 and 0.74); 0.05 gives only 0.33 to 0.45 |
| H3 (relevance) | simulated | detectable at 0.05 vs 0.15, or 0.10 vs 0.25 (power 0.65 to 0.88); 0.05 vs 0.10 is not detectable (about 0.2) |
| H4 (resolve rate) | WP5 simulation scaled (WP5: OR 2.5 had power 0.79 at p0 0.10, α/3) | only large harm is detectable: about OR ≤ 0.4, a resolve rate of about 0.17 → about 0.07 |

**Expected uptake is low.**

- **WP5 verbal uptake.** "Repository context" was mentioned in 0 to 9 % of runs.
- **Tool compliance.** When a task's B guidance named tox, make, nox or a linter, B runs used it in 5 % (diffusiongemma) and 10 % (nemotron) of runs, against 3 % in A.
- **Test-running baseline.** Only 19 to 36 % of WP5 runs ran any test command.

H1 is therefore plausible but not certain, and H2 is expected to be borderline.

**Exact simulation before the run freeze.** The power is re-simulated with `simulate_power`, using the WP5 per-task Y2 distribution, and written to `wp6_power.json` before `wp6-run-freeze`. The label is POWERED or UNDER-POWERED for H2 at +0.28. A 3-replicate option (1,920 runs, about 30 h, MDE about 0.23) is decided **before** the freeze, never after.

## 6. Decision language (fixed now)

- **H1 rejected, F_R > T.** "Agents acted on injected false claims: x % of F_R runs took at least one action on a false item (counterfactual T: y %)."
  - Not rejected: "no detectable uptake (MDE hit rate about 0.08)". H2 to H4 are then read as harm through routes other than direct action, not as evidence that manifests are harmless.
- **H2 rejected, F_R > T.** "False task-relevant claims cost Δ wasted steps per run [CI]."
  - Not rejected: "inconclusive at MDE about 0.28 steps per run". It is never read as "no harm".
- **H3 rejected.** "The location of a false claim matters", with direction. Not rejected: "no evidence that relevance matters at this power".
- **H4.** As WP5 §15: a non-rejection is "no detectable change in resolve rate (MDE OR ≈ 0.4)".
- **Effects opposite to the hypothesised direction** (for example, F_R < T on Y2) are reported as found. No subgroup is promoted post hoc.
- **Scope sentence, always.** Two NIM models, mini-SWE-agent in text mode, 40 steps, a manifest injected into the prompt (not read from a file), short synthetic manifests, Python SWE-rebench tasks.

## 7. Threats

- **Construct.**
  - The injected errors copy the RQ2 kinds but not their context: real wrong claims sit in long, partly stale manifests, and tree diagrams can be recognisably aspirational.
  - The dose is a stress level (§2.2).
  - Relevance uses the gold patch, which is an oracle. This is legitimate for a manipulation but is not available in practice.
  - Commands differ by slot between F_R and F_I. The H3 contrast therefore also includes the loss of the true test command in F_R. Per-kind Y4 separates the effects.
- **Floor and ceiling.** Low uptake (above) and the 40-step ceiling. Hence the action-level primaries.
- **Venv contamination.** In WP5 the per-task venv was shared across runs, and agents' `pip install` persisted. WP6 hashes `uv pip freeze` before and after each run and rebuilds the venv after any change (Y7). Run order within a task is seeded and random.
- **Parsing validity.** Uniqueness constraints, unit tests and SA6/SA7.
- **Endpoint drift.** All conditions are run concurrently and interleaved; fresh A is compared with WP5 A.
- **External validity.** As in WP5 §15.

## 8. Process and deviation logging

**Commit order:**

1. This design.
2. Code and unit tests: the parser tested on synthetic and WP5 trajectories; the analysis runner tested on simulated data.
3. Generator development on the WP5 development tasks only; tag `wp6-generator-freeze`.
4. Generate all manifests and the verification report. All gates in §2.3 must pass. Commit the manifests, the index with sha256 and token sets, and `wp6_power.json`; tag `wp6-run-freeze`.
5. Pilot (development tasks only, never analysed).
6. Runs.
7. Commit the ledger hashes as `wp6-runs-complete`.
8. Analysis.

**No peeking.** Until `wp6-runs-complete`, the monitor shows only terminal states, infra failures, venv rebuild counts and prompt-token counts by condition. Prompt tokens are the injection integrity check. No Y1, Y2 or `resolved` value is aggregated by condition.

**Infra failures, ITT and drift.** These follow WP5 §5 verbatim.

**Deviations.** Any change after this document is committed is logged in `papers/paper1/wp6-deviations-log.md` and `results/real_v2/wp6/wp6_deviations.json`, before it takes effect, with these fields:

- date;
- position relative to the three tags;
- what changed;
- why;
- whether it was decided with knowledge of any outcome by condition;
- expected impact.

The paper reports all of them.

**Outputs.** All under `experiments/paper1_ontology_manifests/results/real_v2/wp6/`, a new directory: nothing under `wp5/`, other `real_v2` directories or JSS-era results is written. No LLM is used in manifest generation, verification, outcome measurement or analysis.

## 9. Code: reused and new (effort for one implementer)

**Reused unchanged:**

- **WP5:** `wp5/agent.py` (KeyPool, CountingModel, injection via the `manifest` template variable); `wp5/envs.py` (workspace, venv, pytest runner); `wp5/evaluate.py` (`resolved`); `wp5/metrics.py` (diff filtering, Y5/Y6); `wp5/ledgers.py`; the WP5 validation and drift results.
- **WP2:** `wp2/repo.py` (`RepoAt`), `depparse.py` (census), `measure.py`, the frozen claims TBox with HermiT (`step_reason` path) and `recheck.py`.
- **Statistics:** `shared/evaluation/statistics.py`: `gee_fit`, `wald_contrast`, `holm_adjusted_p`, `paired_task_bootstrap`, `simulate_power`.
- **Analysis:** the GEE and report scaffolding of `run_wp5_analysis.py`.

**New code:**

| Item | Effort |
|---|---|
| `wp6/manifests.py`: T slot builder, the four falsification operators with R/I placement and uniqueness constraints, renderer, length check; `configs/wp6_competitors.yaml` | 1.5 d |
| `wp6/verify.py`: manifest claims → WP2 claim records → measure, HermiT, recheck; runtime probes; `wp6_verification.json` gate. Small adapter, because the WP2 steps are file- and slug-driven | 1 d |
| `wp6/trajparse.py`: §3 rules, Y1 to Y8, with unit tests | 1 d |
| Runner generalisation: condition list and manifest directory from `configs/wp6.yaml`; output directory parameter; venv freeze-hash guard and rebuild (`run_wp6.py`, thin wrapper over `wp5.runner`) | 0.5 d |
| `run_wp6_analysis.py`: §4, and the power re-simulation | 1 d |

**Total: about 5 working days** before the run freeze, then about 21 h of runs.

## Coordinator decisions (frozen 2026-10-09, before any WP6 code was written or any run started)
- Conditions A, T, F_R and F_I are all run; A is run fresh so all four conditions are concurrent.
- Two replicates per task, condition and model (1,280 runs), as designed; no third replicate.
- Four falsified claims per F manifest (the four kinds above); no fifth (version) falsification. The dose (4 of about 19 claims) is a deliberate stress dose and is reported as such.
- Name WP6; output directory `experiments/paper1_ontology_manifests/results/real_v2/wp6/`.
- The task virtual environment is reset before every run in WP6. The WP5 shared-venv issue is logged as WP5 deviation 14 and disclosed as a WP5 threat.
