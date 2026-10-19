## Repository context

The following information about nose-devs/nose2 was computed from its git history up to the base commit of this task (2024-05-31). Repository-level figures cover 36 complete months ending 2024-04; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 12845 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 13212 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | -0.15 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | 0.189 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.00 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 6 | Commits with author date in the last three window months. |
| Months with at least one commit | 26 | Window months with one or more commits. |
| Share of months with at least one commit | 0.72 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 3.08 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 1.54 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 2.92 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.20 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.11 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.33 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.47 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.00 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 0.03 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 367.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| docs | 54 | 0 | 0 | 0 | 0 % | 22 |
| nose2/__init__.py | 3 | 4 | 3 | 8 | 267 % | 0 |
| nose2/__main__.py | 8 | 0 | 0 | 0 | 0 % | 51 |
| nose2/_toml.py | 19 | 3 | 1 | 30 | 158 % | 0 |
| nose2/collector.py | 68 | 0 | 0 | 0 | 0 % | 51 |
| nose2/config.py | 63 | 1 | 1 | 1 | 2 % | 4 |
| nose2/events.py | 906 | 3 | 2 | 42 | 5 % | 0 |
| nose2/exceptions.py | 9 | 1 | 1 | 2 | 22 % | 4 |
| nose2/loader.py | 96 | 1 | 1 | 1 | 1 % | 4 |
| nose2/main.py | 290 | 4 | 4 | 28 | 10 % | 0 |
| nose2/plugins | 3704 | 11 | 6 | 106 | 3 % | 0 |
| nose2/result.py | 111 | 2 | 2 | 5 | 5 % | 4 |
| nose2/runner.py | 51 | 1 | 1 | 1 | 2 % | 4 |
| nose2/session.py | 206 | 3 | 3 | 30 | 15 % | 0 |
| nose2/sphinxext.py | 223 | 1 | 1 | 2 | 1 % | 1 |
| nose2/suite.py | 139 | 1 | 1 | 2 | 1 % | 1 |
| nose2/tools | 380 | 1 | 1 | 4 | 1 % | 4 |
| nose2/util.py | 306 | 2 | 2 | 3 | 1 % | 4 |

Other modules: 0 not listed.

### Monthly activity

| Month | Commits | LOC | Distinct authors | Lines added | Lines deleted |
|---|---|---|---|---|---|
| 2024-04 | 6 | 13212 | 2 | 86 | 36 |
| 2024-03 | 0 | 13176 | 0 | 0 | 0 |
| 2024-02 | 0 | 13176 | 0 | 0 | 0 |
| 2024-01 | 8 | 13176 | 2 | 22 | 83 |
| 2023-12 | 20 | 13176 | 4 | 111 | 31 |
| 2023-11 | 2 | 13158 | 2 | 3 | 3 |
| 2023-10 | 3 | 13158 | 2 | 1 | 1 |
| 2023-09 | 5 | 13158 | 2 | 0 | 0 |
| 2023-08 | 2 | 13158 | 2 | 3 | 7 |
| 2023-07 | 0 | 13162 | 0 | 0 | 0 |
| 2023-06 | 0 | 13162 | 0 | 0 | 0 |
| 2023-05 | 5 | 13162 | 2 | 0 | 0 |
| 2023-04 | 9 | 13162 | 3 | 20 | 75 |
| 2023-03 | 1 | 13212 | 1 | 0 | 0 |
| 2023-02 | 1 | 13212 | 1 | 3 | 23 |
| 2023-01 | 2 | 13212 | 1 | 0 | 0 |
| 2022-12 | 4 | 13212 | 1 | 0 | 0 |
| 2022-11 | 3 | 13212 | 3 | 0 | 0 |
| 2022-10 | 5 | 13212 | 1 | 0 | 0 |
| 2022-09 | 2 | 13212 | 1 | 0 | 0 |
