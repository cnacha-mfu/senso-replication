## Repository context

The following information about PyCQA/isort was computed from its git history up to the base commit of this task (2024-01-15). Repository-level figures cover 36 complete months ending 2023-12; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 21958 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 23366 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.19 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | 0.099 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.00 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 45 | Commits with author date in the last three window months. |
| Months with at least one commit | 36 | Window months with one or more commits. |
| Share of months with at least one commit | 1.00 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 1.90 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 1.20 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 1.58 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.33 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.38 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.78 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.81 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.14 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 0.06 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 469.33 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| isort/__init__.py | 37 | 0 | 0 | 0 | 0 % | 31 |
| isort/_vendored | 641 | 0 | 0 | 0 | 0 % | 13 |
| isort/api.py | 581 | 0 | 0 | 0 | 0 % | 13 |
| isort/core.py | 463 | 2 | 1 | 2 | < 1 % | 11 |
| isort/deprecated | 328 | 3 | 2 | 27 | 8 % | 11 |
| isort/exceptions.py | 146 | 0 | 0 | 0 | 0 % | 30 |
| isort/files.py | 36 | 0 | 0 | 0 | 0 % | 33 |
| isort/format.py | 127 | 0 | 0 | 0 | 0 % | 13 |
| isort/hooks.py | 77 | 1 | 1 | 5 | 6 % | 12 |
| isort/identify.py | 178 | 2 | 2 | 8 | 4 % | 1 |
| isort/io.py | 58 | 0 | 0 | 0 | 0 % | 13 |
| isort/literal.py | 83 | 0 | 0 | 0 | 0 % | 12 |
| isort/main.py | 1237 | 2 | 2 | 6 | < 1 % | 11 |
| isort/output.py | 585 | 0 | 0 | 0 | 0 % | 13 |
| isort/parse.py | 532 | 5 | 3 | 39 | 7 % | 1 |
| isort/place.py | 115 | 1 | 1 | 2 | 2 % | 12 |
| isort/profiles.py | 86 | 1 | 1 | 2 | 2 % | 3 |
| isort/settings.py | 817 | 4 | 2 | 14 | 2 % | 1 |
| isort/setuptools_commands.py | 51 | 1 | 1 | 2 | 4 % | 12 |
| isort/sorting.py | 108 | 0 | 0 | 0 | 0 % | 13 |
| isort/stdlibs | 1865 | 2 | 1 | 237 | 13 % | 1 |
| isort/utils.py | 51 | 0 | 0 | 0 | 0 % | 27 |
| isort/wrap.py | 137 | 1 | 1 | 17 | 12 % | 3 |
| isort/wrap_modes.py | 319 | 1 | 1 | 3 | 1 % | 3 |
| scripts | 516 | 3 | 2 | 16 | 3 % | 1 |

Other modules: 9 not listed.

### Monthly activity

| Month | Commits | LOC | Distinct authors | Lines added | Lines deleted |
|---|---|---|---|---|---|
| 2023-12 | 31 | 23366 | 5 | 266 | 101 |
| 2023-11 | 5 | 23101 | 4 | 3 | 2 |
| 2023-10 | 9 | 23101 | 5 | 117 | 21 |
| 2023-09 | 10 | 23101 | 3 | 1 | 1 |
| 2023-08 | 7 | 23101 | 3 | 0 | 0 |
| 2023-07 | 7 | 23101 | 4 | 1 | 1 |
| 2023-06 | 3 | 23101 | 3 | 0 | 0 |
| 2023-05 | 6 | 23101 | 2 | 0 | 0 |
| 2023-04 | 3 | 23101 | 1 | 0 | 0 |
| 2023-03 | 6 | 23101 | 4 | 0 | 0 |
| 2023-02 | 21 | 23101 | 6 | 7 | 79 |
| 2023-01 | 26 | 23155 | 8 | 122 | 68 |
| 2022-12 | 103 | 24157 | 11 | 661 | 1732 |
| 2022-11 | 6 | 24040 | 3 | 4 | 16 |
| 2022-10 | 1 | 24040 | 1 | 0 | 2 |
| 2022-09 | 2 | 24040 | 2 | 6 | 2 |
| 2022-08 | 1 | 24040 | 1 | 1 | 1 |
| 2022-07 | 1 | 24040 | 1 | 1 | 1 |
| 2022-06 | 1 | 24040 | 1 | 0 | 0 |
| 2022-05 | 22 | 24040 | 4 | 18 | 14 |
| 2022-04 | 2 | 23969 | 1 | 23 | 1 |
| 2022-03 | 1 | 23969 | 1 | 0 | 0 |
| 2022-02 | 5 | 23969 | 3 | 33 | 23 |
| 2022-01 | 5 | 23969 | 4 | 0 | 0 |
| 2021-12 | 7 | 23969 | 3 | 115 | 14 |
| 2021-11 | 38 | 23927 | 4 | 404 | 62 |
| 2021-10 | 38 | 23594 | 8 | 554 | 170 |
| 2021-09 | 13 | 23092 | 5 | 491 | 8 |
| 2021-08 | 13 | 22841 | 3 | 831 | 1448 |
| 2021-07 | 49 | 23436 | 6 | 216 | 67 |
| 2021-06 | 85 | 23316 | 11 | 1267 | 595 |
| 2021-05 | 24 | 22586 | 7 | 122 | 30 |
| 2021-04 | 36 | 22546 | 5 | 260 | 80 |
| 2021-03 | 55 | 22470 | 5 | 450 | 136 |
| 2021-02 | 47 | 22128 | 7 | 417 | 73 |
| 2021-01 | 18 | 21958 | 3 | 95 | 116 |
