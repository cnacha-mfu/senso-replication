# RQ1 pre-registered analysis plan: lifecycle-stage inference compared with maintainer-declared status

`papers/paper1/rq1-preregistration.md`. Status: **PRE-REGISTERED**. It must be committed before any repository in the RQ1 sample is mined, measured or reasoned over.

> No agreement number, label or per-repository measurement for the 120 sampled repositories existed when this plan was written. The only things looked at were the ground-truth file's structure, its per-stratum label-source counts and the WP3 summary.

---

## 0. Commitment and frozen inputs

| Item | Frozen value |
|---|---|
| Ground-truth sample | `experiments/paper1_ontology_manifests/results/real_v2/wp3/ground_truth_sample.json`, sha256 `ef5f098d6e5418b72407a3d469dcbf91c1d7f7a7ff227f6f423e7ba066d6e74a` (commit `c9c800d`) |
| Ground-truth config | `configs/wp3_ground_truth.yaml`, sha256 `66f607da…f37f5a` |
| Candidate pool (used for the holdout and replacements) | `results/real_v2/wp3/candidates_raw.json`, sha256 `c3865577…1d869` |
| Snapshot | S = 2025-06-30T23:59:59Z; snapshot month M_S = 2025-06 |
| Sample | 120 repositories. Strata of 30 each: initial_development (ID), evolution (EVO), servicing (SERV), phase_out (PO). All are conflict-free. |
| Stage mapping | The mapping in `wp3_ground_truth.yaml` is adopted **as is**. In the same commit as this plan, `stage_mapping`'s comment and `mapping_status` change from PROVISIONAL to `FROZEN (rq1-preregistration)`. Nothing else in that file changes. |

**Composition of the labels** (label source only, no measurements):
- ID: 30 from classifier (2 at 2, 7 at 3, 21 at 4).
- EVO: 30 at classifier 5.
- SERV: 24 at classifier 6, 6 from README "maintenance mode".
- PO: 27 `archived_valid` (2 of them also classifier 7), 3 README-unmaintained. 9 PO repos carry `close_down_candidate`.

**The analysis script must refuse to run** if the ground-truth sha256 does not match. It must also refuse if the git tree has uncommitted changes under `ontology/` or `experiments/paper1_ontology_manifests/`.

---

## 1. Construct: Rajlich & Bennett stages and what repository data can show

Rajlich & Bennett (2000, IEEE Computer 33(7):66-71; verify before citing) define these stages:
- **Initial development**: the first functioning version is built.
- **Evolution**: capabilities and functionality are extended, possibly substantially.
- **Servicing**: only minor tactical changes (patches, wrappers), after architectural integrity or key expertise is lost.
- **Phase-out**: no more servicing, but the system may still be in use.
- **Close-down**: the system is withdrawn.

What mined history can and cannot show:

1. **Initial development and evolution cannot be told apart from LOC trend, or from any measure mined here.**
   - Every sampled repository has at least 24 months of history and a PyPI release before the snapshot. In R&B terms each one has already shipped a working version, so it is past initial development in the strict sense.
   - PyPI "Alpha/Beta" declares API-stability intent, not an R&B stage.
   - Both strata are expected to add capability, so both should show LOC growth. No theory gives a repository-observable separator.
   - **Consequence: the primary analysis uses three collapsed classes.**
     - ACTIVE = ID ∪ EVO (n = 60)
     - SERVICING = SERV (n = 30)
     - PHASE_OUT = PO (n = 30)
   - The 4-class picture is reported only descriptively (§7.4).
2. **Phase-out leaves the code unchanged, it does not shrink it.**
   - A project with no further servicing has a constant monthly LOC series.
   - For a constant series, `pymannkendall.original_test` returns S = 0, p = 1.0 (checked on `[5]*24`). The canonical classifier therefore labels a frozen repository **Stabilization**, not Decline.
   - LOC trend alone cannot separate servicing from phase-out. Recency of change can.
3. **Mann-Kendall is rank-based and ignores magnitude.**
   - A servicing project that adds a few lines of patches every month has a nearly monotone LOC series, so τ is close to 1 and p is very small. That is "Growth".
   - Separating evolution from servicing needs a measure of *how much* the code grows (the Sen slope relative to size), not only whether it grows.
