## Repository context

The following information about networkx/networkx was computed from its git history up to the base commit of this task (2024-03-07). Repository-level figures cover 36 complete months ending 2024-02; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): active development. Evidence: active development: recent commits, significant LOC growth (tau = 0.97, p < 0.001) of 0.07 of median size per year.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 0.97, p < 0.001, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 36 of 36 months active (ratio 1.00 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): consistent with this regularity. Churn CV 0.99 < 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): consistent with this regularity. Commit-rate CV 0.54 < 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 0.97, p < 0.001, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): consistent with this regularity. Bug-fix ratio second half 0.21 >= 0.9 x first half 0.24. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): not consistent with this regularity. Merge months 0.00 <= 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| networkx/exception.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| networkx/lazy_imports.py | stable | changed in 2 of the last 12 months; lines changed = 7 % of its size; rule: at most 2 change months and under 10 % relative churn |
| benchmarks | active | 139 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| doc | active | changed in 8 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| examples | active | changed in 12 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| networkx/__init__.py | active | changed in 5 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| networkx/algorithms | active | 20 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| networkx/classes | active | changed in 10 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| networkx/convert.py | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| networkx/convert_matrix.py | active | 18 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| networkx/drawing | active | changed in 10 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| networkx/generators | active | changed in 12 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| networkx/linalg | active | changed in 10 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| networkx/readwrite | active | changed in 11 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| networkx/relabel.py | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| networkx/utils | active | changed in 8 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| tools | active | 154 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 0 stable, 0 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): LOC grows significantly (τ = 0.97, p < 0.001) and by 0.07 of median size per year, at or above 0.05; the stage rule therefore infers active development.
- N4 (stage and modules): Although the repository-level stage is active development, these modules were rarely changed in the last 12 months: networkx/lazy_imports.py (143 LOC); networkx/exception.py (84 LOC).
