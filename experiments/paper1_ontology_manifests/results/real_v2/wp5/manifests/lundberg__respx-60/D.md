## Repository context

The following information about lundberg/respx was computed from its git history up to the base commit of this task (2020-06-01). Repository-level figures cover 7 complete months ending 2020-05; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 7 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 7 | Month ends at which the lines of code were counted. |
| LOC in the first month | 1025 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 1856 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.71 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | 0.019 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.91 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 14 | Commits with author date in the last three window months. |
| Months with at least one commit | 6 | Window months with one or more commits. |
| Share of months with at least one commit | 0.86 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 1.39 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 1.33 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 1.40 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.09 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.09 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.71 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.29 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.00 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 0.81 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 831.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| respx/__init__.py | 46 | 10 | 4 | 86 | 187 % | 1 |
| respx/__version__.py | 1 | 9 | 5 | 17 | 1700 % | 0 |
| respx/api.py | 194 | 29 | 4 | 2049 | 1056 % | 1 |
| respx/fixtures.py | 11 | 2 | 1 | 14 | 127 % | 5 |
| respx/mocks.py | 175 | 6 | 3 | 1166 | 666 % | 0 |
| respx/models.py | 271 | 20 | 5 | 674 | 249 % | 0 |
| respx/transports.py | 363 | 3 | 2 | 446 | 123 % | 0 |

Other modules: 0 not listed.