4. **Cumulative monthly LOC is strongly autocorrelated.** The original Mann-Kendall test therefore over-rejects (Hamed & Rao 1998; verify). D6 keeps the original test, and a modified test is a sensitivity analysis (§8).
5. **Close-down is not separable from phase-out** with these signals. It is not a class. The 9 `close_down_candidate` repositories stay PO, and results for them are reported separately as a descriptive breakdown.

---

## 2. Classifiers under test

All stage labels for C1 and C2 are **classes inferred by Pellet over the measured ABox**: they are read from the inferred graph, never recomputed in the analysis script. CF is an evaluation comparator and is computed in Python on purpose (§2.3).

### 2.1 C1: canonical Mann-Kendall stages (D6), unchanged

These are the existing `seo-inference` classes (`build_ontology.py:1292-1310`):
- `GrowthStage ≡ MKApplicable ⊓ locMKpValue[<α] ⊓ locMKTau[>0]`
- `DeclineStage ≡ MKApplicable ⊓ locMKpValue[<α] ⊓ locMKTau[<0]`
- `StabilizationStage ≡ MKApplicable ⊓ locMKpValue[≥α]`

Parameters: α = 0.05 (`mk_alpha`), `mk_min_months` = 4.

**A-priori mapping to the collapsed classes**, fixed here and used for the primary analysis:

| MK phase | Collapsed R&B class | Reason |
|---|---|---|
| Growth | ACTIVE | Significant net growth in code means capability is being added (evolution, Law VI). |
| Stabilization | SERVICING | No net functional growth while the project persists is the closest LOC-trend reading of "minor tactical change only". |
| Decline | PHASE_OUT | This is the SEO model's own claim ("decline" as end-of-life, Law VI non-conformant), and it is the claim being tested. |
| none (undetermined) | UNDETERMINED | See §5. |

The Decline mapping is the one the model claimed, not the one R&B theory supports (see §1.2). One alternative mapping, Decline→SERVICING, is reported as a secondary result (§8, S6). It can never change the verdict.

### 2.2 C2: R&B lifecycle rule set (pre-specified fallback stage model)

**Purpose.** To fix, using theory and not this sample, the two measurability defects predicted in §1.2-1.3. Only two activity measures are added. Every other candidate measure is excluded from the rules, for the reasons below, and is reported only descriptively in §7.4.

| Candidate measure | In the rules? | Reason |
|---|---|---|
| Months since last commit | **Yes** | R&B phase-out is defined as "no more servicing". Absence of change is directly observable. |
| Relative LOC growth rate (Sen slope / median LOC) | **Yes** | R&B separate evolution from servicing by the *size* of changes; MK cannot (§1.3). |
| Commits per month (level) | No | It depends on team and project size. There is no scale-free threshold and no R&B basis. |
| Active-month ratio | No | It largely duplicates recency, and it would add a threshold with no theory behind it. |
| Author counts | No | The R&B mechanism (loss of expertise) is not validly proxied by headcount, which depends on size. |
| Feature-commit (`feat:`) ratio | No | Conventional-Commit adoption is unknown per repository, so a count of 0 cannot be interpreted. |
| Bug-fix ratio (D8 `BugFixCommit`) | No | It fits theory (servicing is corrective), but there is no a-priori threshold and keyword precision is unvalidated. It is tested directionally in §7.4. |
| Release cadence | No | It is PyPI metadata, the same source as the ground-truth classifier, which would create shared-source dependence. It is also not repository history. |

**New measured properties.** Python asserts these. Both are Functional. They are measurements under WP1 §3.1, with no threshold applied.
- `monthsSinceLastCommit` (xsd:integer). This is 12·(year(M_S) − year(M_last)) + (month(M_S) − month(M_last)), where M_last is the month of the latest commit author-date ≤ S. It is computed over the **full history**, not bounded by the window, and is 0 if a commit falls in 2025-06. Author date is used for consistency with `measures.monthly_series`.
- `locRelSenSlopeAnnual` (xsd:decimal). This is 12 · `locSenSlope` / max(median(LOC series), 1): a ratio of two measurements.

**New thresholds** (added to `thresholds.yaml`, group `lifecycle`, `used_in_ontology: true`):

