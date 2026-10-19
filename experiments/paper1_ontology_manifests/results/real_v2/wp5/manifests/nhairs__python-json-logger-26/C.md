## Repository context

The following information about nhairs/python-json-logger was computed from its git history up to the base commit of this task (2024-11-05). Repository-level figures cover 36 complete months ending 2024-10; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): active development. Evidence: active development: recent commits, significant LOC growth (tau = 0.70, p < 0.001) of 0.13 of median size per year.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 0.70, p < 0.001, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): not consistent with this regularity. 14 of 36 months active (ratio 0.39 < 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): not consistent with this regularity. Churn CV 3.86 >= 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): not consistent with this regularity. Commit-rate CV 2.05 >= 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 0.70, p < 0.001, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): consistent with this regularity. Bug-fix ratio second half 0.12 >= 0.9 x first half 0.09. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): not consistent with this regularity. Merge months 0.11 <= 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| scripts | active | 140 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pythonjsonlogger/__init__.py | active | 248 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pythonjsonlogger/core.py | active | 145 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pythonjsonlogger/defaults.py | active | 143 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pythonjsonlogger/exception.py | active | 142 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pythonjsonlogger/json.py | active | 184 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pythonjsonlogger/msgspec.py | active | 159 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pythonjsonlogger/orjson.py | active | 167 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/pythonjsonlogger/utils.py | active | 138 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 0 stable, 0 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): LOC grows significantly (τ = 0.70, p < 0.001) and by 0.13 of median size per year, at or above 0.05; the stage rule therefore infers active development.
