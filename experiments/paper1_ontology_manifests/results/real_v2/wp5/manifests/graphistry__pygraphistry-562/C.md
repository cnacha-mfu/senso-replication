## Repository context

The following information about graphistry/pygraphistry was computed from its git history up to the base commit of this task (2024-04-06). Repository-level figures cover 36 complete months ending 2024-03; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Lifecycle stage (inferred)

- Lifecycle stage (rule-based): active development. Evidence: active development: recent commits, significant LOC growth (tau = 0.96, p < 0.001) of 0.30 of median size per year.
- LOC trend: growth. Evidence: significant growing LOC trend (Mann-Kendall tau = 0.96, p < 0.001, 36 months).
This label is a rule-based inference; it has not been shown to agree with maintainer-declared status.

### Observed evolution regularities (Lehman's laws, descriptive)

- Law I (continuing change): consistent with this regularity. 34 of 36 months active (ratio 0.94 >= 0.5). Thresholds: p_law1_active_ratio, p_law1_min_months.
- Law II (increasing complexity): not determined (complexity is not measured).
- Law III (self-regulation): consistent with this regularity. Churn CV 1.63 < 2.0 over 36 months. Thresholds: p_law3_churn_cv, p_law3_min_months.
- Law IV (conservation of organisational stability): consistent with this regularity. Commit-rate CV 1.31 < 1.5 over 36 months. Thresholds: p_law4_commit_cv, p_law4_min_months.
- Law VI (continuing growth): consistent with this regularity. Significant growing LOC trend (Mann-Kendall tau = 0.96, p < 0.001, 36 months). Thresholds: mk_alpha, mk_min_months.
- Law VII (declining quality): consistent with this regularity. Bug-fix ratio second half 0.41 >= 0.9 x first half 0.35. Thresholds: p_law7_min_active_months, p_law7_tolerance.
- Law VIII (feedback system): consistent with this regularity. Merge months 0.53 > 0.3 and multi-author months 0.69 > 0.3. Thresholds: p_law8_merge_ratio, p_law8_min_months, p_law8_multiauthor_ratio.

### Inferred anti-patterns

none inferred

### Module stability (inferred)

| Module | Label | Evidence |
|---|---|---|
| demos | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| graphistry/Plottable.py | stable | changed in 2 of the last 12 months; lines changed = 6 % of its size; rule: at most 2 change months and under 10 % relative churn |
| graphistry/_version.py | stable | changed in 1 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| graphistry/ai_utils.py | stable | changed in 1 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| graphistry/dgl_utils.py | stable | changed in 2 of the last 12 months; lines changed = 2 % of its size; rule: at most 2 change months and under 10 % relative churn |
| graphistry/features.py | stable | changed in 1 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| graphistry/gremlin.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| graphistry/hyper_dask.py | stable | changed in 1 of the last 12 months; lines changed = 1 % of its size; rule: at most 2 change months and under 10 % relative churn |
| graphistry/layout | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| graphistry/layouts.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| graphistry/networks.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| graphistry/nodexlistry.py | stable | changed in 1 of the last 12 months; lines changed = 3 % of its size; rule: at most 2 change months and under 10 % relative churn |
| graphistry/text_utils.py | stable | changed in 1 of the last 12 months; lines changed = 2 % of its size; rule: at most 2 change months and under 10 % relative churn |
| versioneer.py | stable | changed in 0 of the last 12 months; lines changed = 0 % of its size; rule: at most 2 change months and under 10 % relative churn |
| docs | active | 19 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| graphistry/PlotterBase.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| graphistry/arrow_uploader.py | active | changed in 6 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| graphistry/compute | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| graphistry/embed_utils.py | active | 19 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| graphistry/feature_utils.py | active | changed in 5 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| graphistry/plugins | active | 15 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| graphistry/pygraphistry.py | active | changed in 6 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| graphistry/umap_utils.py | active | changed in 3 of the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| graphistry/util.py | active | 18 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |
| graphistry/validate | active | 116 % of its lines changed in the last 12 months; rule: more than 2 change months or at least 10 % relative churn |

Other modules: 8 stable, 6 active, 0 undetermined.

### Notes from the reasoner

- N2 (undetermined label families): Law II (complexity is not measured).
- N3 (stage rules): LOC grows significantly (τ = 0.96, p < 0.001) and by 0.30 of median size per year, at or above 0.05; the stage rule therefore infers active development.
- N4 (stage and modules): Although the repository-level stage is active development, these modules were rarely changed in the last 12 months: graphistry/layout (2676 LOC); versioneer.py (1558 LOC); graphistry/gremlin.py (721 LOC); graphistry/hyper_dask.py (677 LOC); graphistry/dgl_utils.py (560 LOC).
