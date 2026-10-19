## Repository context

The following information about cevoaustralia/aws-google-auth was computed from its git history up to the base commit of this task (2017-12-21). Repository-level figures cover 6 complete months ending 2017-11; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): servicing. Evidence: servicing: recent commits, but no substantial LOC growth.
- LOC trend: stabilization. Evidence: no significant LOC trend (Mann-Kendall tau = 0.60, p = 0.071, 6 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 5 of 6 months active (ratio 0.83 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): consistent with this regularity. Churn CV 1.40 < 2.0 over 6 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): consistent with this regularity. Commit-rate CV 1.46 < 1.5 over 6 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. No significant LOC trend (Mann-Kendall tau = 0.60, p = 0.071, 6 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): not consistent with this regularity. Bug-fix ratio second half 0.08 < 0.9 x first half 0.23. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): consistent with this regularity. Merge months 0.50 > 0.3 and multi-author months 0.50 > 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| aws_google_auth/__init__.py | active | 204 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| aws_google_auth/_version.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| aws_google_auth/prepare.py | active | 204 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| aws_google_auth/u2f.py | active | 133 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 0 stable, 0 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): There is no significant LOC trend (τ = 0.60, p = 0.071); the stage rule therefore infers servicing.
- N4 (stage and modules): Although the repository-level stage is servicing, these modules changed often in the last 12 months: aws_google_auth/__init__.py (858 lines changed); aws_google_auth/prepare.py (194 lines changed); aws_google_auth/u2f.py (97 lines changed); aws_google_auth/_version.py (11 lines changed).
