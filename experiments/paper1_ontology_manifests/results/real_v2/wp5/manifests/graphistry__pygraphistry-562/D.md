## Repository context

The following information about graphistry/pygraphistry was computed from its git history up to the base commit of this task (2024-04-06). Repository-level figures cover 36 complete months ending 2024-03; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 10735 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 33562 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.96 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.30 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 51 | Commits with author date in the last three window months. |
| Months with at least one commit | 34 | Window months with one or more commits. |
| Share of months with at least one commit | 0.94 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 1.63 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 1.31 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 1.64 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.35 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.41 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.53 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.69 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.00 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 2.13 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 1037.59 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| demos | 452 | 0 | 0 | 0 | 0 % | 29 |
| docs | 284 | 12 | 2 | 53 | 19 % | 4 |
| graphistry/Plottable.py | 287 | 5 | 2 | 16 | 6 % | 4 |
| graphistry/PlotterBase.py | 1884 | 8 | 3 | 123 | 7 % | 3 |
| graphistry/_version.py | 444 | 2 | 1 | 6 | 1 % | 12 |
| graphistry/ai_utils.py | 405 | 1 | 1 | 4 | 1 % | 11 |
| graphistry/arrow_uploader.py | 613 | 13 | 6 | 101 | 16 % | 1 |
| graphistry/compute | 2776 | 40 | 3 | 2908 | 105 % | 2 |
| graphistry/dgl_utils.py | 560 | 2 | 2 | 9 | 2 % | 4 |
| graphistry/embed_utils.py | 502 | 7 | 2 | 97 | 19 % | 8 |
| graphistry/feature_utils.py | 2484 | 20 | 5 | 133 | 5 % | 1 |
| graphistry/features.py | 253 | 1 | 1 | 3 | 1 % | 4 |
| graphistry/gremlin.py | 721 | 0 | 0 | 0 | 0 % | 17 |
| graphistry/hyper_dask.py | 677 | 2 | 1 | 4 | 1 % | 12 |
| graphistry/layout | 2676 | 0 | 0 | 0 | 0 % | 14 |
| graphistry/layouts.py | 221 | 0 | 0 | 0 | 0 % | 21 |
| graphistry/networks.py | 263 | 0 | 0 | 0 | 0 % | 16 |
| graphistry/nodexlistry.py | 199 | 1 | 1 | 6 | 3 % | 8 |
| graphistry/plugins | 769 | 7 | 4 | 113 | 15 % | 4 |
| graphistry/pygraphistry.py | 2028 | 25 | 6 | 280 | 14 % | 1 |
| graphistry/text_utils.py | 245 | 2 | 1 | 4 | 2 % | 11 |
| graphistry/umap_utils.py | 673 | 5 | 3 | 21 | 3 % | 8 |
| graphistry/util.py | 340 | 3 | 1 | 62 | 18 % | 4 |
| graphistry/validate | 455 | 3 | 1 | 526 | 116 % | 2 |
| versioneer.py | 1558 | 0 | 0 | 0 | 0 % | 18 |

Other modules: 14 not listed.

### Monthly activity

| Month | Commits | LOC | Distinct authors | Lines added | Lines deleted |
|---|---|---|---|---|---|
| 2024-03 | 18 | 33562 | 5 | 100 | 46 |
| 2024-02 | 32 | 33559 | 3 | 2210 | 1055 |
| 2024-01 | 1 | 32539 | 1 | 19 | 6 |
| 2023-12 | 81 | 32539 | 4 | 3522 | 973 |
| 2023-11 | 12 | 30414 | 2 | 308 | 69 |
| 2023-10 | 21 | 30199 | 3 | 139 | 56 |
| 2023-09 | 22 | 30180 | 4 | 33 | 25 |
| 2023-08 | 13 | 30164 | 1 | 28 | 18 |
| 2023-07 | 7 | 30164 | 4 | 4 | 5 |
| 2023-06 | 5 | 30164 | 1 | 33 | 32 |
| 2023-05 | 16 | 30164 | 3 | 20 | 14 |
| 2023-04 | 100 | 28601 | 5 | 716 | 577 |
| 2023-03 | 68 | 28601 | 5 | 519 | 432 |
| 2023-02 | 44 | 28601 | 6 | 543 | 406 |
| 2023-01 | 123 | 28601 | 4 | 3299 | 2029 |
| 2022-12 | 38 | 28601 | 3 | 2250 | 529 |
| 2022-11 | 4 | 27422 | 3 | 773 | 63 |
| 2022-10 | 20 | 26858 | 5 | 895 | 221 |
| 2022-09 | 18 | 26230 | 5 | 633 | 413 |
| 2022-08 | 2 | 26072 | 2 | 0 | 0 |
| 2022-07 | 4 | 26072 | 1 | 2761 | 616 |
| 2022-06 | 6 | 24171 | 4 | 2885 | 2252 |
| 2022-05 | 6 | 23641 | 2 | 1283 | 105 |
| 2022-04 | 11 | 22628 | 2 | 10711 | 3671 |
| 2022-03 | 7 | 16331 | 1 | 3657 | 188 |
| 2022-02 | 0 | 13335 | 0 | 0 | 0 |
| 2022-01 | 0 | 13335 | 0 | 0 | 0 |
| 2021-12 | 8 | 13335 | 2 | 9 | 2 |
| 2021-11 | 4 | 13329 | 2 | 239 | 11 |
| 2021-10 | 2 | 13148 | 2 | 4 | 1 |
| 2021-09 | 1 | 13145 | 1 | 0 | 0 |
| 2021-08 | 17 | 13145 | 2 | 377 | 19 |
| 2021-07 | 47 | 12870 | 2 | 1843 | 237 |
