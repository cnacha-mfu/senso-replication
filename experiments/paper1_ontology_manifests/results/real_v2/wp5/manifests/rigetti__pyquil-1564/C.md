## Repository context

The following information about rigetti/pyquil was computed from its git history up to the base commit of this task (2023-04-13). Repository-level figures cover 36 complete months ending 2023-03; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): servicing. Evidence: servicing: recent commits, but no substantial LOC growth.
- LOC trend: stabilization. Evidence: no significant LOC trend (Mann-Kendall tau = -0.15, p = 0.204, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 29 of 36 months active (ratio 0.81 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): not consistent with this regularity. Churn CV 3.05 >= 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): consistent with this regularity. Commit-rate CV 0.95 < 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. No significant LOC trend (Mann-Kendall tau = -0.15, p = 0.204, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): consistent with this regularity. Bug-fix ratio second half 0.24 >= 0.9 x first half 0.23. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): not consistent with this regularity. Merge months 0.08 <= 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| docs | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pyquil/__init__.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pyquil/_memory.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pyquil/_parser | stable | changed in 1 of the last 12 months; lines changed < 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pyquil/_version.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pyquil/compatibility | stable | changed in 1 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pyquil/experiment | stable | changed in 1 of the last 12 months; lines changed < 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pyquil/external | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pyquil/latex | stable | changed in 1 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pyquil/noise.py | stable | changed in 1 of the last 12 months; lines changed = 5 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pyquil/noise_gates.py | stable | changed in 1 of the last 12 months; lines changed = 8 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pyquil/operator_estimation.py | stable | changed in 1 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pyquil/parser.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pyquil/paulis.py | stable | changed in 1 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pyquil/pyqvm.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pyquil/quantum_processor | stable | changed in 1 of the last 12 months; lines changed = 4 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pyquil/quilatom.py | stable | changed in 1 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pyquil/quilbase.py | stable | changed in 2 of the last 12 months; lines changed < 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pyquil/quiltcalibrations.py | stable | changed in 1 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pyquil/quiltwaveforms.py | stable | changed in 1 of the last 12 months; lines changed = 8 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pyquil/wavefunction.py | stable | changed in 1 of the last 12 months; lines changed = 5 % of its size; rule: at most 2 change months and under 10 % relative churn |
| pyquil/api | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| pyquil/gates.py | active | 13 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| pyquil/quil.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| pyquil/simulation | active | 13 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 0 stable, 0 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): There is no significant LOC trend (τ = -0.15, p = 0.204); the stage rule therefore infers servicing.
- N4 (stage and modules): Although the repository-level stage is servicing, these modules changed often in the last 12 months: pyquil/simulation (167 lines changed); pyquil/gates.py (128 lines changed); pyquil/api (118 lines changed); pyquil/quil.py (86 lines changed).
