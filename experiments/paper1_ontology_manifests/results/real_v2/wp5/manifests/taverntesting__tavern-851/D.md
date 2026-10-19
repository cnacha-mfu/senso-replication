## Repository context

The following information about taverntesting/tavern was computed from its git history up to the base commit of this task (2023-02-16). Repository-level figures cover 36 complete months ending 2023-01; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 7446 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 9106 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.95 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.04 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 40 | Commits with author date in the last three window months. |
| Months with at least one commit | 29 | Window months with one or more commits. |
| Share of months with at least one commit | 0.81 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 4.20 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 1.06 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 4.00 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.31 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.23 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.00 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.75 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.00 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 0.22 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 1660.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| docs | 159 | 20 | 9 | 127 | 80 % | 0 |
| example | 640 | 3 | 2 | 246 | 38 % | 1 |
| tavern/__init__.py | 2 | 20 | 9 | 40 | 2000 % | 0 |
| tavern/_core | 3468 | 4 | 2 | 5317 | 153 % | 0 |
| tavern/_plugins | 1448 | 7 | 4 | 1161 | 80 % | 0 |
| tavern/core.py | 74 | 4 | 4 | 299 | 404 % | 0 |
| tavern/entry.py | 76 | 2 | 1 | 4 | 5 % | 0 |
| tavern/helpers.py | 175 | 3 | 2 | 285 | 163 % | 0 |
| tavern/request.py | 17 | 3 | 2 | 28 | 165 % | 0 |
| tavern/response.py | 231 | 4 | 2 | 422 | 183 % | 0 |

Other modules: 0 not listed.

### Monthly activity

| Month | Commits | LOC | Distinct authors | Lines added | Lines deleted |
|---|---|---|---|---|---|
| 2023-01 | 8 | 9106 | 3 | 6129 | 5179 |