| id | value | status | sensitivity | Rationale |
|---|---|---|---|---|
| `rb_dormancy_months` | 12 | UNJUSTIFIED (a-priori convention) | 6, 18, 24 | One full annual cycle with no change at all means no servicing in the R&B sense. A one-year inactivity window is a common proxy for unmaintained or abandoned OSS projects (e.g. Coelho & Valente FSE 2017; Avelino et al. 2019; **verify both before citing**). **24 coincides with the WP3 sampling filter** (§8, S3). |
| `rb_min_rel_loc_growth_per_year` | 0.05 | UNJUSTIFIED (a-priori convention) | 0, 0.02, 0.10 | 5 % net growth a year separates feature extension from patch accumulation in a 10 kLOC library (about 500 net LOC a year, against a stream of 10-20-line fixes). No literature value exists. The value 0 reduces C2 to "MK + dormancy", the ablation in §8. |

**Rules.** These are OWL 2 DL defined classes in `seo-inference.owl`. They are SWRL-free, every union operand and negated operand is a named class (WP1 pitfall 4b), and they use D = `rb_dormancy_months` and G = `rb_min_rel_loc_growth_per_year`.
```
Dormant                  ≡ SoftwareProject ⊓ monthsSinceLastCommit some integer[>= D]
RecentlyActive           ≡ SoftwareProject ⊓ monthsSinceLastCommit some integer[<  D]
SubstantialLocGrowth     ≡ SoftwareProject ⊓ locRelSenSlopeAnnual some decimal[>= G]
MinorLocGrowth           ≡ SoftwareProject ⊓ locRelSenSlopeAnnual some decimal[<  G]
NonSubstantialChange     ≡ StabilizationStage ⊔ DeclineStage ⊔ MinorLocGrowth
RBPhaseOutStage          ≡ Dormant
RBActiveDevelopmentStage ≡ RecentlyActive ⊓ GrowthStage ⊓ SubstantialLocGrowth
RBServicingStage         ≡ RecentlyActive ⊓ NonSubstantialChange
AllDisjoint(RBActiveDevelopmentStage, RBServicingStage, RBPhaseOutStage)
```
- Disjointness follows from the Functional properties and the complementary facets. An inconsistency is a reportable outcome (§5).
- Dormant takes precedence by construction, because Active and Servicing both require RecentlyActive.
- PHASE_OUT can be inferred without any LOC data. ACTIVE and SERVICING need the MK inputs.
- Explanation templates are added in the WP1 style. Example: "no commit for {monthsSinceLastCommit} months".

The mapping to the collapsed classes is the identity: RBActive→ACTIVE, RBServicing→SERVICING, RBPhaseOut→PHASE_OUT.

C1 is **not** modified. C2 lives in additional classes, so both are inferred in the same reasoning pass.

### 2.3 CF: independent LOC-free comparator (WP3 convergent validity)

CF uses the monthly **commit-count** series only. It never uses LOC, it is computed in the analysis script (independent implementation), and it **can never become the canonical stage model**. Its parameters are the same α and D.
1. PHASE_OUT if `monthsSinceLastCommit` ≥ D.
2. Otherwise SERVICING if Mann-Kendall on the zero-filled monthly commit counts gives p < α and τ < 0. In R&B, the move to servicing is marked by reduced change effort.
3. Otherwise ACTIVE: the commit rate is increasing or sustained. Lehman's invariant work rate applies to an evolving system.
4. UNDETERMINED if the series has fewer than 4 months.

**Independence.** CF shares no input with C1. It shares the recency rule with C2. So C2 is compared with CF both on all repositories and on the subset where neither is PHASE_OUT; in that subset the comparison is LOC-trend-and-magnitude against commit trend (§7.3).

---

## 3. Measurement protocol (applies to every repository and every configuration)

- **Commits.** All commits reachable from the default-branch HEAD of a fresh clone with author date ≤ S. Commits after S are discarded.
- **Window W_L.** The months from max(M_S − L + 1, M_0) to M_S inclusive, where M_0 is the month of the first commit. Months before the first commit are **left-truncated, never zero-filled**, so no artificial growth from 0 appears. L = 36 is primary; 24 and 48 are sensitivity values. One mining run covers 48 months, and the 24- and 36-month series are taken from it. No re-mining is done per configuration.
- **Monthly commit series.** Zero-filled over W_L (`measures.monthly_series`).
- **Monthly LOC.**
  - Use the D9 repository-LOC instrument: LOC of the last first-parent default-branch commit with committer date ≤ month end.
  - Use the same tool and the same file filter for all months, frozen at the pipeline tag (§9).
  - If any month fails, the LOC series is absent (the existing `project_measurements` behaviour). C1 is then UNDETERMINED, and so is C2 unless the repository is Dormant.
