## Repository context

The following information about fair-software/howfairis was computed from its git history up to the base commit of this task (2021-03-02). Repository-level figures cover 6 complete months ending 2021-02; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): active development. Evidence: active development: recent commits, significant LOC growth (tau = 0.80, p = 0.027) of 0.43 of median size per year.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 0.80, p = 0.027, 6 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 4 of 6 months active (ratio 0.67 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): consistent with this regularity. Churn CV 1.70 < 2.0 over 6 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): consistent with this regularity. Commit-rate CV 1.33 < 1.5 over 6 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 0.80, p = 0.027, 6 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): not consistent with this regularity. Bug-fix ratio second half 0.14 < 0.9 x first half 0.26. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): consistent with this regularity. Merge months 0.67 > 0.3 and multi-author months 0.50 > 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| docs | active | 166 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| howfairis/__init__.py | active | 1083 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| howfairis/__version__.py | active | 3900 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| howfairis/checker.py | active | 334 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| howfairis/cli | active | 312 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| howfairis/code_repository_platforms.py | active | 125 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| howfairis/compliance.py | active | 316 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| howfairis/exceptions | active | 900 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| howfairis/get_apikeys_from_env_vars.py | active | 128 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| howfairis/mixins | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| howfairis/readme.py | active | 297 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| howfairis/readme_format.py | active | 129 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| howfairis/repo.py | active | 233 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| howfairis/requesting | active | 417 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| howfairis/schema.py | active | 475 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| howfairis/workarounds | active | 408 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 0 stable, 0 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): LOC grows significantly (τ = 0.80, p = 0.027) and by 0.43 of median size per year, at or above 0.05; the stage rule therefore infers active development.
