## Repository context

The following information about taverntesting/tavern was computed from its git history up to the base commit of this task (2023-02-16). Repository-level figures cover 36 complete months ending 2023-01; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): servicing. Evidence: servicing: recent commits, but no substantial LOC growth.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 0.95, p < 0.001, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 29 of 36 months active (ratio 0.81 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): not consistent with this regularity. Churn CV 4.20 >= 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): consistent with this regularity. Commit-rate CV 1.06 < 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 0.95, p < 0.001, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): not consistent with this regularity. Bug-fix ratio second half 0.23 < 0.9 x first half 0.31. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): not consistent with this regularity. Merge months 0.00 <= 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| tavern/entry.py | stable | changed in 1 of the last 12 months; lines changed = 5 % of its size; rule: at most 2 change months and under 10 % relative churn |
| docs | active | changed in 9 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| example | active | 38 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| tavern/__init__.py | active | 2000 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| tavern/_core | active | 153 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| tavern/_plugins | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| tavern/core.py | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| tavern/helpers.py | active | 163 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| tavern/request.py | active | 165 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| tavern/response.py | active | 183 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 0 stable, 0 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): LOC grows significantly (τ = 0.95, p < 0.001) but by only 0.04 of median size per year, below 0.05; the stage rule therefore infers servicing.
- N4 (stage and modules): Although the repository-level stage is servicing, these modules changed often in the last 12 months: tavern/_core (5317 lines changed); tavern/_plugins (1161 lines changed); tavern/response.py (422 lines changed); tavern/core.py (299 lines changed); tavern/helpers.py (285 lines changed).
