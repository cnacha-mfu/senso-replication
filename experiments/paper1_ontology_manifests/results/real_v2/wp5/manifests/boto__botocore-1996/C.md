## Repository context

The following information about boto/botocore was computed from its git history up to the base commit of this task (2020-03-09). Repository-level figures cover 36 complete months ending 2020-02; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): active development. Evidence: active development: recent commits, significant LOC growth (tau = 0.99, p < 0.001) of 0.14 of median size per year.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 0.99, p < 0.001, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 36 of 36 months active (ratio 1.00 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): consistent with this regularity. Churn CV 1.08 < 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): consistent with this regularity. Commit-rate CV 0.24 < 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 0.99, p < 0.001, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): not consistent with this regularity. Bug-fix ratio second half 0.04 < 0.9 x first half 0.05. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): consistent with this regularity. Merge months 1.00 > 0.3 and multi-author months 1.00 > 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| botocore/auth.py | stable | changed in 1 of the last 12 months; lines changed = 2 % of its size; rule: at most 2 change months and under 10 % relative churn |
| botocore/docs | stable | changed in 1 of the last 12 months; lines changed < 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| botocore/eventstream.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| botocore/hooks.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| botocore/loaders.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| botocore/model.py | stable | changed in 2 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| botocore/monitoring.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| botocore/paginate.py | stable | changed in 1 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| botocore/parsers.py | stable | changed in 1 of the last 12 months; lines changed < 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| botocore/retryhandler.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| botocore/serialize.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| botocore/signers.py | stable | changed in 1 of the last 12 months; lines changed = 4 % of its size; rule: at most 2 change months and under 10 % relative churn |
| botocore/stub.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| botocore/waiter.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| botocore/args.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| botocore/awsrequest.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| botocore/client.py | active | changed in 5 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| botocore/compat.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| botocore/configprovider.py | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| botocore/credentials.py | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| botocore/exceptions.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| botocore/handlers.py | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| botocore/retries | active | 137 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| botocore/session.py | active | changed in 5 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| botocore/utils.py | active | changed in 8 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 10 stable, 3 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): LOC grows significantly (τ = 0.99, p < 0.001) and by 0.14 of median size per year, at or above 0.05; the stage rule therefore infers active development.
- N4 (stage and modules): Although the repository-level stage is active development, these modules were rarely changed in the last 12 months: botocore/docs (2976 LOC); botocore/parsers.py (832 LOC); botocore/auth.py (742 LOC); botocore/model.py (624 LOC); botocore/serialize.py (595 LOC).
