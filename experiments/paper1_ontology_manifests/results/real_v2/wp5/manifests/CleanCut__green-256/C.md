## Repository context

The following information about CleanCut/green was computed from its git history up to the base commit of this task (2022-01-12). Repository-level figures cover 36 complete months ending 2021-12; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): active development. Evidence: active development: recent commits, significant LOC growth (tau = 0.90, p < 0.001) of 0.08 of median size per year.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 0.90, p < 0.001, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 20 of 36 months active (ratio 0.56 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): not consistent with this regularity. Churn CV 3.86 >= 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): consistent with this regularity. Commit-rate CV 1.29 < 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 0.90, p < 0.001, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): consistent with this regularity. Bug-fix ratio second half 0.38 >= 0.9 x first half 0.33. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): not consistent with this regularity. Multi-author months 0.25 <= 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| example | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| green/__init__.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| green/__main__.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| green/cmdline.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| green/command.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| green/config.py | stable | changed in 1 of the last 12 months; lines changed = 3 % of its size; rule: at most 2 change months and under 10 % relative churn |
| green/djangorunner.py | stable | changed in 1 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| green/examples.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| green/exceptions.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| green/junit.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| green/loader.py | stable | changed in 1 of the last 12 months; lines changed < 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| green/output.py | stable | changed in 1 of the last 12 months; lines changed = 6 % of its size; rule: at most 2 change months and under 10 % relative churn |
| green/result.py | stable | changed in 2 of the last 12 months; lines changed = 4 % of its size; rule: at most 2 change months and under 10 % relative churn |
| green/runner.py | stable | changed in 1 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| green/suite.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| green/version.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| green/process.py | active | 35 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 0 stable, 0 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): LOC grows significantly (τ = 0.90, p < 0.001) and by 0.08 of median size per year, at or above 0.05; the stage rule therefore infers active development.
- N4 (stage and modules): Although the repository-level stage is active development, these modules were rarely changed in the last 12 months: green/config.py (757 LOC); green/result.py (720 LOC); green/loader.py (431 LOC); green/suite.py (228 LOC); green/output.py (180 LOC).
