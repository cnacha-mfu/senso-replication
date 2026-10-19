# WP5 pre-registered analysis plan: execution-based agent evaluation (RQ3, RQ4)

`papers/paper1/wp5-analysis-plan.md`. Status: **PRE-REGISTERED**. It must be committed before any non-pilot agent run, before any condition C or D manifest is generated for a sample task, and before the task list is frozen.

> When this plan was written, the only agent outcomes in existence were the toy feasibility runs (`~/research/wp5_feasibility/toy_*`) and the running pilot (10 tasks × 2 models × conditions A, B × 1 run). No C or D manifest had been generated, and no outcome had been computed for any condition C or D.

---

## 0. Commitment and frozen inputs

| Item | Value or rule | Frozen when |
|---|---|---|
| This plan | commit hash recorded in `wp5_run_manifest.json` | now |
| Module-stability thresholds | §3.2 values (verbatim here, copied to `thresholds.yaml` later) | now |
| Agent | mini-SWE-agent, text mode (`mini_textbased.yaml`), step limit 40, `cost_limit=0`, wall-time limit 900 s per run (as in the pilot) | now |
| Models | `nvidia/nemotron-3-super-120b-a12b`, `google/diffusiongemma-26b-a4b-it` (NIM). No substitutes in the confirmatory analysis. | now |
| Sampling | Temperature 0.7, top_p 0.95 for both models, `max_tokens` as in the pilot. If the pilot used a different non-zero temperature, the pilot value is adopted and logged before `wp5-run-freeze`. | `wp5-run-freeze` |
| Replicates | 2 runs per task × condition × model | now |
| Conditions | A none; B human contributor guidance; C SENSO manifest; D no-reasoning flat summary (§3) | now |
| Task list | `wp5_tasks.json` (sha256), §2.1 | before manifest generation |
| Pilot baseline p̂0 | `wp5_pilot_summary.json` | before the power decision (§7) |
| Generators and templates | git tag `wp5-generator-freeze` | before sample manifests are generated |
| All run inputs | git tag `wp5-run-freeze`: tasks, manifests, prompt template, harness config | before the first non-pilot run |

The analysis script refuses to run if any of the following holds:
- `wp5-run-freeze` is not an ancestor of HEAD;
- the task-list or manifest-index sha256 does not match;
- any scheduled run is not in a terminal state (§5);
- `configs/wp5_analysis.yaml` differs from the frozen copy.

---

## 1. Questions, estimands, hypotheses

- **RQ3.** Do evolution-aware manifests change measured outcomes of agent patches, and does the effect depend on lifecycle stage?
- **RQ4.** Does a manifest built from reasoner output differ from one built from the same mined facts without reasoning?

The primary outcome is `resolved` (§4.1). The estimand is the population-averaged (marginal) odds ratio between conditions over the sampled tasks and the two models, with stage and model as covariates.

| ID | Hypothesis (two-sided) | Answers |
|---|---|---|
| H1 | OR(C vs A) ≠ 1 | RQ3 |
| H2 | OR(C vs D) ≠ 1 | RQ4 |
| H3 | The C-vs-A log-OR differs across declared stage (§2.2) | RQ3, stage dependence |

These three form the confirmatory family, with Holm at a familywise α = 0.05. Everything else is secondary or exploratory and is labelled as such.

A fixed-sequence alternative (H1, then H2, then H3) was considered and rejected. H2 must be testable whatever H1 shows, because D could differ from C even when C does not differ from A.

---

## 2. Design

### 2.1 Tasks
- **Source.** SWE-rebench fail-to-pass tasks that pass validation: the environment builds, the F2P tests fail at base and pass with the gold patch, and the P2P tests pass in both states. The gold run is repeated 3 times, and any task with a flaky F2P or P2P result is excluded before freezing.
- **Cap.** At most 8 tasks per repository. When a repository has more, tasks are picked in a seeded order (`numpy.random.default_rng(20261006)` permutation of task ids, sorted lexicographically first).
- **Expected supply.** About 15-20 tasks each for ID, EVO and SERV, and 5-10 for PO.
- **Task count.** Decided by §7.
- **Development set.** 3-5 validated tasks that cannot be in the sample (for example, no classifier history at the base date). They are used only to debug the generators and the harness, and are never reported.
- **Pilot tasks** may enter the sample. Pilot runs never enter any analysis, and every sample run is fresh.
- **Recorded per task:** `instance_id`, repo, `base_commit`, base committer date S (UTC), declared stage and its evidence (the PyPI release and classifier in effect at S), F2P and P2P lists, gold patch, test patch, whether B is available (§3.7), and whether agent-manifest files are present in the tree at base.

### 2.2 Stage variable
- **Declared stage** at S is the maintainer's PyPI Development Status in effect at the base date: ID (2-4), EVO (5), SERV (6), PO (7). It is the confirmatory stage variable **whatever RQ1 concludes**. Choosing the variable from the RQ1 result would be a forking path. It is also independent of the treatment, which uses the inferred stage.
- **For H3**, stages are collapsed as in RQ1 §1.1: ACTIVE = ID ∪ EVO, and SERVICING = SERV.
  - PO is a third H3 level only if it has ≥ 10 tasks from ≥ 4 repositories.
  - Otherwise H3 has 1 df (ACTIVE vs SERVICING). PO tasks still contribute to H1 and H2 as their own covariate level, and PO-specific estimates are exploratory.
- The four-level declared stage is descriptive only.
- If RQ1 ends in GO, the inferred stage (the canonical classifier at S) replaces the declared stage in an exploratory re-analysis (§10).

### 2.3 Runs and order
- **Per task:** A, C and D always, and B when it is available. That is 2 models × 2 replicates per condition, so 12 or 16 runs per task.
- **Order.**
  - Tasks are executed in a seeded random order, with strata interleaved by a round-robin over the stratum-wise permutations.
  - Within a task, its runs are executed in a seeded random order.
  - So time, NIM load and endpoint drift are not aligned with condition or stage.
