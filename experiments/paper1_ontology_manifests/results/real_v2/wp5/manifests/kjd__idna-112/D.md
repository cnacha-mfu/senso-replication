## Repository context

The following information about kjd/idna was computed from its git history up to the base commit of this task (2021-10-03). Repository-level figures cover 36 complete months ending 2021-09; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 11086 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 11506 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.70 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.02 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 5 | Commits with author date in the last three window months. |
| Months with at least one commit | 13 | Window months with one or more commits. |
| Share of months with at least one commit | 0.36 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 4.85 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 2.14 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 4.68 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.28 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.03 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.17 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.17 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.00 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 0.04 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 420.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| idna/__init__.py | 43 | 2 | 1 | 46 | 107 % | 9 |
| idna/codec.py | 93 | 2 | 1 | 41 | 44 % | 9 |
| idna/compat.py | 12 | 1 | 1 | 4 | 33 % | 9 |
| idna/core.py | 339 | 2 | 2 | 102 | 30 % | 0 |
| idna/idnadata.py | 2136 | 1 | 1 | 137 | 6 % | 1 |
| idna/intranges.py | 49 | 1 | 1 | 5 | 10 % | 9 |
| idna/package_data.py | 1 | 3 | 2 | 6 | 600 % | 5 |
| idna/uts46data.py | 8507 | 3 | 3 | 924 | 11 % | 1 |
| tools | 1 | 0 | 0 | 0 | 0 % | 50 |

Other modules: 0 not listed.
