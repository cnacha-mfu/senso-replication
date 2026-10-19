## Repository context

The following information about taverntesting/tavern was computed from its git history up to the base commit of this task (2021-02-20). Repository-level figures cover 36 complete months ending 2021-01; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 3250 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 7865 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.96 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.19 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 21 | Commits with author date in the last three window months. |
| Months with at least one commit | 33 | Window months with one or more commits. |
| Share of months with at least one commit | 0.92 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 1.65 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 1.44 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 1.59 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.27 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.28 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.17 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.75 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.00 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 1.42 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 4615.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| docs | 153 | 31 | 8 | 64 | 42 % | 0 |
| example | 629 | 0 | 0 | 0 | 0 % | 18 |
| tavern/__init__.py | 2 | 31 | 8 | 62 | 3100 % | 0 |
| tavern/_plugins | 1128 | 14 | 8 | 302 | 27 % | 0 |
| tavern/core.py | 271 | 5 | 4 | 216 | 80 % | 1 |
| tavern/entry.py | 76 | 1 | 1 | 2 | 3 % | 1 |
| tavern/plugins.py | 204 | 2 | 2 | 6 | 3 % | 5 |
| tavern/request | 18 | 1 | 1 | 15 | 83 % | 2 |
| tavern/response | 187 | 3 | 3 | 75 | 40 % | 3 |
| tavern/schemas | 426 | 8 | 6 | 199 | 47 % | 1 |
| tavern/testutils | 921 | 14 | 9 | 547 | 59 % | 1 |
| tavern/util | 1235 | 12 | 8 | 920 | 74 % | 1 |

Other modules: 0 not listed.

### Monthly activity

| Month | Commits | LOC | Distinct authors | Lines added | Lines deleted |
|---|---|---|---|---|---|
| 2021-01 | 5 | 7865 | 2 | 252 | 72 |
