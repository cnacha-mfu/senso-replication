## Repository context

The following information about PyCQA/isort was computed from its git history up to the base commit of this task (2024-01-15). Repository-level figures cover 36 complete months ending 2023-12; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): servicing. Evidence: servicing: recent commits, but no substantial LOC growth.
- LOC trend: stabilization. Evidence: no significant LOC trend (Mann-Kendall tau = 0.19, p = 0.099, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 36 of 36 months active (ratio 1.00 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): consistent with this regularity. Churn CV 1.90 < 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): consistent with this regularity. Commit-rate CV 1.20 < 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. No significant LOC trend (Mann-Kendall tau = 0.19, p = 0.099, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): consistent with this regularity. Bug-fix ratio second half 0.38 >= 0.9 x first half 0.33. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): consistent with this regularity. Merge months 0.78 > 0.3 and multi-author months 0.81 > 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| isort/__init__.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| isort/_vendored | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| isort/api.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| isort/core.py | stable | changed in 1 of the last 12 months; lines changed < 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| isort/deprecated | stable | changed in 2 of the last 12 months; lines changed = 8 % of its size; rule: at most 2 change months and under 10 % relative churn |
| isort/exceptions.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| isort/files.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| isort/format.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| isort/hooks.py | stable | changed in 1 of the last 12 months; lines changed = 6 % of its size; rule: at most 2 change months and under 10 % relative churn |
| isort/identify.py | stable | changed in 2 of the last 12 months; lines changed = 4 % of its size; rule: at most 2 change months and under 10 % relative churn |
| isort/io.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| isort/literal.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| isort/main.py | stable | changed in 2 of the last 12 months; lines changed < 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| isort/output.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| isort/place.py | stable | changed in 1 of the last 12 months; lines changed = 2 % of its size; rule: at most 2 change months and under 10 % relative churn |
| isort/profiles.py | stable | changed in 1 of the last 12 months; lines changed = 2 % of its size; rule: at most 2 change months and under 10 % relative churn |
| isort/settings.py | stable | changed in 2 of the last 12 months; lines changed = 2 % of its size; rule: at most 2 change months and under 10 % relative churn |
| isort/setuptools_commands.py | stable | changed in 1 of the last 12 months; lines changed = 4 % of its size; rule: at most 2 change months and under 10 % relative churn |
| isort/sorting.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| isort/utils.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| isort/wrap_modes.py | stable | changed in 1 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| scripts | stable | changed in 2 of the last 12 months; lines changed = 3 % of its size; rule: at most 2 change months and under 10 % relative churn |
| isort/parse.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| isort/stdlibs | active | 13 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| isort/wrap.py | active | 12 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 9 stable, 0 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): There is no significant LOC trend (τ = 0.19, p = 0.099); the stage rule therefore infers servicing.
- N4 (stage and modules): Although the repository-level stage is servicing, these modules changed often in the last 12 months: isort/stdlibs (237 lines changed); isort/parse.py (39 lines changed); isort/wrap.py (17 lines changed).
