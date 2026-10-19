## Repository context

The following information about seung-lab/cloud-volume was computed from its git history up to the base commit of this task (2021-04-30). Repository-level figures cover 36 complete months ending 2021-03; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): active development. Evidence: active development: recent commits, significant LOC growth (tau = 1.00, p < 0.001) of 0.36 of median size per year.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 1.00, p < 0.001, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 36 of 36 months active (ratio 1.00 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): consistent with this regularity. Churn CV 1.70 < 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): consistent with this regularity. Commit-rate CV 0.63 < 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 1.00, p < 0.001, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): consistent with this regularity. Bug-fix ratio second half 0.34 >= 0.9 x first half 0.22. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): consistent with this regularity. Merge months 0.50 > 0.3 and multi-author months 0.72 > 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| benchmarks | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| cloudvolume/connectionpools.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| cloudvolume/dask.py | stable | changed in 1 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| cloudvolume/provenance.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| cloudvolume/py_compressed_segmentation.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| cloudvolume/sharedmemory.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| cloudvolume/skeleton.py | stable | changed in 2 of the last 12 months; lines changed < 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| cloudvolume/storage | stable | changed in 1 of the last 12 months; lines changed = 6 % of its size; rule: at most 2 change months and under 10 % relative churn |
| cloudvolume/threaded_queue.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| cloudvolume/volumecutout.py | stable | changed in 1 of the last 12 months; lines changed = 3 % of its size; rule: at most 2 change months and under 10 % relative churn |
| cloudvolume/__init__.py | active | changed in 11 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| cloudvolume/cacheservice.py | active | changed in 6 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| cloudvolume/chunks.py | active | changed in 5 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| cloudvolume/cloudvolume.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| cloudvolume/datasource | active | changed in 12 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| cloudvolume/exceptions.py | active | 21 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| cloudvolume/frontends | active | changed in 8 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| cloudvolume/lib.py | active | changed in 6 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| cloudvolume/lru.py | active | 26 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| cloudvolume/mesh.py | active | 17 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| cloudvolume/microviewer | active | 12 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| cloudvolume/paths.py | active | 18 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| cloudvolume/scheduler.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| cloudvolume/secrets.py | active | 34 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| cloudvolume/server.py | active | 21 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 1 stable, 1 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): LOC grows significantly (τ = 1.00, p < 0.001) and by 0.36 of median size per year, at or above 0.05; the stage rule therefore infers active development.
- N4 (stage and modules): Although the repository-level stage is active development, these modules were rarely changed in the last 12 months: cloudvolume/storage (1005 LOC); cloudvolume/skeleton.py (941 LOC); benchmarks (239 LOC); cloudvolume/py_compressed_segmentation.py (223 LOC); cloudvolume/threaded_queue.py (202 LOC).