- **Mann-Kendall.** `pymannkendall.original_test`, two-sided, with no autocorrelation correction (D6). τ, S, p and the Sen slope are asserted as in `measures.mann_kendall`. Values are rounded to 6 decimal places (xsd:decimal). Boundary comparisons follow the OWL facets exactly: p < α strict, ≥ D, ≥ G.
- **Sensitivity rebuilds.** α, D and G vary by rebuilding the TBox over the **unchanged ABox** (WP1 §3.3). L and the MK variant vary by re-measuring from the cached mining output.

---

## 4. Analysis population

- **Unmineable**: the clone fails, or there are zero commits ≤ S. Only these infrastructure failures count; anything the reasoner outputs does not.
  - An unmineable repository is replaced by the next **clean** candidate at positions ≥ 60 of the same stratum's seeded order. The order is reproduced by `sample_ground_truth` (seed 20261006, `candidates_raw.json`).
  - Positions 30-59 are reserved for the holdout (§6).
  - Every replacement is logged.
- **Everything else is analysed.** A repository without a stage label is an outcome, not an exclusion (§5).

---

## 5. Undetermined and inconsistent outcomes

- **UNDETERMINED** means the reasoner infers none of the three stage classes. Typical causes are a missing measured property or an LOC instrument failure. **REASONER_INCONSISTENT** means the ABox is inconsistent; its `pellet explain --inconsistent` output is stored. Both are counted by reason and by stratum.
- **Primary treatment: intention-to-classify.** UNDETERMINED (inconsistent included) is a fourth predicted category, U, that never matches any true class. Cohen's κ is computed over the category union {A, S, P, U}. U adds 0 to p_e because no repository has a true label of U, and it counts as disagreement in p_o.
- **Secondary**: a complete-case analysis that drops U, reported with the number dropped.
- **Gate**: an undetermined rate above 10 % for a classifier caps its verdict at WEAK (§6).

---

## 6. Primary analysis and go/no-go

### 6.1 Primary (confirmatory) estimand

Unweighted Cohen's κ (Cohen 1960) between the collapsed ground truth (A/S/P) and the classifier's collapsed label (A/S/P/U). Configuration: L = 36, α = 0.05, D = 12, G = 0.05, original MK, intention-to-classify, n = 120.

The confirmatory family has two members: **κ_C1** (primary) and **κ_C2** (pre-specified fallback). Decisions use **97.5 % two-sided percentile bootstrap CIs**, a Bonferroni split over the two. The 95 % CIs are also reported.

**Why unweighted Cohen's κ.**
- A classifier is compared with a reference standard. These are not two interchangeable coders, so Krippendorff's α, which assumes interchangeable coders and is built for multiple coders and missing data, does not fit. It is not computed.
- Unweighted κ is the conservative choice and decomposes by class.
- R&B stages are ordered in time (A < S < P), so linearly weighted κ (Cohen 1968) is a pre-specified secondary metric. Weights are |i−j|/2 for A = 0, S = 1, P = 2, and U has disagreement weight 1 against every class.

**Expected precision.** With collapsed marginals (0.5, 0.25, 0.25) and κ around 0.6, SE(κ) ≈ 0.063. The 97.5 % CI half-width is about ±0.14.

### 6.2 Secondary metrics (always reported, never decisive)

- Linearly weighted κ.
- Macro-F1 over {A, S, P}. Precision_k = n_kk / (predicted k). Recall_k = n_kk / (true k), with U in the denominator. If no repository is predicted as k, F1_k = 0.
- Balanced accuracy (mean recall; independent of prevalence under this design).
- Per-class precision, recall and F1, each with a CI.
- Confusion matrices:
  - (i) collapsed truth (3) × predicted (A/S/P/U);
  - (ii) the four ground-truth strata × predicted (A/S/P/U);
  - (iii) for C1 only, the **unmapped** table of the four strata × {Growth, Stabilization, Decline, U}, so readers can apply any mapping they like.
- Complete-case versions of κ and macro-F1.
- **Population-weighted accuracy and κ (exploratory).** Each stratum is weighted by its clean eligible count divided by 30, with N = {ID 1053, EVO 2060, SERV 76, PO 399} from `summary.json`. The point is that the stratified κ describes the balanced design, not the PyPI population.

