## Repository context

The following information about rfverbruggen/rachiopy was computed from its git history up to the base commit of this task (2020-10-07). Repository-level figures cover 36 complete months ending 2020-09; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 269 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 287 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.59 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.02 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 17 | Commits with author date in the last three window months. |
| Months with at least one commit | 8 | Window months with one or more commits. |
| Share of months with at least one commit | 0.22 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 4.48 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 2.58 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 4.33 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.08 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.13 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.11 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.06 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.00 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 0.07 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 18.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| docs | 40 | 6 | 2 | 132 | 330 % | 0 |
| rachiopy/__init__.py | 22 | 5 | 3 | 177 | 805 % | 0 |
| rachiopy/device.py | 159 | 11 | 3 | 532 | 335 % | 0 |
| rachiopy/flexschedulerule.py | 17 | 8 | 2 | 60 | 353 % | 0 |
| rachiopy/notification.py | 105 | 8 | 2 | 356 | 339 % | 0 |
| rachiopy/person.py | 29 | 4 | 2 | 96 | 331 % | 0 |
| rachiopy/rachioobject.py | 72 | 8 | 2 | 324 | 450 % | 0 |
| rachiopy/schedulerule.py | 62 | 8 | 2 | 208 | 335 % | 0 |
| rachiopy/zone.py | 114 | 9 | 3 | 360 | 316 % | 0 |

Other modules: 0 not listed.
