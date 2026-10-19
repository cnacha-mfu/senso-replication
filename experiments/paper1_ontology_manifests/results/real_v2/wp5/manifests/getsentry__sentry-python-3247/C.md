## Repository context

The following information about getsentry/sentry-python was computed from its git history up to the base commit of this task (2024-07-03). Repository-level figures cover 36 complete months ending 2024-06; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): active development. Evidence: active development: recent commits, significant LOC growth (tau = 0.99, p < 0.001) of 0.45 of median size per year.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 0.99, p < 0.001, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 36 of 36 months active (ratio 1.00 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): consistent with this regularity. Churn CV 0.89 < 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): consistent with this regularity. Commit-rate CV 0.72 < 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 0.99, p < 0.001, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): not consistent with this regularity. Bug-fix ratio second half 0.17 < 0.9 x first half 0.26. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): consistent with this regularity. Merge months 0.94 > 0.3 and multi-author months 0.94 > 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| sentry_sdk/_lru_cache.py | stable | changed in 1 of the last 12 months; lines changed = 2 % of its size; rule: at most 2 change months and under 10 % relative churn |
| sentry_sdk/_queue.py | stable | changed in 1 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| docs | active | changed in 12 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| scripts | active | 162 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| sentry_sdk/_types.py | active | changed in 8 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| sentry_sdk/api.py | active | 159 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| sentry_sdk/client.py | active | changed in 10 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| sentry_sdk/consts.py | active | changed in 12 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| sentry_sdk/crons | active | changed in 5 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| sentry_sdk/db | active | 147 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| sentry_sdk/envelope.py | active | 14 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| sentry_sdk/hub.py | active | changed in 8 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| sentry_sdk/integrations | active | changed in 13 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| sentry_sdk/metrics.py | active | 186 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| sentry_sdk/profiler | active | 125 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| sentry_sdk/scope.py | active | 154 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| sentry_sdk/scrubber.py | active | changed in 5 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| sentry_sdk/serializer.py | active | 21 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| sentry_sdk/session.py | active | 10 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| sentry_sdk/sessions.py | active | 32 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| sentry_sdk/tracing.py | active | changed in 12 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| sentry_sdk/tracing_utils.py | active | changed in 11 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| sentry_sdk/transport.py | active | changed in 9 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| sentry_sdk/utils.py | active | changed in 11 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| sentry_sdk/worker.py | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 2 stable, 8 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): LOC grows significantly (τ = 0.99, p < 0.001) and by 0.45 of median size per year, at or above 0.05; the stage rule therefore infers active development.
- N4 (stage and modules): Although the repository-level stage is active development, these modules were rarely changed in the last 12 months: sentry_sdk/_queue.py (226 LOC); sentry_sdk/_lru_cache.py (114 LOC); sentry_sdk/_werkzeug.py (85 LOC); sentry_sdk/attachments.py (49 LOC).