### 6.3 Bootstrap

- Repository-level, **stratified by the four ground-truth strata** to match the sampling design: 30 are resampled with replacement within each stratum.
- B = 10,000 with `numpy.random.default_rng(20261006)`. One set of index draws is shared by all classifiers and all metrics, so comparisons are paired.
- Percentile intervals.
- Stratification guarantees every true class appears in each resample, so κ is always defined.
- Paired Δκ (C2 − C1, C1 − CF, C2 − CF) is reported with 95 % CIs, descriptively.

### 6.4 Verdict per classifier X ∈ {C1, C2} (primary configuration)

- **PASS**: κ̂ ≥ 0.60, and the 97.5 % lower bound of κ > 0.40, and the point recall is ≥ 0.50 for **each** of A, S and P, and the undetermined rate is ≤ 10 %.
  - The cut-offs follow Landis & Koch (1977): "substantial" from 0.61, and "fair or worse" at ≤ 0.40 is excluded. These bands are conventions, and the paper says so (McHugh 2012).
  - The per-class recall gate stops a model from passing while missing a whole stratum. This is the R1.m1/m3 concern about thin decline data.
- **WEAK**: not PASS, and the 97.5 % lower bound of κ > 0.
- **FAIL**: the 97.5 % lower bound of κ ≤ 0.

### 6.5 Decision table (fixed now)

| C1 | C2 | Action |
|---|---|---|
| PASS | any | **GO.** MK (D6) stays canonical. C2 is reported as a secondary result. |
| not PASS | PASS | **REVISE (pre-specified).** C2 becomes the candidate canonical model, confirmed on the **holdout**: positions 30-59 of each stratum's clean seeded order (servicing has 46 clean candidates left, enough), with replacements from positions ≥ 60. C2 is applied with nothing changed. If the holdout verdict is PASS (95 % CI used, single test), the decision is **GO with C2**: the authors record D10, amending D6, and the paper reports the holdout κ as the confirmatory estimate. Otherwise it is **NO-GO**. |
| not PASS | not PASS | **NO-GO.** No stage model is claimed valid. Any new model is exploratory and needs a new pre-registration and a fresh holdout. |

### 6.6 What may be claimed

- **GO**:
  - "Reasoner-inferred lifecycle stages agree with maintainer-declared status (κ = …, 97.5 % CI …) on a stratified sample of 120 PyPI-published Python repositories with at least 24 months of history."
  - Scope: initial development and evolution are **not** distinguished. The result applies to the balanced design; the population-weighted figure is reported alongside.
- **NO-GO with WEAK**:
  - The model agrees better than chance but not adequately.
  - Per-class claims are allowed only for classes whose recall 95 % lower bound is ≥ 0.50.
  - RQ3/WP5 stratifies by **declared** stage, not inferred stage.
  - Manifests may still report the measured trend with its justification ("LOC τ = …, p = …") but must not present a stage name as validated.
- **NO-GO with FAIL**:
  - This is a reported negative result: R&B stages as maintainers declare them are not recoverable from these repository measurements.
  - The ontology's contribution rests on RQ2 (consistency checking and explanations) and RQ4.
  - The same WP5 fallback applies.
- **Under every outcome**:
  - RQ1 says nothing about whether Lehman's laws are valid.
  - The C1 numbers must not be described as the JSS-era κ = 0.68.

---

## 7. Secondary analyses

### 7.1 Ablation ladder (descriptive)

C1 (MK only), then C2 with G = 0 (MK plus dormancy), then C2 (adds magnitude). Report κ, per-class recall and Δκ with CIs. This shows what each rule component adds.

### 7.2 4-class reporting

- The four strata × predicted table for every classifier.
- The proportion of ID repositories and of EVO repositories predicted ACTIVE, with a 95 % CI on the difference.
- No 4-class κ is computed, because no classifier outputs four classes.

### 7.3 Convergent validity (WP3)

Report κ with 95 % CIs for C1 vs CF, C2 vs CF, and C1 vs C2:
- on all 120 repositories;
- for C2 vs CF also on the subset where both are non-PHASE_OUT, which removes the shared recency rule.

The pre-stated expectation is κ(C1, CF) > 0. This is not a decision criterion. CF's own agreement with the ground truth is reported with every §6.2 metric.

### 7.4 Descriptive measures and directional contrasts