- **Recorded per run:** model id string returned by the API, timestamps, prompt and completion tokens, exit status, steps, wall time, retries.

### 2.4 Workspace and leakage control
- **Workspace.** Each run gets a fresh workspace: a new repository into which the ancestry of `base_commit` is fetched from the cache clone, then a detached checkout of `base_commit`.
- **Leakage checks**, done per task at validation:
  - no object reachable only from commits after the base is present;
  - the latest committer date in `git log --all` is ≤ S;
  - the F2P tests are not in the tree.
- **History and in-tree files are the same in every condition.** Agents can run `git log` in every condition. In-tree CONTRIBUTING and agent files are not removed. Their presence is a recorded covariate (SA3).

### 2.5 Prompt injection
- **Prompt.** mini-SWE-agent's default text-mode instance template with the SWE-rebench `problem_statement`.
- **B, C and D** append a section after the problem statement, starting with the fixed heading `## Repository context`.
- **A** appends nothing.
- No other part of the prompt differs between conditions. The prompt template's sha256 is frozen.

---

## 3. Condition generation (deterministic; no LLM at any step)

C and D come from **the same pipeline run at the same snapshot** and read the same per-task population JSON. They differ only in the presentation layer. No LLM synthesis is used, so no LLM confound exists between C and D. The WP2 claim extraction uses an LLM and is therefore **not** part of C.

### 3.1 Pipeline at the base commit (adaptation of `populate_v2.py`)

A new mode, `--snapshot-commit SHA --task-id ID`, works as follows. All other behaviour stays as in RQ1 §3.
1. **Reference point.** S is the committer date of `base_commit`. M_S is the last complete calendar month before the month of S. The repository-level snapshot date is the last day of M_S.
2. **Ancestry only.** `history_index`, `mine_commits` and `month_end_commits` walk from `base_commit`, not `HEAD`. The cache clone fetches `base_commit` if it is missing. The mining-cache key includes the SHA.
3. **Configuration.**
   - Primary configuration only: α 0.05, L 36, D 12, G 0.05, original Mann-Kendall.
   - Explanations on. Complexity off, matching the RQ1 freeze run, so Law II is undetermined.
   - Fuseki dataset `seo_v2_wp5`, optional. Readers use the per-task JSON, which mirrors the inferred graph.
4. **Modules.** The module measurements (§3.2) are added to the same ABox and reasoned in the same stage-B HermiT pass. Pellet-CLI explanations are produced for the stage classes, the law classes, inferred anti-patterns, and the module labels shown in C.
5. **Output.** `results/real_v2/wp5/population/{task_id}.json`, with a `modules` block added.
6. **Regression check.** On the 120 RQ1 repositories, the extended TBox must give project-level labels identical to the `rq1-freeze` TBox (differential test). Any difference blocks `wp5-generator-freeze`.

**Two anchors, on purpose:**
- Repository-level measures use complete months ending at M_S, which reuses the frozen RQ1 monthly instrument.
- Module-level measures describe the tree the agent edits, so they are anchored at S itself.

### 3.2 Module-level stability (WP1 pattern: measurements in Python, classes in OWL)

**Module partition**, computed from the base tree; Python files only, using `is_source_path` and `.py`:
1. Test files are excluded. A test file matches `(^|/)(tests?|testing)/|(^|/)test_[^/]*\.py$|_test\.py$|(^|/)conftest\.py$`, or is touched by the task's test patch.
2. **Package roots:**
   - every directory at the repository root that contains `__init__.py`;
   - every immediate subdirectory of `src/`, with or without `__init__.py`;
   - excluding the names `tests test testing docs doc examples example benchmarks benchmark scripts tools build dist`.
3. **Module of a file f under package root R:** `R/<first path component below R>`. That gives `R/sub` for a subpackage and `R/name.py` for a module file directly under R, including `R/__init__.py`.
4. **Other non-test `.py` files:** the module is their top-level directory. Root-level files are their own module, except `setup.py`, `noxfile.py`, `tasks.py` and `conf.py`, which are excluded.

The same mapping is applied to historical paths. Paths that map to a module absent from the base tree are ignored.

**Measured properties.** These are new `MEASURED_PROPERTIES` entries with domain code `Mo` (module); all are Functional. Each module individual is linked by `hasModule`.

| Property | Type | Definition |
|---|---|---|
| `modulePath` | string | module id from the partition |
| `moduleLoc` | int | non-blank lines of the module's `.py` files at the base tree (same instrument as `LOC_INSTRUMENT`) |
| `moduleCommitsInWindow` | int | non-merge ancestor commits with author date in (S − W, S] that touch the module |
| `moduleChangeMonthsInWindow` | int | distinct UTC calendar months among those commits |
| `moduleLinesChangedInWindow` | int | Σ (insertions + deletions) from `--numstat --no-renames` on the module's files |
| `moduleRelChurnInWindow` | decimal | `moduleLinesChangedInWindow / moduleLoc`; asserted only if `moduleLoc > 0` |
| `moduleMonthsSinceLastChange` | int | months from month(S) back to the month of the last commit touching the module, over the full history; descriptive only, used by no rule |

W is 12 months. `attach_churn` already parses numstat paths (`populate_v2.py:276-281`). It must keep per-commit (path, insertions, deletions).

