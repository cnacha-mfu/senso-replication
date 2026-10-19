## Repository context

The following information about VirtusLab/git-machete was computed from its git history up to the base commit of this task (2022-04-07). Repository-level figures cover 36 complete months ending 2022-03; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 1421 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 8017 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.99 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.49 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 56 | Commits with author date in the last three window months. |
| Months with at least one commit | 34 | Window months with one or more commits. |
| Share of months with at least one commit | 0.94 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 1.84 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 0.84 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 1.78 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.29 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.44 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.03 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.44 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.00 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 4.64 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 6596.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| docs | 49 | 2 | 2 | 66 | 135 % | 0 |
| git_machete/__init__.py | 1 | 15 | 8 | 30 | 3000 % | 2 |
| git_machete/cli.py | 765 | 27 | 7 | 1885 | 246 % | 0 |
| git_machete/client.py | 2143 | 35 | 7 | 4130 | 193 % | 0 |
| git_machete/constants.py | 32 | 5 | 4 | 94 | 294 % | 2 |
| git_machete/docs.py | 605 | 16 | 9 | 911 | 151 % | 0 |
| git_machete/exceptions.py | 19 | 6 | 3 | 37 | 195 % | 5 |
| git_machete/git_operations.py | 788 | 30 | 9 | 2150 | 273 % | 0 |
| git_machete/github.py | 228 | 23 | 8 | 616 | 270 % | 0 |
| git_machete/options.py | 57 | 5 | 4 | 76 | 133 % | 0 |
| git_machete/utils.py | 186 | 12 | 8 | 381 | 205 % | 0 |

Other modules: 0 not listed.
