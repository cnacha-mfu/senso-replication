## Repository context

The following information about stravalib/stravalib was computed from its git history up to the base commit of this task (2023-11-05). Repository-level figures cover 36 complete months ending 2023-10; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): active development. Evidence: active development: recent commits, significant LOC growth (tau = 0.89, p < 0.001) of 0.09 of median size per year.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 0.89, p < 0.001, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 20 of 36 months active (ratio 0.56 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): not consistent with this regularity. Churn CV 3.61 >= 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): not consistent with this regularity. Commit-rate CV 1.84 >= 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 0.89, p < 0.001, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): consistent with this regularity. Bug-fix ratio second half 0.46 >= 0.9 x first half 0.37. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): consistent with this regularity. Merge months 0.31 > 0.3 and multi-author months 0.44 > 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| docs | active | 231 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| examples | active | 109 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/stravalib/__init__.py | active | 133 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/stravalib/client.py | active | 121 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/stravalib/exc.py | active | 139 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/stravalib/field_conversions.py | active | 160 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/stravalib/model.py | active | 129 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/stravalib/protocol.py | active | 115 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/stravalib/strava_model.py | active | 110 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/stravalib/unit_registry.py | active | 133 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/stravalib/unithelper.py | active | 128 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/stravalib/util | active | 118 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 0 stable, 0 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): LOC grows significantly (τ = 0.89, p < 0.001) and by 0.09 of median size per year, at or above 0.05; the stage rule therefore infers active development.
