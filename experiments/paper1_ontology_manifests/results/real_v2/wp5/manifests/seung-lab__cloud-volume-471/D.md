## Repository context

The following information about seung-lab/cloud-volume was computed from its git history up to the base commit of this task (2021-04-30). Repository-level figures cover 36 complete months ending 2021-03; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 5193 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 17371 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 1.00 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.36 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 32 | Commits with author date in the last three window months. |
| Months with at least one commit | 36 | Window months with one or more commits. |
| Share of months with at least one commit | 1.00 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 1.70 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 0.63 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 1.58 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.22 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.34 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.50 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.72 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.00 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 2.35 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 87.61 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| benchmarks | 239 | 0 | 0 | 0 | 0 % | 16 |
| cloudvolume/__init__.py | 64 | 42 | 11 | 84 | 131 % | 0 |
| cloudvolume/cacheservice.py | 464 | 8 | 6 | 251 | 54 % | 2 |
| cloudvolume/chunks.py | 170 | 8 | 5 | 79 | 46 % | 2 |
| cloudvolume/cloudvolume.py | 240 | 3 | 3 | 14 | 6 % | 0 |
| cloudvolume/connectionpools.py | 110 | 0 | 0 | 0 | 0 % | 22 |
| cloudvolume/dask.py | 137 | 1 | 1 | 2 | 1 % | 0 |
| cloudvolume/datasource | 5210 | 69 | 12 | 3296 | 63 % | 0 |
| cloudvolume/exceptions.py | 98 | 2 | 2 | 21 | 21 % | 6 |
| cloudvolume/frontends | 1127 | 17 | 8 | 186 | 17 % | 0 |
| cloudvolume/lib.py | 734 | 8 | 6 | 83 | 11 % | 2 |
| cloudvolume/lru.py | 198 | 1 | 1 | 52 | 26 % | 11 |
| cloudvolume/mesh.py | 381 | 4 | 3 | 63 | 17 % | 2 |
| cloudvolume/microviewer | 165 | 2 | 2 | 19 | 12 % | 6 |
| cloudvolume/paths.py | 142 | 3 | 2 | 25 | 18 % | 7 |
| cloudvolume/provenance.py | 132 | 0 | 0 | 0 | 0 % | 13 |
| cloudvolume/py_compressed_segmentation.py | 223 | 0 | 0 | 0 | 0 % | 29 |
| cloudvolume/scheduler.py | 88 | 3 | 3 | 53 | 60 % | 0 |
| cloudvolume/secrets.py | 128 | 2 | 2 | 43 | 34 % | 0 |
| cloudvolume/server.py | 48 | 1 | 1 | 10 | 21 % | 9 |
| cloudvolume/sharedmemory.py | 168 | 0 | 0 | 0 | 0 % | 12 |
| cloudvolume/skeleton.py | 941 | 2 | 2 | 3 | < 1 % | 4 |
| cloudvolume/storage | 1005 | 2 | 1 | 57 | 6 % | 11 |
| cloudvolume/threaded_queue.py | 202 | 0 | 0 | 0 | 0 % | 16 |
| cloudvolume/volumecutout.py | 88 | 1 | 1 | 3 | 3 % | 6 |

Other modules: 2 not listed.

### Monthly activity

| Month | Commits | LOC | Distinct authors | Lines added | Lines deleted |
|---|---|---|---|---|---|
| 2021-03 | 7 | 17371 | 2 | 10 | 5 |
| 2021-02 | 19 | 17367 | 2 | 154 | 35 |
| 2021-01 | 6 | 17262 | 2 | 167 | 40 |
| 2020-12 | 3 | 17150 | 1 | 7 | 6 |
| 2020-11 | 11 | 17150 | 1 | 318 | 125 |
| 2020-10 | 19 | 16993 | 1 | 222 | 136 |
| 2020-09 | 24 | 16920 | 4 | 301 | 116 |
| 2020-08 | 13 | 16750 | 3 | 315 | 304 |
| 2020-07 | 21 | 16733 | 3 | 841 | 653 |
| 2020-06 | 22 | 16584 | 4 | 653 | 296 |
| 2020-05 | 19 | 16298 | 1 | 855 | 232 |
| 2020-04 | 35 | 15644 | 2 | 1890 | 611 |
| 2020-03 | 21 | 14799 | 1 | 411 | 93 |
| 2020-02 | 1 | 14540 | 1 | 0 | 0 |
| 2020-01 | 18 | 14540 | 2 | 495 | 58 |
| 2019-12 | 28 | 14163 | 5 | 643 | 166 |
| 2019-11 | 20 | 13747 | 2 | 433 | 232 |
| 2019-10 | 28 | 13592 | 2 | 1047 | 188 |
| 2019-09 | 10 | 12889 | 3 | 41 | 14 |
| 2019-08 | 49 | 12865 | 4 | 4462 | 2316 |
| 2019-07 | 67 | 11148 | 3 | 7896 | 5487 |
| 2019-06 | 14 | 9217 | 2 | 2974 | 2456 |
| 2019-05 | 6 | 8795 | 3 | 63 | 17 |
| 2019-04 | 21 | 8756 | 2 | 154 | 45 |
| 2019-03 | 9 | 8674 | 2 | 27 | 13 |
| 2019-02 | 23 | 8662 | 2 | 283 | 167 |
| 2019-01 | 18 | 8555 | 4 | 188 | 36 |
| 2018-12 | 42 | 8427 | 3 | 1010 | 479 |
| 2018-11 | 47 | 8009 | 4 | 3494 | 1653 |
| 2018-10 | 33 | 6474 | 1 | 1252 | 826 |
| 2018-09 | 23 | 6121 | 2 | 129 | 101 |
