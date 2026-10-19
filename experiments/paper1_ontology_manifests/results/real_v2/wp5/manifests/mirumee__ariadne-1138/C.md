## Repository context

The following information about mirumee/ariadne was computed from its git history up to the base commit of this task (2023-11-08). Repository-level figures cover 36 complete months ending 2023-10; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): active development. Evidence: active development: recent commits, significant LOC growth (tau = 0.96, p < 0.001) of 0.36 of median size per year.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 0.96, p < 0.001, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 32 of 36 months active (ratio 0.89 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): consistent with this regularity. Churn CV 1.69 < 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): consistent with this regularity. Commit-rate CV 0.94 < 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 0.96, p < 0.001, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): not consistent with this regularity. Bug-fix ratio second half 0.13 < 0.9 x first half 0.18. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): consistent with this regularity. Merge months 0.53 > 0.3 and multi-author months 0.81 > 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| ariadne/validation | stable | changed in 2 of the last 12 months; lines changed = 4 % of its size; rule: at most 2 change months and under 10 % relative churn |
| ariadne/__init__.py | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ariadne/asgi | active | changed in 6 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ariadne/contrib | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ariadne/enums.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ariadne/executable_schema.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ariadne/explorer | active | 16 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ariadne/extensions.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ariadne/file_uploads.py | active | 59 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ariadne/graphql.py | active | changed in 5 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ariadne/inputs.py | active | 126 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ariadne/interfaces.py | active | 103 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ariadne/objects.py | active | 103 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ariadne/resolvers.py | active | 78 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ariadne/scalars.py | active | 100 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ariadne/schema_names.py | active | 131 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ariadne/schema_visitor.py | active | 28 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ariadne/subscriptions.py | active | 100 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ariadne/types.py | active | changed in 7 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ariadne/unions.py | active | 110 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ariadne/utils.py | active | 79 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ariadne/wsgi.py | active | changed in 5 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| benchmark | active | 137 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| generate_reference.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| tests_mypy | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 2 stable, 3 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): LOC grows significantly (τ = 0.96, p < 0.001) and by 0.36 of median size per year, at or above 0.05; the stage rule therefore infers active development.
- N4 (stage and modules): Although the repository-level stage is active development, these modules were rarely changed in the last 12 months: ariadne/validation (351 LOC); ariadne/logger.py (16 LOC); ariadne/constants.py (8 LOC).
