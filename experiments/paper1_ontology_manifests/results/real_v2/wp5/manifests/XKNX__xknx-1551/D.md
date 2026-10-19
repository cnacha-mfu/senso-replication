## Repository context

The following information about XKNX/xknx was computed from its git history up to the base commit of this task (2024-08-19). Repository-level figures cover 36 complete months ending 2024-07; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 41563 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 54329 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.94 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.09 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 85 | Commits with author date in the last three window months. |
| Months with at least one commit | 36 | Window months with one or more commits. |
| Share of months with at least one commit | 1.00 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 1.26 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 0.42 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 1.14 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.06 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.04 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.11 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 1.00 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.56 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 0.31 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 12766.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| examples | 1063 | 12 | 6 | 314 | 30 % | 1 |
| script | 140 | 0 | 0 | 0 | 0 % | 18 |
| xknx/__init__.py | 5 | 2 | 2 | 2 | 40 % | 2 |
| xknx/__version__.py | 2 | 5 | 4 | 10 | 500 % | 0 |
| xknx/cemi | 775 | 3 | 3 | 12 | 2 % | 2 |
| xknx/core | 779 | 11 | 4 | 207 | 27 % | 0 |
| xknx/devices | 3278 | 23 | 5 | 1540 | 47 % | 0 |
| xknx/dpt | 3419 | 26 | 5 | 9108 | 266 % | 0 |
| xknx/exceptions | 177 | 3 | 3 | 11 | 6 % | 2 |
| xknx/io | 3443 | 10 | 7 | 208 | 6 % | 1 |
| xknx/knxip | 2533 | 3 | 2 | 43 | 2 % | 3 |
| xknx/management | 527 | 7 | 5 | 312 | 59 % | 2 |
| xknx/profile | 289 | 2 | 2 | 4 | 1 % | 2 |
| xknx/remote_value | 1250 | 20 | 5 | 1153 | 92 % | 0 |
| xknx/secure | 1057 | 4 | 4 | 35 | 3 % | 2 |
| xknx/telegram | 2057 | 11 | 6 | 970 | 47 % | 0 |
| xknx/tools | 114 | 4 | 2 | 22 | 19 % | 2 |
| xknx/typing | 17 | 4 | 2 | 24 | 141 % | 1 |
| xknx/util | 9 | 1 | 1 | 1 | 11 % | 3 |
| xknx/xknx.py | 171 | 8 | 3 | 35 | 20 % | 2 |

Other modules: 0 not listed.

### Monthly activity

| Month | Commits | LOC | Distinct authors | Lines added | Lines deleted |
|---|---|---|---|---|---|
| 2024-07 | 31 | 54329 | 3 | 3543 | 3123 |
| 2024-06 | 38 | 53959 | 4 | 6580 | 5794 |
| 2024-05 | 16 | 53293 | 3 | 1624 | 492 |
| 2024-04 | 10 | 52545 | 3 | 4 | 4 |
| 2024-03 | 15 | 52545 | 3 | 43 | 12 |
| 2024-02 | 25 | 52516 | 3 | 410 | 321 |
| 2024-01 | 16 | 52431 | 3 | 341 | 32 |
| 2023-12 | 15 | 52168 | 5 | 1225 | 8 |
| 2023-11 | 8 | 51180 | 2 | 2 | 2 |
| 2023-10 | 14 | 51180 | 3 | 3 | 3 |
| 2023-09 | 15 | 51180 | 3 | 0 | 0 |
| 2023-08 | 15 | 51180 | 4 | 10 | 0 |
| 2023-07 | 11 | 51171 | 3 | 35 | 9 |
| 2023-06 | 18 | 51149 | 3 | 170 | 174 |
| 2023-05 | 24 | 51140 | 4 | 415 | 8 |
