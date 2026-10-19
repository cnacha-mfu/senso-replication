## Repository context

The following information about ncclient/ncclient was computed from its git history up to the base commit of this task (2020-12-31). Repository-level figures cover 36 complete months ending 2020-11; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): active development. Evidence: active development: recent commits, significant LOC growth (tau = 0.95, p < 0.001) of 0.11 of median size per year.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 0.95, p < 0.001, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 34 of 36 months active (ratio 0.94 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): not consistent with this regularity. Churn CV 2.16 >= 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): consistent with this regularity. Commit-rate CV 0.85 < 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 0.95, p < 0.001, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): not consistent with this regularity. Bug-fix ratio second half 0.24 < 0.9 x first half 0.30. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): consistent with this regularity. Merge months 0.86 > 0.3 and multi-author months 0.89 > 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| docs | stable | changed in 2 of the last 12 months; lines changed = 5 % of its size; rule: at most 2 change months and under 10 % relative churn |
| ncclient/_version.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| ncclient/capabilities.py | stable | changed in 1 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| ncclient/debug.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| ncclient/logging_.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| versioneer.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| examples | active | 15 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ncclient/__init__.py | active | 26 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ncclient/devices | active | changed in 7 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ncclient/manager.py | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ncclient/operations | active | changed in 6 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ncclient/transport | active | changed in 6 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ncclient/xml_.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 0 stable, 0 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): LOC grows significantly (τ = 0.95, p < 0.001) and by 0.11 of median size per year, at or above 0.05; the stage rule therefore infers active development.
- N4 (stage and modules): Although the repository-level stage is active development, these modules were rarely changed in the last 12 months: versioneer.py (1529 LOC); ncclient/_version.py (439 LOC); docs (147 LOC); ncclient/capabilities.py (120 LOC); ncclient/logging_.py (21 LOC).
