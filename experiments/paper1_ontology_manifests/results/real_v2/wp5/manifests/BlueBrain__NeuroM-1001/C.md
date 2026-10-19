## Repository context

The following information about BlueBrain/NeuroM was computed from its git history up to the base commit of this task (2022-03-10). Repository-level figures cover 36 complete months ending 2022-02; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): servicing. Evidence: servicing: recent commits, but no substantial LOC growth.
- LOC trend: stabilization. Evidence: no significant LOC trend (Mann-Kendall tau = -0.17, p = 0.141, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 27 of 36 months active (ratio 0.75 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): not consistent with this regularity. Churn CV 2.85 >= 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): consistent with this regularity. Commit-rate CV 1.01 < 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. No significant LOC trend (Mann-Kendall tau = -0.17, p = 0.141, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): consistent with this regularity. Bug-fix ratio second half 0.23 >= 0.9 x first half 0.25. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): not consistent with this regularity. Merge months 0.00 <= 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| neurom/stats.py | stable | changed in 1 of the last 12 months; lines changed = 2 % of its size; rule: at most 2 change months and under 10 % relative churn |
| doc | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| examples | active | 37 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| neurom/__init__.py | active | 93 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| neurom/apps | active | changed in 5 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| neurom/check | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| neurom/core | active | changed in 6 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| neurom/exceptions.py | active | 69 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| neurom/features | active | changed in 10 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| neurom/geom | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| neurom/io | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| neurom/morphmath.py | active | 21 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| neurom/utils.py | active | 67 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| neurom/view | active | 205 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| neurom/viewer.py | active | 64 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 0 stable, 0 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): There is no significant LOC trend (τ = -0.17, p = 0.141); the stage rule therefore infers servicing.
- N4 (stage and modules): Although the repository-level stage is servicing, these modules changed often in the last 12 months: neurom/features (3462 lines changed); neurom/core (3423 lines changed); neurom/view (2051 lines changed); neurom/io (1033 lines changed); neurom/check (987 lines changed).