**Rules** in `seo-inference.owl`. They are SWRL-free, and every operand of a union is a named class (WP1 pitfall 4b).
```
LowRelChurnModule    ≡ Module ⊓ moduleRelChurnInWindow some decimal[<  Rs]
HighRelChurnModule   ≡ Module ⊓ moduleRelChurnInWindow some decimal[>= Rs]
RarelyChangedModule  ≡ Module ⊓ moduleChangeMonthsInWindow some integer[<= Ms]
OftenChangedModule   ≡ Module ⊓ moduleChangeMonthsInWindow some integer[>  Ms]
StableModule         ≡ LowRelChurnModule ⊓ RarelyChangedModule
ActiveModule         ≡ HighRelChurnModule ⊔ OftenChangedModule      (Horn subclass axioms, as _Rules.union)
AllDisjoint(StableModule, ActiveModule)
```
A module with no asserted `moduleRelChurnInWindow` (LOC 0) is undetermined.

**Explanation templates:**
- StableModule: `changed in {moduleChangeMonthsInWindow} of the last 12 months; lines changed = {moduleRelChurnInWindow} of its size`
- ActiveModule branches: `{moduleRelChurnInWindow} of its lines changed in the last 12 months` / `changed in {moduleChangeMonthsInWindow} of the last 12 months`

**Thresholds** (to add to `thresholds.yaml`, group `module_stability`):

| id | value | used_in_ontology | status | sensitivity | Rationale |
|---|---|---|---|---|---|
| `mod_window_months` | 12 | false (measurement window) | UNJUSTIFIED (a-priori convention) | 6, 24 | One annual cycle, matching `rb_dormancy_months`. |
| `mod_stable_max_rel_churn` (Rs) | 0.10 | true | UNJUSTIFIED | 0.05, 0.20 | Under a tenth of a module's lines rewritten in a year means occasional patching, not redevelopment. Relative churn as a measure: Nagappan & Ball, ICSE 2005 (verify before citing). The literature gives no cut-off. |
| `mod_stable_max_change_months` (Ms) | 2 | true | UNJUSTIFIED | 0, 1, 4 | Touched in at most one month in six is the module-level analogue of R&B servicing ("minor tactical change"). |

Sensitivity variants change **only the outcome measurement** (§9, SA9). The manifests use the primary values and are never regenerated.

### 3.3 Condition C: SENSO manifest

Sections in fixed order. Every number is filled from the facts in the reasoner's justification (WP1 §3.4).

