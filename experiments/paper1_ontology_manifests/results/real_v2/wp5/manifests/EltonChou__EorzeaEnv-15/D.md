## Repository context

The following information about EltonChou/EorzeaEnv was computed from its git history up to the base commit of this task (2024-07-01). Repository-level figures cover 36 complete months ending 2024-06; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 1665 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 6369 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.83 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.23 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 3 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 0 | Commits with author date in the last three window months. |
| Months with at least one commit | 8 | Window months with one or more commits. |
| Share of months with at least one commit | 0.22 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 3.33 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 3.28 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 3.25 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.23 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.23 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.08 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.00 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.00 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 2.83 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 4704.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| EorzeaEnv/Data | 6356 | 2 | 1 | 5143 | 81 % | 0 |
| EorzeaEnv/__init__.py | 16 | 1 | 1 | 2 | 13 % | 0 |
| EorzeaEnv/eorzea_lang.py | 8 | 0 | 0 | 0 | 0 % | 22 |
| EorzeaEnv/eorzea_place_name.py | 129 | 0 | 0 | 0 | 0 % | 22 |
| EorzeaEnv/eorzea_rainwbow.py | 57 | 0 | 0 | 0 | 0 % | 22 |
| EorzeaEnv/eorzea_time.py | 212 | 1 | 1 | 34 | 16 % | 12 |
| EorzeaEnv/eorzea_weather.py | 182 | 2 | 2 | 14 | 8 % | 0 |
| EorzeaEnv/errors.py | 7 | 1 | 1 | 6 | 86 % | 0 |

Other modules: 0 not listed.
