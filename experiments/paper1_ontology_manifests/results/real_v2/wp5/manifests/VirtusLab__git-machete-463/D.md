## Repository context

The following information about VirtusLab/git-machete was computed from its git history up to the base commit of this task (2022-03-10). Repository-level figures cover 36 complete months ending 2022-02; module-level figures cover the 12 months before the base commit. Use it as background when working on the task.

### Repository measurements

| Measurement | Value | Definition |
|---|---|---|
| Months in the observation window | 36 | Calendar months covered by the repository-level figures. |
| Months with a LOC measurement | 36 | Month ends at which the lines of code were counted. |
| LOC in the first month | 1421 | Non-blank source lines at the end of the first month. |
| LOC in the last month | 7978 | Non-blank source lines at the end of the last month. |
| Kendall tau of the monthly LOC series | 0.99 | Rank correlation of month index and LOC (Mann-Kendall S over n(n-1)/2). |
| Mann-Kendall p-value of the monthly LOC series | < 0.001 | Two-sided p-value of the Mann-Kendall test on monthly LOC. |
| Sen slope of monthly LOC relative to median LOC, per year | 0.46 | 12 times the Theil-Sen slope of monthly LOC, divided by the median monthly LOC. |
| Months since the last commit | 0 | Whole months from the last commit to the end of the last window month (full history). |
| Commits in the last 3 months | 44 | Commits with author date in the last three window months. |
| Months with at least one commit | 34 | Window months with one or more commits. |
| Share of months with at least one commit | 0.94 | Months with a commit divided by months in the window. |
| Variation of monthly lines changed | 1.82 | Standard deviation of monthly lines added plus deleted divided by max(mean, 1). |
| Variation of monthly commit counts | 0.87 | Standard deviation of monthly commits divided by max(mean, 1). |
| Variation of monthly lines added | 1.76 | Standard deviation of monthly lines added divided by max(mean, 1). |
| Share of bug-fix commits, first half of the months | 0.32 | Mean monthly share of commits whose subject names a fix, over the first half of the months with commits. |
| Share of bug-fix commits, second half of the months | 0.38 | Mean monthly share of commits whose subject names a fix, over the second half of the months with commits. |
| Share of months with a merge commit | 0.03 | Months with at least one merge commit divided by months in the window. |
| Share of months with more than one author | 0.42 | Months with two or more distinct author e-mails divided by months in the window. |
| Share of agent-attributed commits, last 3 months | 0.00 | Mean over the last three months of the share of commits with an AI-agent co-author or bot author. |
| Relative change of LOC, first to last month | 4.61 | (LOC last - LOC first) / max(LOC first, 1). |
| LOC change per feature commit | 6557.00 | Net LOC change divided by max(feature commits, 1). |

### Module measurements

| Module | LOC | Commits | Months with changes | Lines changed | Lines changed / LOC | Months since last change |
|---|---|---|---|---|---|---|
| docs | 48 | 1 | 1 | 63 | 131 % | 6 |
| git_machete/__init__.py | 1 | 17 | 10 | 34 | 3400 % | 1 |
| git_machete/cli.py | 743 | 24 | 6 | 1810 | 244 % | 0 |
| git_machete/client.py | 2115 | 32 | 6 | 4005 | 189 % | 0 |
| git_machete/constants.py | 32 | 5 | 4 | 94 | 294 % | 1 |
| git_machete/docs.py | 576 | 14 | 7 | 866 | 150 % | 1 |
| git_machete/exceptions.py | 19 | 6 | 3 | 37 | 195 % | 4 |
| git_machete/git_operations.py | 770 | 28 | 7 | 2085 | 271 % | 1 |
| git_machete/github.py | 222 | 25 | 8 | 704 | 317 % | 0 |
| git_machete/options.py | 56 | 4 | 3 | 75 | 134 % | 5 |
| git_machete/utils.py | 189 | 11 | 7 | 376 | 199 % | 0 |

Other modules: 0 not listed.
