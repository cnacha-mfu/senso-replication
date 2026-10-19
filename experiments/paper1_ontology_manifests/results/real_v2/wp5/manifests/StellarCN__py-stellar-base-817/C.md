## Repository context

The following information about StellarCN/py-stellar-base was computed from its git history up to the base commit of this task (2023-11-13). Repository-level figures cover 36 complete months ending 2023-10; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): active development. Evidence: active development: recent commits, significant LOC growth (tau = 0.90, p < 0.001) of 0.12 of median size per year.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 0.90, p < 0.001, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 34 of 36 months active (ratio 0.94 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): consistent with this regularity. Churn CV 1.51 < 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): consistent with this regularity. Commit-rate CV 0.70 < 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 0.90, p < 0.001, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): consistent with this regularity. Bug-fix ratio second half 0.09 >= 0.9 x first half 0.06. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): consistent with this regularity. Merge months 0.69 > 0.3 and multi-author months 0.78 > 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| stellar_sdk/asset.py | stable | changed in 2 of the last 12 months; lines changed = 3 % of its size; rule: at most 2 change months and under 10 % relative churn |
| stellar_sdk/base_server.py | stable | changed in 2 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| stellar_sdk/server.py | stable | changed in 2 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| stellar_sdk/server_async.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| docs | active | 121 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| examples | active | changed in 11 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| stellar_sdk/call_builder | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| stellar_sdk/client | active | changed in 5 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| stellar_sdk/exceptions.py | active | 36 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| stellar_sdk/keypair.py | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| stellar_sdk/memo.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| stellar_sdk/operation | active | changed in 9 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| stellar_sdk/preconditions.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| stellar_sdk/scval.py | active | 140 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| stellar_sdk/sep | active | changed in 5 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| stellar_sdk/signer_key.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| stellar_sdk/soroban_rpc.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| stellar_sdk/soroban_server.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| stellar_sdk/soroban_server_async.py | active | 117 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| stellar_sdk/strkey.py | active | changed in 5 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| stellar_sdk/transaction.py | active | changed in 7 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| stellar_sdk/transaction_builder.py | active | changed in 10 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| stellar_sdk/transaction_envelope.py | active | changed in 6 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| stellar_sdk/utils.py | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| stellar_sdk/xdr | active | changed in 10 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 0 stable, 20 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): LOC grows significantly (τ = 0.90, p < 0.001) and by 0.12 of median size per year, at or above 0.05; the stage rule therefore infers active development.
- N4 (stage and modules): Although the repository-level stage is active development, these modules were rarely changed in the last 12 months: stellar_sdk/server_async.py (320 LOC); stellar_sdk/server.py (317 LOC); stellar_sdk/base_server.py (307 LOC); stellar_sdk/asset.py (190 LOC).