**Descriptives.** Medians and IQRs by the four ground-truth strata for:
- `meanMonthlyCommits`, `activeMonthRatio`, `monthsSinceLastCommit`;
- `distinctAuthorsInWindow` (new count measure), `multiAuthorMonthRatio`;
- feature-commit share, among repositories with at least one `feat:` commit, with the share of such repositories reported;
- bug-fix ratio from the inferred `BugFixCommit` (D8);
- `locMKTau`, `locRelSenSlopeAnnual`, commit-MK τ.

**Directional contrasts.** A = collapsed ground truth. Each uses a one-sided Mann-Whitney test and Cliff's δ with a bootstrap 95 % CI (B = 10,000, seed 20261006). The family E1-E6 is Holm-corrected at 0.05.

| ID | Contrast |
|---|---|
| E1 | activeMonthRatio A > S |
| E2 | activeMonthRatio S > P |
| E3 | locRelSenSlopeAnnual A > S |
| E4 | bug-fix ratio S > A |
| E5 | feature share A > S |
| E6 | commit-MK τ A > S |

**Exploratory, uncorrected, labelled as such**: X1 and X2 compare ID vs EVO, two-sided, on locRelSenSlopeAnnual and activeMonthRatio. This is the measurability check for §1.1.

None of these results may change a rule or threshold on this sample.

---

## 8. Sensitivity analyses (reported in full; they never change the verdict)

Each variant changes one factor at a time from the primary configuration and is run by the reasoner (authoritative). Each reports κ, the 97.5 % CI, per-class recall and the verdict category for C1, C2 and CF as applicable.

| ID | Factor | Values | Applies to |
|---|---|---|---|
| S1 | α | 0.01, 0.10 | C1, C2, CF |
| S2 | lookback L | 24, 48 (left-truncation counts reported) | C1, C2, CF |
| S3 | D | 6, 18, 24 | C2, CF |
| S4 | G | 0, 0.02, 0.10 | C2 |
| S5 | MK variant | Hamed-Rao modified test (`hamed_rao_modification_test`) | C1, C2 |
| S6 | C1 mapping | Decline→SERVICING | C1 |

**D = 24 is not independent evidence.**
- Sampling took only conflict-free repositories. "classifier_X_but_no_push_24m_at_snapshot" counts as a conflict, so every sampled ID, EVO and SERV repository was pushed to within 24 months of the snapshot.
- Agreement on non-PO classes at D = 24 is therefore partly guaranteed by how the sample was built. The paper must say so.
- Note: `pushed_at` is not the date of the last default-branch commit, so the guarantee is not complete.

**Full factorial (descriptive heatmap).** α(3) × L(3) × D(4) × G(4) × MK(2) = 288 configurations for C2 (and the matching subsets for C1 and CF). These are computed with a Python oracle, used only after it passes the differential test (100 % agreement with the reasoner) on all 120 repositories in the primary and one-at-a-time configurations.

**Robustness statement (pre-defined).**
- The canonical model's verdict is **robust** if its category is the same in every one-at-a-time variant except D = 24.
- Otherwise it is **fragile**, and the paper reports that, naming the factor.

### 8.1 Ground-truth noise subsets (from the WP3 noise fields)

| ID | Subset | Definition |
|---|---|---|
| N1-lenient | drop recently changed classifiers | For classifier-sourced labels, drop the repository if any release in (2024-06-30, S], or the release in effect on 2024-06-30, has a dev status that maps to a **different 4-class stage** than the snapshot value. This uses `history.releases[].time`/`dev_status`. |
| N1-strict | also drop unverifiable histories | As N1-lenient, and also drop repositories whose 12-month window cannot be verified: a release in the window has `fetched=false`, no classifier field or a null dev status, or `truncated=true` with unfetched releases in the window. |
| N2 | drop stale classifiers | Drop `classifier_stale_vs_latest = true`. |
| N3 | classifier and archive labels only | Drop the 9 README-sourced labels (6 SERV, 3 PO); README timing cannot be verified. |
| N-clean | combined | N1-strict ∩ N2 ∩ N3. |

Archive-sourced and README-sourced labels are unaffected by N1. Report every primary and secondary metric for C1, C2 and CF on each subset, with a stratified bootstrap inside the subset. A stratum with fewer than 10 repositories in a subset gets its per-class numbers marked "n < 10, not interpreted". PO results are also reported split by `close_down_candidate` (descriptive).

