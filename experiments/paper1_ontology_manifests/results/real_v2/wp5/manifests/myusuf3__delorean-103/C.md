## Repository context

The following information about myusuf3/delorean was computed from its git history up to the base commit of this task (2018-02-07). Repository-level figures cover 36 complete months ending 2018-01; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): servicing. Evidence: servicing: recent commits, but no substantial LOC growth.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 0.76, p < 0.001, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): not consistent with this regularity. 13 of 36 months active (ratio 0.36 < 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): not consistent with this regularity. Churn CV 5.57 >= 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): not consistent with this regularity. Commit-rate CV 3.57 >= 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 0.76, p < 0.001, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): not consistent with this regularity. Bug-fix ratio second half 0.11 < 0.9 x first half 0.30. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): not consistent with this regularity. Multi-author months 0.19 <= 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| delorean/__init__.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| delorean/dates.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| delorean/exceptions.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| delorean/interface.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| docs | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| version.py | active | 200 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 0 stable, 0 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): LOC grows significantly (τ = 0.76, p < 0.001) but by only 0.02 of median size per year, below 0.05; the stage rule therefore infers servicing.
- N4 (stage and modules): Although the repository-level stage is servicing, these modules changed often in the last 12 months: version.py (2 lines changed).
