## Repository context

The following information about VirtusLab/git-machete was computed from its git history up to the base commit of this task (2022-06-10). Repository-level figures cover 36 complete months ending 2022-05; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): active development. Evidence: active development: recent commits, significant LOC growth (tau = 0.99, p < 0.001) of 0.62 of median size per year.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 0.99, p < 0.001, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 35 of 36 months active (ratio 0.97 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): consistent with this regularity. Churn CV 1.69 < 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): consistent with this regularity. Commit-rate CV 0.82 < 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 0.99, p < 0.001, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): consistent with this regularity. Bug-fix ratio second half 0.45 >= 0.9 x first half 0.29. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): not consistent with this regularity. Merge months 0.06 <= 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| docs | active | 138 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| git_machete/__init__.py | active | 3400 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| git_machete/cli.py | active | 253 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| git_machete/client.py | active | 213 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| git_machete/constants.py | active | 574 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| git_machete/docs.py | active | 171 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| git_machete/exceptions.py | active | 205 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| git_machete/git_operations.py | active | 298 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| git_machete/github.py | active | changed in 10 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| git_machete/options.py | active | 140 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| git_machete/utils.py | active | 261 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 0 stable, 0 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): LOC grows significantly (τ = 0.99, p < 0.001) and by 0.62 of median size per year, at or above 0.05; the stage rule therefore infers active development.
