## Repository context

The following information about facelessuser/wcmatch was computed from its git history up to the base commit of this task (2023-04-26). Repository-level figures cover 36 complete months ending 2023-03; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 6391 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 8153 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.87 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.06 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 1 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 3 | Commits with author date in the last three window months. |
| Months with at least one commit | 15 | Window months with one or more commits. |
| Share of months with at least one commit | 0.42 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 2.23 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 1.58 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 2.24 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.31 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.24 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.08 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.03 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.00 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 0.28 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 1762.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| hatch_build.py | 39 | 2 | 2 | 50 | 128 % | 0 |
| wcmatch/__init__.py | 5 | 1 | 1 | 17 | 340 % | 11 |
| wcmatch/__meta__.py | 156 | 5 | 3 | 9 | 6 % | 0 |
| wcmatch/_wcmatch.py | 274 | 3 | 2 | 49 | 18 % | 2 |
| wcmatch/_wcparse.py | 1442 | 11 | 3 | 396 | 27 % | 2 |
| wcmatch/fnmatch.py | 94 | 6 | 3 | 115 | 122 % | 2 |
| wcmatch/glob.py | 804 | 10 | 3 | 340 | 42 % | 2 |
| wcmatch/pathlib.py | 202 | 4 | 4 | 89 | 44 % | 0 |
| wcmatch/posix.py | 71 | 1 | 1 | 2 | 3 % | 7 |
| wcmatch/util.py | 202 | 6 | 4 | 16 | 8 % | 0 |
| wcmatch/wcmatch.py | 248 | 4 | 3 | 34 | 14 % | 2 |

Other modules: 0 not listed.