---

## 9. Process controls (the garden-of-forking-paths guard)

1. **This commit.** It contains this file, plus `thresholds.yaml` with `rb_dormancy_months`, `rb_min_rel_loc_growth_per_year` and `mk_test_variant: original`, plus `mapping_status: FROZEN`. Implementation code may follow in later commits, but it must implement exactly this plan.
2. **Development set.** The pipeline is debugged only on a development set: 3 clean repositories per stratum at positions ≥ 90 of the seeded order (servicing: whatever exists beyond 76 is unavailable, so use 3 SERV *conflicted* repositories instead). It is never reported as evidence. Rule and threshold edits are forbidden. Measurement-code fixes are allowed only with a failing unit test that does not depend on agreement.
3. **Pipeline freeze.** Git tag `rq1-freeze`, recording the TBox sha256, the Pellet jar hashes and the LOC-tool version. The 120 repositories are mined and reasoned **once** at that tag. Reruns are allowed only for infrastructure failure, and each is logged.
4. **Reasoner check.** Reasoner labels are cross-checked against the Python oracle (WP1 differential test). Any mismatch is reported and resolved as an encoding bug, before the ground truth is joined to the labels. The script joins labels to the ground truth only after `rq1_labels.json` has been written and hashed.
5. **Deviations.** Every departure from this plan goes in `rq1_deviations.json` (what, why, when, and whether it was made before or after unblinding). The paper reports them.
6. **No human raters and no LLM labels** at any step.

---

## 10. A-priori predictions (stated for transparency; not criteria)

- **C1**: high ACTIVE recall; low SERVICING recall (MK flags small monotone patch accumulation as growth); PHASE_OUT recall near 0 (frozen code is Stabilization, which maps to SERVICING); Decline rare in every stratum. **C1 is expected not to PASS.**
- **C2**: higher PHASE_OUT recall, bounded by how many archived repositories were already quiet 12 months before the snapshot. Most remaining errors are expected to be EVO↔SERV confusion. Two reasons:
  - PyPI 5 versus 6 is a weak proxy for R&B evolution versus servicing.
  - Many "Production/Stable" libraries are in servicing in R&B terms.
- **κ(C1, CF)**: positive but modest.

---

## 11. Output files

All go under `experiments/paper1_ontology_manifests/results/real_v2/rq1/` and are force-added, per CLAUDE.md. The runner is `experiments/paper1_ontology_manifests/run_rq1_v2.py` (new; not merged with the JSS-era runners). Its configuration is `configs/rq1_analysis.yaml`: seeds, B, grids, threshold ids, ground-truth hashes and the verdict cut-offs.

