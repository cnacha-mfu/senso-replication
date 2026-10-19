## Repository context

The following information about learningequality/ricecooker was computed from its git history up to the base commit of this task (2022-09-16). Repository-level figures cover 36 complete months ending 2022-08; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): active development. Evidence: active development: recent commits, significant LOC growth (tau = 0.93, p < 0.001) of 0.20 of median size per year.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 0.93, p < 0.001, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 34 of 36 months active (ratio 0.94 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): not consistent with this regularity. Churn CV 2.94 >= 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): consistent with this regularity. Commit-rate CV 0.74 < 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 0.93, p < 0.001, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): consistent with this regularity. Bug-fix ratio second half 0.19 >= 0.9 x first half 0.19. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): consistent with this regularity. Merge months 0.89 > 0.3 and multi-author months 0.72 > 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| docs | active | 36 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| examples | active | 121 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| resources | active | 50 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ricecooker/__init__.py | active | changed in 5 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ricecooker/chefs.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ricecooker/classes | active | changed in 8 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ricecooker/cli.py | active | 127 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ricecooker/commands.py | active | 87 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ricecooker/config.py | active | changed in 5 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ricecooker/exceptions.py | active | 193 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ricecooker/managers | active | 160 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ricecooker/utils | active | 88 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| ricecooker/templates | undetermined | not determined (the module has no non-blank lines) |

Other modules: 0 stable, 0 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured); module stability for 1 module(s) without non-blank lines.
- N3 (stage rules): LOC grows significantly (τ = 0.93, p < 0.001) and by 0.20 of median size per year, at or above 0.05; the stage rule therefore infers active development.
