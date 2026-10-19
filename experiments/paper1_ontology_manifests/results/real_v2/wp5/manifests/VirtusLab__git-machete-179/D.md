## Repository context

The following information about VirtusLab/git-machete was computed from its git history up to the base commit of this task (2021-08-23). Repository-level figures cover 36 complete months ending 2021-07; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 0 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 4506 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.96 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.55 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 55 | Commits with author date in the last three window months. |
| Months with at least one commit | 34 | Window months with one or more commits. |
| Share of months with at least one commit | 0.94 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 1.61 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 0.92 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 1.50 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.25 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.34 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.00 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.33 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.00 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 4506.00 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 4506.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| git_machete/__init__.py | 1 | 16 | 11 | 32 | 3200 % | 0 |
| git_machete/cmd.py | 1974 | 66 | 11 | 13777 | 698 % | 0 |
| git_machete/constants.py | 23 | 1 | 1 | 28 | 122 % | 0 |
| git_machete/docs.py | 544 | 4 | 1 | 735 | 135 % | 0 |
| git_machete/exceptions.py | 19 | 2 | 1 | 27 | 142 % | 0 |
| git_machete/git_operations.py | 609 | 2 | 1 | 955 | 157 % | 0 |
| git_machete/github.py | 181 | 10 | 3 | 395 | 218 % | 0 |
| git_machete/options.py | 34 | 2 | 1 | 37 | 109 % | 0 |
| git_machete/utils.py | 177 | 2 | 1 | 249 | 141 % | 0 |

Other modules: 0 not listed.