| § | Content |
|---|---|
| C0 | Shared header (identical to D0) |
| C1 | **Lifecycle stage (inferred).** The C2 stage class (`RBActiveDevelopmentStage` / `RBServicingStage` / `RBPhaseOutStage`) with its filled template, and the C1 LOC-trend class (`GrowthStage` / `StabilizationStage` / `DeclineStage`) with its filled template. If the RQ1 verdict is not GO, the fixed sentence "This label is a rule-based inference; it has not been shown to agree with maintainer-declared status." is added. C1 and C2 are both always shown, so C's structure does not depend on RQ1. |
| C2 | **Observed evolution regularities (Lehman's laws, descriptive).** One line each for Laws I, II, III, IV, VI, VII, VIII: "consistent with" or "not consistent with" the regularity, then the filled template including the threshold and its id. Law V is omitted (WP4). An undetermined law reads "not determined ({reason})". The words "violation" and "conform" are never used. |
| C3 | **Inferred anti-patterns:** each inferred `Exhibits*` class with its filled template, or "none inferred". |
| C4 | **Module stability (inferred).** A table of the K largest modules by `moduleLoc` (K = 25, lowered to keep length; §3.5), grouped stable / active / undetermined and alphabetical within each group. Columns: module, label, evidence (filled template plus "rule: at most 2 change months and under 10 % relative churn"). Then one line: "Other modules: x stable, y active, z undetermined." |
| C5 | **Notes from the reasoner** (fixed templates, listed in the order below; "none" if empty) |

The C5 notes:
- **N1**: ABox inconsistent. The first line of the `pellet explain --inconsistent` output is shown. C1-C4 then show no labels.
- **N2**: undetermined label families, with fixed reason texts mapped from `undetermined_reason` codes (for example "complexity is not measured").
- **N3**: C1/C2 combination text, from a fixed 3×3 lookup table. Example: Growth with Servicing gives "LOC grows significantly (τ = …, p = …) but by only {locRelSenSlopeAnnual} of median size per year, below 0.05; the stage rule therefore infers servicing."
- **N4**: stage-module tension.
  - If C2 is Servicing or PhaseOut and at least one ActiveModule exists: "Although the repository-level stage is {stage}, these modules changed often in the last 12 months: …" (up to 5 modules, by lines changed, descending).
  - If C2 is Active and at least one StableModule exists: "… these modules were rarely changed: …" (up to 5, by LOC, descending).

N3 and N4 only present combinations of inferred labels and compare nothing with a constant. Under WP1 §4 item 8 they are non-inferential presentation.

**C contains no imperatives.** "Use it as background when working on the task." appears in the shared header, so it is in D as well.

### 3.4 Condition D: no-reasoning flat summary

| § | Content |
|---|---|
| D0 | Shared header: "The following information about {repo} was computed from its git history up to the base commit of this task ({S date}). Repository-level figures cover {n} complete months ending {M_S}; module-level figures cover the 12 months before the base commit. Use it as background when working on the task." |
| D1 | **Repository measurements.** One row per asserted property in the fixed set Φ: measurement (neutral display name), value, definition. Φ is every project-level property that appears as a placeholder in an explanation template of a class C can display (stage, laws including Law V's `linesAddedCV`, anti-patterns), plus `monthsSinceLastCommit`, `locStart`, `locEnd`, `commitsLast3Months`. Φ and the display names are frozen in `configs/wp5.yaml`. Rows are in a fixed order. |
| D2 | **Module measurements:** the same K modules as C4, alphabetical. Columns: LOC, commits, months with changes, lines changed, lines changed / LOC, months since last change. Then "Other modules: n not listed." |
| D3 | **Monthly activity:** the m most recent months of the window, with commits and LOC. This section is the length equalizer (§3.5). |

D contains no labels, no thresholds, no comparisons, no explanations and no ranking. Modules are alphabetical; selection is by size only, the same rule as in C.

**What C has that D lacks:** inferred stage and trend labels with explanation text; law-consistency labels with thresholds and justifications; anti-pattern labels; module stability labels; the reasoner notes N1-N4.

**What D has that C lacks:** nothing interpretive. It has extra raw numbers, so D's facts are a superset of C's (checked in §3.6).

### 3.5 Length budget and equalization

Length is measured in Unicode characters of the full appended section, including the header. Actual prompt tokens per run are logged as a check.

1. **Hard cap** of 8,000 characters for B, C and D.
2. **Build C** with K = 25. If L_C > 8,000, lower K in steps of 5, down to a minimum of 10. The same K is then used for D.
3. **Build D** with m = 0.
   - While L_D < 0.90 · L_C and m < n_months, add the next older month to D3.
   - If L_D > 1.10 · L_C at m = 0, drop D1 rows whose property is not cited in C, in fixed reverse Φ order, until L_D ≤ 1.10 · L_C.
4. **Tolerance:** |L_C − L_D| ≤ 0.10 · L_C. A task still outside it is flagged `length_violation`. It is kept in the primary analysis, excluded in SA4, and log(L_C/L_D) is added as a covariate there.

### 3.6 Determinism and lint checks (all must pass before `wp5-run-freeze`)
- **Determinism.** Running the generators twice from the same population JSON gives byte-identical output. The sha256 of each manifest goes in `wp5_manifests_index.json`.
- **D lint.** Case-insensitive, D must not contain: `stable stabil active dormant stage phase servic declin growth conform law lehman regular significan threshold consistent risk should must avoid recommend warning`. Display names are chosen so that no property name trips the lint (for example "Sen slope of monthly LOC relative to median LOC, per year").
- **C lint.** C must not contain the imperatives `should must avoid "do not" "don't" never recommend`.
- **Fact containment.** Every formatted number in C1-C4 appears in D1 or D2. One formatting function is shared by C and D:
  - integers as is;
  - p-values to 3 decimal places, or "< 0.001";
  - τ and other decimals to 2 decimal places;
  - percentages to whole numbers.
- **Neither C nor D** contains the declared PyPI status or anything taken from the gold patch or test patch.
- **Explanation fallback.** If a Pellet explanation fails, the template is filled from the asserted values of the class's own placeholder properties and flagged `explanation_fallback`. The count is reported.

### 3.7 Condition B: human contributor guidance at the base commit
- **Sources**, in this order, from the base tree if present and non-empty: `CONTRIBUTING{,.md,.rst,.txt}`, `.github/CONTRIBUTING*`, `docs/CONTRIBUTING*`, `docs/contributing*`, `docs/development*.{md,rst}`, `HACKING*`, `DEVELOPMENT*`, `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.cursorrules`, `.cursor/rules/*`, `.github/copilot-instructions.md`. README is excluded.
- **Format.** Files are concatenated with `### <path>` headers under `## Repository context` and the line "The following contributor guidance is taken from the repository at the task's base commit." The whole is cut at 8,000 characters at a line boundary, with `[truncated]` appended.
- **B unavailable** means none of these files exists. B is then **not run**, because a run would duplicate A. B-availability is a task attribute. B is in no confirmatory hypothesis (§8.4).

### 3.8 Dependence on RQ1
The only RQ1-dependent element is the qualifier sentence in C1, fixed at `wp5-generator-freeze` from the recorded RQ1 verdict. If RQ1 has not finished by then, the qualifier is included, and that is logged.

---

## 4. Outcomes (all computed without LLMs)

### 4.1 Shared definitions
- **Agent diff.** At agent exit, whatever the exit status, run `git add -A && git diff --cached base_commit`. Paths matching `__pycache__/`, `*.pyc`, `*.egg-info/`, the venv directory and `.pytest_cache/` are excluded.
- **Non-test diff:** the agent diff minus test files (regex in §3.2, plus the files in the test patch).
- **Changed lines:** added plus deleted lines from `git diff --numstat`.
- **Gold:** the SWE-rebench `patch` field, non-test part.

### 4.2 Primary outcome
**resolved** ∈ {0, 1}, computed as follows:
1. Revert the agent's changes to files in the test patch.
2. Apply the agent diff to `base_commit`, then apply the test patch.
3. Run the task's F2P and P2P tests with the SWE-rebench test command.

`resolved = 1` iff every F2P and every P2P test passes. An empty diff, or a diff that does not apply, gives 0 and is not an infra failure.

### 4.3 Secondary outcomes (pre-specified)

| ID | Outcome | Operational definition | Defined when |
|---|---|---|---|
| Y1 | ΔCCN on touched functions | Run lizard 1.24.1 on the base and patched versions of each changed non-test `.py` file. Functions are matched by (file, `long_name`). A function is touched if its patched line range overlaps a new-side hunk, or it was added (base CCN 0) or deleted (patched CCN 0). ΔCCN = Σ over touched functions of (CCN_patched − CCN_base). | non-test diff non-empty |
| Y2 | New cross-module import edges | `ast`-parse the imports of changed non-test `.py` files at base and patched. Resolve absolute imports (`R.sub…`) and relative imports to §3.2 modules. Edge m1→m2 with m1 ≠ m2, both partition modules. Y2 = \|E_patched − E_base\|. | non-test diff non-empty |
| Y3 | Share of changed lines in StableModule modules | Changed lines in modules labelled StableModule at base, divided by changed lines in modules with any stability label. Also Y3_gold (the same for the gold patch) and Y3_excess = Y3 − Y3_gold. | denominator > 0 |
| Y4 | Diff size relative to gold | log2(non-test changed lines of agent / of gold) | non-test diff non-empty |
| Y5 | Files touched | distinct non-test files in the agent diff | always (0 allowed) |
| Y6 | Steps used | `agent.n_calls`; also `hit_step_limit` = exit status `LimitsExceeded` | always |
| Y0 | Patch produced | non-test diff non-empty | always |

Two caveats apply to these outcomes:
- **Y3 is partly a manipulation check.** It uses the labels that C shows. Y3_excess and a threshold-free variant, Y3w (the mean over changed lines of the module's within-repository percentile of `moduleRelChurnInWindow`), are reported with it.
- **Y1, Y2 and Y4 are conditional on Y0.** Conditioning on a post-treatment variable can introduce selection, so Y0 is reported by condition (exploratory).

### 4.4 Uptake (descriptive manipulation check)
Per run, record whether the assistant messages contain:
- (i) the phrase "repository context";
- (ii) for C, any C label term (`stable`, `active`, `servicing`, `Law `);
- (iii) for D, any D1 display name.

These are reported by condition and model. No test is run on them.

---

## 5. Analysis population, terminal states, failures

**Terminal states:**
- **Agent terminations** (valid): `Submitted`, `LimitsExceeded` (step limit), wall-time limit reached. The diff is evaluated in every case.
- **Infra failure:** no usable trajectory because of API errors after the client's retries, environment setup failure, or a harness exception. Infra failures are retried from scratch up to 2 times. This is decided by the error type alone, without knowing the outcome. The final state is recorded.
- **Evaluation crash** (not a failing test): re-evaluated up to 2 times. If it still crashes, it counts as an infra failure.

**Primary analysis (intention-to-treat):** every scheduled run is analysed, and a final infra failure counts as `resolved = 0`. SA1 excludes final infra failures.

**Other rules:**
- **Task validation is done before runs.** A task whose environment fails validation is replaced before any run. After the first run, tasks are never dropped.
- **Environment drift.** The gold patch is re-evaluated for every task after all runs. Tasks where the gold patch now fails are flagged and excluded in SA5.
- **Model withdrawn mid-study.** The confirmatory analysis uses tasks with complete A, C and D runs for both models. All runs of the surviving model are analysed separately (exploratory). This is logged as a deviation. Replacement models are never used in the confirmatory analysis.
- **No interim analysis and no optional stopping.**

---

## 6. Primary (confirmatory) analysis

### 6.1 Models
Fitted on rows of conditions A, C and D only. B rows are analysed separately (§8.4).
- **M1 (H1, H2):** `resolved ~ C(condition, Treatment('A')) + C(stage_H3) + C(model)`
- **M2 (H3):** `resolved ~ C(condition, Treatment('A')) * C(stage_H3) + C(model)`

The GLMM is fully specified as `resolved ~ condition * stage + (1|repo) + (1|task) + model`.

**Why model is a fixed effect, not random:**
- A variance component cannot be estimated from 2 levels (1 df).
- The two models are not a random sample of LLMs: they are the only ones that worked.
- Inference is therefore conditional on these two models, and the paper says so.
- Condition × model is exploratory (§10).

### 6.2 Estimator (pure Python; R and rpy2 are not installed and will not be added)
- **Confirmatory: GEE.** Binomial family, logit link (`statsmodels` 0.15 `GEE`), `groups = repo`, exchangeable working correlation, Mancl-DeRouen bias-reduced sandwich covariance (`cov_type="bias_reduced"`).
  - Wald statistics are referred to t(G − 1) for 1-df contrasts and F(q, G − 1) for joint tests, where G is the number of repositories.
  - Tasks are nested in repositories, so clustering by repository covers both task-level and repository-level dependence, as well as the replicate and model correlation within a task.
  - The robust covariance is valid even if the working correlation is wrong.
  - The quick simulation in §7.3 gave a type I error of 0.047 at α = 0.05 and 0.013 at α/3.
- **Why not the GLMM as the confirmatory estimator.** The only pure-Python mixed logit is `BinomialBayesMixedGLM`, a variational-Bayes or Laplace posterior. Its posterior SDs are not calibrated frequentist standard errors.
- **Fallback chain**, pre-specified, applied if GEE fails to converge or the covariance is singular:
  1. the same GEE with an independence working correlation;
  2. conditional logistic regression stratified by task (`statsmodels ConditionalLogit`: condition plus condition × stage terms; model enters as a covariate), with p-values from a stratified task-level cluster bootstrap (B = 10,000).
- **Pre-specified secondary estimators**, reported alongside and never decisive:
  - (i) `BinomialBayesMixedGLM.fit_vb` with variance components for repo and task, giving conditional ORs and 95 % credible intervals;
  - (ii) the conditional logit above.
  - If the sign of the H1 or H2 estimate differs between GEE and either of these, the result is reported as "estimator-sensitive".

### 6.3 Contrasts and tests
- **H1:** β_C in M1. Two-sided t(G − 1).
- **H2:** β_C − β_D in M1, a linear contrast using the robust covariance. Two-sided t(G − 1).
- **H3:** joint Wald test of the `C:stage` interaction coefficients in M2, F(q, G − 1), with q = number of stage levels − 1.
- **Multiplicity:** Holm on (p_H1, p_H2, p_H3) at 0.05, using the existing `holm_adjusted_p`.
- **Reported effect sizes:**
  - marginal OR with 95 % CI;
  - risk difference from the paired task-level bootstrap (§8.2);
  - the stage-specific C−A and C−D ORs from M2.

---

## 7. Power analysis and task-count decision rule

### 7.1 Inputs
- **p̂0** = resolved / total among the pilot's condition-A runs, pooled over both models (20 runs), with a Jeffreys 80 % interval.
- **Model log-OR:** the pilot's model contrast over A ∪ B runs, halved and clipped to ±1.5.
- **Pilot ICC:** reported but not used (10 tasks are too few).
- **Design:** the actual frozen task-to-repository-to-stage mapping (supply S_s per stratum after the cap and validation).

### 7.2 Simulation (`simulate_power_glmm`, 1,000 replications per cell, seed 20261006)
- **Data-generating process:**
  - logit p = α + β_cond + γ_model + u_repo + v_task, with u ~ N(0, 0.2·σ²) and v ~ N(0, 0.8·σ²);
  - latent ICC = σ²/(σ² + π²/3), over the grid {0.3, **0.5**, 0.7};
  - α is calibrated by Gauss-Hermite quadrature so the marginal P(resolved | A) = p0.
- **Effects (conditional ORs):**
  - OR_C ∈ {1.25, 1.5, 2.0, 2.5, 3.0};
  - for H2, OR_D ∈ {1, √OR_C};
  - for H3, log-OR_C = 0 in ACTIVE and log 2.5 in SERVICING.
- **Analysis:** the exact §6 pipeline, run on A, C and D rows with 2 runs per cell.
- **Power** is the rejection rate at α/3 (the first Holm step, conservative) and at 0.05.
- **p0 values:** computed at p̂0 and at both Jeffreys 80 % limits.
- **MDE** = the smallest OR_C on the grid with power ≥ 0.80 at α/3 and ICC 0.5.

### 7.3 Indicative numbers
These come from a quick simulation made while drafting this plan, not the final §7.2 run. Settings: 2 tasks per repository, ICC 0.5, model log-OR −0.5, 300 replications each.

| N tasks | p0 | OR 1.5 (α/3, α) | OR 2.0 (α/3, α) |
|---|---|---|---|
| 50 | 0.10 / 0.20 / 0.35 | .07,.14 / .14,.28 / .16,.32 | .21,.41 / .41,.62 / .53,.74 |
| 60 | 0.10 / 0.20 / 0.35 | .11,.19 / .14,.31 / .15,.33 | .27,.42 / .52,.70 / .62,.80 |
| 70 | 0.10 / 0.20 / 0.35 | .10,.21 / .17,.30 / .22,.42 | .35,.52 / .57,.75 / .74,.87 |

Conclusion: at the expected supply, the design detects only large effects (conditional OR around 2.5 or more). OR 1.5 is not detectable.

### 7.4 Decision rule (fixed now)
1. **N = min(Σ S_s, 80)**, so every validated task is run. The 80-task cap is the budget: about 1,280 runs, roughly 43 hours at 30 runs per hour.
   - If supply exceeds 80: all PO tasks are kept, then equal allocation across ID, EVO and SERV in each stratum's seeded order.
   - Runs per task, step limit and models never change.
2. **Labels, from power P at (p̂0, OR 2.0, ICC 0.5, α/3)**, written into `wp5_power.json` before `wp5-run-freeze`:
   - **POWERED**: P ≥ 0.80.
   - **UNDER-POWERED**: 0.50 ≤ P < 0.80.
   - **UNINFORMATIVE**: P < 0.50, or p̂0 < 0.05, or p̂0 > 0.90.
3. **Under every label** H1-H3 are tested as specified, and the MDE is reported in the paper's method section.
   - Under UNDER-POWERED or UNINFORMATIVE, a non-rejection is pre-declared to mean "inconclusive at MDE = x", never "no effect".
   - The primary outcome is never switched.
4. **If Σ S_s < 40**, WP5 becomes exploratory as a whole: no confirmatory family, and estimates with CIs only.
5. **PO** joins H3 only under the §2.2 rule.
6. **Within-stage claims** are made only for strata with ≥ 15 tasks from ≥ 5 repositories. Other strata are descriptive.

---

## 8. Secondary analyses (pre-specified; never confirmatory)

### 8.1 Secondary outcome models
Formula `y ~ C(condition) + C(stage_H3) + C(model)`, GEE clustered by repository, exchangeable, bias-reduced, t(G − 1):

| Outcome | Family |
|---|---|
| Y1 ΔCCN, Y4, Y3_excess | Gaussian, identity |
| Y2, Y5, Y6 | Poisson, log |
| Y3, Y3w | binomial fractional logit on the proportion (Papke-Wooldridge quasi-likelihood) |
| Y0, `hit_step_limit`, any-new-edge (Y2 > 0) | binomial |

- **Contrasts:** C−A, C−D and D−A, with 95 % CIs.
- **Holm** is applied across the 7 outcomes (Y0-Y6) × {C−A, C−D} as a descriptive guard only.
- **Y1, Y2 and Y4** are also reported among resolved runs.

### 8.2 Task-level paired bootstrap
- For each task t and pair (X, A), d_t = mean outcome in X minus mean in A, over that task's runs (4 per condition).
- Resample tasks with replacement within declared stage (`stratified_bootstrap_indices`, B = 10,000, seed 20261006). Percentile 95 % CI of the mean of d_t.
- Applied to `resolved` (risk difference) and to Y0-Y6. Medians are also given for Y1 and Y4.
- SA6 uses a two-stage cluster bootstrap: repositories, then tasks within each repository.

### 8.3 Within-stage estimates
C−A and C−D ORs per collapsed stage from M2, and per four-level stratum descriptively, with CIs. The §7.4 rule 6 limits claims.

### 8.4 Condition B
On the B-available subset T_B: `resolved ~ C(condition) + C(stage_H3) + C(model)` over A, B, C and D. Report B−A and C−B, plus the composition of T_B by stratum and the B length distribution.

---

## 9. Sensitivity analyses (reported in full; they never change a confirmatory verdict)

| ID | Variant |
|---|---|
| SA1 | Exclude final infra failures |
| SA2 | Each model alone |
| SA3 | Exclude tasks with an agent-manifest file in the tree at base |
| SA4 | Exclude `length_violation` tasks; add log(L_C/L_D) as a covariate |
| SA5 | Exclude tasks whose gold patch fails at the drift check |
| SA6 | GEE grouped by task instead of repository; two-stage bootstrap |
| SA7 | Fallback estimators (§6.2) even if GEE converged |
| SA8 | Exclude tasks with any `explanation_fallback` in C |
| SA9 | Y3 recomputed under the module thresholds Rs ∈ {0.05, 0.20}, Ms ∈ {0, 1, 4}, W ∈ {6, 24}, one at a time. Done by TBox rebuild and re-reasoning the unchanged module ABox; W needs re-measurement. |

---

## 10. Exploratory (labelled as such, no multiplicity claims)
- condition × model;
- D vs A (do facts alone change outcomes?);
- the four-level declared-stage interaction;
- the inferred stage replacing the declared stage (only if RQ1 = GO);
- per-model per-stage tables;
- uptake (§4.4) by condition;
- step-efficiency curves;
- outcome differences by C's inferred stage within each declared stratum.

---

## 11. Process controls (the garden-of-forking-paths guard)

1. **Commit order:**
   - (a) this plan, markdown only, now;
   - (b) once the RQ1 population run has finished and its outputs are hashed: the `thresholds.yaml` `module_stability` group, the module classes in `build_ontology.py`, the module measures, `populate_v2.py --snapshot-commit`, the generators, the harness, the outcome extractors, the analysis runner and the statistics functions, with unit tests;
   - (c) generators debugged on development tasks only, then tag **`wp5-generator-freeze`**;
   - (d) commit the task list, the pilot summary and `wp5_power.json` with the N decision;
   - (e) generate B, C and D for all sample tasks, run the lints, commit the manifests and the index, then tag **`wp5-run-freeze`**;
   - (f) runs;
   - (g) commit the ledger hash as `wp5-runs-complete`;
   - (h) analysis.

   Editing `thresholds.yaml` before step (b) is not allowed: `build_tboxes` would rebuild RQ1 variant TBoxes from it.
2. **After `wp5-generator-freeze`**, a generator bug found before the first run is fixed and **all** manifests are regenerated, with a logged deviation. After the first non-pilot run, generators, prompts, tasks and thresholds never change.
3. **No peeking.**
   - Until `wp5-runs-complete`, no one computes resolve rates or secondary outcomes by condition, by model × condition or by stage × condition.
   - The monitor may show only: runs by terminal state, infra failures and retries by condition and model, prompt-token counts by condition (an integrity check on the injection), and evaluation errors.
   - Evaluation workers write `wp5_outcomes.jsonl`, which nobody aggregates.
   - The analysis runner is tested beforehand on synthetic data from the power simulator, and that test is committed.
4. **Pilot.** Its A/B results are reported as a pilot only. They are used only for p̂0 and the model log-OR (§7.1).
5. **Deviations** go in `wp5_deviations.json` and `papers/paper1/wp5-deviations-log.md` (what, why, when, and whether before or after `wp5-runs-complete`). The paper reports them.
6. **No LLM** appears anywhere in manifest generation, outcome measurement or analysis. No human raters are used.

---

## 12. Outputs (`experiments/paper1_ontology_manifests/results/real_v2/wp5/`, force-added per CLAUDE.md)

Runners: `experiments/paper1_ontology_manifests/run_wp5.py` and `run_wp5_analysis.py`. Generators: `manifests/generator/wp5_manifests.py`; the JSS-era `generate.py` stays untouched. Configs: `configs/wp5.yaml` and `configs/wp5_analysis.yaml`.

| File | Contents |
|---|---|
| `wp5_tasks.json` | frozen tasks, stage evidence, exclusions with reasons, cap selection, development set |
| `wp5_pilot_summary.json` | p̂0 with its Jeffreys interval, model log-OR, pilot ICC (descriptive) |
| `wp5_power.json` | the §7.2 grid, MDE, label, N decision |
| `population/{task}.json` | base-commit pipeline output including `modules` |
| `manifests/{task}/{B,C,D}.md`, `wp5_manifests_index.json` | sha256, characters, K, m, lint, containment and length flags, explanation fallbacks |
| `runs/{task}/{cond}/{model}/{k}/` | `traj.json.gz`, `patch.diff`, `eval.json`. Archived with sha256 if too large to commit. |
| `wp5_runs.jsonl` | ledger: schedule order, states, retries, tokens, model id |
| `wp5_outcomes.jsonl` | per-run Y0-Y6, resolved, uptake |
| `wp5_run_manifest.json` | plan commit, the three tags, hashes (tasks, manifests, TBox, prompt, configs), library and agent versions, seeds, timestamps |
| `wp5_primary.json` | M1/M2 estimates, H1-H3 raw and Holm p-values, verdicts, estimator agreement |
| `wp5_secondary.json`, `wp5_sensitivity.json`, `wp5_exploratory.json` | §8, §9, §10 |
| `wp5_deviations.json` | always present |

---

## 13. Additions to `shared/evaluation/statistics.py`

Pure functions, no file I/O, `np.random.default_rng(seed)`. Existing functions are unchanged; `holm_adjusted_p`, `stratified_bootstrap_indices` and `percentile_ci` are reused.
```python
def gee_fit(df, formula, groups, family="binomial", cov_struct="exchangeable",
            cov_type="bias_reduced") -> dict          # params, robust cov, converged, n_clusters, fallback_used
def wald_contrast(params, cov, L, df_denom=None) -> dict   # est, se, t/F, p (t(G-1) / F(q, G-1) when df_denom)
def conditional_logit_by_stratum(df, formula, strata, n_boot=10_000, seed=20261006,
                                 boot_strata=None) -> dict
def binomial_mixed_glm_vb(df, fixed_formula, vc_formulas: dict) -> dict   # posterior means, 95 % CrI, ORs
def calibrate_marginal_intercept(p0, sigma2, n_quad=40) -> float
def simulate_glmm_binary(design_df, alpha, betas: dict, sigma2_repo, sigma2_task, rng) -> np.ndarray
def simulate_power(design_df, p0, effects: dict, icc, repo_share, model_logor, test_fn,
                   n_rep=1000, seed=20261006, alphas=(0.05/3, 0.05)) -> dict
def mde_from_grid(power_grid, target=0.80) -> float | None
def jeffreys_interval(k, n, level=0.80) -> tuple[float, float]
def paired_task_bootstrap(df, outcome, cond_x, cond_ref, task_col, strata_col,
                          n_boot=10_000, seed=20261006, stat="mean") -> dict
def two_stage_cluster_bootstrap_indices(repos, tasks, strata, n_boot, seed) -> list[np.ndarray]
```
Unit tests:
- the GEE test recovers a known log-OR on simulated data;
- type I error ≤ 0.06 at OR 1 over 500 replications;
- the Jeffreys interval matches `scipy.stats.beta`;
- the bootstrap is reproducible for a fixed seed.

**Other code needed before `wp5-generator-freeze`:**
- `measures.py`: module partition and module measures;
- `MEASURED_PROPERTIES` with domain `Mo`;
- `AboxWriter.module()`;
- the module classes in `build_inference_module()`;
- `populate_v2.py` snapshot-commit mode, with numstat paths kept;
- the outcome extractors (lizard, ast imports, numstat).

---

## 14. Predictions (stated for transparency; not criteria)
- **H1** is likely null at the realistic MDE. Manifest content rarely helps localise or fix a specific bug.
- **Y3, Y5 and Y4** are more likely to move than `resolved`.
- **Uptake** is expected to be higher for C than for D.
- **Declared PO tasks** will be inferred as servicing or active (§3.1).

---

## 15. What can be claimed

The scope sentence always reads: two NIM models, mini-SWE-agent in text mode, a 40-step limit, manifests injected into the prompt (not read from a file), and Python SWE-rebench tasks. Nothing generalises to other agents or to models as a class.

- **H1 and H2 not rejected (null):**
  - The claim is that evolution-aware manifests did not detectably change the resolve rate (marginal OR, CI), and that the design could detect OR ≥ MDE with 80 % power.
  - Smaller effects are not excluded. The claim "manifests do not help" is never made.
  - As the revision plan fixes, the ontology's contribution then rests on RQ1 and RQ2: explanations and consistency guarantees.
  - Secondary differences are hypotheses for future work.
- **H1 positive, H2 null:**
  - The benefit cannot be attributed to reasoning: the same mined facts without labels do as well.
  - This is the measured answer to R1.M4: no measurable outcome benefit from reasoning.
- **H2 positive (C ≠ D):**
  - Length-equalized, justified labels (stage, law consistency, module stability, notes) change outcomes compared with the raw facts.
  - Two limits:
    - (i) There is no component ablation, so which part of C drives the effect is unknown.
    - (ii) A Python implementation of the same rules would produce an identical C (the WP1 differential test), so the result supports "interpreted, justified labels", not "OWL reasoning" in particular.
  - What is specific to OWL remains provenance and consistency (RQ1, RQ2).
- **Negative (C < A or C < D):**
  - Reported as harm in this setting.
  - Uptake, steps and Y0 are examined descriptively for mechanisms such as distraction or context use. No post-hoc subgroup is promoted.
- **H3:**
  - A rejection means the C-vs-A effect differs by declared stage. The direction is described per stratum within the §7.4 limits.
  - A non-rejection is "no evidence of stage dependence", and given the power it is not "the effect is stage-independent".
- **Y3 (edits to stable modules):** the strongest allowed form is "C runs put a different share of changed lines into modules C labels stable, relative to the gold patch (Y3_excess)". It is never presented as better quality or better architecture, because the labels are part of the treatment.
- **Under every outcome:** WP5 says nothing about whether Lehman's laws are valid. B results are exploratory. Pilot numbers are not evidence.

---

### Critical files for implementation
- /home/adtgrade/research/senso-framework/ontology/population/populate_v2.py (`--snapshot-commit`: ancestry-only history at :176, :190, :329; keep numstat paths in `attach_churn` :248-283; `modules` block and module explanations in `populate_repo` :719)
- /home/adtgrade/research/senso-framework/ontology/modules/build_ontology.py (`Mo`-domain `MEASURED_PROPERTIES` :189; StableModule/ActiveModule in `build_inference_module` :1264, next to the C2 classes :1322-1353; `Module`/`hasModule` already at :296/:380)
- /home/adtgrade/research/senso-framework/ontology/modules/thresholds.yaml (`module_stability` group, added only after the RQ1 run finishes)
- /home/adtgrade/research/senso-framework/ontology/population/measures.py (module partition and module measures)
- /home/adtgrade/research/senso-framework/shared/evaluation/statistics.py (§13 functions)
- New: /home/adtgrade/research/senso-framework/manifests/generator/wp5_manifests.py, /home/adtgrade/research/senso-framework/experiments/paper1_ontology_manifests/run_wp5.py, /home/adtgrade/research/senso-framework/experiments/paper1_ontology_manifests/run_wp5_analysis.py, /home/adtgrade/research/senso-framework/experiments/paper1_ontology_manifests/configs/wp5.yaml and /home/adtgrade/research/senso-framework/experiments/paper1_ontology_manifests/configs/wp5_analysis.yaml

## 16. Main-session alignment notes (2026-10-06, before commit)

- Harness CLI is `experiments/paper1_ontology_manifests/run_wp5.py` (subcommands build-pool, validate, run, evaluate, report), built in parallel with this plan; `run_wp5.py` replaces the plan's `run_wp5_agents.py`. The analysis runner remains `run_wp5_analysis.py`.
- The pilot summary is written by the harness under `results/real_v2/wp5_pilot/`; it is copied to `results/real_v2/wp5/wp5_pilot_summary.json` before the power decision.
- RQ1 uses HEAD-reachable commits filtered by author date, exactly as its pre-registration (§3) specifies; the ancestry-only `--snapshot-commit` mode is required for WP5 only.
