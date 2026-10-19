## Repository context

The following information about lundberg/respx was computed from its git history up to the base commit of this task (2020-06-01). Repository-level figures cover 7 complete months ending 2020-05; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): active development. Evidence: active development: recent commits, significant LOC growth (tau = 0.71, p = 0.019) of 0.91 of median size per year.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 0.71, p = 0.019, 7 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 6 of 7 months active (ratio 0.86 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): consistent with this regularity. Churn CV 1.39 < 2.0 over 7 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): consistent with this regularity. Commit-rate CV 1.33 < 1.5 over 7 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 0.71, p = 0.019, 7 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): consistent with this regularity. Bug-fix ratio second half 0.09 >= 0.9 x first half 0.09. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): not consistent with this regularity. Multi-author months 0.29 <= 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| respx/__init__.py | active | 187 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| respx/__version__.py | active | changed in 5 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| respx/api.py | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| respx/fixtures.py | active | 127 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| respx/mocks.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| respx/models.py | active | changed in 5 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| respx/transports.py | active | 123 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 0 stable, 0 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): LOC grows significantly (τ = 0.71, p = 0.019) and by 0.91 of median size per year, at or above 0.05; the stage rule therefore infers active development.
