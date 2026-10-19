## Repository context

The following information about VirtusLab/git-machete was computed from its git history up to the base commit of this task (2021-11-18). Repository-level figures cover 36 complete months ending 2021-10; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): active development. Evidence: active development: recent commits, significant LOC growth (tau = 0.98, p < 0.001) of 0.49 of median size per year.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 0.98, p < 0.001, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 34 of 36 months active (ratio 0.94 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): consistent with this regularity. Churn CV 1.76 < 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): consistent with this regularity. Commit-rate CV 0.89 < 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 0.98, p < 0.001, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): consistent with this regularity. Bug-fix ratio second half 0.38 >= 0.9 x first half 0.25. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): not consistent with this regularity. Merge months 0.03 <= 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| docs | active | 131 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| git_machete/__init__.py | active | 3000 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| git_machete/cli.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| git_machete/client.py | active | 168 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| git_machete/constants.py | active | 239 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| git_machete/docs.py | active | 148 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| git_machete/exceptions.py | active | 184 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| git_machete/git_operations.py | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| git_machete/github.py | active | changed in 6 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| git_machete/options.py | active | 134 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| git_machete/utils.py | active | 181 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 0 stable, 0 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): LOC grows significantly (τ = 0.98, p < 0.001) and by 0.49 of median size per year, at or above 0.05; the stage rule therefore infers active development.