| File | Contents |
|---|---|
| `rq1_run_manifest.json` | This plan's commit hash; the `rq1-freeze` tag and commit; ground-truth, TBox and jar hashes; library versions; seeds; B; timestamps; unmineable repositories and their replacements |
| `rq1_labels.json` | Per repository: repo, 4-class stratum, collapsed truth, label source, noise-subset memberships, the measured inputs used (n, τ, p, Sen slope, locRelSenSlopeAnnual, monthsSinceLastCommit, commit-MK τ and p), C1 raw phase, C1/C2/CF collapsed labels, undetermined or inconsistent reason, explanation graph IRI. Written and hashed **before** the join |
| `rq1_primary.json` | For C1, C2 and CF: κ (95 % and 97.5 % CIs), weighted κ, macro-F1, balanced accuracy, per-class P/R/F1 with CIs, the three confusion matrices, complete-case metrics, undetermined counts, verdicts, the decision-table outcome |
| `rq1_secondary.json` | The ablation ladder, 4-class tables with the ID-vs-EVO difference, population-weighted metrics, paired Δκ |
| `rq1_convergent.json` | Pairwise κ between classifiers (all repositories and the non-PHASE_OUT subset) |
| `rq1_sensitivity.json` | One-at-a-time results S1-S6, the robustness statement, the D = 24 flag |
| `rq1_sensitivity_grid.json` | The 288-configuration factorial (oracle) plus the differential-test result |
| `rq1_noise_subsets.json` | N1-lenient, N1-strict, N2, N3, N-clean, and the close-down split |
| `rq1_descriptive.json` | Measure distributions by stratum; E1-E6 (raw p, Holm-adjusted p, Cliff's δ with CI); X1-X2 |
| `rq1_holdout_labels.json`, `rq1_holdout_primary.json` | Only if §6.5 triggers |
| `rq1_deviations.json` | Always present; may be empty |

---

## 12. Additions to `shared/evaluation/statistics.py`

These are pure functions using NumPy and SciPy, with no file I/O. Random draws use `np.random.default_rng(seed)`. The existing `bootstrap_ci` (RandomState) is left untouched. Unit tests check them against `sklearn.metrics.cohen_kappa_score` (sklearn 1.9.1 is in `.venv`) on square cases and against hand-computed non-square cases with U.

```python
def confusion_table(y_true, y_pred, true_labels, pred_labels) -> np.ndarray
    # non-square |true_labels| x |pred_labels| counts (supports pred-only 'U')
def cohen_kappa(y_true, y_pred, labels, weights: np.ndarray | None = None) -> float
    # labels = union incl. pred-only categories; weights = disagreement matrix (None = unweighted)
def ordinal_disagreement_weights(order, extra_max_disagreement=(), scheme="linear") -> np.ndarray
    # |i-j|/(k-1); extra categories (e.g. 'U') get weight 1 vs all
def per_class_metrics(y_true, y_pred, classes) -> dict
    # precision/recall/F1/support per class (pred-only categories count against recall),
    # macro_f1 (F1_k = 0 if never predicted), balanced_accuracy
def stratified_bootstrap_indices(strata, n_boot: int, seed: int) -> np.ndarray
    # (n_boot, N) indices, resampling with replacement within each stratum
def percentile_ci(samples, level: float) -> tuple[float, float]
def bootstrap_agreement(y_true, preds: dict[str, Sequence], strata, metric_fns: dict[str, Callable],
                        n_boot=10_000, seed=20261006, levels=(0.95, 0.975),
                        pairwise_diff: Sequence[tuple[str, str]] = ()) -> dict
    # point estimates + CIs per (classifier, metric); paired differences on shared indices
def agreement_verdict(kappa, kappa_lb, recalls: dict, undetermined_rate,
                      kappa_pass=0.60, lb_pass=0.40, recall_pass=0.50,
                      max_undetermined=0.10) -> str   # 'PASS' | 'WEAK' | 'FAIL'
def stratum_weighted_metrics(y_true, y_pred, strata, stratum_weights: dict, classes, labels) -> dict
    # inverse-sampling-weighted accuracy, recall, kappa
def mann_whitney_one_sided(x, y, alternative: str) -> tuple[float, float]
def cliffs_delta_ci(x, y, n_boot=10_000, seed=20261006, level=0.95) -> tuple[float, float, float]
def holm_adjusted_p(p_values) -> list[float]
    # adjusted p-values (keeps existing holm_bonferroni unchanged)
```

**Ontology and measurement additions** are needed before `rq1-freeze`. They are owned by WP1 but listed here so the freeze is complete:
- `measures.py`: `months_since_last_commit`, `rel_sen_slope_annual`, `distinct_authors_in_window`, left-truncated windows anchored at the snapshot, and an MK-variant switch.
- The `MEASURED_PROPERTIES` entries.
- The C2 classes in `build_inference_module()`.

**Important**: `populate.py:159` currently anchors the lookback at "now − L·30 days". RQ1 requires the window to be anchored at the snapshot month.

---

### Critical files for implementation
- /home/adtgrade/research/senso-framework/ontology/modules/build_ontology.py (C2 classes next to the MK stages at :1292-1310; new `MEASURED_PROPERTIES` entries at :189)
- /home/adtgrade/research/senso-framework/ontology/modules/thresholds.yaml (new `lifecycle` thresholds; `mk_alpha` and `lookback_months` sensitivity already present)
- /home/adtgrade/research/senso-framework/ontology/population/measures.py (snapshot-anchored left-truncated window, `monthsSinceLastCommit`, `locRelSenSlopeAnnual`, MK variant)
- /home/adtgrade/research/senso-framework/shared/evaluation/statistics.py (functions in §12)
- /home/adtgrade/research/senso-framework/experiments/paper1_ontology_manifests/wp3_ground_truth.py (`sample_ground_truth` seeded order, reused for replacements, the holdout at positions 30-59 and the development set) and configs/wp3_ground_truth.yaml (`mapping_status` → FROZEN)
