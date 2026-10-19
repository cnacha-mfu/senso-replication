## Repository context

The following information about kjd/idna was computed from its git history up to the base commit of this task (2020-02-17). Repository-level figures cover 36 complete months ending 2020-01; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): phase-out. Evidence: phase-out: no commit for 13 months.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 0.52, p < 0.001, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): not consistent with this regularity. 8 of 36 months active (ratio 0.22 < 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): not consistent with this regularity. Churn CV 3.64 >= 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): not consistent with this regularity. Commit-rate CV 2.61 >= 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 0.52, p < 0.001, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): not consistent with this regularity. Bug-fix ratio second half 0.23 < 0.9 x first half 0.57. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): not consistent with this regularity. Merge months 0.03 <= 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| idna/__init__.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| idna/idnadata.py | stable | changed in 1 of the last 12 months; lines changed = 3 % of its size; rule: at most 2 change months and under 10 % relative churn |
| idna/intranges.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| tools | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| idna/codec.py | active | 43 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| idna/compat.py | active | 25 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| idna/core.py | active | 23 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| idna/package_data.py | active | 200 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| idna/uts46data.py | active | 150 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 0 stable, 0 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): LOC grows significantly (τ = 0.52, p < 0.001), but the last commit was 13 months before the end of the window, at or above the 12-month dormancy limit; the stage rule therefore infers phase-out.
- N4 (stage and modules): Although the repository-level stage is phase-out, these modules changed often in the last 12 months: idna/uts46data.py (12355 lines changed); idna/core.py (70 lines changed); idna/codec.py (40 lines changed); idna/compat.py (2 lines changed); idna/package_data.py (2 lines changed).
