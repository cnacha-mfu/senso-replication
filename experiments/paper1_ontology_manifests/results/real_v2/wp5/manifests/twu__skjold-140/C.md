## Repository context

The following information about twu/skjold was computed from its git history up to the base commit of this task (2022-09-30). Repository-level figures cover 32 complete months ending 2022-08; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): active development. Evidence: active development: recent commits, significant LOC growth (tau = 0.81, p < 0.001) of 0.27 of median size per year.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 0.81, p < 0.001, 32 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 22 of 32 months active (ratio 0.69 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): not consistent with this regularity. Churn CV 2.30 >= 2.0 over 32 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): consistent with this regularity. Commit-rate CV 1.12 < 1.5 over 32 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 0.81, p < 0.001, 32 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): not consistent with this regularity. Bug-fix ratio second half 0.13 < 0.9 x first half 0.25. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): not consistent with this regularity. Merge months 0.00 <= 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

- Copy-paste over reuse: recent agent ratio 0.42 > 0.3 with LOC growth 1.02 > 0.5 and bloat evidence. Thresholds: a_agent_copy, a_loc_growth_copy, a_loc_growth_copy2, a_loc_per_feature, a_loc_vs_cx_factor, a_min_months.

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| src/skjold/cvss.py | stable | changed in 1 of the last 12 months; lines changed = 3 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/skjold/cli.py | active | 10 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/skjold/core.py | active | 134 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/skjold/formats.py | active | 59 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/skjold/ignore.py | active | 18 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/skjold/sources | active | 38 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/skjold/tasks.py | active | 17 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/skjold/__init__.py | undetermined | not determined (the module has no non-blank lines) |

Other modules: 0 stable, 0 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured); module stability for 1 module(s) without non-blank lines.
- N3 (stage rules): LOC grows significantly (τ = 0.81, p < 0.001) and by 0.27 of median size per year, at or above 0.05; the stage rule therefore infers active development.
- N4 (stage and modules): Although the repository-level stage is active development, these modules were rarely changed in the last 12 months: src/skjold/cvss.py (144 LOC).
