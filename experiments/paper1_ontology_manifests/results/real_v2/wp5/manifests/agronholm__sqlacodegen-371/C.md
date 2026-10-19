## Repository context

The following information about agronholm/sqlacodegen was computed from its git history up to the base commit of this task (2025-02-25). Repository-level figures cover 36 complete months ending 2025-01; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): servicing. Evidence: servicing: recent commits, but no substantial LOC growth.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 0.63, p < 0.001, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 24 of 36 months active (ratio 0.67 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): not consistent with this regularity. Churn CV 4.14 >= 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): not consistent with this regularity. Commit-rate CV 1.56 >= 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 0.63, p < 0.001, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): not consistent with this regularity. Bug-fix ratio second half 0.09 < 0.9 x first half 0.14. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): not consistent with this regularity. Multi-author months 0.19 <= 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

- Copy-paste over reuse: recent agent ratio 0.38 > 0.3 with LOC growth 0.52 > 0.5 and bloat evidence. Thresholds: a_agent_copy, a_loc_growth_copy, a_loc_growth_copy2, a_loc_per_feature, a_loc_vs_cx_factor, a_min_months.

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| src/sqlacodegen/__main__.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/sqlacodegen/generators.py | stable | changed in 2 of the last 12 months; lines changed = 4 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/sqlacodegen/models.py | stable | changed in 1 of the last 12 months; lines changed = 7 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/sqlacodegen/utils.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| src/sqlacodegen/cli.py | active | 21 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/sqlacodegen/__init__.py | undetermined | not determined (the module has no non-blank lines) |

Other modules: 0 stable, 0 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured); module stability for 1 module(s) without non-blank lines.
- N3 (stage rules): LOC grows significantly (τ = 0.63, p < 0.001) but by only 0.02 of median size per year, below 0.05; the stage rule therefore infers servicing.
- N4 (stage and modules): Although the repository-level stage is servicing, these modules changed often in the last 12 months: src/sqlacodegen/cli.py (20 lines changed).
