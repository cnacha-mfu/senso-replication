## Repository context

The following information about python-trio/trio was computed from its git history up to the base commit of this task (2024-09-23). Repository-level figures cover 36 complete months ending 2024-08; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): active development. Evidence: active development: recent commits, significant LOC growth (tau = 0.92, p < 0.001) of 0.12 of median size per year.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 0.92, p < 0.001, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 36 of 36 months active (ratio 1.00 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): not consistent with this regularity. Churn CV 3.31 >= 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): consistent with this regularity. Commit-rate CV 0.60 < 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 0.92, p < 0.001, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): consistent with this regularity. Bug-fix ratio second half 0.15 >= 0.9 x first half 0.13. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): consistent with this regularity. Merge months 1.00 > 0.3 and multi-author months 1.00 > 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| docs | active | changed in 11 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| notes-to-self | active | changed in 7 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/trio/_abc.py | active | changed in 5 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/trio/_channel.py | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/trio/_core | active | changed in 11 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/trio/_dtls.py | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/trio/_file_io.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/trio/_highlevel_open_tcp_listeners.py | active | changed in 5 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/trio/_highlevel_open_tcp_stream.py | active | 117 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/trio/_highlevel_socket.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/trio/_highlevel_ssl_helpers.py | active | 128 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/trio/_path.py | active | changed in 7 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/trio/_signals.py | active | 124 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/trio/_socket.py | active | changed in 5 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/trio/_ssl.py | active | 112 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/trio/_subprocess.py | active | changed in 7 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/trio/_subprocess_platform | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/trio/_sync.py | active | 140 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/trio/_tests | active | changed in 7 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/trio/_threads.py | active | changed in 7 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/trio/_timeouts.py | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/trio/_tools | active | changed in 9 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/trio/_unix_pipes.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/trio/_util.py | active | changed in 6 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| src/trio/socket.py | active | changed in 4 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 0 stable, 14 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): LOC grows significantly (τ = 0.92, p < 0.001) and by 0.12 of median size per year, at or above 0.05; the stage rule therefore infers active development.
