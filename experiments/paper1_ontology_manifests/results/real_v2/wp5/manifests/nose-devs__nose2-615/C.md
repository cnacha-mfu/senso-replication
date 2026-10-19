## Repository context

The following information about nose-devs/nose2 was computed from its git history up to the base commit of this task (2024-05-31). Repository-level figures cover 36 complete months ending 2024-04; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): servicing. Evidence: servicing: recent commits, but no substantial LOC growth.
- LOC trend: stabilization. Evidence: no significant LOC trend (Mann-Kendall tau = -0.15, p = 0.189, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 26 of 36 months active (ratio 0.72 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): not consistent with this regularity. Churn CV 3.08 >= 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): not consistent with this regularity. Commit-rate CV 1.54 >= 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. No significant LOC trend (Mann-Kendall tau = -0.15, p = 0.189, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): not consistent with this regularity. Bug-fix ratio second half 0.11 < 0.9 x first half 0.20. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): consistent with this regularity. Merge months 0.33 > 0.3 and multi-author months 0.47 > 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| docs | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| nose2/__main__.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| nose2/collector.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| nose2/config.py | stable | changed in 1 of the last 12 months; lines changed = 2 % of its size; rule: at most 2 change months and under 10 % relative churn |
| nose2/events.py | stable | changed in 2 of the last 12 months; lines changed = 5 % of its size; rule: at most 2 change months and under 10 % relative churn |
| nose2/loader.py | stable | changed in 1 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| nose2/result.py | stable | changed in 2 of the last 12 months; lines changed = 5 % of its size; rule: at most 2 change months and under 10 % relative churn |
| nose2/runner.py | stable | changed in 1 of the last 12 months; lines changed = 2 % of its size; rule: at most 2 change months and under 10 % relative churn |
| nose2/sphinxext.py | stable | changed in 1 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| nose2/suite.py | stable | changed in 1 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| nose2/tools | stable | changed in 1 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| nose2/util.py | stable | changed in 2 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| nose2/__init__.py | active | 267 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| nose2/_toml.py | active | 158 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| nose2/exceptions.py | active | 22 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| nose2/main.py | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| nose2/plugins | active | changed in 6 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| nose2/session.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 0 stable, 0 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): There is no significant LOC trend (τ = -0.15, p = 0.189); the stage rule therefore infers servicing.
- N4 (stage and modules): Although the repository-level stage is servicing, these modules changed often in the last 12 months: nose2/plugins (106 lines changed); nose2/_toml.py (30 lines changed); nose2/session.py (30 lines changed); nose2/main.py (28 lines changed); nose2/__init__.py (8 lines changed).
